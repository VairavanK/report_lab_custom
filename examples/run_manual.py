from pathlib import Path
import pandas as pd
from reportlabcustom import generate_report, report_colors

outdir = Path("build"); outdir.mkdir(exist_ok=True)
svg = outdir / "bg.svg"
svg.write_text("""<?xml version="1.0" encoding="UTF-8"?>
<svg width="612" height="792" xmlns="http://www.w3.org/2000/svg">
  <rect width="612" height="792" fill="#FFFFFF"/>
  <rect x="20" y="20" width="572" height="40" fill="#1E3A8A" opacity="0.08"/>
</svg>""", encoding="utf-8")

df = pd.DataFrame({
    "Name": ["A","B","C"],
    "Status": ["Active","Pending","Inactive"],
    "Score": [95.0, 70.5, 59.5],
    "Date": pd.to_datetime(["2025-11-01","2025-10-20","2025-09-30"])
})

template = [
    {"type":"title","title":"Manual Check","subtitle":"Visual sanity"},
    {"type":"table","df":df}
]

pdf = generate_report(template, output_filename=str(outdir/"manual.pdf"),
                      format="pdf",
                      header_config={"text":"Manual", "draw_line":True},
                      footer_config={"page_numbers":{"position":"center"}},
                      background_svg=str(svg))
print("PDF:", pdf)

docx = generate_report(template, output_filename=str(outdir/"manual.docx"), format="docx")
print("DOCX:", docx)
