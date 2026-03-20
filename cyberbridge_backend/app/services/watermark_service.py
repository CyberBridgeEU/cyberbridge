# services/watermark_service.py
"""
Watermark Service - Adds watermarks to downloaded files.
Supports PDF and image files.
Watermark includes: auditor name, date, engagement ID, "CONFIDENTIAL" marking.
"""
import os
import uuid
from datetime import datetime
from typing import Optional, BinaryIO
from io import BytesIO

from PIL import Image, ImageDraw, ImageFont


def add_watermark_to_pdf(
    pdf_buffer: BinaryIO,
    auditor_name: str,
    engagement_id: str,
    engagement_name: str
) -> BytesIO:
    """
    Add watermark overlay to a PDF file.
    """
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.colors import Color
    from reportlab.pdfgen import canvas
    from PyPDF2 import PdfReader, PdfWriter

    # Create watermark PDF
    watermark_buffer = BytesIO()
    c = canvas.Canvas(watermark_buffer, pagesize=A4)
    width, height = A4

    # Set watermark properties
    c.setFont("Helvetica", 10)
    watermark_color = Color(0.7, 0.7, 0.7, alpha=0.5)  # Light gray, semi-transparent
    c.setFillColor(watermark_color)

    # Create watermark text
    watermark_text = f"CONFIDENTIAL - {auditor_name} - {datetime.utcnow().strftime('%Y-%m-%d')} - {engagement_name[:30]}"

    # Add watermark at multiple positions
    c.saveState()
    c.translate(width / 2, height / 2)
    c.rotate(45)
    c.setFont("Helvetica-Bold", 40)
    c.drawCentredString(0, 0, "CONFIDENTIAL")
    c.restoreState()

    # Footer watermark
    c.setFont("Helvetica", 8)
    c.setFillColor(Color(0.5, 0.5, 0.5, alpha=0.8))
    footer_text = f"Downloaded by: {auditor_name} | Date: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')} | Engagement: {engagement_id[:8]}"
    c.drawString(20, 20, footer_text)

    c.save()
    watermark_buffer.seek(0)

    # Read the watermark PDF
    watermark_pdf = PdfReader(watermark_buffer)
    watermark_page = watermark_pdf.pages[0]

    # Read the original PDF
    pdf_buffer.seek(0)
    original_pdf = PdfReader(pdf_buffer)
    output = PdfWriter()

    # Merge watermark with each page
    for page in original_pdf.pages:
        page.merge_page(watermark_page)
        output.add_page(page)

    # Write output
    result_buffer = BytesIO()
    output.write(result_buffer)
    result_buffer.seek(0)

    return result_buffer


def add_watermark_to_image(
    image_buffer: BinaryIO,
    auditor_name: str,
    engagement_id: str,
    engagement_name: str,
    file_type: str = "png"
) -> BytesIO:
    """
    Add watermark to an image file.
    """
    # Open image
    image_buffer.seek(0)
    image = Image.open(image_buffer)

    # Convert to RGBA if necessary
    if image.mode != 'RGBA':
        image = image.convert('RGBA')

    # Create watermark overlay
    watermark_layer = Image.new('RGBA', image.size, (255, 255, 255, 0))
    draw = ImageDraw.Draw(watermark_layer)

    # Try to use a system font, fallback to default
    try:
        # Try common system fonts
        font_paths = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
            "/System/Library/Fonts/Helvetica.ttc",
            "C:\\Windows\\Fonts\\arial.ttf"
        ]

        font = None
        for font_path in font_paths:
            if os.path.exists(font_path):
                font = ImageFont.truetype(font_path, 24)
                small_font = ImageFont.truetype(font_path, 14)
                break

        if font is None:
            font = ImageFont.load_default()
            small_font = font
    except Exception:
        font = ImageFont.load_default()
        small_font = font

    # Calculate positions
    width, height = image.size

    # Add diagonal "CONFIDENTIAL" watermark
    text = "CONFIDENTIAL"
    diagonal_layer = Image.new('RGBA', image.size, (255, 255, 255, 0))
    diagonal_draw = ImageDraw.Draw(diagonal_layer)

    # Draw text at center
    diagonal_draw.text(
        (width // 2 - 100, height // 2 - 20),
        text,
        font=font,
        fill=(128, 128, 128, 100)  # Semi-transparent gray
    )

    # Rotate the watermark layer
    diagonal_layer = diagonal_layer.rotate(45, expand=False, center=(width // 2, height // 2))

    # Composite the diagonal watermark
    image = Image.alpha_composite(image, diagonal_layer)

    # Add footer watermark
    footer_text = f"Downloaded by: {auditor_name} | {datetime.utcnow().strftime('%Y-%m-%d')} | {engagement_name[:20]}"

    # Create footer background
    footer_layer = Image.new('RGBA', image.size, (255, 255, 255, 0))
    footer_draw = ImageDraw.Draw(footer_layer)

    # Draw semi-transparent background for footer
    footer_draw.rectangle(
        [(0, height - 30), (width, height)],
        fill=(255, 255, 255, 180)
    )

    # Draw footer text
    footer_draw.text(
        (10, height - 25),
        footer_text,
        font=small_font,
        fill=(80, 80, 80, 255)
    )

    # Composite footer
    image = Image.alpha_composite(image, footer_layer)

    # Convert back to RGB for JPEG
    if file_type.lower() in ['jpg', 'jpeg']:
        image = image.convert('RGB')

    # Save to buffer
    result_buffer = BytesIO()
    save_format = 'JPEG' if file_type.lower() in ['jpg', 'jpeg'] else 'PNG'
    image.save(result_buffer, format=save_format)
    result_buffer.seek(0)

    return result_buffer


def apply_watermark(
    file_buffer: BinaryIO,
    file_type: str,
    auditor_name: str,
    engagement_id: str,
    engagement_name: str
) -> Optional[BytesIO]:
    """
    Apply watermark based on file type.
    Returns watermarked file buffer or None if unsupported.
    """
    file_type_lower = file_type.lower()

    if file_type_lower == 'pdf' or file_type_lower == 'application/pdf':
        return add_watermark_to_pdf(
            file_buffer, auditor_name, engagement_id, engagement_name
        )

    elif file_type_lower in ['png', 'jpg', 'jpeg', 'image/png', 'image/jpeg']:
        # Determine actual image format
        if 'png' in file_type_lower:
            fmt = 'png'
        else:
            fmt = 'jpeg'

        return add_watermark_to_image(
            file_buffer, auditor_name, engagement_id, engagement_name, fmt
        )

    else:
        # Unsupported file type, return original
        file_buffer.seek(0)
        return None
