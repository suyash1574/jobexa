import os
import uuid
import logging
from typing import Optional

logger = logging.getLogger("jobexa")

def compile_markdown_to_pdf(markdown_text: str, output_filename: Optional[str] = None) -> str:
    """
    Compiles raw Markdown text into a styled PDF resume variant.
    Saves the generated PDF file to static/uploads/ and returns the relative/absolute file path.
    """
    if not output_filename:
        output_filename = f"resume_variant_{uuid.uuid4().hex[:8]}.pdf"

    static_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "static", "uploads"))
    os.makedirs(static_dir, exist_ok=True)
    pdf_filepath = os.path.join(static_dir, output_filename)

    # Simple HTML template for styling Markdown resumes
    html_template = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            body {{ font-family: 'Helvetica Neue', Arial, sans-serif; margin: 40px; color: #333; line-height: 1.6; }}
            h1 {{ font-size: 24px; border-bottom: 2px solid #2563eb; padding-bottom: 8px; color: #1e3a8a; }}
            h2 {{ font-size: 18px; color: #1e40af; margin-top: 20px; }}
            h3 {{ font-size: 14px; color: #374151; }}
            p, li {{ font-size: 12px; color: #4b5563; }}
            ul {{ padding-left: 20px; }}
            .header {{ text-align: center; margin-bottom: 30px; }}
        </style>
    </head>
    <body>
        <div>
            {_markdown_to_simple_html(markdown_text)}
        </div>
    </body>
    </html>
    """

    try:
        # Try compiling with Weasyprint if available
        import weasyprint
        weasyprint.HTML(string=html_template).write_pdf(pdf_filepath)
        logger.info(f"Successfully compiled PDF using WeasyPrint: {pdf_filepath}")
        return pdf_filepath
    except Exception as e:
        logger.warning(f"WeasyPrint compilation fallback triggered ({e}). Creating HTML/PDF output.")
        # Fallback: Write HTML file directly if binary PDF engines are uninstalled
        html_filepath = pdf_filepath.replace(".pdf", ".html")
        with open(html_filepath, "w", encoding="utf-8") as f:
            f.write(html_template)
        return html_filepath

def _markdown_to_simple_html(text: str) -> str:
    """Basic markdown parser fallback for headers, bold text, and bullet lists."""
    lines = text.split("\n")
    html_lines = []
    in_list = False

    for line in lines:
        line_str = line.strip()
        if line_str.startswith("# "):
            if in_list:
                html_lines.append("</ul>")
                in_list = False
            html_lines.append(f"<h1>{line_str[2:]}</h1>")
        elif line_str.startswith("## "):
            if in_list:
                html_lines.append("</ul>")
                in_list = False
            html_lines.append(f"<h2>{line_str[3:]}</h2>")
        elif line_str.startswith("### "):
            if in_list:
                html_lines.append("</ul>")
                in_list = False
            html_lines.append(f"<h3>{line_str[4:]}</h3>")
        elif line_str.startswith("- ") or line_str.startswith("* "):
            if not in_list:
                html_lines.append("<ul>")
                in_list = True
            html_lines.append(f"<li>{line_str[2:]}</li>")
        elif not line_str:
            if in_list:
                html_lines.append("</ul>")
                in_list = False
        else:
            if in_list:
                html_lines.append("</ul>")
                in_list = False
            html_lines.append(f"<p>{line_str}</p>")

    if in_list:
        html_lines.append("</ul>")

    return "\n".join(html_lines)
