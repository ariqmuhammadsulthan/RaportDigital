# Rapor Digital

[English](README.md) | **Bahasa Indonesia**

Template aplikasi buku nilai untuk satuan pendidikan di Indonesia. Guru bisa
mengisi atau menempelkan nilai, memeriksa data setiap kelas, lalu mencetak rapor
ukuran A4. Aplikasi menggunakan Flask, SQLite, dan JavaScript biasa, tanpa proses
build frontend, CDN, atau akun layanan luar.
Antarmuka aplikasi menggunakan bahasa Indonesia.

Jalankan di komputer sendiri, pasang sebagai layanan bersama aplikasi lain, atau
hubungkan editornya ke backend Anda. Template ini adalah dasar aplikasi yang
Anda kelola sendiri. Proyek ini tidak menyediakan hosting atau menjanjikan
pembaruan berkelanjutan.
Periksa contoh mata pelajaran dan format rapor sebelum memakai data siswa asli.

Gunakan pilihan bawaan **SD, SMP, SMA IPA dan SMA IPS**, beralih ke **Paket A/B/C**,
atau tentukan nama program sendiri. [Pengaturan program](docs/integration.id.md#pilih-jenjang-dan-program)
mengubah nama pada menu dan rapor tanpa mengganti ID buku atau memindahkan nilai.

## Jalankan di komputer sendiri

Siapkan Python 3.11 atau yang lebih baru. Unduh atau clone repositori ini,
buka foldernya, lalu jalankan:

**Windows — Command Prompt (CMD)**

```bat
python -m venv .venv
.venv\Scripts\python -m pip install -e .
.venv\Scripts\raportdigital init
.venv\Scripts\raportdigital teacher
.venv\Scripts\raportdigital serve --local
```

**macOS / Linux**

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -e .
.venv/bin/raportdigital init
.venv/bin/raportdigital teacher
.venv/bin/raportdigital serve --local
```

Buka [127.0.0.1:8765](http://127.0.0.1:8765). Buat akun saat diminta; tidak ada
kata sandi bawaan. Data dan kunci enkripsinya disimpan di luar folder kode,
yaitu `~/.raportdigital`. Hentikan aplikasi dengan Ctrl+C.

## Pilih panduan

| Keperluan | Panduan |
|---|---|
| Mengisi nilai dan mencetak rapor | [Panduan guru](docs/using.id.md) |
| Menyesuaikan kode atau menghubungkan backend lain | [Integrasi](docs/integration.id.md) |
| Memasang di server, mencadangkan, menguji, atau memperbarui | [Pengelolaan aplikasi](docs/operations.id.md) |
| Memahami asal kode dan izin penggunaannya | [Cakupan lisensi](docs/origins.id.md) |
| Melihat perubahan template | [Catatan perubahan](CHANGELOG.id.md) |

Aplikasi menyediakan akun guru terpisah, penyimpanan otomatis, lima revisi buku
sebelumnya, arsip terbit yang tidak bisa diubah, serta penyiapan daftar siswa untuk
tahun berikutnya. Data Excel dimasukkan dengan salin-tempel, bukan unggahan berkas
`.xlsx`. SSO, kelas yang dikelola bersama, dan PDF bertanda tangan digital belum
tersedia.

Pengembangan aplikasi dan template yang dibuat di fork ini [berlisensi MIT](LICENSE).
Sebagian editor dan tata letak rapor berasal dari proyek asal yang belum menyatakan
lisensinya. Batas cakupannya dijelaskan dalam [catatan asal kode](docs/origins.id.md).
