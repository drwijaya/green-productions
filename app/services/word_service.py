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
    """Export DSO to PDF using WeasyPrint (Linux/Railway compatible)."""
    from weasyprint import HTML, CSS
    
    order = dso.order
    dewasa = dso.size_chart_dewasa
    anak = dso.size_chart_anak
    
    # Build HTML for DSO
    html_content = f'''
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            @page {{ size: A4; margin: 1cm; }}
            body {{ font-family: Arial, sans-serif; font-size: 10pt; }}
            h1 {{ text-align: center; color: #2e7d32; font-size: 18pt; margin-bottom: 20px; }}
            h2 {{ color: #1976d2; font-size: 12pt; margin-top: 15px; border-bottom: 1px solid #ccc; padding-bottom: 5px; }}
            .header-info {{ display: flex; justify-content: space-between; margin-bottom: 20px; background: #f5f5f5; padding: 10px; border-radius: 5px; }}
            .header-item {{ text-align: center; }}
            .header-item strong {{ display: block; font-size: 11pt; }}
            table {{ width: 100%; border-collapse: collapse; margin: 10px 0; }}
            th, td {{ border: 1px solid #ddd; padding: 6px 8px; text-align: left; }}
            th {{ background: #e3f2fd; font-weight: bold; }}
            .size-table th {{ text-align: center; }}
            .size-table td {{ text-align: center; }}
            .total-row {{ background: #fff3e0; font-weight: bold; }}
            .image-container {{ text-align: center; margin: 15px 0; }}
            .image-container img {{ max-width: 300px; max-height: 300px; border: 1px solid #ddd; border-radius: 5px; }}
            .notes {{ background: #fffde7; padding: 10px; border-radius: 5px; margin-top: 10px; }}
        </style>
    </head>
    <body>
        <h1>DETAIL SPEC ORDER (DSO)</h1>
        
        <div class="header-info">
            <div class="header-item">
                <span>Invoice</span>
                <strong>{order.order_code or '-'}</strong>
            </div>
            <div class="header-item">
                <span>Model</span>
                <strong>{order.model or '-'}</strong>
            </div>
            <div class="header-item">
                <span>Deadline</span>
                <strong>{order.deadline.strftime('%d/%m/%Y') if order.deadline else '-'}</strong>
            </div>
            <div class="header-item">
                <span>Versi</span>
                <strong>v{dso.version}</strong>
            </div>
        </div>
        
        <h2>Informasi Produk</h2>
        <table>
            <tr><th width="30%">Jenis</th><td>{dso.jenis or '-'}</td></tr>
            <tr><th>Bahan</th><td>{dso.bahan or '-'}</td></tr>
            <tr><th>Warna</th><td>{dso.warna or '-'}</td></tr>
            <tr><th>Sablon</th><td>{dso.sablon or '-'}</td></tr>
            <tr><th>Posisi</th><td>{dso.posisi or '-'}</td></tr>
        </table>
        
        <h2>Aksesoris</h2>
        <table>
            <tr>
                <th>Aksesoris 1</th><td>{dso.acc_1 or '-'}</td>
                <th>Aksesoris 2</th><td>{dso.acc_2 or '-'}</td>
            </tr>
            <tr>
                <th>Aksesoris 3</th><td>{dso.acc_3 or '-'}</td>
                <th>Aksesoris 4</th><td>{dso.acc_4 or '-'}</td>
            </tr>
            <tr>
                <th>Kancing</th><td>{dso.kancing or '-'}</td>
                <th>Saku</th><td>{dso.saku or '-'}</td>
            </tr>
            <tr>
                <th>Resleting</th><td>{dso.resleting or '-'}</td>
                <th>Model Badan Bawah</th><td>{dso.model_badan_bawah or '-'}</td>
            </tr>
        </table>
        
        <h2>Size Chart - Dewasa</h2>
        <table class="size-table">
            <tr>
                <th>Tipe</th><th>XS</th><th>S</th><th>M</th><th>L</th><th>XL</th><th>XXL</th><th>3XL</th><th>4XL</th><th>5XL</th><th>Total</th>
            </tr>
            <tr>
                <td><strong>Pendek</strong></td>
                <td>{dewasa.pendek_xs if dewasa else 0}</td>
                <td>{dewasa.pendek_s if dewasa else 0}</td>
                <td>{dewasa.pendek_m if dewasa else 0}</td>
                <td>{dewasa.pendek_l if dewasa else 0}</td>
                <td>{dewasa.pendek_xl if dewasa else 0}</td>
                <td>{dewasa.pendek_xxl if dewasa else 0}</td>
                <td>{dewasa.pendek_x3l if dewasa else 0}</td>
                <td>{dewasa.pendek_x4l if dewasa else 0}</td>
                <td>{dewasa.pendek_x5l if dewasa else 0}</td>
                <td><strong>{dewasa.jum_pendek if dewasa else 0}</strong></td>
            </tr>
            <tr>
                <td><strong>Panjang</strong></td>
                <td>{dewasa.panjang_xs if dewasa else 0}</td>
                <td>{dewasa.panjang_s if dewasa else 0}</td>
                <td>{dewasa.panjang_m if dewasa else 0}</td>
                <td>{dewasa.panjang_l if dewasa else 0}</td>
                <td>{dewasa.panjang_xl if dewasa else 0}</td>
                <td>{dewasa.panjang_xxl if dewasa else 0}</td>
                <td>{dewasa.panjang_x3l if dewasa else 0}</td>
                <td>{dewasa.panjang_x4l if dewasa else 0}</td>
                <td>-</td>
                <td><strong>{dewasa.jum_panjang if dewasa else 0}</strong></td>
            </tr>
            <tr class="total-row">
                <td colspan="9"><strong>Total Dewasa</strong></td>
                <td colspan="2"><strong>{dewasa.total if dewasa else 0} pcs</strong></td>
            </tr>
        </table>
        
        <h2>Size Chart - Anak</h2>
        <table class="size-table">
            <tr>
                <th>Tipe</th><th>XS</th><th>S</th><th>M</th><th>L</th><th>XL</th><th>XXL</th><th>3XL</th><th>4XL</th><th>5XL</th><th>Total</th>
            </tr>
            <tr>
                <td><strong>Pendek</strong></td>
                <td>{anak.pendek_xs if anak else 0}</td>
                <td>{anak.pendek_s if anak else 0}</td>
                <td>{anak.pendek_m if anak else 0}</td>
                <td>{anak.pendek_l if anak else 0}</td>
                <td>{anak.pendek_xl if anak else 0}</td>
                <td>{anak.pendek_xxl if anak else 0}</td>
                <td>{anak.pendek_x3l if anak else 0}</td>
                <td>{anak.pendek_x4l if anak else 0}</td>
                <td>{anak.pendek_x5l if anak else 0}</td>
                <td><strong>{anak.jum_pendek if anak else 0}</strong></td>
            </tr>
            <tr>
                <td><strong>Panjang</strong></td>
                <td>{anak.panjang_xs if anak else 0}</td>
                <td>{anak.panjang_s if anak else 0}</td>
                <td>{anak.panjang_m if anak else 0}</td>
                <td>{anak.panjang_l if anak else 0}</td>
                <td>{anak.panjang_xl if anak else 0}</td>
                <td>{anak.panjang_xxl if anak else 0}</td>
                <td>{anak.panjang_x3l if anak else 0}</td>
                <td>{anak.panjang_x4l if anak else 0}</td>
                <td>-</td>
                <td><strong>{anak.jum_panjang if anak else 0}</strong></td>
            </tr>
            <tr class="total-row">
                <td colspan="9"><strong>Total Anak</strong></td>
                <td colspan="2"><strong>{anak.total if anak else 0} pcs</strong></td>
            </tr>
        </table>
        
        {'<h2>Gambar Design</h2><div class="image-container"><img src="' + dso.gambar_depan_url + '" alt="Design"></div>' if dso.gambar_depan_url else ''}
        
        <h2>Catatan</h2>
        <div class="notes">
            <p><strong>Label:</strong> {dso.label or '-'}</p>
            <p><strong>Catatan 1:</strong> {dso.catatan_customer_1 or '-'}</p>
            <p><strong>Catatan 2:</strong> {dso.catatan_customer_2 or '-'}</p>
            <p><strong>Catatan 3:</strong> {dso.catatan_customer_3 or '-'}</p>
        </div>
    </body>
    </html>
    '''
    
    # Generate PDF
    pdf_buffer = io.BytesIO()
    HTML(string=html_content).write_pdf(pdf_buffer)
    pdf_buffer.seek(0)
    
    return pdf_buffer

