"""PDF generation service using WeasyPrint."""
import io
from datetime import datetime
from flask import render_template_string


def generate_dso_pdf(dso):
    """Generate DSO PDF document."""
    try:
        from weasyprint import HTML
        
        order = dso.order
        
        html_content = f'''
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{ font-family: Arial, sans-serif; font-size: 12px; margin: 20px; }}
                .header {{ text-align: center; border-bottom: 2px solid #333; padding-bottom: 10px; margin-bottom: 20px; }}
                .header h1 {{ margin: 0; font-size: 18px; }}
                .header h2 {{ margin: 5px 0; font-size: 14px; color: #666; }}
                .info-table {{ width: 100%; border-collapse: collapse; margin-bottom: 20px; }}
                .info-table td {{ padding: 8px; border: 1px solid #ddd; }}
                .info-table .label {{ background: #f5f5f5; font-weight: bold; width: 150px; }}
                .section {{ margin-bottom: 20px; }}
                .section h3 {{ background: #333; color: white; padding: 8px; margin: 0 0 10px 0; font-size: 14px; }}
                .accessories-table {{ width: 100%; border-collapse: collapse; }}
                .accessories-table th, .accessories-table td {{ padding: 8px; border: 1px solid #ddd; text-align: left; }}
                .accessories-table th {{ background: #f5f5f5; }}
                .sizes-table {{ width: 100%; border-collapse: collapse; }}
                .sizes-table th, .sizes-table td {{ padding: 8px; border: 1px solid #ddd; text-align: center; }}
                .sizes-table th {{ background: #f5f5f5; }}
                .footer {{ text-align: center; margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd; font-size: 10px; color: #666; }}
                .approval {{ margin-top: 40px; }}
                .approval-box {{ display: inline-block; width: 45%; text-align: center; }}
                .approval-line {{ border-top: 1px solid #333; margin-top: 60px; padding-top: 5px; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>GREEN PRODUCTION BANDUNG</h1>
                <h2>DSO - Digital Standard Operation</h2>
                <p>Version {dso.version} | {dso.status.value.upper()}</p>
            </div>
            
            <div class="section">
                <h3>Order Information</h3>
                <table class="info-table">
                    <tr><td class="label">Order Code</td><td>{order.order_code}</td></tr>
                    <tr><td class="label">Model</td><td>{order.model}</td></tr>
                    <tr><td class="label">Customer</td><td>{order.customer.name if order.customer else '-'}</td></tr>
                    <tr><td class="label">Quantity</td><td>{order.qty_total} pcs</td></tr>
                    <tr><td class="label">Deadline</td><td>{order.deadline.strftime('%d/%m/%Y') if order.deadline else '-'}</td></tr>
                </table>
            </div>
            
            <div class="section">
                <h3>Material Specifications</h3>
                <table class="info-table">
                    <tr><td class="label">Bahan</td><td>{dso.bahan or '-'}</td></tr>
                    <tr><td class="label">Warna</td><td>{dso.warna or '-'}</td></tr>
                    <tr><td class="label">Gramasi</td><td>{dso.gramasi or '-'}</td></tr>
                    <tr><td class="label">Jahitan</td><td>{dso.jahitan or '-'}</td></tr>
                    <tr><td class="label">Benang</td><td>{dso.benang or '-'}</td></tr>
                </table>
            </div>
            
            <div class="section">
                <h3>Accessories (ACC)</h3>
                <table class="accessories-table">
                    <thead>
                        <tr><th>No</th><th>Item</th><th>Specification</th><th>Qty</th><th>Notes</th></tr>
                    </thead>
                    <tbody>
                        {''.join(f'<tr><td>{i+1}</td><td>{acc.name}</td><td>{acc.specification or "-"}</td><td>{acc.qty or "-"}</td><td>{acc.notes or "-"}</td></tr>' for i, acc in enumerate(dso.accessories.all())) or '<tr><td colspan="5" style="text-align:center">No accessories</td></tr>'}
                    </tbody>
                </table>
            </div>
            
            <div class="section">
                <h3>Size Specifications</h3>
                <table class="sizes-table">
                    <thead>
                        <tr><th>Size</th><th>Qty</th><th>Notes</th></tr>
                    </thead>
                    <tbody>
                        {''.join(f'<tr><td>{size.size_label}</td><td>{size.qty}</td><td>{size.notes or "-"}</td></tr>' for size in dso.sizes.all()) or '<tr><td colspan="3" style="text-align:center">No sizes defined</td></tr>'}
                    </tbody>
                </table>
            </div>
            
            <div class="section">
                <h3>Notes</h3>
                <p><strong>Production Notes:</strong> {dso.catatan_produksi or '-'}</p>
                <p><strong>Customer Notes:</strong> {dso.catatan_customer or '-'}</p>
            </div>
            
            <div class="approval">
                <div class="approval-box">
                    <div class="approval-line">Prepared By</div>
                </div>
                <div class="approval-box">
                    <div class="approval-line">Approved By</div>
                </div>
            </div>
            
            <div class="footer">
                <p>Generated: {datetime.now().strftime('%d/%m/%Y %H:%M')} | GREEN PRODUCTION BANDUNG</p>
            </div>
        </body>
        </html>
        '''
        
        html = HTML(string=html_content)
        pdf = html.write_pdf()
        
        return {'success': True, 'pdf': pdf}
        
    except Exception as e:
        return {'success': False, 'error': str(e)}


def generate_qc_report_pdf(qc_sheet):
    """Generate QC Report PDF."""
    try:
        from weasyprint import HTML
        
        task = qc_sheet.production_task
        order = task.order
        
        html_content = f'''
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{ font-family: Arial, sans-serif; font-size: 12px; margin: 20px; }}
                .header {{ text-align: center; margin-bottom: 20px; }}
                .result-pass {{ color: green; font-weight: bold; }}
                .result-fail {{ color: red; font-weight: bold; }}
                table {{ width: 100%; border-collapse: collapse; margin-bottom: 15px; }}
                th, td {{ padding: 8px; border: 1px solid #ddd; }}
                th {{ background: #f5f5f5; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>QC Inspection Report</h1>
                <p>{qc_sheet.inspection_code}</p>
            </div>
            
            <table>
                <tr><td><strong>Order</strong></td><td>{order.order_code} - {order.model}</td></tr>
                <tr><td><strong>Process</strong></td><td>{task.process.value.title()}</td></tr>
                <tr><td><strong>Inspector</strong></td><td>{qc_sheet.inspector.name if qc_sheet.inspector else '-'}</td></tr>
                <tr><td><strong>Date</strong></td><td>{qc_sheet.inspected_at.strftime('%d/%m/%Y %H:%M') if qc_sheet.inspected_at else '-'}</td></tr>
                <tr><td><strong>Result</strong></td><td class="result-{qc_sheet.result.value}">{qc_sheet.result.value.upper()}</td></tr>
            </table>
            
            <h3>Inspection Summary</h3>
            <table>
                <tr><td>Qty Inspected</td><td>{qc_sheet.qty_inspected}</td></tr>
                <tr><td>Qty Passed</td><td>{qc_sheet.qty_passed}</td></tr>
                <tr><td>Qty Failed</td><td>{qc_sheet.qty_failed}</td></tr>
                <tr><td>Pass Rate</td><td>{qc_sheet.get_pass_rate()}%</td></tr>
            </table>
            
            <h3>Defects Found</h3>
            <table>
                <thead><tr><th>Type</th><th>Severity</th><th>Qty</th><th>Description</th></tr></thead>
                <tbody>
                    {''.join(f'<tr><td>{d.defect_type}</td><td>{d.severity.value}</td><td>{d.qty_defect}</td><td>{d.description or "-"}</td></tr>' for d in qc_sheet.defects.all()) or '<tr><td colspan="4" style="text-align:center">No defects</td></tr>'}
                </tbody>
            </table>
            
            <p><strong>Notes:</strong> {qc_sheet.notes or '-'}</p>
        </body>
        </html>
        '''
        
        html = HTML(string=html_content)
        pdf = html.write_pdf()
        
        return {'success': True, 'pdf': pdf}
        
    except Exception as e:
        return {'success': False, 'error': str(e)}
