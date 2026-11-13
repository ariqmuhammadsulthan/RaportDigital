# Pengujian melalui browser

[English](README.md) | **Bahasa Indonesia**

[← README](../README.id.md) · [Pengelolaan aplikasi](../docs/operations.id.md)

Pasang Playwright beserta browser-nya di folder sementara di luar repositori,
atau gunakan instalasi yang sudah ada. Perangkat pengujian browser tidak menjadi
bagian dari aplikasi. Dari folder utama repositori, jalankan di CMD:

```bat
set "PYTHON_BIN=%CD%\.venv\Scripts\python.exe"
set "RAPOR_PLAYWRIGHT=C:\path\to\node_modules\playwright"
set "RAPOR_EDUCATION=school"
set "RAPOR_BROWSER=firefox"
node tools\browser_check.cjs
set "RAPOR_EDUCATION=equivalency"
node tools\browser_check.cjs
set "RAPOR_EDUCATION=school"
set "RAPOR_BROWSER=chromium"
node tools\browser_check.cjs
set "RAPOR_EDUCATION=equivalency"
node tools\browser_check.cjs
set "RAPOR_EDUCATION="
```

`RAPOR_CHROMIUM` bisa diisi dengan lokasi berkas program Chrome yang sudah
terpasang. Tetapkan `PLAYWRIGHT_BROWSERS_PATH` jika folder unduhan browser tidak
memakai lokasi bawaan.

Skrip pengujian menjalankan aplikasi melalui port loopback sementara di jalur
`/grades`, dengan basis data SQLite sementara dan kata sandi akun uji yang dibuat
otomatis. Pemeriksaan mencakup masuk, nama/sampul/isian bawaan semua program,
salin-tempel Excel, penyimpanan dan pemuatan ulang, pratinjau ukuran ponsel,
penerbitan arsip, mode cetak, serta keluar. Setelah selesai, skrip menutup browser
dan server lalu menghapus data sementaranya. Pengujian tidak memakai data guru
asli, layanan produksi, atau penyedia login luar.

Uji setiap browser dengan pilihan `school` (bawaan) dan `equivalency`. Anda juga
bisa memakai berkas `RAPOR_PROGRAM_NAMES` untuk memeriksa nama sendiri dan
memastikan nama tersebut ditampilkan dengan aman.
