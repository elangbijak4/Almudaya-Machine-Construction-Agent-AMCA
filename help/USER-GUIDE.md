# AMCA User Guide

Panduan ini membawa pengguna dari problem statement atau YAML contoh sampai mesin diverifikasi dan dijalankan. AMCA adalah PoC lokal untuk DAG berbasis komponen terdaftar.

## Pilih cara kerja

| Kebutuhan | GUI | CLI |
|---|---|---|
| Membuat YAML dari bahasa alami | Form problem statement dan tombol agent | `amca_agent.cli chat` |
| Merevisi melalui percakapan berulang | Chat di halaman yang sama | Perintah `revisi ...` pada sesi interaktif |
| Menggunakan contoh | Dropdown contoh | `examples`, lalu `example ...` atau `chat --example ...` |
| Memeriksa dan meninjau DAG | Validasi dan graf pada halaman | `validate`, `graph` |
| Menjalankan mesin | Input JSON dan checkbox approval | `chat` → `run ...` → ketik `RUN` |
| Melihat hasil lama | Explorer artefak dan pemuat sesi | `sessions`, `artifacts`, `show` |

## Memulai GUI

Di PowerShell dari root repository:

```powershell
py -3.12 -m venv .venv
$Python = ".\.venv\Scripts\python.exe"
if (-not (Test-Path $Python)) { throw "Virtual environment not found. Run: py -3.12 -m venv .venv" }
& $Python -m pip install -r requirements-app.txt
$env:PYTHONPATH = "src"
& $Python -m streamlit run app.py
```

Buka [http://localhost:8501](http://localhost:8501). GUI dapat digunakan sepenuhnya lokal dengan memilih YAML contoh; API key hanya dibutuhkan saat meminta AI.

## Membuat dan memperbaiki mesin

1. Pilih `valid_parallel_analysis` di dropdown jika ingin memulai dari graph referensi, lalu muat ke editor.
2. Isi problem statement yang konkret. Contoh: “Terima satu teks, validasi teks, hitung karakter dan kata, lalu buat ringkasan.”
3. Untuk generasi AI, pilih provider, isi key di sidebar, kemudian tekan **Buat YAML dengan agent**.
4. Baca YAML dan status/verifier. Output AI tetap kandidat sampai diverifikasi.
5. Untuk mengubah hasil, ketik instruksi di chat, misalnya “Gunakan nama machine_id `text_review_v2`.” YAML baru disimpan sebagai versi baru. Periksa ulang statusnya.
6. Jika tidak memakai AI, tempel/edit YAML langsung dan pilih **Validasi YAML saat ini**.

Jangan masukkan credential atau data yang tidak boleh dikirim ke provider. Problem, chat, dan YAML terkait dikirim ke provider saat generasi/revisi AI diminta.

## Meninjau dan menjalankan

1. Pastikan hasil menunjukkan `verified`; status ini hanya menyatakan checks AMCA yang didefinisikan lolos.
2. Tinjau DAG dan JSON kandidat. DAG bercabang tetap dijalankan sequential oleh runtime saat ini.
3. Masukkan JSON object. Contoh: `{"text":"AMCA builds a graph."}`.
4. Pilih checkbox persetujuan dan klik **Jalankan mesin**.
5. Baca execution record. Unduh machine YAML, graph DOT, verification report, candidate graph, dan execution record dari artefak terkait.
6. Run dan chat tersimpan lokal di `artifacts/`.

## Menggunakan CLI

Siapkan venv dan modul:

```powershell
py -3.12 -m venv .venv
$Python = ".\.venv\Scripts\python.exe"
if (-not (Test-Path $Python)) { throw "Virtual environment not found. Run: py -3.12 -m venv .venv" }
& $Python -m pip install -r requirements-app.txt
$env:PYTHONPATH = "src"
$PY = $Python
```

Contoh tanpa AI:

```powershell
& $PY -m amca_agent.cli examples
& $PY -m amca_agent.cli example valid_parallel_analysis --output machine.yaml
& $PY -m amca_agent.cli validate machine.yaml
& $PY -m amca_agent.cli graph machine.yaml --output machine-dag.dot
& $PY -m amca.cli run machine.yaml --inputs examples/reference-input.json --output result.json
& $PY -m amca.cli report result.json
```

Perintah `python -m amca_agent.cli run machine.yaml --inputs examples/reference-input.json` juga menghasilkan execution record dan menyimpan folder bukti lengkap di `artifacts/runs/`, tetapi tidak meminta konfirmasi interaktif.

Sesi AI dan revisi:

```powershell
& $PY -m amca_agent.cli chat --provider Gemini --example valid_parallel_analysis
```

Masukkan problem statement jika diminta, kemudian key provider diminta tersembunyi. Dalam prompt `amca>` jalankan `revisi <perubahan>` untuk iterasi. `show` menampilkan YAML, `versions` menampilkan riwayat, `restore <n>` memulihkan versi lama sebagai versi baru, dan `load <path.yaml>` memuat YAML hasil edit di editor eksternal. `validate` mengulang checks, `graph` menyimpan DOT, dan `run examples/reference-input.json` meminta konfirmasi akhir. Ketik `RUN` untuk menjalankan atau teks lain untuk batal. `quit` menyimpan sesi.

Sesi yang sudah tersimpan dapat dibuka dengan `amca-agent.cli sessions`, lalu `amca-agent.cli chat --session <id>`. Run artifacts dapat dijelajahi menggunakan `artifacts` / `artifacts --show <run_id>` dan dibaca dengan `show <path>`.

## Memahami hasil

- **valid / verified:** spesifikasi bisa dibentuk dan pemeriksaan verifier yang terdefinisi lulus.
- **rejected:** spesifikasi gagal parser/schema/verifier; runtime seharusnya tidak dipanggil.
- **inconclusive:** pemeriksaan yang tersedia tidak dapat memberi keputusan konklusif; perlakukan sebagai belum mendapat izin eksekusi.
- **succeeded:** runtime selesai; output per node tercatat dalam execution record.
- **failed:** runtime berhenti saat komponen gagal; periksa node dan diagnostik pada record.

## Kapan menggunakan CLI inti

Untuk menjalankan YAML tulisan tangan tanpa instalasi Streamlit atau API AI, instal `requirements-dev.txt`, set `PYTHONPATH=src`, lalu gunakan `python -m amca.cli validate|verify|run|report`. CLI inti paling ringan, sedangkan `amca_agent.cli` menyediakan generasi, revisi, DAG, sesi, dan akses artefak yang setara fitur inti GUI.
