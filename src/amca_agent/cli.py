"""CLI for the optional AMCA YAML-authoring agent and local artifacts."""
from __future__ import annotations

import argparse
import getpass
import json
import os
import sys
import uuid
from pathlib import Path

from amca.constructor import construct
from amca.errors import AMCAError
from amca.runtime import run
from amca.specification import load_spec
from amca.verifier import verify_candidate
from amca_agent.artifacts import ARTIFACT_ROOT, ROOT, list_sessions, load_chat, save_chat, save_run
from amca_agent.graph import to_dot
from amca_agent.provider import ProviderError, generate_yaml


DEFAULT_MODELS = {"Gemini": "gemini-3.8-flash", "xAI (Grok)": "grok-4.7", "OpenAI": "gpt-4.1-mini"}


def _check(text: str):
    spec = load_spec(text.encode("utf-8"))
    candidate = construct(spec)
    verification = verify_candidate(candidate)
    return candidate, verification


def _json(value, output: str | None = None) -> None:
    rendered = json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    if output:
        Path(output).write_text(rendered, encoding="utf-8")
    else:
        sys.stdout.write(rendered)


def _yaml(value: str, output: str | None = None) -> None:
    if output:
        Path(output).write_text(value.rstrip() + "\n", encoding="utf-8")
    else:
        print(value)


def _examples() -> list[Path]:
    return sorted((ROOT / "examples").glob("*.yaml"))


def _example(name: str) -> Path:
    matches = [p for p in _examples() if p.name == name or p.stem == name]
    if len(matches) != 1:
        raise ValueError(f"Contoh tidak ditemukan atau ambigu: {name}")
    return matches[0]


def _rejected(message: str) -> dict:
    return {"report_version": "1.0", "status": "rejected", "candidate_sha256": None,
            "profile_id": "not_constructed", "checks": [], "reasons": [{"message": message}], "assumptions": []}


def _record(session_id: str, messages: list[dict], versions: list[dict], source: str) -> tuple[object | None, object | None, str | None]:
    text = versions[-1]["yaml"]
    try:
        candidate, verification = _check(text)
        error = None
        dot = to_dot(candidate) if verification.status == "verified" else None
        record = verification.as_dict()
        status = verification.status
    except AMCAError as exc:
        candidate = verification = dot = None
        error = getattr(exc, "message", str(exc))
        record, status = _rejected(error), "rejected"
    versions[-1].update({"source": source, "validation_status": status, "error": error})
    save_run(text, record, candidate.as_dict() if candidate else None, dot, None, status)
    save_chat(session_id, messages, versions)
    return candidate, verification, error


def _provider_args(args) -> tuple[str, str, str]:
    provider = args.provider
    model = args.model or DEFAULT_MODELS[provider]
    key = os.environ.get("AMCA_API_KEY", "")
    if not key:
        key = getpass.getpass(f"API key {provider} (tidak disimpan): ")
    return provider, model, key


def _generate(args, history: list[dict], current: str) -> str:
    provider, model, key = _provider_args(args)
    return generate_yaml(provider=provider, model=model, api_key=key, prompt=args.problem,
                         history=history, current_yaml=current)


def _chat(args) -> int:
    if args.session:
        path = ARTIFACT_ROOT / "agent_sessions" / args.session / "session.json"
        data = load_chat(path)
        session_id, messages, versions = data["session_id"], data.get("messages", []), data.get("versions", [])
        current = versions[-1]["yaml"] if versions else ""
        print(f"Sesi {session_id} dimuat; YAML versi {len(versions)}.")
    else:
        session_id, messages, versions, current = str(uuid.uuid4()), [], [], ""
        if args.example:
            current = _example(args.example).read_text(encoding="utf-8")
            print(f"Contoh dimuat: {args.example}")
        args.problem = args.problem or input("Problem statement: ").strip()
        if not args.problem:
            raise ValueError("Problem statement tidak boleh kosong.")
        messages.append({"role": "user", "content": args.problem})
        current = _generate(args, messages[:-1], current)
        messages.append({"role": "assistant", "content": "YAML kandidat dibuat."})
        versions.append({"yaml": current})
        candidate, verification, error = _record(session_id, messages, versions, "agent")
        print(f"Validasi: {verification.status if verification else 'rejected'}" + (f" — {error}" if error else ""))
        _yaml(current)

    print("Perintah sesi: revisi <permintaan>, show, load <yaml>, versions, restore <nomor>, validate, graph [FILE.dot], run <input.json>, quit")
    while True:
        try:
            line = input("amca> ").strip()
        except EOFError:
            line = "quit"
        if line in {"quit", "exit", "q"}:
            save_chat(session_id, messages, versions)
            print(f"Sesi disimpan: artifacts/agent_sessions/{session_id}/session.json")
            return 0
        if line == "show":
            print(current or "(belum ada YAML)")
        elif line == "versions":
            for index, version in enumerate(versions, 1):
                print(f"v{index}: {version.get('source', 'unknown')} · {version.get('validation_status', 'unchecked')}"
                      + (f" · {version['error']}" if version.get("error") else ""))
        elif line.startswith("restore "):
            try:
                index = int(line.split(maxsplit=1)[1])
                if not 1 <= index <= len(versions):
                    raise ValueError("Nomor versi tidak tersedia.")
                current = versions[index - 1]["yaml"]
                versions.append({"yaml": current})
                candidate, verification, error = _record(session_id, messages, versions, "restore")
                print(f"Versi v{index} dipulihkan sebagai versi baru. Validasi: {verification.status if verification else 'rejected'}"
                      + (f" — {error}" if error else ""))
            except (ValueError, IndexError) as exc:
                print(f"Tidak dapat memulihkan versi: {exc}", file=sys.stderr)
        elif line.startswith("load "):
            try:
                current = Path(line.split(maxsplit=1)[1]).read_text(encoding="utf-8")
                versions.append({"yaml": current})
                candidate, verification, error = _record(session_id, messages, versions, "manual_edit")
                print(f"YAML dimuat sebagai versi v{len(versions)}. Validasi: {verification.status if verification else 'rejected'}"
                      + (f" — {error}" if error else ""))
            except (OSError, AMCAError) as exc:
                print(f"YAML tidak dapat dimuat: {getattr(exc, 'message', str(exc))}", file=sys.stderr)
        elif line == "validate":
            try:
                candidate, verification = _check(current)
                print(json.dumps(verification.as_dict(), ensure_ascii=False, indent=2))
            except AMCAError as exc:
                candidate, verification = None, None
                print(f"REJECTED: {getattr(exc, 'message', str(exc))}", file=sys.stderr)
        elif line.startswith("revisi ") or line.startswith("revise "):
            prompt = line.split(" ", 1)[1].strip()
            if not prompt:
                print("Isi permintaan revisi setelah perintah revisi.", file=sys.stderr)
                continue
            messages.append({"role": "user", "content": prompt})
            args.problem = prompt
            try:
                current = _generate(args, messages[:-1], current)
                messages.append({"role": "assistant", "content": f"YAML versi {len(versions)+1} dibuat."})
                versions.append({"yaml": current})
                candidate, verification, error = _record(session_id, messages, versions, "revision")
                print(f"Validasi: {verification.status if verification else 'rejected'}" + (f" — {error}" if error else ""))
                _yaml(current)
            except ProviderError as exc:
                messages.pop()
                print(str(exc), file=sys.stderr)
        elif line.startswith("graph"):
            parts = line.split(maxsplit=1)
            target = Path(parts[1]) if len(parts) > 1 else ARTIFACT_ROOT / "machine-dag.dot"
            try:
                candidate, verification = _check(current)
                if verification.status != "verified":
                    raise ValueError("Graf hanya dibuat untuk spesifikasi berstatus verified.")
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(to_dot(candidate) + "\n", encoding="utf-8")
                print(f"DAG tersimpan: {target}")
            except (AMCAError, ValueError, OSError) as exc:
                print(f"Tidak dapat membuat DAG: {getattr(exc, 'message', str(exc))}", file=sys.stderr)
        elif line.startswith("run "):
            input_path = Path(line.split(maxsplit=1)[1])
            try:
                candidate, verification = _check(current)
                if verification.status != "verified":
                    raise ValueError("Spesifikasi harus lolos verifikasi sebelum runtime.")
                raw = json.loads(input_path.read_text(encoding="utf-8"))
                if type(raw) is not dict:
                    raise ValueError("Input runtime harus berupa objek JSON.")
                print("Mesin siap dieksekusi. Ketik RUN untuk menyetujui; selain itu dibatalkan.")
                if input("Persetujuan: ").strip() != "RUN":
                    print("Eksekusi dibatalkan.")
                    continue
                execution = run(candidate, verification, raw)
                folder = save_run(current, verification.as_dict(), candidate.as_dict(), to_dot(candidate),
                                  execution, execution["run_status"])
                print(json.dumps(execution, ensure_ascii=False, indent=2))
                print(f"Artefak: {folder}")
            except (AMCAError, OSError, ValueError, json.JSONDecodeError) as exc:
                print(f"Eksekusi ditolak/gagal: {getattr(exc, 'message', str(exc))}", file=sys.stderr)
        elif line:
            print("Perintah tidak dikenal. Ketik show, load, versions, restore, validate, revisi, graph, run, atau quit.")


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="amca-agent", description="Author YAML, validate, inspect DAGs, and run AMCA locally.")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("examples", help="list example YAML specifications")
    example = sub.add_parser("example", help="copy an example YAML")
    example.add_argument("name"); example.add_argument("--output")
    validate = sub.add_parser("validate", help="validate and verify YAML without running")
    validate.add_argument("spec"); validate.add_argument("--output")
    graph = sub.add_parser("graph", help="write Graphviz DOT for a verified YAML")
    graph.add_argument("spec"); graph.add_argument("--output", required=True)
    execute = sub.add_parser("run", help="verify and run YAML with JSON input")
    execute.add_argument("spec"); execute.add_argument("--inputs", required=True); execute.add_argument("--output")
    sessions = sub.add_parser("sessions", help="list saved authoring sessions")
    artifacts = sub.add_parser("artifacts", help="list saved run artifact folders")
    artifacts.add_argument("--show", help="show files in a run folder by run ID")
    show = sub.add_parser("show", help="print a saved artifact file")
    show.add_argument("path")
    chat = sub.add_parser("chat", help="interactive author/revise/validate/graph/run workflow")
    chat.add_argument("--problem"); chat.add_argument("--example"); chat.add_argument("--session")
    chat.add_argument("--provider", choices=DEFAULT_MODELS, default="Gemini"); chat.add_argument("--model")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.command == "examples":
            for path in _examples(): print(path.name)
        elif args.command == "example":
            _yaml(_example(args.name).read_text(encoding="utf-8"), args.output)
        elif args.command == "validate":
            candidate, verification = _check(Path(args.spec).read_text(encoding="utf-8"))
            _json({"status": verification.status, "machine_id": candidate.machine_id,
                   "candidate": candidate.as_dict(), "verification": verification.as_dict()}, args.output)
            return 0 if verification.status == "verified" else 1
        elif args.command == "graph":
            candidate, verification = _check(Path(args.spec).read_text(encoding="utf-8"))
            if verification.status != "verified": raise ValueError("Spesifikasi tidak berstatus verified.")
            Path(args.output).write_text(to_dot(candidate) + "\n", encoding="utf-8")
            print(args.output)
        elif args.command == "run":
            candidate, verification = _check(Path(args.spec).read_text(encoding="utf-8"))
            if verification.status != "verified": raise ValueError("Spesifikasi tidak berstatus verified.")
            inputs = json.loads(Path(args.inputs).read_text(encoding="utf-8"))
            if type(inputs) is not dict: raise ValueError("Input runtime harus berupa objek JSON.")
            record = run(candidate, verification, inputs)
            _json(record, args.output)
            folder = save_run(Path(args.spec).read_text(encoding="utf-8"), verification.as_dict(),
                              candidate.as_dict(), to_dot(candidate), record, record["run_status"])
            print(f"Artefak: {folder}", file=sys.stderr)
            return 0 if record["run_status"] == "succeeded" else 1
        elif args.command == "sessions":
            for path in list_sessions(): print(f"{path.parent.name}\t{path}")
        elif args.command == "artifacts":
            root = ARTIFACT_ROOT / "runs"
            if args.show:
                target = root / args.show
                for file in sorted(target.glob("*")):
                    if file.is_file(): print(file)
            elif root.exists():
                for folder in sorted((p for p in root.iterdir() if p.is_dir()), reverse=True): print(folder.name)
        elif args.command == "show":
            target = Path(args.path)
            if target.suffix == ".json": print(json.dumps(json.loads(target.read_text(encoding="utf-8")), ensure_ascii=False, indent=2))
            else: print(target.read_text(encoding="utf-8"))
        elif args.command == "chat": return _chat(args)
    except (AMCAError, ProviderError, OSError, ValueError, TypeError, json.JSONDecodeError) as exc:
        print(f"amca-agent: {getattr(exc, 'message', str(exc))}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
