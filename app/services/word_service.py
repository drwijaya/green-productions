"""Service for exporting DSO to Word document."""
import os
import io
from docx import Document
from docx.shared import Inches, Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
import requests


def export_dso_to_word(dso):
    """Export DSO data to Word document using template."""
    template_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 
                                  '..', 'template_docs', 'dsotemplates.docx')
    
    if not os.path.exists(template_path):
        raise FileNotFoundError(f"Template not found: {template_path}")
    
    # Load template
    doc = Document(template_path)
    
    # Prepare data mappings
    order = dso.order
    dewasa = dso.size_chart_dewasa
    anak = dso.size_chart_anak
    
    # Build replacement dictionary
    replacements = {
        # Header Info
        '{{INV}}': order.order_code or '',
        '{{DUE DATE}}': order.deadline.strftime('%d/%m/%Y') if order.deadline else '',
        
        # Product Info
        '{{MODEL}}': order.model or '',
        '{{JENIS}}': dso.jenis or '',
        '{{BAHAN}}': dso.bahan or '',
        '{{SABLON}}': dso.sablon or '',
        '{{WARNA}}': dso.warna or '',
        '{{POSISI}}': dso.posisi or '',
        
        # Accessories
        '{{ACC1}}': dso.acc_1 or '',
        '{{ACC2}}': dso.acc_2 or '',
        '{{ACC3}}': dso.acc_3 or '',
        '{{ACC4}}': dso.acc_4 or '',
        '{{ACC5}}': dso.acc_5 or '',
        '{{KANCING}}': dso.kancing or '',
        '{{SAKU}}': dso.saku or '',
        '{{RESLETING}}': dso.resleting or '',
        '{{MODEL BADAN BAWAH}}': dso.model_badan_bawah or '',
        
        # Catatan Customer
        '{{CATATAN CUSTOMER 1}}': dso.catatan_customer_1 or '',
        '{{CATATAN CUSTOMER 2}}': dso.catatan_customer_2 or '',
        '{{CATATAN CUSTOMER 3}}': dso.catatan_customer_3 or '',
        '{{CATATAN CUSTOMER 4}}': dso.catatan_customer_4 or '',
        '{{CATATAN CUSTOMER 5}}': dso.catatan_customer_5 or '',
        '{{CATATAN CUSTOMER 6}}': dso.catatan_customer_6 or '',
        '{{LABEL}}': dso.label or '',
        
        # Size Chart Dewasa - Pendek
        '{{AD}}': str(dewasa.pendek_xs if dewasa else 0),
        '{{BD}}': str(dewasa.pendek_s if dewasa else 0),
        '{{CD}}': str(dewasa.pendek_m if dewasa else 0),
        '{{DD}}': str(dewasa.pendek_l if dewasa else 0),
        '{{ED}}': str(dewasa.pendek_xl if dewasa else 0),
        '{{FD}}': str(dewasa.pendek_xxl if dewasa else 0),
        '{{GD}}': str(dewasa.pendek_x3l if dewasa else 0),
        '{{HD_PENDEK}}': str(dewasa.pendek_x4l if dewasa else 0),
        '{{ID_PENDEK}}': str(dewasa.pendek_x5l if dewasa else 0),
        
        # Size Chart Dewasa - Panjang
        '{{HD}}': str(dewasa.panjang_xs if dewasa else 0),
        '{{ID}}': str(dewasa.panjang_s if dewasa else 0),
        '{{JD}}': str(dewasa.panjang_m if dewasa else 0),
        '{{KD}}': str(dewasa.panjang_l if dewasa else 0),
        '{{LD}}': str(dewasa.panjang_xl if dewasa else 0),
        '{{MD}}': str(dewasa.panjang_xxl if dewasa else 0),
        '{{ND}}': str(dewasa.panjang_x3l if dewasa else 0),
        '{{OD}}': str(dewasa.panjang_x4l if dewasa else 0),
        
        # Dewasa totals
        '{{JUMDA}}': str(dewasa.jum_pendek if dewasa else 0),
        '{{JUMDB}}': str(dewasa.jum_panjang if dewasa else 0),
        '{{QTYD }}': str(dewasa.total if dewasa else 0),
        '{{QTYD}}': str(dewasa.total if dewasa else 0),
        
        # Size Chart Anak - Pendek
        '{{AA}}': str(anak.pendek_xs if anak else 0),
        '{{BA}}': str(anak.pendek_s if anak else 0),
        '{{CA}}': str(anak.pendek_m if anak else 0),
        '{{DA}}': str(anak.pendek_l if anak else 0),
        '{{EA}}': str(anak.pendek_xl if anak else 0),
        '{{FA}}': str(anak.pendek_xxl if anak else 0),
        '{{GA}}': str(anak.pendek_x3l if anak else 0),
        '{{HA_PENDEK}}': str(anak.pendek_x4l if anak else 0),
        '{{IA_PENDEK}}': str(anak.pendek_x5l if anak else 0),
        
        # Size Chart Anak - Panjang
        '{{HA}}': str(anak.panjang_xs if anak else 0),
        '{{IA}}': str(anak.panjang_s if anak else 0),
        '{{JA}}': str(anak.panjang_m if anak else 0),
        '{{KA}}': str(anak.panjang_l if anak else 0),
        '{{LA}}': str(anak.panjang_xl if anak else 0),
        '{{MA}}': str(anak.panjang_xxl if anak else 0),
        '{{NA}}': str(anak.panjang_x3l if anak else 0),
        '{{OA}}': str(anak.panjang_x4l if anak else 0),
        
        # Anak totals
        '{{JUMAA}}': str(anak.jum_pendek if anak else 0),
        '{{JUMAB}}': str(anak.jum_panjang if anak else 0),
        '{{QTYA }}': str(anak.total if anak else 0),
        '{{QTYA}}': str(anak.total if anak else 0),
    }
    
    # Replace text in all tables
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                for key, value in replacements.items():
                    if key in cell.text:
                        # Replace while preserving formatting
                        for paragraph in cell.paragraphs:
                            for run in paragraph.runs:
                                if key in run.text:
                                    run.text = run.text.replace(key, value)
                            # Also check full paragraph text if runs don't have it
                            if key in paragraph.text:
                                paragraph.text = paragraph.text.replace(key, value)
    
    # Replace in paragraphs outside tables
    for paragraph in doc.paragraphs:
        for key, value in replacements.items():
            if key in paragraph.text:
                for run in paragraph.runs:
                    if key in run.text:
                        run.text = run.text.replace(key, value)
    
    # Handle image placeholder {{GAMBAR}}
    if dso.gambar_depan_url:
        for table in doc.tables:
            for row in table.rows:
                for cell in row.cells:
                    if '{{GAMBAR}}' in cell.text:
                        # Clear the cell
                        for paragraph in cell.paragraphs:
                            paragraph.clear()
                        
                        # Try to add image
                        try:
                            # Download image from URL
                            response = requests.get(dso.gambar_depan_url, timeout=10)
                            if response.status_code == 200:
                                image_stream = io.BytesIO(response.content)
                                # Add image to cell
                                paragraph = cell.paragraphs[0] if cell.paragraphs else cell.add_paragraph()
                                run = paragraph.add_run()
                                run.add_picture(image_stream, width=Inches(4))
                                paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
                        except Exception as e:
                            print(f"Error adding image: {e}")
                            cell.paragraphs[0].add_run("(Gambar tidak tersedia)")
    else:
        # Remove placeholder if no image
        for table in doc.tables:
            for row in table.rows:
                for cell in row.cells:
                    if '{{GAMBAR}}' in cell.text:
                        for paragraph in cell.paragraphs:
                            paragraph.text = paragraph.text.replace('{{GAMBAR}}', '')
    
    # Save to BytesIO buffer
    buffer = io.BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    
    return buffer


def export_dso_to_pdf(dso):
    """Export DSO data to PDF document.
    
    On Windows: uses docx2pdf for Word-to-PDF conversion (best fidelity).
    On Linux: uses WeasyPrint to generate PDF from HTML (Railway compatible).
    """
    import sys
    import platform
    
    # Check if we're on Windows
    is_windows = platform.system() == 'Windows'
    
    if is_windows:
        return _export_dso_to_pdf_windows(dso)
    else:
        return _export_dso_to_pdf_weasyprint(dso)


def _export_dso_to_pdf_windows(dso):
    """Export DSO to PDF using docx2pdf (Windows only)."""
    import tempfile
    import site
    import os

    # Fix for pywin32 DLL load error (pywintypes314.dll not found)
    try:
        import sys
        paths_to_check = sys.path + site.getsitepackages()
        for path in paths_to_check:
            dll_path = os.path.join(path, 'pywin32_system32')
            if os.path.exists(dll_path):
                os.environ['PATH'] = dll_path + os.pathsep + os.environ['PATH']
                break
    except Exception as e:
        print(f"Warning: Could not patch PATH for pywin32: {e}")

    try:
        from docx2pdf import convert
        import pythoncom
    except ImportError as e:
        raise ImportError(f"PDF generation requires docx2pdf and pywin32. Error: {e}")
    
    word_buffer = export_dso_to_word(dso)
    
    with tempfile.NamedTemporaryFile(suffix='.docx', delete=False) as tmp_docx:
        tmp_docx.write(word_buffer.getvalue())
        tmp_docx_path = tmp_docx.name
    
    tmp_pdf_path = tmp_docx_path.replace('.docx', '.pdf')
    
    try:
        pythoncom.CoInitialize()
        convert(tmp_docx_path, tmp_pdf_path)
        
        with open(tmp_pdf_path, 'rb') as f:
            pdf_content = f.read()
            
        pdf_buffer = io.BytesIO(pdf_content)
        return pdf_buffer
        
    finally:
        if os.path.exists(tmp_docx_path):
            os.remove(tmp_docx_path)
        if os.path.exists(tmp_pdf_path):
            os.remove(tmp_pdf_path)


def _export_dso_to_pdf_weasyprint(dso):
    """Export DSO to PDF using fpdf2 (Linux/Railway compatible - pure Python)."""
    from fpdf import FPDF
    
    order = dso.order
    dewasa = dso.size_chart_dewasa
    anak = dso.size_chart_anak
    
    # Create PDF using fpdf2
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    
    # Title
    pdf.set_font('Helvetica', 'B', 18)
    pdf.set_text_color(46, 125, 50)
    pdf.cell(0, 15, 'DETAIL SPEC ORDER (DSO)', ln=True, align='C')
    pdf.ln(5)
    
    # Header info
    pdf.set_fill_color(245, 245, 245)
    pdf.set_text_color(0, 0, 0)
    pdf.set_font('Helvetica', '', 10)
    col_width = 47.5
    pdf.cell(col_width, 8, f'Invoice: {order.order_code or "-"}', border=1, fill=True, align='C')
    pdf.cell(col_width, 8, f'Model: {order.model or "-"}', border=1, fill=True, align='C')
    deadline_str = order.deadline.strftime("%d/%m/%Y") if order.deadline else "-"
    pdf.cell(col_width, 8, f'Deadline: {deadline_str}', border=1, fill=True, align='C')
    pdf.cell(col_width, 8, f'Versi: v{dso.version}', border=1, fill=True, align='C')
    pdf.ln(12)
    
    # Helper function
    def add_row(label, value):
        pdf.set_font('Helvetica', 'B', 10)
        pdf.cell(50, 6, label, border=0)
        pdf.set_font('Helvetica', '', 10)
        pdf.cell(0, 6, str(value or '-'), border=0, ln=True)
    
    # Section: Informasi Produk
    pdf.set_font('Helvetica', 'B', 12)
    pdf.set_text_color(25, 118, 210)
    pdf.cell(0, 8, 'Informasi Produk', ln=True)
    pdf.set_text_color(0, 0, 0)
    add_row('Jenis:', dso.jenis)
    add_row('Bahan:', dso.bahan)
    add_row('Warna:', dso.warna)
    add_row('Sablon:', dso.sablon)
    add_row('Posisi:', dso.posisi)
    pdf.ln(5)
    
    # Section: Aksesoris
    pdf.set_font('Helvetica', 'B', 12)
    pdf.set_text_color(25, 118, 210)
    pdf.cell(0, 8, 'Aksesoris', ln=True)
    pdf.set_text_color(0, 0, 0)
    add_row('Aksesoris 1:', dso.acc_1)
    add_row('Aksesoris 2:', dso.acc_2)
    add_row('Kancing:', dso.kancing)
    add_row('Saku:', dso.saku)
    pdf.ln(5)
    
    # Section: Size Chart Dewasa
    pdf.set_font('Helvetica', 'B', 12)
    pdf.set_text_color(25, 118, 210)
    pdf.cell(0, 8, 'Size Chart - Dewasa', ln=True)
    pdf.set_text_color(0, 0, 0)
    pdf.set_font('Helvetica', 'B', 9)
    pdf.set_fill_color(227, 242, 253)
    col_w = 19
    for s in ['Tipe', 'XS', 'S', 'M', 'L', 'XL', 'XXL', '3XL', '4XL', 'Total']:
        pdf.cell(col_w, 7, s, border=1, fill=True, align='C')
    pdf.ln()
    pdf.set_font('Helvetica', '', 9)
    pdf.cell(col_w, 7, 'Pendek', border=1, align='C')
    for v in [dewasa.pendek_xs if dewasa else 0, dewasa.pendek_s if dewasa else 0, 
              dewasa.pendek_m if dewasa else 0, dewasa.pendek_l if dewasa else 0,
              dewasa.pendek_xl if dewasa else 0, dewasa.pendek_xxl if dewasa else 0,
              dewasa.pendek_x3l if dewasa else 0, dewasa.pendek_x4l if dewasa else 0,
              dewasa.jum_pendek if dewasa else 0]:
        pdf.cell(col_w, 7, str(v), border=1, align='C')
    pdf.ln()
    pdf.cell(col_w, 7, 'Panjang', border=1, align='C')
    for v in [dewasa.panjang_xs if dewasa else 0, dewasa.panjang_s if dewasa else 0,
              dewasa.panjang_m if dewasa else 0, dewasa.panjang_l if dewasa else 0,
              dewasa.panjang_xl if dewasa else 0, dewasa.panjang_xxl if dewasa else 0,
              dewasa.panjang_x3l if dewasa else 0, dewasa.panjang_x4l if dewasa else 0,
              dewasa.jum_panjang if dewasa else 0]:
        pdf.cell(col_w, 7, str(v), border=1, align='C')
    pdf.ln()
    pdf.set_fill_color(255, 243, 224)
    pdf.set_font('Helvetica', 'B', 9)
    pdf.cell(col_w * 8, 7, 'Total Dewasa', border=1, fill=True, align='R')
    pdf.cell(col_w * 2, 7, f'{dewasa.total if dewasa else 0} pcs', border=1, fill=True, align='C')
    pdf.ln(10)
    
    # Section: Catatan
    pdf.set_font('Helvetica', 'B', 12)
    pdf.set_text_color(25, 118, 210)
    pdf.cell(0, 8, 'Catatan', ln=True)
    pdf.set_text_color(0, 0, 0)
    add_row('Label:', dso.label)
    add_row('Catatan 1:', dso.catatan_customer_1)
    add_row('Catatan 2:', dso.catatan_customer_2)
    
    # Output to buffer
    pdf_buffer = io.BytesIO()
    pdf.output(pdf_buffer)
    pdf_buffer.seek(0)
    
    return pdf_buffer

