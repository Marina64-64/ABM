from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
import os
import re

def generate_professional_pdf(input_file, output_file):
    if not os.path.exists(input_file):
        print(f"Error: {input_file} not found")
        return

    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # Explicitly Portrait A4
    doc = SimpleDocTemplate(
        output_file, 
        pagesize=A4, 
        rightMargin=50, 
        leftMargin=50, 
        topMargin=50, 
        bottomMargin=50
    )
    styles = getSampleStyleSheet()
    
    # Custom Styles
    title_style = ParagraphStyle('MainTitle', parent=styles['Heading1'], fontSize=18, spaceAfter=12)
    h2_style = ParagraphStyle('H2', parent=styles['Heading2'], fontSize=14, spaceBefore=10, spaceAfter=6)
    h3_style = ParagraphStyle('H3', parent=styles['Heading3'], fontSize=12, spaceBefore=8, spaceAfter=4)
    body_style = ParagraphStyle('Body', parent=styles['Normal'], fontSize=10, leading=12)

    story = []
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
                # Dynamic column width calculation for Portrait
                col_count = len(table_data[0])
                available_width = doc.width  # Margin aware width
                col_width = available_width / col_count
                
                t = Table(table_data, colWidths=[col_width]*col_count)
                t.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                    ('GRID', (0,0), (-1,-1), 0.5, colors.grey)
                ]))
                story.append(t)
            in_table = False
            table_data = []

        if not line:
            story.append(Spacer(1, 6))
            continue

        if line.startswith('# '):
            story.append(Paragraph(line[2:], title_style))
        elif line.startswith('## '):
            story.append(Paragraph(line[3:], h2_style))
        elif line.startswith('### '):
            story.append(Paragraph(line[4:], h3_style))
        elif line.startswith('* ') or line.startswith('- '):
            story.append(Paragraph(f"&bull; {line[2:]}", body_style))
        else:
            # Proper Markdown Bold to HTML conversion
            clean_text = line
            # Replace **text** with <b>text</b>
            clean_text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', clean_text)
            # Escape & for XML
            clean_text = clean_text.replace('&', '&amp;')
            story.append(Paragraph(clean_text, body_style))

    doc.build(story)
    print(f"✅ Portrait A4 PDF successfully regenerated: {output_file}")

if __name__ == "__main__":
    generate_professional_pdf("docs/Task1QA_MarinaNashaat.md", "docs/Task1QA_MarinaNashaat.pdf")
