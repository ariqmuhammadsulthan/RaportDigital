# Catatan perubahan

[English](CHANGELOG.md) | **Bahasa Indonesia**

[← README](README.id.md)

## Belum dirilis

- Dokumentasi lengkap dalam bahasa Inggris dan Indonesia, dengan pilihan bahasa
  di setiap halaman dan tautan yang mengikuti bahasa terpilih. Cara kerja aplikasi
  tidak berubah.

## 1.1.0 — Pilihan sekolah dan kesetaraan · 2026-11-13

- Pilihan bawaan SD/SMP/SMA, dukungan setara untuk Paket A/B/C, serta nama program
  sendiri melalui konfigurasi. ID penyimpanan dan aturan kenaikan kelas tetap sama.
- Label satuan pendidikan yang umum pada editor dan rapor sekolah. Tingkatan
  kesetaraan, akhiran kelas, dan contoh mata pelajaran mengikuti pilihan yang dipakai.
- Buku lama mempertahankan mata pelajaran dan nilainya. Arsip terbit mempertahankan
  label saat diterbitkan, termasuk format kesetaraan pada arsip lama.

Untuk instalasi pendidikan kesetaraan yang sudah ada, tetapkan
`RAPOR_EDUCATION=equivalency` sebelum memperbarui. Lihat
[pengaturan program](docs/integration.id.md#pilih-jenjang-dan-program).

Pemeriksaan: 15 pengujian backend, kedua pilihan di Firefox/Chrome, keamanan
tampilan nama sendiri di Firefox, pengemasan wheel, dan pemindaian rahasia tanpa temuan.

## 1.0.0 — Template mandiri · 2026-11-13

- Paket Python yang bisa dipasang, lengkap dengan aset, template, dan skema SQL;
  tersedia perintah `raportdigital init`, `teacher`, `check`, dan `serve`.
- Penanganan web/penyimpanan dipisahkan dari aturan buku nilai. `app.py` dan format
  data terenkripsi lama tetap kompatibel.
- URL dan jalur cookie mendukung pemasangan di bawah awalan jalur. Mode hosting
  memerlukan proxy dan nama host tepercaya; mode lokal tetap memakai loopback.
- Pesan kesalahan penyiapan/penyimpanan dan API JSON lebih jelas; pengelolaan kunci
  diberi pengaman. Data terenkripsi yang tidak valid ditolak tanpa menampilkan
  rincian diagnostik kriptografi.
- Image Docker tanpa akses root, alur CI sederhana, dan skrip pengujian melalui browser.
- Panduan awal singkat; panduan guru, integrasi, dan pengelolaan terpisah; lisensi
  MIT untuk kontribusi baru serta penjelasan asal kode.
- Perbaikan salah ketik pada label rapor dan penjelasan penyimpanan otomatis,
  penerbitan, serta pemulihan revisi.

Aplikasi tetap menyediakan penyimpanan otomatis, lima revisi sebelumnya, arsip
kelas yang tidak bisa diubah, pemeriksaan salin-tempel spreadsheet, dan perpindahan
kelas berdasarkan keputusan akhir tahun. Tidak ada ketergantungan pada layanan
luar atau sinkronisasi terjadwal dengan proyek asal.

Pemeriksaan: 12 pengujian backend di Windows/Linux, alur Firefox dan Chrome,
pemasangan wheel di lingkungan bersih, serta penyiapan Docker tanpa root dan
pemeriksaan proxy HTTPS. Pengujian browser memakai data buatan melalui loopback,
bukan bukti pemasangan di server produksi. Perintah tersedia dalam
[panduan pengelolaan](docs/operations.id.md#pengujian-dan-pembaruan) dan
[pengujian browser](tools/README.id.md).
