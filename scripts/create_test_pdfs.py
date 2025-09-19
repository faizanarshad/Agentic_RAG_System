#!/usr/bin/env python3
"""
Script to create PDF test documents for the RAG system.
This converts text files to PDFs for testing purposes.
"""

import os
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch

def create_pdf_from_text(text_file, output_pdf):
    """Convert a text file to PDF format."""
    
    # Read the text file
    with open(text_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Create PDF document
    doc = SimpleDocTemplate(output_pdf, pagesize=letter)
    styles = getSampleStyleSheet()
    
    # Create custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=16,
        spaceAfter=12,
        fontName='Helvetica-Bold'
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        spaceAfter=8,
        fontName='Helvetica-Bold'
    )
    
    body_style = ParagraphStyle(
        'CustomBody',
        parent=styles['Normal'],
        fontSize=11,
        spaceAfter=6,
        fontName='Helvetica'
    )
    
    # Parse content and create paragraphs
    story = []
    lines = content.split('\n')
    
    for line in lines:
        line = line.strip()
        if not line:
            story.append(Spacer(1, 6))
        elif line.startswith('# '):
            # Main title
            story.append(Paragraph(line[2:], title_style))
            story.append(Spacer(1, 12))
        elif line.startswith('## '):
            # Section heading
            story.append(Paragraph(line[3:], heading_style))
            story.append(Spacer(1, 8))
        elif line.startswith('### '):
            # Subsection heading
            story.append(Paragraph(line[4:], heading_style))
            story.append(Spacer(1, 6))
        elif line.startswith('- '):
            # Bullet point
            story.append(Paragraph(f"• {line[2:]}", body_style))
        elif line.startswith('**') and line.endswith('**'):
            # Bold text
            bold_text = line[2:-2]
            story.append(Paragraph(f"<b>{bold_text}</b>", body_style))
        else:
            # Regular paragraph
            if line:
                story.append(Paragraph(line, body_style))
    
    # Build PDF
    doc.build(story)
    print(f"Created PDF: {output_pdf}")

def main():
    """Create PDF test documents."""
    
    # Create sample_documents directory if it doesn't exist
    os.makedirs('sample_documents', exist_ok=True)
    
    # Define text files and their corresponding PDF outputs
    documents = [
        ('sample_documents/ai_ml_basics.txt', 'sample_documents/ai_ml_basics.pdf'),
        ('sample_documents/rag_systems.txt', 'sample_documents/rag_systems.pdf')
    ]
    
    print("Creating PDF test documents...")
    
    for text_file, pdf_file in documents:
        if os.path.exists(text_file):
            create_pdf_from_text(text_file, pdf_file)
        else:
            print(f"Warning: {text_file} not found")
    
    print("\nPDF test documents created successfully!")
    print("You can now upload these PDFs to test your RAG system:")
    print("- sample_documents/ai_ml_basics.pdf")
    print("- sample_documents/rag_systems.pdf")

if __name__ == "__main__":
    main()
