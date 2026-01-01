from io import BytesIO
from datetime import datetime

# ---------- TXT EXPORT ----------
def generate_txt(
    summary_text,
    title=None,
    author=None,
    include_original=False,
    original_text=None,
    generated_at=None,
    version=None,
    **metadata  # ← THIS FIXES EVERYTHING
):
    buffer = BytesIO()
    lines = []

    if title:
        lines.append(f"Title: {title}")

    if author:
        lines.append(f"Author: {author}")

     # Optional metadata (safe, no crash)
    if "model" in metadata and metadata["model"]:
        lines.append(f"Model: {metadata['model']}")

    if "version" in metadata and metadata["version"] is not None:
        lines.append(f"Version: {metadata['version']}")

    if "generated_at" in metadata and metadata["generated_at"]:
        gen_time = metadata["generated_at"]
        if isinstance(gen_time, datetime):
            gen_time = gen_time.strftime("%Y-%m-%d %H:%M")
        lines.append(f"Generated on: {gen_time}")
        
    lines.append("\n" + "=" * 40 + "\n")
    lines.append("SUMMARY\n")
    lines.append("=" * 40 + "\n")
    lines.append(summary_text.strip())

    if include_original and original_text:
        lines.append("\n\n" + "=" * 40 + "\n")
        lines.append("ORIGINAL TEXT\n")
        lines.append("=" * 40 + "\n")
        lines.append(original_text.strip())

    content = "\n".join(lines)
    buffer.write(content.encode("utf-8"))
    buffer.seek(0)
    return buffer


# ---------- PDF EXPORT ----------
def generate_pdf(
    summary_text,
    title=None,
    author=None,
    include_original=False,
    original_text=None,
    generated_at=None,
    version=None
):
    from reportlab.platypus import (
        SimpleDocTemplate,
        Paragraph,
        Spacer,
        PageBreak
    )
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import inch

    buffer = BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40
    )

    styles = getSampleStyleSheet()
    story = []

    # Title
    if title:
        story.append(Paragraph(f"<b>{title}</b>", styles["Title"]))
        story.append(Spacer(1, 0.2 * inch))

    # Metadata
    meta = []
    if author:
        meta.append(f"Author: {author}")
    if version is not None:
        meta.append(f"Version: {version}")
    if generated_at:
        if isinstance(generated_at, datetime):
            generated_at = generated_at.strftime("%Y-%m-%d %H:%M")
        meta.append(f"Generated on: {generated_at}")

    for m in meta:
        story.append(Paragraph(m, styles["Normal"]))

    if meta:
        story.append(Spacer(1, 0.3 * inch))

    # Summary section
    story.append(Paragraph("<b>Summary</b>", styles["Heading2"]))
    story.append(Spacer(1, 0.15 * inch))

    for para in summary_text.split("\n"):
        if para.strip():
            story.append(Paragraph(para, styles["Normal"]))
            story.append(Spacer(1, 0.1 * inch))

    # Original text section (optional)
    if include_original and original_text:
        story.append(PageBreak())
        story.append(Paragraph("<b>Original Text</b>", styles["Heading2"]))
        story.append(Spacer(1, 0.15 * inch))

        for para in original_text.split("\n"):
            if para.strip():
                story.append(Paragraph(para, styles["Normal"]))
                story.append(Spacer(1, 0.1 * inch))

    doc.build(story)
    buffer.seek(0)
    return buffer
