"""PDF generation service using fpdf2 for better cross-platform compatibility."""
import io
from datetime import datetime
from fpdf import FPDF


class PremiumPDF(FPDF):
    def header(self):
        # This is for global header if needed, but we'll do custom ones for report
        pass

    def footer(self):
        self.set_y(-15)
        self.set_font('helvetica', 'I', 8)
        self.set_text_color(148, 163, 184) # slate-400
        self.cell(0, 10, f'Copyright © {datetime.now().year} Green Production Bandung. All rights reserved. | Page {self.page_no()}', 0, 0, 'C')


def generate_qc_analytics_pdf(report_data):
    """Generate QC Analytics Report PDF from summary data using fpdf2."""
    try:
        pdf = PremiumPDF()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()
        
        # Colors
        PRIMARY = (5, 150, 105) # #059669
        SECONDARY = (30, 41, 59) # #1e293b
        TEXT_MUTED = (100, 116, 139) # #64748b
        BG_LIGHT = (248, 250, 252) # #f8fafc
        BORDER_LIGHT = (226, 232, 240) # #e2e8f0
        
        # Grading Colors
        grade_colors = {
            'A': (5, 150, 105), # Emerald
            'B': (16, 185, 129), # Green
            'C': (245, 158, 11), # Amber
            'D': (217, 119, 6), # Orange
            'F': (220, 38, 38)  # Red
        }
        
        grade = report_data['summary']['quality_grade']
        grade_color = grade_colors.get(grade, (100, 116, 139))
        
        # --- HEADER ---
        pdf.set_font('helvetica', 'B', 20)
        pdf.set_text_color(*PRIMARY)
        pdf.cell(100, 10, 'GREEN PRODUCTION', ln=0)
        
        pdf.set_font('helvetica', 'B', 14)
        pdf.set_text_color(*SECONDARY)
        pdf.cell(0, 10, 'QC ANALYTICS REPORT', ln=1, align='R')
        
        pdf.set_font('helvetica', '', 9)
        pdf.set_text_color(*TEXT_MUTED)
        pdf.cell(100, 5, 'Bandung, Indonesia | High Quality Manufacturing', ln=0)
        
        pdf.set_font('helvetica', 'B', 9)
        pdf.set_text_color(*SECONDARY)
        pdf.cell(0, 5, f"Period: {report_data['period_start']} - {report_data['period_end']}", ln=1, align='R')
        
        pdf.set_font('helvetica', '', 9)
        pdf.set_text_color(*TEXT_MUTED)
        pdf.cell(100, 5, 'QC Management System v4.0', ln=0)
        pdf.cell(0, 5, f"Generated: {datetime.now().strftime('%d %b %Y, %H:%M')}", ln=1, align='R')
        
        pdf.ln(5)
        pdf.set_draw_color(*PRIMARY)
        pdf.set_line_width(0.5)
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        pdf.ln(10)
        
        # --- GRADE CARD ---
        start_y = pdf.get_y()
        # Redo light color for BG
        pdf.set_fill_color(int(grade_color[0] + (255-grade_color[0])*0.9), 
                          int(grade_color[1] + (255-grade_color[1])*0.9), 
                          int(grade_color[2] + (255-grade_color[2])*0.9))
        
        pdf.set_draw_color(*grade_color)
        pdf.set_line_width(0.5)
        pdf.rect(10, start_y, 190, 30, style='FD')
        
        pdf.set_font('helvetica', 'B', 10)
        pdf.set_text_color(*grade_color)
        pdf.set_y(start_y + 5)
        pdf.cell(190, 5, 'OVERALL QUALITY GRADE', ln=1, align='C')
        
        pdf.set_font('helvetica', 'B', 18)
        pdf.cell(190, 10, str(grade), ln=1, align='C')
        
        pdf.set_font('helvetica', '', 8)
        pdf.set_text_color(*TEXT_MUTED)
        pdf.cell(190, 5, 'Based on FPY, Quality Score, and Resolved Defects', ln=1, align='C')
        pdf.set_y(start_y + 35)
        
        # --- KPI GRID ---
        pdf.ln(5)
        pdf.set_font('helvetica', 'B', 11)
        pdf.set_text_color(*SECONDARY)
        pdf.cell(0, 10, 'KEY PERFORMANCE INDICATORS', ln=1)
        
        kpi_y = pdf.get_y()
        kpi_w = 45 # Each cell width
        
        def draw_kpi(x, y, label, value, subtext, color=(30, 41, 59)):
            pdf.set_fill_color(*BG_LIGHT)
            pdf.set_draw_color(*BORDER_LIGHT)
            pdf.rect(x, y, kpi_w, 20, style='FD')
            
            pdf.set_xy(x, y + 3)
            pdf.set_font('helvetica', 'B', 7)
            pdf.set_text_color(*TEXT_MUTED)
            pdf.cell(kpi_w, 4, label.upper(), ln=1, align='C')
            
            pdf.set_xy(x, y + 7)
            pdf.set_font('helvetica', 'B', 12)
            pdf.set_text_color(*color)
            pdf.cell(kpi_w, 8, str(value), ln=1, align='C')
            
            pdf.set_xy(x, y + 15)
            pdf.set_font('helvetica', '', 7)
            pdf.set_text_color(*TEXT_MUTED)
            pdf.cell(kpi_w, 4, subtext, ln=1, align='C')

        summary = report_data['summary']
        draw_kpi(10, kpi_y, 'First Pass Yield', f"{summary['fpy']}%", f"{summary['fpy_change']}% vs prev", PRIMARY if summary['fpy_trend'] == 'up' else (220, 38, 38))
        draw_kpi(57.5, kpi_y, 'Quality Score', summary['quality_score'], f"{summary['score_change']} vs prev", PRIMARY if summary['score_trend'] == 'up' else (220, 38, 38))
        draw_kpi(105, kpi_y, 'Total Inspected', summary['total_inspected'], 'Items Checked', SECONDARY)
        
        dr = round(summary['total_failed'] / summary['total_inspected'] * 100, 1) if summary['total_inspected'] > 0 else 0
        draw_kpi(152.5, kpi_y, 'Defect Rate', f"{dr}%", "Global Average", (156, 163, 175))
        
        pdf.set_y(kpi_y + 25)
        
        # --- PROCESS STAGE TABLE ---
        pdf.ln(5)
        pdf.set_font('helvetica', 'B', 11)
        pdf.set_text_color(*SECONDARY)
        pdf.cell(0, 10, 'PROCESS STAGE COMPARISON', ln=1)
        
        # Table Header
        pdf.set_fill_color(241, 245, 249)
        pdf.set_font('helvetica', 'B', 9)
        pdf.set_text_color(71, 85, 106)
        pdf.cell(50, 8, ' Stage', border=1, fill=True)
        pdf.cell(35, 8, ' Sheets', border=1, fill=True, align='C')
        pdf.cell(35, 8, ' Inspected', border=1, fill=True, align='C')
        pdf.cell(35, 8, ' NG Rate (%)', border=1, fill=True, align='C')
        pdf.cell(35, 8, ' Pass Rate (%)', border=1, fill=True, align='C')
        pdf.ln()
        
        pdf.set_font('helvetica', '', 9)
        pdf.set_text_color(*SECONDARY)
        for s in sorted(report_data['process_comparison'], key=lambda x: x['pass_rate'], reverse=True):
            pdf.cell(50, 8, f" {s['name']}", border=1)
            pdf.cell(35, 8, str(s['total_sheets']), border=1, align='C')
            pdf.cell(35, 8, str(s['total_inspected']), border=1, align='C')
            pdf.cell(35, 8, f"{s['ng_rate']}%", border=1, align='C')
            pdf.cell(35, 8, f"{s['pass_rate']}%", border=1, align='C')
            pdf.ln()
            
        # --- TOP ISSUES TABLE ---
        pdf.ln(10)
        pdf.set_font('helvetica', 'B', 11)
        pdf.set_text_color(*SECONDARY)
        pdf.cell(0, 10, 'TOP QUALITY ISSUES (CRITICAL PARAMETERS)', ln=1)
        
        # Table Header
        pdf.set_fill_color(241, 245, 249)
        pdf.set_font('helvetica', 'B', 9)
        pdf.set_text_color(71, 85, 106)
        pdf.cell(80, 8, ' Critical Parameter', border=1, fill=True)
        pdf.cell(25, 8, ' Checks', border=1, fill=True, align='C')
        pdf.cell(25, 8, ' NG Count', border=1, fill=True, align='C')
        pdf.cell(30, 8, ' Fail Rate (%)', border=1, fill=True, align='C')
        pdf.cell(30, 8, ' Trend', border=1, fill=True, align='C')
        pdf.ln()
        
        pdf.set_font('helvetica', '', 9)
        pdf.set_text_color(*SECONDARY)
        for p in report_data['top_issues']:
            pdf.cell(80, 8, f" {p['parameter']}", border=1)
            pdf.cell(25, 8, str(p['total_checked']), border=1, align='C')
            pdf.cell(25, 8, str(p['total_ng']), border=1, align='C')
            pdf.cell(30, 8, f"{p['avg_ng_rate']}%", border=1, align='C')
            
            trend_text = p['trend'].upper()
            if p['trend'] in ['up', 'declining']:
                pdf.set_text_color(220, 38, 38) # Red
            elif p['trend'] in ['down', 'improving']:
                pdf.set_text_color(5, 150, 105) # Green
            else:
                pdf.set_text_color(*TEXT_MUTED)
                
            pdf.cell(30, 8, trend_text, border=1, align='C')
            pdf.set_text_color(*SECONDARY)
            pdf.ln()
        
        # --- DEFECT SUMMARY ---
        pdf.ln(10)
        pdf.set_font('helvetica', 'B', 11)
        pdf.set_text_color(*SECONDARY)
        pdf.cell(0, 10, 'DEFECT STATISTICS', ln=1)
        
        pdf.set_font('helvetica', '', 9)
        pdf.cell(60, 8, 'Total Defects Logged', border='B')
        pdf.set_font('helvetica', 'B', 9)
        pdf.cell(30, 8, str(summary['total_defects']), border='B', align='R', ln=1)
        
        pdf.set_font('helvetica', '', 9)
        pdf.cell(60, 8, 'Open / Unresolved Issues', border='B')
        pdf.set_font('helvetica', 'B', 9)
        pdf.set_text_color(220, 38, 38)
        pdf.cell(30, 8, str(summary['open_defects']), border='B', align='R', ln=1)
        
        pdf.set_text_color(*SECONDARY)
        res_pct = round((summary['total_defects'] - summary['open_defects']) / summary['total_defects'] * 100, 1) if summary['total_defects'] > 0 else 100
        pdf.set_font('helvetica', '', 9)
        pdf.cell(60, 8, 'Resolution Percentage', border='B')
        pdf.set_font('helvetica', 'B', 9)
        pdf.cell(30, 8, f"{res_pct}%", border='B', align='R', ln=1)
        
        # DSO and QC Report placeholders (fixing weasyprint issues for others too)
        # We'll stick to analytics for now as requested.
        
        output = pdf.output()
        return {'success': True, 'pdf': output}
        
    except Exception as e:
        import traceback
        return {'success': False, 'error': str(e), 'traceback': traceback.format_exc()}


def generate_dso_pdf(dso):
    """Placeholder for DSO PDF - needs conversion to fpdf2 later."""
    return {'success': False, 'error': 'WeasyPrint not available. PDF service undergoing maintenance.'}


def generate_qc_report_pdf(qc_sheet):
    """Placeholder for QC Report PDF - needs conversion to fpdf2 later."""
    return {'success': False, 'error': 'WeasyPrint not available. PDF service undergoing maintenance.'}
