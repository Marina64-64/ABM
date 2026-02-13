from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, HRFlowable, Image
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
import os
import re
from datetime import datetime

# --- Premium Design Tokens ---
indigo = colors.HexColor("#1A237E")  # Deep Indigo (Primary)
slate_blue = colors.HexColor("#3949AB") # Secondary
soft_grey = colors.HexColor("#F5F7F9") # Backgrounds
border_color = colors.HexColor("#E0E6ED")
accent_gold = colors.HexColor("#FFD700") # Subtle accent
text_main = colors.HexColor("#2C3E50")
text_muted = colors.HexColor("#7F8C8D")

def draw_branding(canvas, doc):
    canvas.saveState()
    # Left Vertical Accents
    canvas.setFillColor(indigo)
    canvas.rect(0, 0, 0.4*inch, A4[1], fill=1, stroke=0)
    canvas.setFillColor(slate_blue)
    canvas.rect(0, A4[1] - 1.5*inch, 0.4*inch, 0.5*inch, fill=1, stroke=0)
    
    # Header Info
    canvas.setFont('Helvetica-Bold', 9)
    canvas.setFillColor(indigo)
    canvas.drawString(0.6*inch, A4[1]-0.5*inch, "MARINA NASHAAT")
    
    # Footer
    canvas.setFont('Helvetica', 8)
    canvas.setFillColor(text_muted)
    canvas.drawString(0.6*inch, 0.4*inch, "ABM Technical Assessment")
    
    # Page Number with indigo box
    canvas.setFillColor(indigo)
    canvas.rect(A4[0]-0.8*inch, 0.3*inch, 0.35*inch, 0.2*inch, fill=1, stroke=0)
    canvas.setFillColor(colors.white)
    canvas.setFont('Helvetica-Bold', 8)
    canvas.drawRightString(A4[0]-0.5*inch, 0.37*inch, str(doc.page))
    
    canvas.restoreState()

def generate_premium_report(input_file, output_file):
    if not os.path.exists(input_file):
        print(f"Error: {input_file} not found")
        return

    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()

    doc = SimpleDocTemplate(
        output_file, 
        pagesize=A4, 
        rightMargin=40, 
        leftMargin=60, 
        topMargin=80, 
        bottomMargin=60
    )
    
    styles = getSampleStyleSheet()
    
    # --- Advanced Typographic Styles ---
    cover_h1 = ParagraphStyle('CH1', fontSize=32, leading=38, textColor=indigo, fontName='Helvetica-Bold', spaceAfter=10)
    cover_h2 = ParagraphStyle('CH2', fontSize=14, leading=18, textColor=slate_blue, letterSpacing=3, spaceAfter=80)
    
    h1_style = ParagraphStyle('H1', fontSize=22, leading=26, textColor=indigo, fontName='Helvetica-Bold', spaceBefore=30, spaceAfter=15)
    h2_style = ParagraphStyle('H2', fontSize=16, leading=20, textColor=slate_blue, fontName='Helvetica-Bold', spaceBefore=20, spaceAfter=10)
    h3_style = ParagraphStyle('H3', fontSize=11, leading=14, textColor=text_main, fontName='Helvetica-Bold', spaceBefore=12, spaceAfter=6)
    
    body_style = ParagraphStyle('BodyText', parent=styles['Normal'], fontSize=10.5, leading=15, textColor=text_main, spaceAfter=10)
    list_style = ParagraphStyle('List', parent=body_style, leftIndent=20, firstLineIndent=0, spaceBefore=2, spaceAfter=2)
    
    story = []

    # --- LUXURY COVER PAGE ---
    story.append(Spacer(1, 2*inch))
    story.append(Paragraph("QA & Automation<br/>Verification Report", cover_h1))
    story.append(Paragraph("TECHNICAL ASSESSMENT REPORT", cover_h2))
    
    story.append(HRFlowable(width="20%", thickness=3, color=indigo, lineCap='round', spaceAfter=100, hAlign='LEFT'))
    
    # Summary Box on Cover
    summary_data = [
        [Paragraph("Marina Nashaat", body_style)],
        [Paragraph("ABM Egypt Recruitment Team", body_style)],
        [Paragraph("<font color='#27AE60'>Technical Assessment Submission</font>", body_style)]
    ]
    st = Table(summary_data, colWidths=[3*inch])
    st.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), soft_grey),
        ('LEFTPADDING', (0,0), (-1,-1), 20),
        ('TOPPADDING', (0,0), (-1,-1), 15),
        ('BOTTOMPADDING', (0,0), (-1,-1), 15),
        ('LINEABOVE', (0,0), (0,0), 2, indigo),
    ]))
    story.append(st)
    story.append(PageBreak())

    # --- DYNAMIC CONTENT PARSER ---
    lines = content.split('\n')
    in_table = False
    table_data = []

    for line in lines:
        line = line.strip()
        
        # Tables detection
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
                t = Table(table_data, colWidths=[(doc.width/col_count)]*col_count)
                t.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), indigo),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                    ('LEFTPADDING', (0, 0), (-1, -1), 12),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
                    ('GRID', (0,0), (-1,-1), 0.5, border_color),
                    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, soft_grey])
                ]))
                story.append(Spacer(1, 10))
                story.append(t)
                story.append(Spacer(1, 20))
            in_table = False
            table_data = []

        if not line:
            story.append(Spacer(1, 8))
            continue

        # Markdown Processing
        line = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', line)
        line = line.replace('&', '&amp;')

        if line.startswith('# '):
            story.append(Paragraph(line[2:], h1_style))
            story.append(HRFlowable(width="100%", thickness=1, color=indigo, spaceAfter=15))
        elif line.startswith('## '):
            story.append(Paragraph(line[3:], h2_style))
        elif line.startswith('### '):
            story.append(Paragraph(line[4:], h3_style))
        elif line.startswith('* ') or line.startswith('- '):
            # Indigo dot list
            story.append(Paragraph(f"<font color='#1A237E'>&bull;</font> {line[2:]}", list_style))
        else:
            story.append(Paragraph(line, body_style))

    doc.build(story, onFirstPage=draw_branding, onLaterPages=draw_branding)
    print(f"✅ Premium Executive Report successfully generated: {output_file}")

if __name__ == "__main__":
    generate_premium_report("docs/Task1QA_MarinaNashaat.md", "docs/Task1QA_MarinaNashaat.pdf")
