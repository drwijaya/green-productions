# Rencana Implementasi Sistem Monitoring QC & Defect Management

Berdasarkan permintaan Anda dan gambar "FORM REWORK / PERBAIKAN PRODUK" yang dilampirkan, berikut adalah rencana implementasi komprehensif untuk modul QC Monitoring.

## 1. Analisis Kebutuhan

Tujuannya adalah mendigitalkan formulir manual menjadi sistem terintegrasi yang memungkinkan tracking cacat, analisis tren, dan pelaporan otomatis.

### Komponen Formulir (Mapping ke Data Digital):
*   **A. Identitas Produk:**
    *   *Nama Pemesan & No. Order*: Diambil otomatis dari database `Order`.
    *   *Jenis Produk*: Diambil dari `Order` atau `DSO`.
    *   *Tahap Proses*: Dropdown/Checkbox (Cutting, Sewing, Sablon, Finishing).
*   **B. Informasi Defect:**
    *   Daftar cacat yang memungkinkan input multiple item (Jenis, Jumlah, Deskripsi).
*   **C. Tindakan Penanganan:**
    *   Rencana perbaikan, PIC (Person In Charge), dan Target Selesai.
*   **D. Verifikasi Hasil:**
    *   Validasi QC setelah perbaikan (Sesuai/Tidak Sesuai).
*   **E. Tanda Tangan:**
    *   Digital approval/tracking user yang login.

---

## 2. Skema Database (Enhanced Models)

Kita akan memodifikasi model yang ada di `app/models/qc.py` agar sesuai dengan kebutuhan form rework.

### Update `QCSheet` (Identitas & Verifikasi)
Menambahkan field untuk mengakomodasi data formulir bagian A dan D.

```python
class QCSheet(db.Model):
    # ... existing fields ...
    
    # Bagian A: Identitas Tambahan
    process_stage = db.Column(db.String(50)) # Cutting, Sewing, dll
    batch_number = db.Column(db.String(50))
    
    # Bagian D: Verifikasi
    rework_result = db.Column(db.String(50)) # 'pass', 'fail'
    final_status = db.Column(db.String(50))  # 'closed', 'continue_action'
    
    # Bagian E: Tanda Tangan (Approval)
    rework_operator_id = db.Column(db.Integer, db.ForeignKey('employees.id'))
    qc_operator_id = db.Column(db.Integer, db.ForeignKey('employees.id')) # Existing: inspector_id
```

### Update `DefectLog` (Detail Defect & Penanganan)
Menambahkan field untuk bagian B dan C.

```python
class DefectLog(db.Model):
    # ... existing fields ...
    
    # Bagian C: Penanganan
    responsible_department = db.Column(db.String(100)) # Bagian Penanggung Jawab
    target_resolution_date = db.Column(db.Date) # Target Penyelesaian
    actual_resolution_date = db.Column(db.Date) # Tanggal Penyelesaian (Existing: resolved_at)
```

### Model Baru: `DefectMaster` (Master Data)
Untuk standardisasi kategori cacat agar analisa tren akurat.
*   `id`
*   `category` (e.g., Sewing, Material)
*   `name` (e.g., Jahitan Loncat, Bolong)
*   `severity_default`

---

## 3. Fitur Dashboard QC

Dashboard akan dibagi menjadi 3 segmen utama:

### A. KPI Cards (Real-time)
1.  **Total Defect Rate**: Persentase produk cacat vs total produksi.
2.  **Open Issues**: Jumlah cacat yang statusnya belum "Closed".
3.  **Rework Success Rate**: Berapa % perbaikan yang lolos verifikasi pertama kali.

### B. Visualisasi Grafik (Chart.js)
1.  **Tren Cacat per Periode**: Line chart (Harian/Mingguan).
2.  **Pareto Chart Cacat**: Bar chart untuk melihat jenis cacat terbanyak (Top 5 Defect Types).
3.  **Defect by Stage**: Pie chart untuk melihat di tahap mana cacat paling sering terjadi (Cutting vs Sewing vs Finishing vs Sablon vs).

### C. Tabel Monitoring (List View)
*   Tabel interaktif berisi daftar Form Defect dengan status warna-warni.
*   Filter: Periode, No. Order, Status (Open/Closed).

---
---

## Pertanyaan Konfirmasi
Apakah Anda setuju dengan penambahan field database di atas? Jika ya, saya akan mulai dengan **Tahap 1: Migrasi Database**.
