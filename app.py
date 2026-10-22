"""AMCA local web UI: problem statement -> candidate YAML -> verification -> run."""
from __future__ import annotations

import json
import sys
import uuid
from pathlib import Path
from typing import Any

import streamlit as st

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from amca.constructor import construct
from amca.errors import AMCAError
from amca.registry import component_ids
from amca.runtime import run
from amca.scheduler import topological_order
from amca.specification import load_spec
from amca.verifier import verify_candidate
from amca_agent.artifacts import ARTIFACT_ROOT, load_chat, list_sessions, save_chat, save_run
from amca_agent.graph import to_dot
from amca_agent.provider import ProviderError, generate_yaml


st.set_page_config(page_title="AMCA Machine Builder", page_icon="🧩", layout="wide")
st.title("AMCA · Machine Builder")
st.caption("Susun kandidat pipeline DAG dari problem statement, validasi dengan AMCA, lalu tinjau dan jalankan secara eksplisit.")


def _init() -> None:
    st.session_state.setdefault("session_id", str(uuid.uuid4()))
    st.session_state.setdefault("messages", [])
    st.session_state.setdefault("versions", [])
    st.session_state.setdefault("problem", "")
    st.session_state.setdefault("machine_yaml", "")
    st.session_state.setdefault("verification", None)
    st.session_state.setdefault("candidate", None)
    st.session_state.setdefault("dot", None)
    st.session_state.setdefault("validation_error", None)
    st.session_state.setdefault("last_artifact", None)


def _validate(yaml_text: str) -> tuple[Any | None, Any | None, str | None]:
    try:
        spec = load_spec(yaml_text.encode("utf-8"))
        candidate = construct(spec)
        verification = verify_candidate(candidate)
        return candidate, verification, None
    except (AMCAError, UnicodeEncodeError) as exc:
        return None, None, getattr(exc, "message", str(exc))


def _record_version(source: str) -> None:
    text = st.session_state.machine_yaml
    candidate, verification, error = _validate(text)
    st.session_state.candidate = candidate
    st.session_state.verification = verification
    st.session_state.validation_error = error
    st.session_state.dot = to_dot(candidate) if candidate is not None and verification.status == "verified" else None
    st.session_state.versions.append({
        "yaml": text,
        "source": source,
        "validation_status": verification.status if verification else "rejected",
        "error": error or ("; ".join(r.message for r in verification.reasons) if verification and verification.status != "verified" else None),
    })
    record = verification.as_dict() if verification else {
        "report_version": "1.0", "status": "rejected", "candidate_sha256": None,
        "profile_id": "not_constructed", "checks": [], "reasons": [{"message": error}], "assumptions": [],
    }
    folder = save_run(text, record, candidate.as_dict() if candidate else None, st.session_state.dot, None,
                      verification.status if verification else "rejected")
    st.session_state.last_artifact = str(folder)
    save_chat(st.session_state.session_id, st.session_state.messages, st.session_state.versions)


_init()

with st.sidebar:
    st.header("Pengaturan agent")
    provider = st.selectbox("Provider model", ["Gemini", "xAI (Grok)", "OpenAI"])
    default_models = {"Gemini": "gemini-3.8-flash", "xAI (Grok)": "grok-4.7", "OpenAI": "gpt-4.1-mini"}
    model = st.text_input("Model", value=default_models[provider], key=f"model_{provider}")
    api_key = st.text_input("API key (hanya di memori sesi)", type="password")
    st.caption("Key tidak ditulis ke artefak. Permintaan AI dikirim ke provider yang dipilih; validasi dan runtime tetap lokal.")
    st.divider()
    st.subheader("Sesi tersimpan di komputer ini")
    sessions = list_sessions()
    if sessions:
        labels = [f"{p.parent.name} · {p.parent}" for p in sessions]
        chosen = st.selectbox("Muat sesi", [None, *range(len(sessions))], format_func=lambda x: "Sesi saat ini" if x is None else labels[x])
        if st.button("Buka sesi terpilih", disabled=chosen is None):
            data = load_chat(sessions[chosen])
            st.session_state.session_id = data["session_id"]
            st.session_state.messages = data.get("messages", [])
            st.session_state.versions = data.get("versions", [])
            if st.session_state.versions:
                st.session_state.machine_yaml = st.session_state.versions[-1]["yaml"]
                candidate, verification, error = _validate(st.session_state.machine_yaml)
                st.session_state.candidate = candidate
                st.session_state.verification = verification
                st.session_state.validation_error = error
                st.session_state.dot = to_dot(candidate) if candidate and verification.status == "verified" else None
            st.rerun()
    st.caption(f"Session ID: `{st.session_state.session_id[:8]}`")

example_files = sorted((ROOT / "examples").glob("*.yaml"))
example_map = {f"{p.stem} — {p.name}": p for p in example_files}
left, right = st.columns([1, 1])
with left:
    st.subheader("1 · Problem statement")
    selected_example = st.selectbox("Contoh YAML sebagai titik awal", ["(tanpa contoh)", *example_map])
    if st.button("Muat contoh ke editor"):
        if selected_example == "(tanpa contoh)":
            st.session_state.machine_yaml = ""
        else:
            st.session_state.machine_yaml = example_map[selected_example].read_text(encoding="utf-8")
        st.session_state.verification = None
        st.session_state.candidate = None
        st.session_state.dot = None
        st.rerun()
    st.text_area("Jelaskan mesin yang ingin dibuat", key="problem", height=130,
                 placeholder="Contoh: Buat pipeline untuk memeriksa teks, menghitung karakter dan kata, lalu merangkum hasilnya.")
    if st.button("Buat YAML dengan agent", type="primary", disabled=not st.session_state.problem.strip()):
        request = st.session_state.problem.strip()
        st.session_state.messages.append({"role": "user", "content": request})
        try:
            current = st.session_state.machine_yaml
            if not current and selected_example != "(tanpa contoh)":
                current = example_map[selected_example].read_text(encoding="utf-8")
            result = generate_yaml(provider=provider, model=model, api_key=api_key, prompt=request,
                                  history=st.session_state.messages[:-1], current_yaml=current)
            st.session_state.machine_yaml = result
            st.session_state.messages.append({"role": "assistant", "content": f"YAML versi {len(st.session_state.versions) + 1} dibuat oleh {provider}/{model}."})
            _record_version("agent")
            st.rerun()
        except ProviderError as exc:
            st.error(str(exc))
            st.session_state.messages.pop()
    st.subheader("2 · Revisi lewat chat")
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])
    revision = st.chat_input("Minta perubahan pada YAML…", key="revision_input", submit_mode="disable")
    if revision:
        request = revision.strip()
        st.session_state.messages.append({"role": "user", "content": request})
        try:
            with st.status("Meminta revisi dan memvalidasi YAML…", expanded=False):
                result = generate_yaml(provider=provider, model=model, api_key=api_key, prompt=request,
                                      history=st.session_state.messages[:-1], current_yaml=st.session_state.machine_yaml)
                st.session_state.machine_yaml = result
                candidate, verification, error = _validate(result)
                state = verification.status if verification else "rejected"
                st.session_state.messages.append({"role": "assistant", "content": f"YAML versi {len(st.session_state.versions) + 1} dibuat oleh {provider}/{model}. Hasil pemeriksaan awal: {state}."})
                _record_version("revision")
            st.rerun()
        except ProviderError as exc:
            st.error(str(exc))
            st.session_state.messages.pop()

with right:
    st.subheader("3 · Tinjau dan validasi YAML")
    st.caption("YAML hasil agent adalah kandidat. Ia tidak dijalankan otomatis.")
    st.text_area("Spesifikasi mesin YAML", key="machine_yaml", height=340)
    if st.button("Validasi YAML saat ini"):
        _record_version("manual_edit")
    if st.session_state.verification is not None:
        status = st.session_state.verification.status
        (st.success if status == "verified" else st.error)(f"Validasi AMCA: {status.upper()}")
    elif st.session_state.validation_error:
        st.error(st.session_state.validation_error)
    if st.session_state.validation_error:
        st.code(st.session_state.validation_error)
    elif st.session_state.verification and st.session_state.verification.reasons:
        for reason in st.session_state.verification.reasons:
            st.warning(f"{reason.code}: {reason.message}")
    if st.session_state.versions:
        labels = [f"v{i} · {v['source']} · {v['validation_status']}" for i, v in enumerate(st.session_state.versions, 1)]
        version_index = st.selectbox("Versi YAML", list(range(len(labels))), format_func=lambda i: labels[i], key="version_index")
        if st.button("Pulihkan versi terpilih"):
            st.session_state.machine_yaml = st.session_state.versions[version_index]["yaml"]
            st.session_state.verification = None
            st.rerun()

if st.session_state.candidate is not None and st.session_state.verification and st.session_state.verification.status == "verified":
    st.subheader("4 · Graf DAG mesin")
    st.graphviz_chart(st.session_state.dot, width="stretch", alt="Graf DAG dari spesifikasi mesin yang lolos verifikasi AMCA")
    st.download_button("Unduh graf DAG (.dot)", st.session_state.dot, file_name="machine-dag.dot", mime="text/vnd.graphviz")
    with st.expander("Candidate graph JSON"):
        st.json(st.session_state.candidate.as_dict())

st.subheader("5 · Eksekusi yang disetujui user")
if st.session_state.verification is None or st.session_state.verification.status != "verified":
    st.info("Validasi YAML hingga status `verified` untuk membuka eksekusi.")
else:
    source_nodes = [n for n in st.session_state.candidate.nodes if n.component == "input_source"]
    input_key = source_nodes[0].config["input_key"] if source_nodes else "text"
    input_json = st.text_area("Input runtime (JSON)", value=json.dumps({input_key: "AMCA builds a graph."}, ensure_ascii=False), height=85)
    approved = st.checkbox("Saya menyetujui eksekusi mesin ini")
    if st.button("Jalankan mesin", type="primary", disabled=not approved):
        try:
            inputs = json.loads(input_json)
            if type(inputs) is not dict:
                raise ValueError("Input runtime harus berupa objek JSON.")
            record = run(st.session_state.candidate, st.session_state.verification, inputs)
            folder = save_run(st.session_state.machine_yaml, st.session_state.verification.as_dict(),
                              st.session_state.candidate.as_dict(), st.session_state.dot, record,
                              record["run_status"])
            st.session_state.last_artifact = str(folder)
            st.session_state.last_execution = record
            st.rerun()
        except (AMCAError, ValueError, json.JSONDecodeError) as exc:
            st.error(f"Input JSON tidak valid: {exc}")

if "last_execution" in st.session_state:
    st.subheader("Hasil execution record")
    st.json(st.session_state.last_execution)

st.subheader("6 · Artefak tersimpan")
if st.session_state.last_artifact:
    folder = Path(st.session_state.last_artifact)
    st.caption(f"Folder artefak terakhir: `{folder}`")
    for path in sorted(folder.glob("*")):
        if path.is_file():
            mime = "application/json" if path.suffix == ".json" else "text/plain"
            st.download_button(f"Unduh {path.name}", path.read_bytes(), file_name=path.name, mime=mime, key=f"dl-{path.name}-{folder.name}")

run_root = ARTIFACT_ROOT / "runs"
if run_root.exists():
    runs = sorted((p for p in run_root.iterdir() if p.is_dir()), reverse=True)
    if runs:
        with st.expander("Jelajahi artefak siklus sebelumnya"):
            chosen_run = st.selectbox("Run tersimpan", runs, format_func=lambda p: p.name)
            for path in sorted(chosen_run.glob("*")):
                if path.is_file():
                    st.markdown(f"**{path.name}**")
                    if path.suffix == ".json":
                        try:
                            st.json(json.loads(path.read_text(encoding="utf-8")))
                        except json.JSONDecodeError:
                            st.warning("JSON artefak rusak.")
                    elif path.suffix in {".yaml", ".dot"}:
                        st.code(path.read_text(encoding="utf-8"), language="yaml" if path.suffix == ".yaml" else "dot")
                    st.download_button(f"Unduh {path.name}", path.read_bytes(), file_name=path.name,
                                       mime="application/json" if path.suffix == ".json" else "text/plain",
                                       key=f"history-{chosen_run.name}-{path.name}")

st.caption(f"Komponen allowlist saat ini: {', '.join(component_ids())}. Eksekusi lokal, berurutan, dan hanya melalui runtime AMCA.")
