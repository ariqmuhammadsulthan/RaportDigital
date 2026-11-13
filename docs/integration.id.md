# Menyesuaikan dan mengintegrasikan aplikasi

[English](integration.md) | **Bahasa Indonesia**

[← README](../README.id.md) · [Pengelolaan aplikasi](operations.id.md)

Backend bawaan menggunakan Python/Flask. Jika memakai stack lain, Anda bisa
menjalankannya sebagai layanan terpisah di belakang reverse proxy, atau membuat
backend yang mengikuti kontrak HTTP di bawah. Integrasi ke framework lain tetap
perlu penyesuaian. Gunakan origin yang sama untuk editor dan API; cookie lintas
origin, CORS, dan SSO memerlukan rancangan autentikasi tersendiri.

## Peta kode

| Berkas | Tanggung jawab |
|---|---|
| `raportdigital/web.py` | Pembuatan aplikasi, akun, sesi, data terenkripsi, rute HTTP |
| `raportdigital/domain.py` | ID program, kelas, validasi, dan aturan akhir tahun |
| `raportdigital/programs.py` | Pilihan sekolah/kesetaraan, nama program, dan label arsip |
| `raportdigital/schema.sql` | Tabel SQLite dan perlindungan arsip terbit |
| `raportdigital/cli.py` | Perintah penyiapan, pemeriksaan, dan menjalankan aplikasi secara lokal atau melalui proxy |
| `raportdigital/static/report.js` | Buku baru, tabel isian, salin-tempel dari spreadsheet, dan tampilan rapor |
| `raportdigital/static/workbook.js` | Pemuatan, penyimpanan otomatis, pemeriksaan revisi, penerbitan, dan navigasi |
| `raportdigital/templates/` | Halaman masuk, daftar buku, kerangka editor, dan URL yang dihasilkan aplikasi |
| `raportdigital/static/*.css` | Tampilan aplikasi dan tata letak cetak A4 |

Untuk mengganti identitas satuan pendidikan atau mata pelajaran, gunakan
**Pengaturan** terlebih dahulu. Nilai bawaan buku baru ada di `def`, `mkc`, dan
`mkms` dalam `report.js`; perubahannya tidak menimpa buku yang sudah tersimpan.
Jika mengganti ID program/kelas atau struktur data, sesuaikan nilai bawaan di
browser dan validasi server, lalu sediakan migrasi data lama. Pertahankan cabang
`reportVersion` dan profil lama agar arsip terbit lama tetap dapat ditampilkan.

## Pilih jenjang dan program

Tetapkan konfigurasi berikut sebelum menjalankan layanan. Setelah mengubahnya,
jalankan ulang layanan dan muat ulang halaman buku yang masih terbuka:

| Pengaturan | Bawaan | Kegunaan |
|---|---|---|
| `RAPOR_EDUCATION` | `school` | `school` untuk SD/SMP/SMA; `equivalency` untuk Paket A/B/C |
| `RAPOR_PROGRAM_NAMES` | Tidak diisi | Lokasi berkas JSON UTF-8 untuk mengganti nama pada menu dan sampul |

Untuk pendidikan kesetaraan, jalankan di CMD Windows:

```bat
set "RAPOR_EDUCATION=equivalency"
.venv\Scripts\raportdigital serve --local
```

Di macOS/Linux, jalankan `export RAPOR_EDUCATION=equivalency` sebelum menyalakan
layanan. Untuk container, gunakan `-e RAPOR_EDUCATION=equivalency`.

Untuk nama sendiri, buat berkas seperti `C:\RaporConfig\programs.json`:

```json
{"a": "MI", "b": "MTs", "c-ipa": "MA IPA", "c-ips": "MA IPS"}
```

Isi `RAPOR_PROGRAM_NAMES` dengan lokasi berkas tersebut. Program yang tidak
dicantumkan tetap memakai nama bawaan. Nama berupa teks biasa, maksimal 120
karakter. Konfigurasi ini dikelola oleh pengelola server; guru tetap mengubah
identitas satuan pendidikan dan mata pelajaran melalui **Pengaturan**. Jika
dipasang dalam aplikasi lain, gunakan
`create_app(education="school", program_names={"a": "MI"})`.

| ID tetap | Sekolah | Kesetaraan | Kelas |
|---|---|---|---|
| `a` | SD | Paket A | I–VI |
| `b` | SMP | Paket B | VII–IX |
| `c-ipa` | SMA IPA | Paket C IPA | X–XII |
| `c-ips` | SMA IPS | Paket C IPS | X–XII |

Keduanya memakai alur pengisian, pencetakan, pengarsipan, dan pergantian tahun yang
sama. Pilihan kesetaraan menyertakan Tingkatan, akhiran kelas MIA/IIS, serta contoh
muatan pemberdayaan dan keterampilan. Pilihan sekolah memakai label rapor umum,
dengan contoh mata pelajaran seni dan olahraga yang terpisah. Mata pelajaran bisa
diubah; contoh bawaan bukan ketentuan kurikulum resmi. Rentang kelas atau sistem
penilaian yang berbeda memerlukan perubahan kode, bukan sekadar nama.

Pergantian pilihan mengubah label buku aktif tanpa mengubah mata pelajaran, siswa,
atau nilai yang sudah tersimpan. Buku baru mengikuti pilihan tersebut. Arsip
terbit mempertahankan label saat diterbitkan; arsip lama tetap memakai format
kesetaraan semula. Menerbitkan ulang revisi buku yang sama akan membuka arsip yang
sudah ada. Simpan perubahan buku sebelum menerbitkan arsip pengganti.

## Jalankan bersama aplikasi lain

Factory WSGI tersedia di `raportdigital:create_app()` dan secara bawaan mewajibkan
HTTPS. `app.py` tetap tersedia agar perintah Flask lama bisa dipakai.

Perintah bawaan mendukung awalan jalur URL:

```sh
raportdigital serve --local --prefix /grades
```

Buka `http://127.0.0.1:8765/grades/`. Untuk pemasangan di server, ikuti
[pengaturan proxy](operations.id.md#hosting). Jika mengatur mount WSGI sendiri,
isi `SCRIPT_NAME` dan hapus awalan tersebut dari `PATH_INFO`. Tautan, URL API,
pengalihan halaman, dan jalur cookie mengikuti mount itu. Aplikasi tidak otomatis
memercayai header yang diteruskan proxy.

Elemen body pada kerangka editor menyediakan `data-program`, `data-profile`,
`data-year`, `data-issue`, `data-csrf`, `data-endpoint`, dan `data-login`. Jika
mengganti backend, tampilkan nilai tersebut dengan aman dan pertahankan ID elemen
DOM yang dipakai kedua skrip.
`data-profile` berisi JSON yang sudah di-escape untuk HTML, dengan kolom `name`,
`cover`, `track`, dan `equivalency`. Untuk arsip, nilainya berasal dari
`reportProfile` dalam salinan terenkripsi; jika belum ada, aplikasi memakai profil
kesetaraan lama. Server mengisi kolom ini saat penerbitan dan mengabaikan
`reportProfile` kiriman browser saat menyimpan buku.

## Kontrak HTTP

Semua endpoint data memerlukan sesi guru. Setiap POST harus menyertakan `Origin`
yang sesuai; POST setelah masuk juga memerlukan `X-CSRF-Token` atau kolom formulir
`csrf`. Gunakan JSON untuk permintaan data. Pemilik data selalu ditentukan dari
sesi yang sudah diautentikasi, bukan dari ID pemilik kiriman browser.

| Endpoint | Permintaan / hasil |
|---|---|
| `POST /login` | Formulir `name`, `password`; membuat cookie HttpOnly, SameSite=Strict |
| `POST /logout` | Mencabut sesi server saat ini |
| `GET /api/book/{program}/{year}` | `{rev, state}`; buku baru mengembalikan `rev: 0, state: null` |
| `POST /api/book/{program}/{year}` | `{rev, state}` menyimpan revisi berikutnya secara atomik; hasil `{rev}` |
| Endpoint yang sama, `action: "history"` | `{rev, action}` menghasilkan `{versions: [...]}`, dari yang terbaru |
| Endpoint yang sama, `action: "restore"` | `{rev, action, version}` memulihkan buku lama sebagai revisi baru |
| Endpoint yang sama, `action: "issue"` | `{rev, action}` mengarsipkan kelas/semester terpilih; hasil `{url}` |
| Endpoint yang sama, `action: "rollover"` | `{rev, action}` membuat buku tahun berikutnya; hasil `{url}` |
| `GET /api/issued/{id}` | `{rev, state}` untuk arsip tetap milik pengguna; tidak ada endpoint untuk mengubahnya |

`state` memuat `sch` (satuan pendidikan dan kelas/semester terpilih), `logo` (data
URL PNG), `c` (data kelas), serta `rows` bila digunakan. Tiap kelas memuat `st`
(siswa), `ms` (pengaturan Ganjil/Genap), `wali`, `nip`, `naik`, dan `tahun`.
Pengaturan memuat kelompok mata pelajaran `u`, `p`, `k`, ekstrakurikuler `e`,
tanggal rapor `tgl`, dan ambang nilai `batas`. Kolom `n` siswa memetakan semester
ke nilai berbentuk string seperti `u0`, `p0`, `k0`, `e0`, `izin`, `sakit`, `alpa`,
dan `catatan`. Kolom dan batas yang diizinkan ada di `domain.validate()`;
`test_app.py` menyediakan contoh buku sederhana dengan data uji.

Bandingkan revisi dan tulis data dalam satu transaksi. Kembalikan **409** untuk
revisi kedaluwarsa, **401/403** jika pemeriksaan autentikasi/keamanan gagal,
**404** untuk data yang tidak ada atau bukan milik pengguna, **413** untuk
permintaan di atas 4 MB, dan **422** untuk data tidak valid. Kegagalan API
mengembalikan pesan `error`; kegagalan HTTP biasa juga menyertakan angka `code`.
Jangan kembalikan data hasil dekripsi jika pemeriksaan integritas gagal.
Memindahkan antarmuka saja tidak ikut memindahkan perlindungan di server ini.

## Memperbarui dokumentasi

Perbarui pasangan bahasa Inggris dan Indonesia bersama-sama: `nama.md` dan
`nama.id.md`. Pertahankan perintah dan contoh API yang sama, serta arahkan tautan
ke panduan dalam bahasa yang sedang dibaca.
