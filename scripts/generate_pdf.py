from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, HRFlowable
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
import os
import re

# Color Palette: Corporate Professional
NAVY = colors.HexColor("#002D62")
BLUE_ACCENT = colors.HexColor("#0076CE")
LIGHT_BG = colors.HexColor("#F9FBFD")
BORDER_COLOR = colors.HexColor("#D1D9E6")
TEXT_COLOR = colors.HexColor("#333333")

def draw_header_footer(canvas, doc):
    canvas.saveState()
    # Sidebar Decorative Line
    canvas.setStrokeColor(BLUE_ACCENT)
    canvas.setLineWidth(2)
    canvas.line(0.5*inch, 0.5*inch, 0.5*inch, A4[1]-0.5*inch)
    
    # Header Title
    canvas.setFont('Helvetica-Bold', 8)
    canvas.setFillColor(colors.grey)
    canvas.drawString(0.75*inch, A4[1]-0.4*inch, "MARINA NASHAAT | TECHNICAL ASSESSMENT REPORT")
    
    # Footer
    canvas.setFont('Helvetica', 8)
    canvas.setFillColor(colors.grey)
    page_num = canvas.getPageNumber()
    canvas.drawString(0.75*inch, 0.4*inch, "© 2026 ABM Egypt Submission")
    canvas.drawRightString(A4[0]-0.75*inch, 0.4*inch, f"Page {page_num}")
    canvas.restoreState()

def generate_premium_pdf(input_file, output_file):
    if not os.path.exists(input_file):
        print(f"Error: {input_file} not found")
        return

    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()

    doc = SimpleDocTemplate(
        output_file, 
        pagesize=A4, 
        rightMargin=50, 
        leftMargin=70,  # More room for the sidebar line
        topMargin=60, 
        bottomMargin=60
    )
    styles = getSampleStyleSheet()
    
    # --- Custom Styles ---
    cover_title = ParagraphStyle('CoverTitle', parent=styles['Heading1'], fontSize=28, leading=34, alignment=TA_CENTER, spaceAfter=12, textColor=NAVY, fontName='Helvetica-Bold')
    cover_tagline = ParagraphStyle('CoverTag', parent=styles['Normal'], fontSize=12, alignment=TA_CENTER, spaceAfter=80, textColor=BLUE_ACCENT, letterSpacing=2)
    cover_info = ParagraphStyle('CoverInfo', parent=styles['Normal'], fontSize=11, alignment=TA_CENTER, leading=16, textColor=TEXT_COLOR)
    
    h1_style = ParagraphStyle('H1', parent=styles['Heading1'], fontSize=20, leading=24, spaceAfter=20, textColor=NAVY, fontName='Helvetica-Bold')
    h2_style = ParagraphStyle('H2', parent=styles['Heading2'], fontSize=14, leading=18, spaceBefore=20, spaceAfter=12, textColor=BLUE_ACCENT, fontName='Helvetica-Bold', borderPadding=(5,0,5,0), borderAlpha=0)
    h3_style = ParagraphStyle('H3', parent=styles['Heading3'], fontSize=11, spaceBefore=12, spaceAfter=8, textColor=TEXT_COLOR, fontName='Helvetica-Bold')
    body_style = ParagraphStyle('Body', parent=styles['Normal'], fontSize=10, leading=14, spaceAfter=8, textColor=TEXT_COLOR)

    story = []

    # --- COVER PAGE ---
    story.append(Spacer(1, 2.5*inch))
    story.append(Paragraph("Task 1: Automation Verification & Analysis", cover_title))
    story.append(Paragraph("TECHNICAL DOCUMENTATION", cover_tagline))
    story.append(HRFlowable(width="30%", thickness=1, color=BORDER_COLOR, spaceAfter=40))
    story.append(Spacer(1, 0.5*inch))
    story.append(Paragraph("<b>Prepared For:</b> ABM Egypt Recruitment Team", cover_info))
    story.append(Paragraph("<b>Lead Engineer:</b> Marina Nashaat", cover_info))
    story.append(Paragraph("<b>Submission Version:</b> 1.0.4", cover_info))
    story.append(PageBreak())

    # --- CONTENT PAGES ---
    lines = content.split('\n')
    in_table = False
    table_data = []

    for line in lines:
        line = line.strip()
        
        if line.startswith('|'):
            if not in_table:
                in_table = True
                table_data = []
            
            row = [cell.strip() for cell in line.split('|') if cell.strip()]
            if row and not all(c == '-' for c in row[0]):
                table_data.append([Paragraph(cell, body_style) for cell in row])
            continue
        elif in_table:
            if table_data:
                col_count = len(table_data[0])
                available_width = doc.width
                col_width = available_width / col_count
                
                t = Table(table_data, colWidths=[col_width]*col_count)
                t.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), NAVY),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                    ('LEFTPADDING', (0, 0), (-1, -1), 10),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 10),
                    ('TOPPADDING', (0, 0), (-1, -1), 8),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                    ('GRID', (0,0), (-1,-1), 0.5, BORDER_COLOR),
                    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, LIGHT_BG])
                ]))
                story.append(t)
                story.append(Spacer(1, 15))
            in_table = False
            table_data = []

        if not line:
            story.append(Spacer(1, 6))
            continue

        if line.startswith('# '):
            story.append(Paragraph(line[2:], h1_style))
            story.append(HRFlowable(width="100%", thickness=0.5, color=BORDER_COLOR, spaceAfter=10))
        elif line.startswith('## '):
            story.append(Paragraph(line[3:], h2_style))
        elif line.startswith('### '):
            story.append(Paragraph(line[4:], h3_style))
        elif line.startswith('* ') or line.startswith('- '):
            story.append(Paragraph(f"<b>&bull;</b> {line[2:]}", body_style))
        else:
            # Handle Markdown Bold (**text**)
            clean_text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', line)
            clean_text = clean_text.replace('&', '&amp;')
            story.append(Paragraph(clean_text, body_style))

    doc.build(story, onFirstPage=draw_header_footer, onLaterPages=draw_header_footer)
    print(f"✅ Premium PDF successfully generated: {output_file}")

if __name__ == "__main__":
    generate_premium_pdf("docs/Task1QA_MarinaNashaat.md", "docs/Task1QA_MarinaNashaat.pdf")
