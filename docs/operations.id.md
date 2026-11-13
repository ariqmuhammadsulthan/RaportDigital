# Menjalankan dan mengelola aplikasi

[English](operations.md) | **Bahasa Indonesia**

[← README](../README.id.md) · [Integrasi](integration.id.md)

## Penyimpanan dan akun

Untuk memakai folder selain `~/.raportdigital`, tetapkan `RAPOR_DATA_DIR` sebelum
**setiap** perintah penyiapan atau menjalankan server. Simpan di luar folder kode
dan web root. Di CMD:

```bat
set "RAPOR_DATA_DIR=C:\RaporData"
.venv\Scripts\raportdigital init
.venv\Scripts\raportdigital teacher
.venv\Scripts\raportdigital check
```

`init` bisa dijalankan ulang dan menambahkan struktur basis data yang diperlukan.
Perintah ini menolak membuat kunci baru jika kunci basis data lama hilang.
`teacher` membuat akun atau mengganti kata sandinya sekaligus mencabut semua
sesinya. Kata sandi tidak ditampilkan saat diketik. Tidak ada pendaftaran umum
atau akun bawaan.

`check` memeriksa bentuk kunci, tabel yang diperlukan, dan konsistensi SQLite.
Pemeriksaan ini belum membuktikan bahwa kunci bisa membuka data lama; buka buku
dan arsip untuk memastikannya. Batasi akses folder hanya untuk akun layanan atau
pengelola. Folder dan berkas baru di Unix dibuat dengan izin akses terbatas;
di Windows, atur dan periksa sendiri izin akses folder (ACL).

## Hosting

Gunakan reverse proxy HTTPS tepercaya dan koneksi privat ke backend. Perintah
server menerima satu IP proxy, menolak HTTP biasa dalam mode hosting, dan
mewajibkan nama host publik. Untuk proxy di mesin yang sama, jalankan di CMD:

```bat
set "RAPOR_TRUSTED_HOSTS=grades.example.org"
.venv\Scripts\raportdigital serve --trusted-proxy 127.0.0.1
```

Atur proxy agar mempertahankan `Host` publik, mengisi `X-Forwarded-Proto: https`,
dan mengganti `X-Forwarded-For` dengan alamat klien. Pertahankan alamat backend
bawaan `127.0.0.1:8765`. `--prefix /grades` juga bisa digunakan jika proxy
mempertahankan jalur tersebut. Pisahkan beberapa nama host tepercaya dengan koma
dan gunakan nama host persis. Proxy harus menolak host lain serta mengalihkan
HTTP ke HTTPS.

Untuk container, siapkan satu volume penyimpanan permanen:

```sh
docker build -t raportdigital .
docker volume create raportdigital-data
docker run --rm -v raportdigital-data:/data raportdigital init
docker run --rm -it -v raportdigital-data:/data raportdigital teacher
docker run --rm -v raportdigital-data:/data raportdigital check
```

Image berjalan dengan UID 10001. Isi `RAPOR_TRUSTED_HOSTS` dengan nama host publik
dan `RAPOR_TRUSTED_PROXY` dengan IP proxy yang benar-benar terhubung ke backend.
Server bawaan memakai port 8080. Hubungkan container hanya ke jaringan privat
proxy. Jika memakai bind mount, pastikan UID 10001 bisa menulis ke foldernya.
Penyiapan dijalankan secara eksplisit; aplikasi tidak mereset data saat menyala.

Ganti jaringan, nama host, dan IP proxy pada contoh berikut sesuai pemasangan Anda:

```sh
docker run -d --name raportdigital --network your-proxy-network -v raportdigital-data:/data -e RAPOR_TRUSTED_HOSTS=grades.example.org -e RAPOR_TRUSTED_PROXY=192.0.2.10 raportdigital
```

Arahkan proxy ke `raportdigital:8080` melalui jaringan privat tersebut. Port
backend tidak perlu dibuka ke publik. IP pada contoh hanya penanda, bukan
konfigurasi bawaan yang bisa langsung dipakai.

Factory Python juga bisa dijalankan dengan server WSGI lain. Atur kepercayaan
terhadap proxy pada server itu; jangan langsung menerima forwarded header dari
internet. Lihat [dokumentasi proxy Waitress](https://docs.pylonsproject.org/projects/waitress/en/stable/reverse-proxy.html).
Jangan sajikan repositori ini sebagai situs statis atau membuka server debug Flask.

## Perlindungan dan pencadangan

Buku, riwayat revisi, dan arsip terbit memakai AES-256-GCM dengan konteks akun,
program, tahun, dan revisi. Nama akun serta metadata lain tidak dienkripsi.
Token sesi disimpan sebagai hash di SQLite. Sesi berakhir setelah 30 menit tanpa
aktivitas atau delapan jam sejak dibuat. Mode lokal mengizinkan HTTP hanya untuk
loopback; cookie pada mode hosting memakai atribut Secure.

Administrator host dan siapa pun yang memegang basis data sekaligus kuncinya
merupakan pihak tepercaya. Enkripsi tidak melindungi host yang sudah dikuasai
pihak lain atau mendeteksi pemulihan seluruh basis data ke versi lama. Perlindungan
arsip melalui SQL bukan tanda tangan digital pada PDF.

Hentikan layanan sebelum menyalin `records.sqlite3`. Cadangkan `records.key`
secara terpisah dengan akses terbatas; pastikan basis data dan kunci berasal dari
instalasi yang sama. Gunakan enkripsi disk. Uji pemulihan di folder privat:
jalankan `check`, masuk, lalu buka buku dan arsip. Jika kunci hilang, data
terenkripsi tidak bisa dibuka. Jangan membuat kunci pengganti saat memperbarui.

## Pengujian dan pembaruan

**Untuk memperbarui instalasi pendidikan kesetaraan:** tetapkan
`RAPOR_EDUCATION=equivalency` sebelum menjalankan layanan versi baru. Pilihan
bawaan sekarang adalah SD/SMP/SMA. Nama program sendiri dijelaskan dalam
[pengaturan program](integration.id.md#pilih-jenjang-dan-program). Simpan
pengaturan ini dan berkas nama program bersama konfigurasi layanan dan cadangan.

Setelah memasang dependensi, jalankan dari folder utama repositori:

```bat
.venv\Scripts\python -m unittest discover -v
.venv\Scripts\python -m pip wheel --no-deps . --wheel-dir dist
```

Pengujian memakai folder sementara dan data buatan. CI menjalankan pengujian
Python dan pembuatan wheel di Windows/Linux. Pengujian tambahan melalui browser
dijelaskan di [panduan pengujian browser](../tools/README.id.md). CI memvalidasi
kode, bukan menyediakan pemeliharaan aplikasi berkelanjutan.

Pengguna lama bisa mempertahankan `RAPOR_DATA_DIR`, memasang versi baru, lalu
menjalankan `init` dan `check`. `python app.py` tetap menyalakan server lokal;
perintah `python -m flask --app app init` dan `teacher` juga tetap berlaku.
Buku, akun, dan revisi lama tetap kompatibel. Arsip baru turut menyimpan label
rapornya, sedangkan arsip lama mempertahankan label kesetaraan. Instalasi baru
bisa memakai wheel tanpa folder sumber; template, aset, dan skema sudah disertakan.

Kelola sendiri pembaruan dependensi, cadangan, dan pembatasan akses. Template ini
dibuat sebagai kontribusi satu kali; kompatibilitas dengan perubahan proyek asal
di masa depan tidak dijanjikan.
