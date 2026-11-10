# Rapor Digital

Buku nilai guru untuk program kesetaraan Paket A, B, C IPA, dan C IPS. Antarmuka berbahasa Indonesia mendukung penempelan blok dari Excel, pengisian identitas dan nilai per semester, serta cetak rapor A4 per siswa atau per kelas. Setiap akun memiliki buku sendiri untuk setiap program dan tahun pelajaran.

Aplikasi ini berdiri sendiri dan berjalan di satu komputer. Setiap satuan pendidikan dapat memakainya apa adanya atau menjadikannya titik awal: isi nama dan identitas satuan pendidikan pada **Pengaturan**, lalu sesuaikan daftar mata pelajaran.

## Menjalankan di komputer guru

Siapkan Python 3.11+ dan jalankan perintah berikut dari direktori proyek. Contoh menggunakan PowerShell.

```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements.txt
.\.venv\Scripts\python -m flask --app app init
.\.venv\Scripts\python -m flask --app app teacher
.\.venv\Scripts\python app.py
```

Buka <http://127.0.0.1:8765>. Perintah `teacher` meminta nama akun dan kata sandi melalui terminal. Menjalankannya kembali dengan nama yang sama mengganti kata sandi dan mencabut semua sesi akun itu. Hanya pengelola komputer yang boleh memiliki akses ke terminal, direktori aplikasi, atau direktori data.

## Mengisi dan menerbitkan

1. Pilih tahun awal pelajaran dan program. Lengkapi data sekolah, wali kelas, tanggal rapor, serta mata pelajaran. Setiap kelas menggunakan identitas siswa yang sama untuk kedua semester.
2. Pada **Data Siswa & Nilai**, pilih kolom identitas, nilai, atau kehadiran untuk memperpendek tabel. Tempel satu atau beberapa kolom dari Excel. Tunggu status **Tersimpan** sebelum menutup halaman. Jika dua tab mengubah buku yang sama, server menolak salinan yang lebih lama.
3. Pada **Periksa & cetak**, periksa kelengkapan lalu pilih **Terbitkan arsip kelas**. Arsip mencakup seluruh siswa pada kelas dan semester terpilih. Pilihan siswa dan bagian rapor hanya mengatur hasil cetak. Pratinjau draf ditandai pada setiap halaman.
4. Buka **Arsip terbit** untuk mencetak ulang. Koreksi dilakukan di buku nilai dan diterbitkan sebagai arsip baru. Gunakan nomor arsip untuk membandingkan PDF atau kertas dengan salinan dalam aplikasi.

Data dari versi HTML lama tetap berada di penyimpanan browser asal. Gunakan sumber Excel lama untuk mengisi buku yang sesuai. Periksa identitas, nilai dan hasil cetak sebelum membersihkan penyimpanan lama.

## Periksa nilai dan siapkan tahun berikutnya

- Periksa daftar serta urutan mapel kelas sebelum menempel nilai. Buku baru mengikuti susunan templat upstream November 2026, termasuk IPAS dan Bahasa Inggris untuk Paket A. Buku lama memakai susunan yang sudah disimpan. Sertakan judul kolom dari tabel saat menempel beberapa kolom. Untuk data tanpa judul, cocokkan urutan tujuan yang ditampilkan dengan lembar Excel.
- Di **Periksa & cetak → Rekap kelas & keputusan siswa**, rata-rata menggunakan nilai yang terisi, termasuk nol. Pada semester Genap, pilih keputusan untuk setiap siswa. Keputusan yang masih kosong tidak dicetak. Nomor rapor yang belum diisi tampil sebagai tanda pisah. Arsip yang terbit pada versi lama mempertahankan tampilan nomor dan teks kenaikan sebelumnya.
- Setelah semua kelas dalam program selesai, pilih **Siapkan tahun berikutnya** dan periksa jumlah siswa per kelas. Siswa yang naik atau tinggal kelas disalin ke buku baru. Siswa yang lulus hanya tercatat di tahun asal. Nomor rapor, nilai, kehadiran, keputusan, wali kelas, dan tanggal rapor mulai kosong. Buku tujuan yang sudah tersimpan tidak dapat ditimpa.
- **Riwayat draf** menyimpan lima revisi sebelumnya untuk seluruh buku program pada tahun tersebut. Pemulihan membuat revisi baru. Arsip terbit tetap tersedia secara terpisah.

## Penyimpanan dan batas keamanan

- SQLite, kunci AES-256-GCM dan hash kata sandi berada secara default di `~/.raportdigital`, di luar repositori. Atur `RAPOR_DATA_DIR` ke direktori privat lain sebelum inisialisasi jika diperlukan. Aktifkan enkripsi disk dan batasi izin sistem operasi ke akun layanan atau pengelola. Di Windows, periksa ACL direktori.
- Isi buku dan arsip dienkripsi dengan konteks akun, program, tahun dan revisi. Basis data juga berisi metadata seperti nama akun dan nomor arsip. Pengelola yang menguasai host serta kuncinya merupakan pihak tepercaya. Pemulihan basis data lama dapat mengembalikan seluruh aplikasi ke keadaan sebelumnya.
- Hentikan layanan sebelum menyalin basis data untuk cadangan. Simpan salinan kunci terpisah dari cadangan basis data dengan akses terbatas. Pulihkan keduanya ke direktori privat dan uji pembukaan buku serta arsip. Kehilangan kunci menghilangkan akses ke isi rapor.
- Tidak ada pendaftaran publik. Sesi disimpan di server, kedaluwarsa setelah 30 menit tanpa permintaan atau delapan jam sejak masuk. Gunakan **Keluar** dan kunci layar saat meninggalkan perangkat. Hasil cetak dan PDF mengandung data siswa dan harus disimpan secara privat.
- Perintah `python app.py` mengikat layanan ke loopback. Untuk hosting multi-pengguna, gunakan WSGI dengan `create_app()` di belakang terminasi HTTPS yang tepercaya, konfigurasikan skema HTTPS pada WSGI dan batasi akses langsung ke backend. Mode ini mewajibkan HTTPS dan cookie Secure. Jangan publikasikan folder proyek melalui static hosting. Masuk tunggal dan tanda tangan digital PDF berada di luar versi ini.
