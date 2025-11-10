🧠 Report System — LLM-Friendly Spec (Reality-Accurate, v2.4)

Last updated: 10 Nov 2025

A precise, machine-oriented spec for generating PDF or DOCX reports from a sectioned template. Reflects the current implementation and the SVG background feature.

0) Package Layout (import paths)
reportlabcustom/
├─ README.md
├─ pyproject.toml
└─ src/
   └─ reportlabcustom/
      ├─ __init__.py            # public API (Option A: re-exports)
      ├─ pdf.py                 # PDF renderer + generate_report switch
      ├─ docx.py                # DOCX renderer
      ├─ utils.py               # shared helpers (formatting, df prep, rules, svg loader)
      └─ theme.py               # report_colors (visual tokens)


Import in user code:

from reportlabcustom import generate_report, report_colors

1) Public API
1.1 generate_report(report_sections, output_filename='report.pdf', format='pdf', colors=None, header_config=None, footer_config=None, background_svg=None)

Inputs

report_sections: List[Section] — ordered; see §3.

output_filename: str — required; full or relative path.

format: 'pdf' | 'docx' — default 'pdf'.

colors: Colors | None — optional report-level theme override (see §4). Cascade: section.colors → colors → report_colors.

header_config: HeaderConfig | None — optional PDF header; see §6.2.

footer_config: FooterConfig | None — optional PDF footer; see §6.1.

background_svg: str | None — NEW; PDF-only page background; see §2.2 and SVG section below.

Output

str — output file path.

Runtime notes

For table sections, pass actual pandas.DataFrame objects in Python (not names/strings). JSON in this spec uses placeholders only.

If footer_config is omitted, a minimal footer with centered page numbers ("Page {n} of {total}") is injected automatically for PDF.

2) Deterministic Behavior

Render order equals the order of items in report_sections.

Same template works for PDF and DOCX (renderer switch only).

table_grouped.clean_empty_cols=True cleans per group.

PDF page numbers use a two-pass build for accurate totals.

Footer uses three zones (left/center/right); if page numbers occupy a zone, text in that zone is ignored.

Color precedence: section.colors ▶ report colors (colors) ▶ module defaults (report_colors).

2.1 Smart Pagination (PDF)

Titles (and their immediate content) avoid orphaning via a conditional page-break heuristic (~2″ threshold).

2.2 SVG Background Layer (PDF-only) — NEW

Provide background_svg="path/to/file.svg" to render a vector background behind all content on every page. See full details in “SVG Background Layer Feature” at the end of this spec.

3) Template Model (Discriminated Union)

A template is an array of Section objects. type selects the shape.

{
  "type": "array",
  "items": { "$ref": "#/definitions/Section" },
  "definitions": {
    "Section": { "oneOf": [
      { "$ref": "#/definitions/TitleSection" },
      { "$ref": "#/definitions/TextSection" },
      { "$ref": "#/definitions/TableSection" },
      { "$ref": "#/definitions/GroupedTableSection" },
      { "$ref": "#/definitions/ImageSection" }
    ]},

    "Common": {
      "type": "object",
      "properties": {
        "title": {"type":"string"},
        "subtitle": {"type":"string"},
        "colors": {"$ref": "#/definitions/Colors"}
      },
      "additionalProperties": true
    },

    "TitleSection": { "allOf": [ {"$ref":"#/definitions/Common"}, {
      "type":"object", "required":["type","title"],
      "properties": {
        "type": {"const":"title"},
        "separator_color": {"type":"string"},
        "subtitle_color": {"type":"string"}
      }
    }]},

    "TextSection": { "allOf": [ {"$ref":"#/definitions/Common"}, {
      "type":"object", "required":["type","content"],
      "properties": {
        "type": {"const":"text"},
        "content": {"type":"string"}
      }
    }]},

    "TableSection": { "allOf": [ {"$ref":"#/definitions/Common"}, {
      "type":"object", "required":["type","df"],
      "properties": {
        "type": {"const":"table"},
        "df": {"type":"string", "description":"PLACEHOLDER_NAME_ONLY (pass actual DataFrame at runtime)"},
        "drop_columns": {"type":"array","items":{"type":"string"}},
        "clean_empty_cols": {"type":"boolean"},
        "clean_empty_rows": {"type":"boolean"},
        "title_suffix_from_column": {"type":"string"},
        "column_widths": {"type":"array","items":{"type":"number"}},
        "formatting_rules": {"$ref":"#/definitions/FormattingRules"},
        "column_formats": {"$ref":"#/definitions/ColumnFormats"},
        "cell_formats": {"$ref":"#/definitions/CellFormats"}
      }
    }]},

    "GroupedTableSection": { "allOf": [ {"$ref":"#/definitions/Common"}, {
      "type":"object", "required":["type","df","groupby"],
      "properties": {
        "type": {"const":"table_grouped"},
        "df": {"type":"string"},
        "groupby": {"type":"string"},
        "category_order": {"type":"array","items":{"type":"string"}},
        "drop_columns": {"type":"array","items":{"type":"string"}},
        "clean_empty_cols": {"type":"boolean"},
        "clean_empty_rows": {"type":"boolean"},
        "formatting_rules": {"$ref":"#/definitions/FormattingRules"},
        "column_formats": {"$ref":"#/definitions/ColumnFormats"},
        "cell_formats": {"$ref":"#/definitions/CellFormats"}
      }
    }]},

    "ImageSection": { "allOf": [ {"$ref":"#/definitions/Common"}, {
      "type":"object", "required":["type","image_path"],
      "properties": {
        "type": {"const":"image"},
        "image_path": {"type":"string"},
        "caption": {"type":"string"},
        "width": {"type":"number"}
      }
    }]},

    "Colors": {
      "type":"object",
      "properties": {
        "header_bg": {"type":"string"},
        "header_text": {"type":"string"},
        "row_alt": {"type":"string"},
        "row_normal": {"type":"string"},
        "separator": {"type":"string"},
        "subtitle": {"type":"string"},
        "section_subtitle": {"type":"string"}
      },
      "additionalProperties": false
    }
  }
}


Concrete section shapes (Python)

Title: {'type': 'title', 'title': str, 'subtitle'?: str, 'separator_color'?: str, 'subtitle_color'?: str, 'colors'?: Colors}

Text: {'type': 'text', 'content': str, 'title'?: str, 'subtitle'?: str, 'colors'?: Colors}

Table: {'type': 'table', 'df': DataFrame, 'title'?: str, 'subtitle'?: str, 'drop_columns'?: [str], 'clean_empty_cols'?: bool, 'clean_empty_rows'?: bool, 'title_suffix_from_column'?: str, 'column_widths'?: [float], 'formatting_rules'?: [Rule], 'column_formats'?: ColumnFormats, 'cell_formats'?: CellFormats, 'colors'?: Colors}

Grouped Table: {'type': 'table_grouped', 'df': DataFrame, 'groupby': str, 'title'?: str, 'subtitle'?: str, 'category_order'?: [str], 'drop_columns'?: [str], 'clean_empty_cols'?: bool, 'clean_empty_rows'?: bool, 'formatting_rules'?: [Rule], 'column_formats'?: ColumnFormats, 'cell_formats'?: CellFormats, 'colors'?: Colors}

Image: {'type': 'image', 'image_path': str, 'title'?: str, 'subtitle'?: str, 'caption'?: str, 'width'?: float, 'colors'?: Colors}

4) Colors (Three-Level Cascade)
4.1 Precedence (highest → lowest)

section.colors → colors (API param) → report_colors (module defaults, from reportlabcustom.theme)

4.2 Schema: Colors

Keys (recommended all 7): header_bg, header_text, row_alt, row_normal, separator, subtitle, section_subtitle.

Values: hex strings #RRGGBB.

Partial dicts allowed; missing keys fall back to lower levels.

4.3 Module Defaults
# reportlabcustom/theme.py
report_colors = {
  'header_bg': '#FF8C00', 'header_text': '#FFFFFF',
  'row_alt': '#FFE5CC',   'row_normal': '#FFFFFF',
  'separator': '#FF8C00', 'subtitle': '#666666', 'section_subtitle': '#888888',
}

5) Conditional & Value Formatting (PDF)

All condition types support both scope='row' and scope='cell'.
Implemented in reportlabcustom.utils.evaluate_formatting_rules.

5.1 FormattingRules (complete schema)

(unchanged from v2.3; see your previous block — it remains valid)

Notes

Supported style properties are only: bg_color (hex) and bold (boolean). Text color is not supported.

Rule order matters; later rules can override earlier ones. Cell scope overrides row scope at the same cell.

5.2 ColumnFormats & CellFormats

(schema unchanged; same as v2.3)

5.3 Helper Locations

format_value, prepare_dataframe, evaluate_formatting_rules live in reportlabcustom.utils.

PDF renderer in reportlabcustom.pdf consumes these helpers.

6) PDF Layout: Footer, Header, Page Numbers
6.1 FooterConfig (three zones; page numbers mandatory somewhere)

(schema unchanged; same as v2.3)

6.2 HeaderConfig

(schema unchanged; same as v2.3)

6.3 Page Numbers (defaults)

Default footer (if none provided): centered "Page {n} of {total}", Helvetica 9pt.

Two-pass PDF build ensures accurate {total}.

7) Data Preparation & Limits

Use prepare_dataframe(df) to normalize datetimes (YYYY-MM-DD) with conservative parsing for object columns (parse only if ≥80% look like dates and contain - / :).

For PDF tables, prefer ≤ 500 characters per cell to avoid layout issues.

Ensure image_path exists and is accessible at render time.

8) Minimal Usage Examples
8.1 Defaults
from reportlabcustom import generate_report
path = generate_report(template, output_filename='report.pdf', format='pdf')

8.2 Report Colors + Footer
from reportlabcustom import generate_report, report_colors

blue = {
  'header_bg':'#0066CC','header_text':'#FFFFFF',
  'row_alt':'#E6F2FF','row_normal':'#FFFFFF',
  'separator':'#0066CC','subtitle':'#1E90FF','section_subtitle':'#4169E1'
}
foot = { 'text_left': '© 2025 Ohmyhome', 'page_numbers': {'position':'center'} }

path = generate_report(
  template, output_filename='report.pdf', format='pdf',
  colors=blue, footer_config=foot
)

8.3 Conditional Formatting (Categorical map)
template = [{
  'type':'table', 'df': df,
  'formatting_rules': [{
    'scope':'cell', 'target_column':'Status',
    'condition': { 'type':'color_scale', 'scale_type':'categorical', 'color_map': {
      'Active':'#90EE90', 'Pending':'#FFD700', 'Inactive':'#FFB6C1'
    }},
    'style': { 'bg_color':'#FFFFFF', 'bold': False }
  }]
}]
path = generate_report(template, output_filename='status.pdf', format='pdf')

8.4 Header + Footer + Colors
head = { 'logo_path':'logo.png','logo_width':1.2,'logo_height':0.5,'logo_position':'left',
         'text':'Monthly Report','text_position':'right','draw_line':True }
foot = { 'text_left':'© 2025 Ohmyhome','page_numbers':{'position':'center','format':'{n}/{total}'},
         'text_right':'October 2025','draw_line':True }

path = generate_report(
  template, output_filename='report.pdf', format='pdf',
  colors=blue, header_config=head, footer_config=foot
)

8.5 PDF with SVG Background — NEW
path = generate_report(
  report_sections=template,
  output_filename="monthly_report.pdf",
  format="pdf",
  header_config={'text':'Monthly Report', 'draw_line': True},
  footer_config={'page_numbers': {'position':'center'}},
  background_svg="assets/letterhead_background.svg"
)

9) Feature Matrix
Capability	Tables	Grouped Tables	PDF	DOCX
Conditional formatting (contains/equals/numeric/date/date_column/color_scale)	✓	✓	✓	–
Number/Date formatting	✓	✓	✓	–
Three-zone footer & header	–	–	✓	–
SVG background (all pages, behind content)	–	–	✓	–
10) SVG Background Layer Feature (Full Details)
Overview

The system supports vector SVG backgrounds that render on every PDF page, behind all content (headers, footers, tables, text, images).

Usage (recap)
generate_report(
    report_sections=content,
    output_filename="report.pdf",
    format="pdf",
    header_config={...},
    footer_config={...},
    background_svg="path/to/background.svg"   # NEW
)

Parameter: background_svg

Type: str | None — path to an SVG file

Default: None (no background)

PDF only: not supported in DOCX

Sizing: auto-scaled to letter (8.5″×11″, 612×792 pt), aspect ratio preserved & centered

SVG File Requirements

Recommended

Dimensions: 612×792 pt (8.5″×11″ at 72 DPI)

SVG 1.1, simple shapes/gradients/opacity; <500 KB preferred

Supported

Rects/circles/paths/lines, solid fills/strokes, gradients, opacity, text

Limitations

Avoid embedded fonts / external references / complex filters; very large files (>1 MB) may slow generation

Behavior & Rendering Order

Background SVG

Report content (title, text, tables, images)

Header

Footer

Error Handling

File not found / invalid / parse errors → warning printed; report renders without background.

Performance

SVG is loaded once; drawing is re-used on every page.

11) Dependencies

Base (in pyproject.toml):

pandas, requests (if you use it)

PDF:

reportlab, svglib, pillow

DOCX:

python-docx

If you’re using optional extras, document install as:

pip install "reportlabcustom[pdf,docx]"

12) Versioning & API Surface

Single public entry point: reportlabcustom.generate_report(...)

You chose no version file. The spec label here is informational only: v2.4.2025-11-10.