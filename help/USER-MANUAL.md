# AMCA User Manual (referensi teknis)

**Versi:** sesuai source tree AMCA saat ini · **Bahasa:** Indonesia

Manual ini menjelaskan perilaku yang tersedia pada PoC, bukan keseluruhan teori white paper. AMCA menghasilkan spesifikasi mesin YAML yang dijalankan oleh runtime tetap; sistem tidak mengompilasi mesin baru atau membuat kode komponen baru.

## 1. Batas sistem dan keamanan

- YAML dan input JSON dianggap data tidak tepercaya. Loader YAML aman menolak alias, key duplikat, root selain mapping, dan spesifikasi lebih dari 65.536 byte.
- Mesin hanya dapat menggunakan komponen pada allowlist: `input_source`, `validate_text`, `analysis_a`, `analysis_b`, `aggregate_results`, `generate_report`.
- Tidak ada import modul, perintah OS, Python dari spesifikasi, atau plugin arbitrer.
- Alur AI bersifat opsional. Provider Gemini, xAI (Grok), dan OpenAI mengirim problem statement, riwayat chat terbaru, serta YAML saat ini ke layanan provider ketika generasi/revisi diminta. Jangan kirim data rahasia.
- API key dimasukkan melalui prompt tersembunyi di CLI (`getpass`) atau field password GUI dan tidak dimasukkan ke artefak. CLI dapat membaca `AMCA_API_KEY` dari environment; hindari menyimpannya permanen di profil shell.
- Verifikasi `verified` berarti pemeriksaan terdefinisi lulus; bukan bukti formal kebenaran semantik, keamanan, atau bahwa mesin memenuhi maksud bahasa alami.
- Run hanya terjadi setelah verifikasi berhasil. CLI meminta ketikan persis `RUN`; GUI meminta checkbox persetujuan. Komponen cabang dieksekusi berurutan dengan urutan deterministik, bukan paralel.

## 2. Persyaratan dan pemasangan

Gunakan Windows PowerShell dari root repository dan CPython 3.12+. CLI dasar memakai `requirements-dev.txt`; GUI memakai `requirements-app.txt`.

```powershell
py -3.12 -m venv .venv
$Python = ".\.venv\Scripts\python.exe"
if (-not (Test-Path $Python)) { throw "Virtual environment not found. Run: py -3.12 -m venv .venv" }
& $Python -m pip install -r requirements-app.txt
$env:PYTHONPATH = "src"
```

Untuk hanya CLI inti, ganti `requirements-app.txt` dengan `requirements-dev.txt`. Jalankan GUI menggunakan `& $Python -m streamlit run app.py`, lalu buka `http://localhost:8501`. Untuk bantuan CLI agent, jalankan `& $Python -m amca_agent.cli --help`.

## 3. Model data dan kontrak

File YAML memiliki `schema_version`, `machine_id`, `nodes`, dan `edges`. Setiap node menyatakan `id`, `component`, dan `config`; setiap edge menghubungkan node dan port melalui `from`, `out`, `to`, `in`. Schema dan daftar port yang berlaku dapat diperiksa di `schemas/` dan implementasi registry di `src/amca/registry.py`.

| Komponen | Input/output inti | Fungsi |
|---|---|---|
| `input_source` | output `text:string`; config `input_key` | Membaca string bernama dari objek input JSON. |
| `validate_text` | `text:string → text:string` | Menolak teks kosong/whitespace dan mengembalikan teks yang dinormalisasi. |
| `analysis_a` | `text:string → finding:object` | Menghitung karakter. |
| `analysis_b` | `text:string → finding:object` | Menghitung kata. |
| `aggregate_results` | `finding_a:object`, `finding_b:object → summary:string` | Menggabungkan hasil dua analisis. |
| `generate_report` | `summary:string → report:object` | Membungkus ringkasan menjadi report. |

`examples/valid_parallel_analysis.yaml` adalah DAG cabang/join. Nama contoh “parallel” menunjukkan topologi cabang; runtime sekarang tetap sequential. Input contoh `examples/reference-input.json` menghasilkan summary `characters=20; words=4` untuk teks saat ini.

## 4. Siklus aplikasi

1. Pilih contoh atau tulis problem statement.
2. Opsional: minta provider membuat YAML, lalu tinjau hasilnya. Untuk revisi, berikan instruksi lanjutan di chat yang sama. Setiap hasil disimpan sebagai versi tersendiri.
3. Edit YAML langsung pada GUI atau editor teks. CLI mengizinkan file YAML apa pun yang diberikan pengguna.
4. Validasi memuat schema, membentuk candidate graph, lalu menjalankan pemeriksaan verifier. Siklus menyimpan diagnostik meski spesifikasi ditolak.
5. DAG dapat divisualisasikan setelah verified; CLI mengekspor sumber Graphviz DOT.
6. Sediakan objek JSON sebagai input runtime, tinjau YAML/graf, dan nyatakan persetujuan run secara eksplisit.
7. Periksa execution record serta artefak lokal.

## 5. GUI

Mulai dengan `streamlit run app.py`. Di sidebar pilih provider/model dan masukkan API key bila perlu. Field API key tidak diperlukan untuk alur contoh, validasi lokal, graf, atau run lokal.

Area kiri memuat contoh, problem statement, tombol generasi, dan riwayat revisi. Area kanan menampilkan/mengedit YAML, hasil validasi, alasan penolakan, dan pilihan memulihkan versi. Setelah status `verified`, GUI menampilkan graf serta input JSON. Tombol **Jalankan mesin** aktif setelah checkbox persetujuan dipilih. Bagian artefak menyediakan pratinjau dan unduhan file run; sesi lokal dapat dimuat kembali lewat sidebar.

Simpan sesi chat atau artefak lokal dengan memperhatikan bahwa prompt dan data dapat tersimpan lokal. Folder `artifacts/` dikecualikan Git.

## 6. CLI lengkap

Atur jalur modul satu kali:

```powershell
$env:PYTHONPATH = "src"
$PY = ".\.venv\Scripts\python.exe"
if (-not (Test-Path $PY)) { throw "Virtual environment not found. Run: py -3.12 -m venv .venv" }
```

### YAML dan validasi

```powershell
& $PY -m amca_agent.cli examples
& $PY -m amca_agent.cli example valid_parallel_analysis --output machine.yaml
& $PY -m amca_agent.cli validate machine.yaml
```

`validate` juga membangun candidate dan melaporkan verifikasi; exit code `0` berarti verified, `1` hasil verifikasi tidak lulus, dan `2` kesalahan input/operasional.

### Graf dan run satu-perintah

```powershell
& $PY -m amca_agent.cli graph machine.yaml --output machine-dag.dot
& $PY -m amca.cli run machine.yaml --inputs examples/reference-input.json --output execution-record.json
& $PY -m amca.cli report execution-record.json
```

Subcommand noninteraktif `amca-agent run` dan `amca.cli run` memverifikasi sebelum runtime, tetapi tidak menampilkan prompt persetujuan; jalankan hanya setelah Anda meninjau file dan memang bermaksud mengeksekusinya. `amca-agent run` menyimpan folder bukti di `artifacts/runs/`; CLI inti mengeluarkan report JSON ke stdout atau `--output`. Untuk alur dengan gerbang persetujuan, gunakan sesi `amca-agent chat` lalu perintah `run <input.json>` di dalam chat; sesi itu meminta ketikan persis `RUN`. CLI inti `verify` juga tersedia.

### Generasi dan chat revisi

```powershell
& $PY -m amca_agent.cli chat --provider Gemini --example valid_parallel_analysis
& $PY -m amca_agent.cli chat --provider OpenAI --model gpt-4.1-mini
```

API key diminta tersembunyi setiap kali permintaan AI dibuat (kecuali `AMCA_API_KEY` sudah tersedia pada environment). Di dalam sesi: `show`, `validate`, `revisi <instruksi>`, `graph [file.dot]`, `run <input.json>`, `quit`. Saat `run`, ketik `RUN` untuk menyetujui; input selain itu membatalkan.

Daftar sesi: `python -m amca_agent.cli sessions`. Buka kembali: `python -m amca_agent.cli chat --session <id>` (ID adalah nama folder sesi yang ditampilkan). Dalam chat, `versions` menampilkan riwayat, `restore <nomor>` memulihkan YAML sebagai versi baru, dan `load <path.yaml>` memasukkan YAML yang telah diedit melalui editor eksternal sebagai versi baru. Daftar run: `python -m amca_agent.cli artifacts`; lihat file: `python -m amca_agent.cli artifacts --show <run_id>`; tampilkan file: `python -m amca_agent.cli show <path>`.

### CLI lama

`python -m amca.cli validate <spec>`, `verify <spec>`, `run <spec> --inputs <json> [--output <json>]`, dan `report <json>` tetap tersedia. CLI inti menerima file YAML buatan pengguna dan tidak membutuhkan provider AI atau Streamlit.

## 7. Artefak

GUI dan workflow agent menyimpan `artifacts/runs/<run_id>/` yang dapat berisi `machine.yaml`, `candidate-graph.json`, `machine-dag.dot`, `verification-report.json`, `execution-record.json`, serta `manifest.json`. File eksekusi hanya muncul setelah run. Chat disimpan pada `artifacts/agent_sessions/<session_id>/` sebagai `session.json` dan `spec-vNNN.yaml`. CLI inti `amca.cli --output` menyimpan report JSON sesuai output yang diminta; CLI inti tidak menyimpan folder run lengkap otomatis.

DOT adalah source graf. Untuk gambar PNG jika Graphviz sudah terpasang:

```powershell
dot -Tpng machine-dag.dot -o machine-dag.png
```

## 8. Diagnosis umum

| Gejala | Tindakan |
|---|---|
| `No module named amca` atau `amca_agent` | Dari root repo set `$env:PYTHONPATH="src"`, gunakan interpreter venv yang sama. |
| API key belum diisi / API HTTP error | Pastikan provider, model dan key cocok; koneksi provider eksternal diperlukan hanya untuk generasi. Respons error sengaja tidak menampilkan rahasia. |
| YAML rejected | Periksa alasan/verifier, ID, edge, port, dan seluruh input wajib. Coba revisi atau edit YAML dan validasi ulang. |
| Run ditolak | Jangan jalankan spesifikasi kecuali `verified`; pastikan JSON root object dan nilai sesuai port input. |
| Graphviz tak menampilkan PNG | File `.dot` tetap merupakan artefak; instal Graphviz hanya jika konversi gambar diperlukan. |
| Sesi/artefak tidak ada | Aplikasi menyimpan relatif terhadap root repo, bukan lokasi terminal saat ini. Periksa `artifacts/`. |

## 9. Batasan yang diketahui

Provider AI memerlukan koneksi dan credential pengguna serta tidak deterministik. Belum ada jaminan AI menghasilkan graph yang memenuhi maksud; verifier bersifat struktural dan agent tidak memperbaiki YAML otomatis dari diagnostik tanpa permintaan user. Runtime hanya memuat enam komponen tetap, berjalan lokal sequential, dan tidak menyediakan autentikasi web, isolasi OS, paralelisme, conditional flow, retry/persistence workflow, meta-machine, atau pembuktian formal. Lihat README dan white-paper mapping untuk pembatasan riset lebih luas.
