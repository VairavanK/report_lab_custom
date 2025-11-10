import os
import pandas as pd

from reportlabcustom import generate_report, report_colors

def _make_svg(path: str):
    svg = """<?xml version="1.0" encoding="UTF-8"?>
<svg width="612" height="792" xmlns="http://www.w3.org/2000/svg">
  <rect width="612" height="792" fill="#FFFFFF"/>
  <rect x="20" y="20" width="572" height="40" fill="#1E3A8A" opacity="0.08"/>
  <rect x="20" y="732" width="572" height="40" fill="#1E3A8A" opacity="0.08"/>
</svg>"""
    with open(path, "w", encoding="utf-8") as f:
        f.write(svg)

def test_generate_pdf_and_docx(tmp_path):
    # --- test data ---
    df = pd.DataFrame({
        "Name": ["Alpha", "Beta", "Gamma", "Delta"],
        "Status": ["Active", "Pending", "Active", "Inactive"],
        "Score": [91.2, 74.5, 88.0, 60.0],
        "Date": pd.to_datetime(["2025-11-01", "2025-10-15", "2025-11-05", "2025-09-30"])
    })

    template = [
        {"type": "title", "title": "QA Report", "subtitle": "Automated test run"},
        {"type": "text", "content": "This is a smoke test rendering PDF and DOCX using reportlabcustom."},
        {"type": "table",
         "df": df,
         "formatting_rules": [
             {
               "scope": "cell", "target_column": "Status",
               "condition": {"type": "color_scale", "scale_type": "categorical",
                             "color_map": {"Active": "#C6F6D5", "Pending": "#FEFCBF", "Inactive": "#FED7D7"}},
               "style": {"bg_color": "#FFFFFF", "bold": False}
             }
         ],
         "column_formats": {
             "Score": {"type": "number", "decimal_places": 1},
             "Date": {"type": "date", "format": "YYYY-MM-DD"}
         }}
    ]

    # --- outputs ---
    pdf_out = tmp_path / "sample.pdf"
    docx_out = tmp_path / "sample.docx"
    svg_path = tmp_path / "bg.svg"
    _make_svg(str(svg_path))

    # --- PDF with header/footer + background ---
    head = {"text": "QA Run", "draw_line": True}
    foot = {"page_numbers": {"position": "center"}, "text_left": "Confidential", "draw_line": True}

    pdf_path = generate_report(
        report_sections=template,
        output_filename=str(pdf_out),
        format="pdf",
        colors=report_colors,         # use defaults
        header_config=head,
        footer_config=foot,
        background_svg=str(svg_path)  # NEW feature under test
    )
    assert os.path.exists(pdf_path) and os.path.getsize(pdf_path) > 1000

    # --- DOCX (no background) ---
    docx_path = generate_report(
        report_sections=template,
        output_filename=str(docx_out),
        format="docx"
    )
    assert os.path.exists(docx_path) and os.path.getsize(docx_path) > 1000
