# examples/run_extreme_pdf.py
from __future__ import annotations

from pathlib import Path
from datetime import datetime, timedelta
import random

import pandas as pd
from PIL import Image, ImageDraw, ImageFont

from reportlabcustom import generate_report, report_colors


# -------------------------------
# Helpers: Make assets (SVG & PNG)
# -------------------------------
def make_svg(path: Path):
    path.write_text(
        """<?xml version="1.0" encoding="UTF-8"?>
<svg width="612" height="792" xmlns="http://www.w3.org/2000/svg">
  <!-- Background -->
  <rect width="612" height="792" fill="#FFFFFF"/>
  <!-- Subtle header/footer bars -->
  <rect x="20" y="20" width="572" height="36" fill="#1E3A8A" opacity="0.08"/>
  <rect x="20" y="736" width="572" height="36" fill="#1E3A8A" opacity="0.08"/>
  <!-- Border -->
  <rect x="18" y="18" width="576" height="756" fill="none" stroke="#1E3A8A" stroke-width="1" opacity="0.35"/>
  <!-- Watermark -->
  <text x="306" y="430" font-size="60" fill="#F0F4FF" text-anchor="middle"
        transform="rotate(-30 306 430)">QA / E2E EXTREME</text>
</svg>
""",
        encoding="utf-8",
    )


def make_logo_png(path: Path, w=320, h=120):
    img = Image.new("RGBA", (w, h), (255, 255, 255, 0))
    d = ImageDraw.Draw(img)
    # Accent bar
    d.rectangle((0, 0, w, h), fill=(30, 58, 138, 20))
    d.rectangle((0, h - 10, w, h), fill=(30, 58, 138, 255))
    # Simple text (fallback font)
    text = "reportlabcustom"
    try:
        # Try a common system font; if it fails, we'll use default
        fnt = ImageFont.truetype("arial.ttf", 36)
    except Exception:
        fnt = ImageFont.load_default()
    tw, th = d.textlength(text, font=fnt), 36
    d.text(((w - tw) / 2, (h - th) / 2), text, fill=(30, 58, 138, 255), font=fnt)
    img.save(path)


def make_picture_png(path: Path, w=1000, h=600):
    img = Image.new("RGB", (w, h), (250, 252, 255))
    d = ImageDraw.Draw(img)
    # Fake chart/grid
    for x in range(50, w, 50):
        d.line((x, 0, x, h), fill=(230, 235, 255))
    for y in range(50, h, 50):
        d.line((0, y, w, y), fill=(230, 235, 255))
    # Bars
    bars = [300, 450, 200, 520, 410, 250, 480]
    x0 = 80
    for b in bars:
        d.rectangle((x0, h - b - 50, x0 + 60, h - 50), fill=(30, 58, 138))
        x0 += 100
    d.text((20, 10), "Synthetic KPI Bars", fill=(20, 20, 20))
    img.save(path)


# --------------------
# Synthetic test data
# --------------------
def build_main_df(n_rows=120):
    today = pd.Timestamp(datetime.now().date())
    start_base = today - pd.Timedelta(days=120)
    end_base = today + pd.Timedelta(days=90)
    cats = ["North", "South", "East", "West"]
    statuses = ["Active", "Pending", "Inactive"]
    rows = []
    for i in range(n_rows):
        cat = random.choice(cats)
        status = random.choice(statuses)
        score = round(random.uniform(40, 99), 1)
        amount = round(random.uniform(1000, 50000), 2)
        pct = round(random.uniform(0, 100), 1)
        start = start_base + pd.Timedelta(days=random.randint(0, 120))
        # some ends before/after start
        end = start + pd.Timedelta(days=random.randint(-10, 90))
        due = today + pd.Timedelta(days=random.randint(-30, 30))
        rows.append(
            {
                "Item": f"Item {i+1}",
                "Category": cat,
                "Status": status,
                "Score": score,
                "Amount": amount,
                "Pct": pct,
                "Start": start,
                "End": end,
                "Due": due,
            }
        )
    return pd.DataFrame(rows)


def build_small_df():
    # Smaller DF to test title_suffix_from_column & column_widths
    return pd.DataFrame(
        {
            "Name": ["Alpha", "Beta", "Gamma"],
            "Status": ["Active", "Pending", "Inactive"],
            "Score": [91.2, 74.5, 60.0],
            "Date": pd.to_datetime(["2025-11-01", "2025-10-15", "2025-09-30"]),
            "Kind": ["Summary", "Summary", "Summary"],
        }
    )


# -------------------
# Build the template
# -------------------
def build_template(assets_dir: Path) -> list[dict]:
    """
    Return a list of section dicts exercising all features.
    """
    main_df = build_main_df(n_rows=160)  # large to enforce multipage
    small_df = build_small_df()
    picture = str(assets_dir / "picture.png")

    # Column formats shared across tables
    col_formats = {
        "Amount": {"type": "currency", "decimal_places": 2, "currency_symbol": "$"},
        "Pct": {"type": "percentage", "decimal_places": 1},
        "Score": {"type": "number", "decimal_places": 1, "thousands_separator": False},
        "Start": {"type": "date", "format": "YYYY-MM-DD"},
        "End": {"type": "date", "format": "YYYY-MM-DD"},
        "Due": {"type": "date", "format": "YYYY-MM-DD"},
        "Date": {"type": "date", "format": "YYYY-MM-DD"},
    }

    # Specific cell override: bold a particular cell & custom number format
    # Header is excluded; (row_idx, col_idx) are 0-based for data rows.
    cell_formats = {
        (0, 2): {"type": "number", "decimal_places": 0},  # first row, Score col
    }

    # Comprehensive formatting rules on main_df
    formatting_rules_main = [
        # Row: contains
        {
            "scope": "row",
            "target_column": "Item",
            "condition": {"type": "contains", "value": "Item 1"},
            "style": {"bg_color": "#F7FAFC", "bold": False},
        },
        # Row: equals
        {
            "scope": "row",
            "target_column": "Category",
            "condition": {"type": "equals", "value": "North"},
            "style": {"bg_color": "#EEF2FF", "bold": False},
        },
        # Cell: equals
        {
            "scope": "cell",
            "target_column": "Status",
            "condition": {"type": "equals", "value": "Inactive"},
            "style": {"bg_color": "#FED7D7", "bold": True},
        },
        # Cell: contains
        {
            "scope": "cell",
            "target_column": "Item",
            "condition": {"type": "contains", "value": "5"},
            "style": {"bg_color": "#FFF5E6", "bold": False},
        },
        # Cell: numeric
        {
            "scope": "cell",
            "target_column": "Score",
            "condition": {"type": "numeric", "operator": ">=", "value": 90},
            "style": {"bg_color": "#DCFCE7", "bold": True},
        },
        # Cell: date_compare against today
        {
            "scope": "cell",
            "target_column": "Due",
            "condition": {"type": "date_compare", "operator": "<", "compare_to": "today"},
            "style": {"bg_color": "#FFE4E6", "bold": False},
        },
        # Cell: date_compare_column (End < Start)
        {
            "scope": "cell",
            "target_column": "End",
            "condition": {"type": "date_compare_column", "operator": "<", "compare_column": "Start"},
            "style": {"bg_color": "#FFEDD5", "bold": True},
        },
        # Cell: color_scale categorical (Status)
        {
            "scope": "cell",
            "target_column": "Status",
            "condition": {
                "type": "color_scale",
                "scale_type": "categorical",
                "color_map": {"Active": "#C6F6D5", "Pending": "#FEFCBF", "Inactive": "#FED7D7"},
            },
            "style": {"bg_color": "#FFFFFF", "bold": False},
        },
        # Cell: color_scale numeric (Score, manual min/mid/max)
        {
            "scope": "cell",
            "target_column": "Score",
            "condition": {
                "type": "color_scale",
                "scale_type": "numeric",
                "mode": "manual",
                "colors": ["#F87171", "#FBBF24", "#34D399"],  # red → amber → green
                "min": 50,
                "mid": 75,
                "max": 95,
            },
            "style": {"bg_color": "#FFFFFF", "bold": False},
        },
        # Cell: color_scale date (Due auto)
        {
            "scope": "cell",
            "target_column": "Due",
            "condition": {"type": "color_scale", "scale_type": "date", "mode": "auto",
                          "colors": ["#60A5FA", "#A78BFA", "#F472B6"]},
            "style": {"bg_color": "#FFFFFF", "bold": False},
        },
    ]

    # Smaller table rules (simpler)
    formatting_rules_small = [
        {
            "scope": "cell",
            "target_column": "Status",
            "condition": {"type": "color_scale", "scale_type": "categorical",
                          "color_map": {"Active": "#C6F6D5", "Pending": "#FEFCBF", "Inactive": "#FED7D7"}},
            "style": {"bg_color": "#FFFFFF", "bold": False},
        }
    ]

    # Sections
    sections = [
        # 1) Title (tests separator and subtitle color)
        {
            "type": "title",
            "title": "📊 Extreme PDF Feature Test",
            "subtitle": "Everything, everywhere, all at once (but deterministic).",
            "separator_color": report_colors["separator"],
            "subtitle_color": report_colors["subtitle"],
        },

        # 2) Text (alignment & styling get normalized by renderer)
        {
            "type": "text",
            "title": "Overview",
            "subtitle": "This page validates layout, styles, and rule evaluation.",
            "content": (
                "This report intentionally spans multiple pages, mixes grouped and ungrouped tables, "
                "applies all rule types, and renders an SVG background under headers/footers/content. "
                "It also exercises column widths, column/cell formats, and keep-together behavior for images."
            ),
            "alignment": "left",
            "style": "normal",
            "font_size": 11,
        },

        # 3) Image (kept together; tests caption/subtitle and aspect handling)
        {
            "type": "image",
            "title": "Synthetic KPI Bars",
            "subtitle": "Drawn with Pillow; scaled by ReportLab while preserving ratio.",
            "caption": "Demonstrates KeepTogether() around [title, subtitle, caption, image].",
            "image_path": picture,
            "width": 6.5,  # inches (will be scaled to fit page width)
        },

        # 4) Small table (tests title_suffix_from_column & column_widths)
        {
            "type": "table",
            "title": "Summary Metrics",
            "title_suffix_from_column": "Kind",
            "subtitle": "Column formats (date, number, percentage) + categorical color map.",
            "df": small_df,
            "column_widths": [0.22, 0.22, 0.18, 0.18, 0.20],  # must sum ~1.0
            "formatting_rules": formatting_rules_small,
            "column_formats": col_formats,
            "cell_formats": cell_formats,
            "clean_empty_cols": True,
            "clean_empty_rows": True,
        },

        # 5) Main big table (all rule types; multi-page; alternating rows)
        {
            "type": "table",
            "title": "Detailed Items",
            "subtitle": "Stress test: large dataset, all rules, alternating rows, two-pass pagination.",
            "df": main_df,
            "formatting_rules": formatting_rules_main,
            "column_formats": col_formats,
            "clean_empty_cols": True,
            "clean_empty_rows": True,
        },

        # 6) Grouped table (category-wise) reusing rule/format configs
        {
            "type": "table_grouped",
            "title": "Category Breakdown",
            "subtitle": "Grouped rendering with carry-over formats and rules.",
            "df": main_df,
            "groupby": "Category",
            "category_order": ["North", "South", "East", "West"],
            "formatting_rules": formatting_rules_main,   # reused
            "column_formats": col_formats,               # reused
            "clean_empty_cols": True,
            "clean_empty_rows": True,
        },
    ]

    return sections


def main():
    # -------------
    # Output / assets
    # -------------
    out_dir = Path("build/extreme"); out_dir.mkdir(parents=True, exist_ok=True)
    assets = out_dir / "assets"; assets.mkdir(parents=True, exist_ok=True)

    svg_path = assets / "background.svg"
    logo_path = assets / "logo.png"
    pic_path  = assets / "picture.png"

    make_svg(svg_path)
    make_logo_png(logo_path)
    make_picture_png(pic_path)

    # ------------------------
    # Header / Footer configs
    # ------------------------
    header = {
        "logo_path": str(logo_path),
        "logo_width": 1.4,
        "logo_height": 0.5,
        "logo_position": "left",
        "text": "Extreme QA Suite",
        "text_position": "right",
        "font_size": 10,
        "draw_line": True,
        "height": 0.9,
    }

    footer = {
        "page_numbers": {"position": "right", "format": "Page {n} of {total}"},
        "text_left": "Confidential",
        "text_center": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "text_right": None,
        "font_size": 9,
        "text_color": "#666666",
        "draw_line": True,
        "line_color": "#CCCCCC",
        # height left defaulting is fine; we set explicit anyway:
        "height": 0.75,
    }

    # ------------
    # Build report
    # ------------
    sections = build_template(assets)
    out_pdf = out_dir / "extreme_all_features.pdf"

    path = generate_report(
        report_sections=sections,
        output_filename=str(out_pdf),
        format="pdf",
        colors=report_colors,             # defaults; override if you like
        header_config=header,
        footer_config=footer,
        background_svg=str(svg_path),     # NEW svg background layer
    )

    print("PDF generated:", path)
    print("Open it and verify:\n"
          " - SVG background shows on all pages (behind content)\n"
          " - Header/logo/text and footer/page numbers render correctly (3 zones)\n"
          " - Image block stays together (title/subtitle/caption/image)\n"
          " - Small table honors column widths & title suffix\n"
          " - Main table spans multiple pages; alternating rows + all rules apply\n"
          " - Grouped table shows Category sections in specified order\n"
          " - Currency/percent/date/number formats render\n")


if __name__ == "__main__":
    main()
