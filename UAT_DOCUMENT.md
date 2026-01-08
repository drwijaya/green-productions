# 📋 USER ACCEPTANCE TESTING (UAT)
## Sistem ERP Quality Control - Green Production Bandung

---

| **Versi Dokumen** | 1.0 |
|-------------------|-----|
| **Tanggal** | 7 Januari 2026 |
| **Nama Proyek** | ERP QC Green Production |
| **Environment** | Production (Railway) |
| **URL** | https://web-production-b6d5.up.railway.app |

---

# A.1 MODUL AUTENTIKASI

## A.1.1 Butir Pengujian Login User

| ID Pengujian | Deskripsi Pengujian | Prosedur Pengujian | Data Masukan | Keluaran yang Diharapkan | Hasil yang Didapat | Diterima | Diterima dengan Catatan | Ditolak |
|:-------------|:--------------------|:-------------------|:-------------|:-------------------------|:-------------------|:--------:|:-----------------------:|:-------:|
| A.1.1.1 | Pengujian Login Valid | 1. Buka halaman login | Username: admin | User berhasil login | | ☐ | ☐ | ☐ |
|  |  | 2. Masukkan username | Password: admin123 | dan diarahkan ke |  |  |  |  |
|  |  | 3. Masukkan password |  | Dashboard |  |  |  |  |
|  |  | 4. Klik tombol "Masuk" |  |  |  |  |  |  |
| A.1.1.2 | Pengujian Login Password Salah | 1. Buka halaman login | Username: admin | Muncul pesan error | | ☐ | ☐ | ☐ |
|  |  | 2. Masukkan username benar | Password: salah123 | "Email atau password |  |  |  |  |
|  |  | 3. Masukkan password salah |  | salah" |  |  |  |  |
|  |  | 4. Klik tombol "Masuk" |  |  |  |  |  |  |
| A.1.1.3 | Pengujian Login Username Tidak Terdaftar | 1. Buka halaman login | Username: tidakada | Muncul pesan error | | ☐ | ☐ | ☐ |
|  |  | 2. Masukkan username tidak terdaftar | Password: test123 | "Email atau password |  |  |  |  |
|  |  | 3. Klik tombol "Masuk" |  | salah" |  |  |  |  |
| A.1.1.4 | Pengujian Login Form Kosong | 1. Buka halaman login | Username: (kosong) | Validasi HTML5 | | ☐ | ☐ | ☐ |
|  |  | 2. Klik "Masuk" tanpa isi form | Password: (kosong) | mencegah submit |  |  |  |  |

## A.1.2 Butir Pengujian Logout User

| ID Pengujian | Deskripsi Pengujian | Prosedur Pengujian | Data Masukan | Keluaran yang Diharapkan | Hasil yang Didapat | Diterima | Diterima dengan Catatan | Ditolak |
|:-------------|:--------------------|:-------------------|:-------------|:-------------------------|:-------------------|:--------:|:-----------------------:|:-------:|
| A.1.2.1 | Pengujian Logout | 1. Login sebagai user | - | User berhasil logout | | ☐ | ☐ | ☐ |
|  |  | 2. Klik menu Logout |  | dan diarahkan ke |  |  |  |  |
|  |  |  |  | halaman login |  |  |  |  |
| A.1.2.2 | Pengujian Akses Setelah Logout | 1. Logout dari sistem | URL: /dashboard | User diarahkan ke | | ☐ | ☐ | ☐ |
|  |  | 2. Akses halaman dashboard via URL |  | halaman login |  |  |  |  |

---

# A.2 MODUL DASHBOARD

## A.2.1 Butir Pengujian Tampilan Dashboard

| ID Pengujian | Deskripsi Pengujian | Prosedur Pengujian | Data Masukan | Keluaran yang Diharapkan | Hasil yang Didapat | Diterima | Diterima dengan Catatan | Ditolak |
|:-------------|:--------------------|:-------------------|:-------------|:-------------------------|:-------------------|:--------:|:-----------------------:|:-------:|
| A.2.1.1 | Pengujian Statistik Order | 1. Login ke sistem | - | Dashboard menampilkan | | ☐ | ☐ | ☐ |
|  |  | 2. Lihat halaman dashboard |  | total order, order aktif, |  |  |  |  |
|  |  |  |  | dan pending QC |  |  |  |  |
| A.2.1.2 | Pengujian Recent Orders | 1. Login ke sistem | - | Menampilkan 5 order | | ☐ | ☐ | ☐ |
|  |  | 2. Scroll ke section recent orders |  | terbaru dengan status |  |  |  |  |
| A.2.1.3 | Pengujian Navigasi Dashboard | 1. Klik salah satu card statistik | - | User diarahkan ke | | ☐ | ☐ | ☐ |
|  |  |  |  | halaman terkait |  |  |  |  |

---

# A.3 MODUL MANAJEMEN ORDER

## A.3.1 Butir Pengujian List Order

| ID Pengujian | Deskripsi Pengujian | Prosedur Pengujian | Data Masukan | Keluaran yang Diharapkan | Hasil yang Didapat | Diterima | Diterima dengan Catatan | Ditolak |
|:-------------|:--------------------|:-------------------|:-------------|:-------------------------|:-------------------|:--------:|:-----------------------:|:-------:|
| A.3.1.1 | Pengujian Tampilan Daftar Order | 1. Login ke sistem | - | Menampilkan daftar | | ☐ | ☐ | ☐ |
|  |  | 2. Klik menu "Orders" |  | semua order dengan |  |  |  |  |
|  |  |  |  | pagination |  |  |  |  |
| A.3.1.2 | Pengujian Filter Status | 1. Buka halaman orders | Status: in_production | Hanya menampilkan | | ☐ | ☐ | ☐ |
|  |  | 2. Pilih status dari filter |  | order dengan status |  |  |  |  |
|  |  |  |  | terpilih |  |  |  |  |
| A.3.1.3 | Pengujian Search Order | 1. Buka halaman orders | Search: INV-202601 | Menampilkan order | | ☐ | ☐ | ☐ |
|  |  | 2. Isi search box |  | yang sesuai pencarian |  |  |  |  |
|  |  | 3. Tekan Enter |  |  |  |  |  |  |

## A.3.2 Butir Pengujian Tambah Order

| ID Pengujian | Deskripsi Pengujian | Prosedur Pengujian | Data Masukan | Keluaran yang Diharapkan | Hasil yang Didapat | Diterima | Diterima dengan Catatan | Ditolak |
|:-------------|:--------------------|:-------------------|:-------------|:-------------------------|:-------------------|:--------:|:-----------------------:|:-------:|
| A.3.2.1 | Pengujian Tambah Order Valid | 1. Klik tombol "Tambah Order" | Model: Kaos Polo | Order berhasil disimpan | | ☐ | ☐ | ☐ |
|  |  | 2. Isi semua field | Customer: PT Fashion | dan muncul di daftar |  |  |  |  |
|  |  | 3. Klik "Simpan" | Qty: 100 |  |  |  |  |  |
|  |  |  | Deadline: 15/01/2026 |  |  |  |  |  |
| A.3.2.2 | Pengujian Tambah Order Kosong | 1. Klik tombol "Tambah Order" | Model: (kosong) | Validasi mencegah | | ☐ | ☐ | ☐ |
|  |  | 2. Biarkan field wajib kosong |  | submit, muncul error |  |  |  |  |
|  |  | 3. Klik "Simpan" |  |  |  |  |  |  |

## A.3.3 Butir Pengujian Detail Order

| ID Pengujian | Deskripsi Pengujian | Prosedur Pengujian | Data Masukan | Keluaran yang Diharapkan | Hasil yang Didapat | Diterima | Diterima dengan Catatan | Ditolak |
|:-------------|:--------------------|:-------------------|:-------------|:-------------------------|:-------------------|:--------:|:-----------------------:|:-------:|
| A.3.3.1 | Pengujian Lihat Detail Order | 1. Klik salah satu order dari list | Order ID: 1 | Menampilkan halaman | | ☐ | ☐ | ☐ |
|  |  |  |  | detail dengan info order, |  |  |  |  |
|  |  |  |  | DSO, dan task produksi |  |  |  |  |
| A.3.3.2 | Pengujian Update Status Order | 1. Buka detail order | Status baru: | Status order berubah, | | ☐ | ☐ | ☐ |
|  |  | 2. Klik tombol update status | in_production | halaman refresh |  |  |  |  |

---

# A.4 MODUL DSO (DETAIL SPEC ORDER)

## A.4.1 Butir Pengujian DSO Management

| ID Pengujian | Deskripsi Pengujian | Prosedur Pengujian | Data Masukan | Keluaran yang Diharapkan | Hasil yang Didapat | Diterima | Diterima dengan Catatan | Ditolak |
|:-------------|:--------------------|:-------------------|:-------------|:-------------------------|:-------------------|:--------:|:-----------------------:|:-------:|
| A.4.1.1 | Pengujian Tampilan DSO List | 1. Klik menu "DSO" | Tab: Draft | Menampilkan DSO | | ☐ | ☐ | ☐ |
|  |  | 2. Pilih tab status |  | dengan status draft |  |  |  |  |
| A.4.1.2 | Pengujian Counter Status | 1. Buka halaman DSO management | - | Menampilkan jumlah | | ☐ | ☐ | ☐ |
|  |  |  |  | DSO per status |  |  |  |  |

## A.4.2 Butir Pengujian Edit DSO

| ID Pengujian | Deskripsi Pengujian | Prosedur Pengujian | Data Masukan | Keluaran yang Diharapkan | Hasil yang Didapat | Diterima | Diterima dengan Catatan | Ditolak |
|:-------------|:--------------------|:-------------------|:-------------|:-------------------------|:-------------------|:--------:|:-----------------------:|:-------:|
| A.4.2.1 | Pengujian Edit Informasi Produk | 1. Buka detail DSO | Jenis: Kaos | Data DSO terupdate, | | ☐ | ☐ | ☐ |
|  |  | 2. Edit field Jenis, Bahan, Warna | Bahan: Cotton | muncul notifikasi |  |  |  |  |
|  |  | 3. Klik "Simpan" | Warna: Navy | sukses |  |  |  |  |
| A.4.2.2 | Pengujian Edit Size Chart | 1. Buka detail DSO | S: 10, M: 20 | Total quantity | | ☐ | ☐ | ☐ |
|  |  | 2. Isi quantity per size | L: 15, XL: 5 | terhitung otomatis |  |  |  |  |
|  |  | 3. Klik "Simpan" |  | (50 pcs) |  |  |  |  |
| A.4.2.3 | Pengujian Upload Gambar | 1. Buka detail DSO | File: design.jpg | Gambar berhasil | | ☐ | ☐ | ☐ |
|  |  | 2. Klik area upload gambar | (< 5MB) | diupload dan |  |  |  |  |
|  |  | 3. Pilih file gambar |  | ditampilkan |  |  |  |  |

## A.4.3 Butir Pengujian Export DSO

| ID Pengujian | Deskripsi Pengujian | Prosedur Pengujian | Data Masukan | Keluaran yang Diharapkan | Hasil yang Didapat | Diterima | Diterima dengan Catatan | Ditolak |
|:-------------|:--------------------|:-------------------|:-------------|:-------------------------|:-------------------|:--------:|:-----------------------:|:-------:|
| A.4.3.1 | Pengujian Export Word | 1. Buka detail DSO lengkap | - | File .docx terdownload | | ☐ | ☐ | ☐ |
|  |  | 2. Klik tombol "Export Word" |  | dengan data DSO terisi |  |  |  |  |
| A.4.3.2 | Pengujian Export PDF | 1. Buka detail DSO lengkap | - | File .pdf terdownload | | ☐ | ☐ | ☐ |
|  |  | 2. Klik tombol "Export PDF" |  | sesuai template |  |  |  |  |

---

# A.5 MODUL PRODUKSI

## A.5.1 Butir Pengujian Production Timeline

| ID Pengujian | Deskripsi Pengujian | Prosedur Pengujian | Data Masukan | Keluaran yang Diharapkan | Hasil yang Didapat | Diterima | Diterima dengan Catatan | Ditolak |
|:-------------|:--------------------|:-------------------|:-------------|:-------------------------|:-------------------|:--------:|:-----------------------:|:-------:|
| A.5.1.1 | Pengujian Tampilan Timeline | 1. Klik menu "Production" | - | Menampilkan daftar | | ☐ | ☐ | ☐ |
|  |  |  |  | order dalam format |  |  |  |  |
|  |  |  |  | timeline |  |  |  |  |
| A.5.1.2 | Pengujian Filter Timeline | 1. Klik tab filter status | Tab: In Production | Menampilkan hanya | | ☐ | ☐ | ☐ |
|  |  |  |  | order dengan status |  |  |  |  |
|  |  |  |  | terpilih |  |  |  |  |
| A.5.1.3 | Pengujian Progress Bar | 1. Lihat card order di timeline | - | Progress bar | | ☐ | ☐ | ☐ |
|  |  |  |  | menunjukkan % selesai |  |  |  |  |

## A.5.2 Butir Pengujian Task Produksi

| ID Pengujian | Deskripsi Pengujian | Prosedur Pengujian | Data Masukan | Keluaran yang Diharapkan | Hasil yang Didapat | Diterima | Diterima dengan Catatan | Ditolak |
|:-------------|:--------------------|:-------------------|:-------------|:-------------------------|:-------------------|:--------:|:-----------------------:|:-------:|
| A.5.2.1 | Pengujian Start Task | 1. Klik tombol "Start" pada task | Task: Cutting | Status berubah ke | | ☐ | ☐ | ☐ |
|  |  |  |  | "In Progress", waktu |  |  |  |  |
|  |  |  |  | mulai tercatat |  |  |  |  |
| A.5.2.2 | Pengujian Complete Task | 1. Klik tombol "Complete" | Task: Cutting | Status ke "Completed", | | ☐ | ☐ | ☐ |
|  |  | pada task in progress |  | tombol QC muncul |  |  |  |  |

---

# A.6 MODUL QUALITY CONTROL

## A.6.1 Butir Pengujian QC Checklist

| ID Pengujian | Deskripsi Pengujian | Prosedur Pengujian | Data Masukan | Keluaran yang Diharapkan | Hasil yang Didapat | Diterima | Diterima dengan Catatan | Ditolak |
|:-------------|:--------------------|:-------------------|:-------------|:-------------------------|:-------------------|:--------:|:-----------------------:|:-------:|
| A.6.1.1 | Pengujian Buka Form QC | 1. Klik tombol QC pada task | Task ID: 11 | Form checklist terbuka | | ☐ | ☐ | ☐ |
|  |  | yang sudah complete |  | sesuai proses |  |  |  |  |
| A.6.1.2 | Pengujian Isi Parameter | 1. Isi Qty Checked dan Qty NG | Qty Checked: 100 | Pass rate terhitung | | ☐ | ☐ | ☐ |
|  |  | 2. Pilih status Ya/Tidak | Qty NG: 2 | otomatis |  |  |  |  |
|  |  |  | Status: Ya |  |  |  |  |  |
| A.6.1.3 | Pengujian Submit PASS | 1. Isi parameter dengan NG < 2.5% | Total NG: 2 | Checklist tersimpan | | ☐ | ☐ | ☐ |
|  |  | 2. Klik "Simpan" | dari 100 (2%) | dengan hasil PASS |  |  |  |  |
| A.6.1.4 | Pengujian Submit FAIL | 1. Isi parameter dengan NG > 2.5% | Total NG: 5 | Checklist tersimpan | | ☐ | ☐ | ☐ |
|  |  | 2. Klik "Simpan" | dari 100 (5%) | dengan hasil FAIL |  |  |  |  |

## A.6.2 Butir Pengujian Defect Log

| ID Pengujian | Deskripsi Pengujian | Prosedur Pengujian | Data Masukan | Keluaran yang Diharapkan | Hasil yang Didapat | Diterima | Diterima dengan Catatan | Ditolak |
|:-------------|:--------------------|:-------------------|:-------------|:-------------------------|:-------------------|:--------:|:-----------------------:|:-------:|
| A.6.2.1 | Pengujian Tambah Defect | 1. Isi Qty NG > 0 | Defect: Ukuran | Detail defect | | ☐ | ☐ | ☐ |
|  |  | 2. Klik ikon defect | tidak presisi | tersimpan |  |  |  |  |
|  |  | 3. Pilih tipe dan severity | Severity: Major |  |  |  |  |  |

## A.6.3 Butir Pengujian QC Report List

| ID Pengujian | Deskripsi Pengujian | Prosedur Pengujian | Data Masukan | Keluaran yang Diharapkan | Hasil yang Didapat | Diterima | Diterima dengan Catatan | Ditolak |
|:-------------|:--------------------|:-------------------|:-------------|:-------------------------|:-------------------|:--------:|:-----------------------:|:-------:|
| A.6.3.1 | Pengujian Daftar QC Report | 1. Klik menu Production > QC Report | - | Menampilkan daftar | | ☐ | ☐ | ☐ |
|  |  |  |  | semua QC sheet |  |  |  |  |

---

# A.7 MODUL QC MONITORING

## A.7.1 Butir Pengujian Dashboard Monitoring

| ID Pengujian | Deskripsi Pengujian | Prosedur Pengujian | Data Masukan | Keluaran yang Diharapkan | Hasil yang Didapat | Diterima | Diterima dengan Catatan | Ditolak |
|:-------------|:--------------------|:-------------------|:-------------|:-------------------------|:-------------------|:--------:|:-----------------------:|:-------:|
| A.7.1.1 | Pengujian KPI Dashboard | 1. Klik menu "QC Monitoring" | - | Menampilkan overall | | ☐ | ☐ | ☐ |
|  |  |  |  | pass rate, total inspected |  |  |  |  |
| A.7.1.2 | Pengujian Chart Defect | 1. Scroll ke section chart | - | Chart pie menampilkan | | ☐ | ☐ | ☐ |
|  |  |  |  | distribusi defect |  |  |  |  |
| A.7.1.3 | Pengujian Chart Trend | 1. Scroll ke section trend | - | Chart line menampilkan | | ☐ | ☐ | ☐ |
|  |  |  |  | trend per proses |  |  |  |  |

## A.7.2 Butir Pengujian Filter Monitoring

| ID Pengujian | Deskripsi Pengujian | Prosedur Pengujian | Data Masukan | Keluaran yang Diharapkan | Hasil yang Didapat | Diterima | Diterima dengan Catatan | Ditolak |
|:-------------|:--------------------|:-------------------|:-------------|:-------------------------|:-------------------|:--------:|:-----------------------:|:-------:|
| A.7.2.1 | Pengujian Filter Task | 1. Pilih task dari dropdown | Task: Cutting | Data difilter | | ☐ | ☐ | ☐ |
|  |  |  | INV-202601-0001 | sesuai task |  |  |  |  |

---

# A.8 MODUL REPORT & EXPORT

## A.8.1 Butir Pengujian Invoice Report

| ID Pengujian | Deskripsi Pengujian | Prosedur Pengujian | Data Masukan | Keluaran yang Diharapkan | Hasil yang Didapat | Diterima | Diterima dengan Catatan | Ditolak |
|:-------------|:--------------------|:-------------------|:-------------|:-------------------------|:-------------------|:--------:|:-----------------------:|:-------:|
| A.8.1.1 | Pengujian Halaman Reports | 1. Klik menu "Reports" | - | Menampilkan daftar | | ☐ | ☐ | ☐ |
|  |  |  |  | order untuk report |  |  |  |  |
| A.8.1.2 | Pengujian Generate Report | 1. Klik "View Report" pada order | Order ID: 1 | Menampilkan invoice | | ☐ | ☐ | ☐ |
|  |  |  |  | report dengan detail |  |  |  |  |
| A.8.1.3 | Pengujian Print Report | 1. Buka invoice report | - | Dialog print browser | | ☐ | ☐ | ☐ |
|  |  | 2. Klik tombol "Print" |  | terbuka dengan benar |  |  |  |  |

## A.8.2 Butir Pengujian Barcode

| ID Pengujian | Deskripsi Pengujian | Prosedur Pengujian | Data Masukan | Keluaran yang Diharapkan | Hasil yang Didapat | Diterima | Diterima dengan Catatan | Ditolak |
|:-------------|:--------------------|:-------------------|:-------------|:-------------------------|:-------------------|:--------:|:-----------------------:|:-------:|
| A.8.2.1 | Pengujian Generate Barcode | 1. Klik menu "Barcode" | Order: INV-202601 | Barcode berhasil | | ☐ | ☐ | ☐ |
|  |  | 2. Pilih order |  | digenerate |  |  |  |  |
|  |  | 3. Klik "Generate" |  |  |  |  |  |  |

---

# A.9 MODUL MASTER DATA

## A.9.1 Butir Pengujian Manajemen Customer

| ID Pengujian | Deskripsi Pengujian | Prosedur Pengujian | Data Masukan | Keluaran yang Diharapkan | Hasil yang Didapat | Diterima | Diterima dengan Catatan | Ditolak |
|:-------------|:--------------------|:-------------------|:-------------|:-------------------------|:-------------------|:--------:|:-----------------------:|:-------:|
| A.9.1.1 | Pengujian Daftar Customer | 1. Klik menu "Customers" | - | Menampilkan daftar | | ☐ | ☐ | ☐ |
|  |  |  |  | customer dengan pagination |  |  |  |  |
| A.9.1.2 | Pengujian Tambah Customer | 1. Klik "Tambah Customer" | Nama: PT ABC | Customer tersimpan | | ☐ | ☐ | ☐ |
|  |  | 2. Isi form | Contact: Pak Budi | dan muncul di daftar |  |  |  |  |
|  |  | 3. Klik "Simpan" | Phone: 08123456789 |  |  |  |  |  |
| A.9.1.3 | Pengujian Edit Customer | 1. Klik tombol edit | Nama baru: | Data customer | | ☐ | ☐ | ☐ |
|  |  | 2. Ubah data | PT ABC Jaya | terupdate |  |  |  |  |
|  |  | 3. Klik "Update" |  |  |  |  |  |  |

## A.9.2 Butir Pengujian Manajemen Employee

| ID Pengujian | Deskripsi Pengujian | Prosedur Pengujian | Data Masukan | Keluaran yang Diharapkan | Hasil yang Didapat | Diterima | Diterima dengan Catatan | Ditolak |
|:-------------|:--------------------|:-------------------|:-------------|:-------------------------|:-------------------|:--------:|:-----------------------:|:-------:|
| A.9.2.1 | Pengujian Daftar Employee | 1. Klik menu "Employees" | - | Menampilkan daftar | | ☐ | ☐ | ☐ |
|  |  |  |  | karyawan |  |  |  |  |
| A.9.2.2 | Pengujian Tambah Employee | 1. Klik "Tambah Employee" | Nama: Siti | Employee tersimpan | | ☐ | ☐ | ☐ |
|  |  | 2. Isi form | Dept: Produksi | dengan kode otomatis |  |  |  |  |
|  |  | 3. Klik "Simpan" | Position: Operator |  |  |  |  |  |

## A.9.3 Butir Pengujian Manajemen Vendor

| ID Pengujian | Deskripsi Pengujian | Prosedur Pengujian | Data Masukan | Keluaran yang Diharapkan | Hasil yang Didapat | Diterima | Diterima dengan Catatan | Ditolak |
|:-------------|:--------------------|:-------------------|:-------------|:-------------------------|:-------------------|:--------:|:-----------------------:|:-------:|
| A.9.3.1 | Pengujian Daftar Vendor | 1. Klik menu "Vendors" | - | Menampilkan daftar | | ☐ | ☐ | ☐ |
|  |  |  |  | vendor/supplier |  |  |  |  |
| A.9.3.2 | Pengujian Tambah Vendor | 1. Klik "Tambah Vendor" | Nama: CV Textile | Vendor tersimpan | | ☐ | ☐ | ☐ |
|  |  | 2. Isi form | Contact: 08111222333 |  |  |  |  |  |
|  |  | 3. Klik "Simpan" |  |  |  |  |  |  |

## A.9.4 Butir Pengujian Manajemen SOP

| ID Pengujian | Deskripsi Pengujian | Prosedur Pengujian | Data Masukan | Keluaran yang Diharapkan | Hasil yang Didapat | Diterima | Diterima dengan Catatan | Ditolak |
|:-------------|:--------------------|:-------------------|:-------------|:-------------------------|:-------------------|:--------:|:-----------------------:|:-------:|
| A.9.4.1 | Pengujian Daftar SOP | 1. Klik menu "SOP" | - | Menampilkan daftar | | ☐ | ☐ | ☐ |
|  |  |  |  | dokumen SOP |  |  |  |  |
| A.9.4.2 | Pengujian View SOP | 1. Klik "View" pada dokumen SOP | SOP ID: 1 | Dokumen PDF terbuka | | ☐ | ☐ | ☐ |
|  |  |  |  | di tab baru |  |  |  |  |

---

# A.10 MODUL MANAJEMEN USER

## A.10.1 Butir Pengujian User Management (Admin Only)

| ID Pengujian | Deskripsi Pengujian | Prosedur Pengujian | Data Masukan | Keluaran yang Diharapkan | Hasil yang Didapat | Diterima | Diterima dengan Catatan | Ditolak |
|:-------------|:--------------------|:-------------------|:-------------|:-------------------------|:-------------------|:--------:|:-----------------------:|:-------:|
| A.10.1.1 | Pengujian Daftar User | 1. Login sebagai admin | - | Menampilkan daftar | | ☐ | ☐ | ☐ |
|  |  | 2. Klik menu "Users" |  | semua user |  |  |  |  |
| A.10.1.2 | Pengujian Akses Non-Admin | 1. Login sebagai operator | - | Ditolak, diarahkan | | ☐ | ☐ | ☐ |
|  |  | 2. Akses /users |  | ke dashboard |  |  |  |  |
| A.10.1.3 | Pengujian Tambah User | 1. Klik "Tambah User" | Email: user@test.com | User tersimpan | | ☐ | ☐ | ☐ |
|  |  | 2. Isi form | Username: testuser | dengan role benar |  |  |  |  |
|  |  | 3. Klik "Simpan" | Password: pass123 |  |  |  |  |  |
|  |  |  | Role: Operator |  |  |  |  |  |
| A.10.1.4 | Pengujian Edit Role User | 1. Klik edit pada user | Role baru: QC Line | Role user terupdate | | ☐ | ☐ | ☐ |
|  |  | 2. Ubah role |  |  |  |  |  |  |
|  |  | 3. Simpan |  |  |  |  |  |  |
| A.10.1.5 | Pengujian Nonaktifkan User | 1. Klik toggle status | - | User inactive, | | ☐ | ☐ | ☐ |
|  |  | pada user |  | tidak bisa login |  |  |  |  |

## A.10.2 Butir Pengujian Permission Management

| ID Pengujian | Deskripsi Pengujian | Prosedur Pengujian | Data Masukan | Keluaran yang Diharapkan | Hasil yang Didapat | Diterima | Diterima dengan Catatan | Ditolak |
|:-------------|:--------------------|:-------------------|:-------------|:-------------------------|:-------------------|:--------:|:-----------------------:|:-------:|
| A.10.2.1 | Pengujian Lihat Permission | 1. Klik "Manage Permissions" | User ID: 5 | Menampilkan daftar | | ☐ | ☐ | ☐ |
|  |  | pada user |  | permission dengan |  |  |  |  |
|  |  |  |  | checkbox |  |  |  |  |
| A.10.2.2 | Pengujian Update Permission | 1. Centang/uncentang permission | Permission: | Permission terupdate | | ☐ | ☐ | ☐ |
|  |  | 2. Klik "Save" | can_edit_dso = true |  |  |  |  |  |

---

# 📊 RINGKASAN HASIL UAT

| No | Modul | Jumlah Test Case | Diterima | Diterima dengan Catatan | Ditolak |
|:--:|:------|:----------------:|:--------:|:-----------------------:|:-------:|
| 1 | A.1 Autentikasi | 6 | | | |
| 2 | A.2 Dashboard | 3 | | | |
| 3 | A.3 Manajemen Order | 7 | | | |
| 4 | A.4 DSO | 7 | | | |
| 5 | A.5 Produksi | 5 | | | |
| 6 | A.6 Quality Control | 6 | | | |
| 7 | A.7 QC Monitoring | 4 | | | |
| 8 | A.8 Report & Export | 4 | | | |
| 9 | A.9 Master Data | 10 | | | |
| 10 | A.10 User Management | 7 | | | |
| | **TOTAL** | **59** | | | |

---

# ✍️ TANDA TANGAN PERSETUJUAN

| Peran | Nama | Jabatan | Tanda Tangan | Tanggal |
|:------|:-----|:--------|:-------------|:--------|
| Penguji | | | | |
| Pemilik Aplikasi | | Owner | | |
| Tim Pengembang | | Developer | | |

---

**Keterangan:**
- ☐ = Checkbox untuk diisi saat pengujian
- Hasil **"Diterima dengan Catatan"** memerlukan penjelasan di kolom terpisah
- Hasil **"Ditolak"** harus disertai bug report terpisah

---

*Dokumen ini dibuat pada 7 Januari 2026*
