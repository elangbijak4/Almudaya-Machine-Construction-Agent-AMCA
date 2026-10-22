# AMCA User Tutorial

Tutorial ini mengeksekusi graph referensi end-to-end melalui GUI dan CLI. Jalur lokal contoh tidak memakai API key. Tutorial kedua menunjukkan cara meminta YAML AI dan merevisinya.

## A. Tutorial GUI: contoh → verifikasi → run

1. Pasang dependensi dan jalankan UI:

   ```powershell
   py -3.12 -m venv .venv
   .\.venv\Scripts\python.exe -m pip install -r requirements-app.txt
   $env:PYTHONPATH = "src"
   .\.venv\Scripts\python.exe -m streamlit run app.py
   ```

2. Buka [http://localhost:8501](http://localhost:8501).
3. Pada dropdown contoh pilih `valid_parallel_analysis`, lalu klik **Muat contoh ke editor**.
4. Klik **Validasi YAML saat ini**. Periksa status `VERIFIED`, lalu tinjau graf DAG.
5. Pertahankan contoh input `{"text":"AMCA builds a graph."}` atau masukkan JSON object lain.
6. Pilih **Saya menyetujui eksekusi mesin ini**, lalu klik **Jalankan mesin**.
7. Periksa execution record. Untuk contoh bawaan, ringkasan memuat `characters=20; words=4`.
8. Di bagian artefak, unduh file JSON/YAML/DOT. Sesi dan run lokal berada di `artifacts/`.

## B. Tutorial CLI: eksekusi yang sama

Jalankan dari PowerShell root proyek:

```powershell
py -3.12 -m venv .venv
\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
$env:PYTHONPATH = "src"
$PY = ".\.venv\Scripts\python.exe"

& $PY -m amca_agent.cli examples
& $PY -m amca_agent.cli example valid_parallel_analysis --output machine.yaml
& $PY -m amca_agent.cli validate machine.yaml
& $PY -m amca_agent.cli graph machine.yaml --output machine-dag.dot
& $PY -m amca.cli run machine.yaml --inputs examples/reference-input.json --output execution-record.json
& $PY -m amca.cli report execution-record.json
```

CLI inti `run` langsung menjalankan setelah verifikasi lolos; gunakan hanya jika Anda memang bermaksud menjalankan file dan input yang diberikan. Workflow agent interaktif dengan konfirmasi eksplisit:

```powershell
& $PY -m amca_agent.cli chat --example valid_parallel_analysis
```

Di prompt, ketik `show`, `validate`, `graph`, lalu `run examples/reference-input.json`. Pastikan file dan graph benar; ketika diminta persetujuan ketik `RUN`. Output harus menyertakan `characters=20; words=4`. Gunakan `versions` untuk riwayat, `restore 1` untuk memulihkan versi pertama, dan `load machine.yaml` untuk menerima edit dari editor teks. `quit` menyimpan sesi.

## C. Tutorial AI: membuat dan merevisi YAML

AI memerlukan akun/key provider dan koneksi internet. Prompt, chat terbaru, dan YAML saat ini dikirim kepada provider pilihan.

1. Di GUI pilih Gemini, Grok, atau OpenAI, isi model dan API key di sidebar.
2. Tulis problem statement berisi tujuan, input yang tersedia, langkah analisis, dan bentuk output yang diinginkan.
3. Klik **Buat YAML dengan agent**. Baca YAML hasil model dan status validasi.
4. Ketik perubahan spesifik ke chat, misalnya “Gunakan teks input `review_text` dan jangan ubah perhitungan.” Revisi menghasilkan versi berikutnya.
5. Periksa kembali YAML, status dan graph; jika invalid, arahkan revisi atau edit YAML manual.
6. Jalankan hanya setelah status verified dan review manusia. AI tidak mengeksekusi kodenya sendiri; runtime tetap memilih implementasi dari allowlist.

Padanan CLI:

```powershell
& $PY -m amca_agent.cli chat --provider Gemini --example valid_parallel_analysis
```

CLI meminta problem statement jika belum tersedia, lalu meminta API key secara tersembunyi. Pada sesi interaktif, kirim `revisi Buat machine_id menjadi text_review_v2` dan lanjutkan siklus. Gunakan `sessions` untuk melihat sesi dan `chat --session <id>` untuk melanjutkan.

## D. Tutorial penolakan graph invalid

Jalankan validator pada contoh yang sengaja salah:

```powershell
& $PY -m amca_agent.cli validate examples/invalid_missing_dependency.yaml
```

Hasil nonzero dan diagnostik menunjukkan masalah struktur/verifikasi. Jangan jalankan YAML yang ditolak. Perbaiki dependency melalui editor atau minta AI revisi, simpan YAML baru, lalu validasi lagi.

## E. Menjelajahi bukti

```powershell
& $PY -m amca_agent.cli sessions
& $PY -m amca_agent.cli artifacts
```

Untuk run dari chat, cari `run_id` pada daftar artifacts, lalu:

```powershell
& $PY -m amca_agent.cli artifacts --show <run_id>
& $PY -m amca_agent.cli show artifacts/runs/<run_id>/verification-report.json
& $PY -m amca_agent.cli show artifacts/runs/<run_id>/execution-record.json
```

Gunakan `dot -Tpng machine-dag.dot -o machine-dag.png` bila program Graphviz tersedia. Artefak disimpan lokal dan chat dapat mencakup prompt/data input, jadi jangan membagikannya tanpa meninjau isinya.

## Hasil dan batas tutorial

Tutorial ini membuktikan penggunaan implementasi lokal dengan YAML contoh yang sudah ada. Bagian generasi AI hanya dapat diuji ketika pengguna menyediakan credential provider; contoh ini tidak membuktikan kualitas sintesis atau kebenaran semantik semua graph. Graph cabang/join menunjukkan bentuk DAG nonlinier, tetapi runtime masih mengeksekusi tiap node secara berurutan.
