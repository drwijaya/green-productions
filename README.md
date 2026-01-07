# Panduan Instalasi dan Menjalankan Aplikasi Green Productions

Dokumen ini menjelaskan langkah-langkah untuk menyiapkan dan menjalankan aplikasi Flask ini di komputer lokal Anda (Windows).

## 1. Prasyarat System
Pastikan Anda telah menginstal:
- **Python** (versi 3.8 atau lebih baru).
- **PostgreSQL** (jika menggunakan database lokal) atau koneksi internet untuk Supabase.

## 2. Persiapan Lingkungan (Virtual Environment)
Disarankan untuk menggunakan virtual environment agar package Python tidak bentrok dengan system lain.

1. Buka terminal (Command Prompt atau PowerShell) di folder proyek ini.
2. Jalankan perintah berikut untuk membuat virtual environment (jika folder `venv` belum ada):
   ```bash
   python -m venv venv
   ```
3. Aktifkan virtual environment:
   - **Command Prompt (cmd):**
     ```bash
     venv\Scripts\activate
     ```
   - **PowerShell:**
     ```bash
     .\venv\Scripts\Activate
     ```
   *(Jika berhasil, Anda akan melihat `(venv)` di awal baris terminal)*

## 3. Instalasi Dependencies
Install semua library yang diperlukan yang tercantum di `requirements.txt`:

```bash
pip install -r requirements.txt
```

## 4. Konfigurasi Environment (.env)
Pastikan file `.env` sudah ada di root folder proyek. File ini berisi konfigurasi sensitif seperti koneksi database.

Contoh variabel yang biasanya ada di `.env`:
```env
FLASK_APP=run.py
FLASK_DEBUG=1
DATABASE_URL=postgresql://user:password@localhost:5432/db_name
SECRET_KEY=kunci_rahasia_anda
```
*Catatan: Minta file `.env` yang valid kepada pengembang utama jika Anda belum memilikinya.*

## 5. Menjalankan Aplikasi
Setelah semua siap, jalankan aplikasi dengan perintah:

```bash
python run.py
```

Anda akan melihat output seperti:
```
 * Serving Flask app 'app'
 * Debug mode: on
 * Running on http://127.0.0.1:5000
```

## 6. Mengakses Aplikasi
Buka browser (Chrome/Firefox/Edge) dan kunjungi alamat:

**http://127.0.0.1:5000** atau **http://localhost:5000**

## Masalah Umum (Troubleshooting)
- **`ModuleNotFoundError`**: Pastikan Anda sudah mengaktifkan venv dan menjalankan `pip install -r requirements.txt`.
- **Database Error**: Cek koneksi internet (jika pakai Supabase) atau pastikan PostgreSQL service berjalan (jika lokal). Periksa kembali `DATABASE_URL` di `.env`.
- **Scripts is disabled on this system**: Jika di PowerShell muncul error ini saat activate, jalankan `Set-ExecutionPolicy RemoteSigned -Scope CurrentUser` lalu coba lagi.
