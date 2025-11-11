# 🧠 Report System — LLM-Friendly Spec (Reality-Accurate, v2.6)

**Last updated:** 11 Nov 2025
**Authority:** Matches the shipped code in `pdf.py`, `docx.py`, `utils.py`, `theme.py`.
**Focus:** PDF first; DOCX kept lean by design.
**Note:** JSON below shows *shapes only*—at runtime pass real Python objects (e.g., **pandas.DataFrame**).

---

## 🔥 Critical Quick Reference

### Copy-Paste Starter (PDF)

```python
from reportlabcustom import generate_report, report_colors
import pandas as pd

# 1) Your data
df = pd.DataFrame([
    {"Item": "A", "Qty": 10, "Price": 2.5, "Status": "Active"},
    {"Item": "B", "Qty": 5,  "Price": 4.2, "Status": "Pending"},
])

# 2) Template (ordered sections)
template = [
    {"type":"title", "title":"Monthly Report", "subtitle":"October 2025"},
    {"type":"text", "title":"Overview", "content":"This report summarises key metrics."},
    {
      "type":"table", "title":"Line Items", "df": df,
      "column_formats": {
        "Qty":   {"type":"number", "decimal_places":0},
        "Price": {"type":"currency", "currency_symbol":"$","decimal_places":2}
      },
      "formatting_rules": [{
        "scope":"cell","target_column":"Status",
        "condition":{"type":"color_scale","scale_type":"categorical",
                     "color_map":{"Active":"#D1F7C4","Pending":"#FFE8A3"}},
        "style":{"bg_color":"#FFFFFF","bold":False}
      }],
      "clean_empty_cols": True, "clean_empty_rows": True
    }
]

# 3) Generate (PDF)
path = generate_report(template, output_filename="report.pdf", format="pdf")
print(path)
```

**Defaults to remember**

* Page: US Letter (612×792 pt).
* Colors cascade: `section.colors` → `colors` param → `theme.report_colors`.
* PDF always has page numbers (your footer or an auto default).
* SVG background: `background_svg="path/to/bg.svg"` (PDF-only).

---

## 😵 Common Parameter Confusion Matrix (NOT THIS → USE THIS)

| Confusion           | ❌ NOT THIS                                 | ✅ USE THIS                               | Why                                                                       |
| ------------------- | ------------------------------------------ | ---------------------------------------- | ------------------------------------------------------------------------- |
| DataFrames          | `"df": "my_df_name"`                       | `"df": actual_pandas_dataframe`          | Code expects a real DataFrame object, not a string.                       |
| Format switch       | `"format": "PDF"`                          | `"format": "pdf"` (lowercase)            | The switch compares lowercase strings.                                    |
| Column widths       | Raw inches or points                       | **Fractions** that sum ≈ `1.0`           | Current code supports fractional widths only (scaled to available width). |
| Text color in rules | `"style": {"text_color":"#000"}`           | Omit; only `bg_color` + `bold` supported | Text color isn’t implemented in rules.                                    |
| Date rule name      | `"type":"date"`                            | `"type":"date_compare"`                  | Implementation uses `date_compare` (& `date_compare_column`).             |
| Date vs Date Column | `"type":"date"` when comparing two columns | `"type":"date_compare_column"`           | Column vs column needs the dedicated rule.                                |
| Title suffix source | Expect suffix after drops/cleans           | Suffix comes from **original df**        | Current code reads from original, pre-clean/drop.                         |
| DOCX parity         | Expect PDF features in DOCX                | Use DOCX only for basic export           | DOCX omits header/footer, rules, SVG, widths.                             |
| Links in PDF        | Raw URLs                                   | `<link href="...">text</link>`           | ReportLab hyperlinks require `<link>` tags in text/cells.                 |

---

## 🧩 Section Schemas (with inline examples)

> Shapes are illustrative. At runtime pass **actual** DataFrames and Python dicts.

### TitleSection

**Shape**

```json
{
  "type":"title",
  "title":"string",
  "subtitle":"string?",
  "separator_color":"#RRGGBB?",
  "subtitle_color":"#RRGGBB?",
  "colors": {"header_bg":"#..","header_text":"#..","row_alt":"#..","row_normal":"#..","separator":"#..","subtitle":"#..","section_subtitle":"#.."}?
}
```

**Example**

```python
{"type":"title","title":"Estate Dashboard","subtitle":"October 2025","separator_color":"#FF8C00"}
```

---

### TextSection

**Shape**

```json
{
  "type":"text",
  "title":"string?",
  "subtitle":"string?",
  "content":"string",
  "style":"normal|bold|italic",
  "alignment":"left|center|right",
  "font_size": number,
  "colors": Colors?
}
```

**Example**

```python
{"type":"text","title":"Notes","content":"Visit <link href=\"https://example.com\" color=\"blue\">portal</link> for details."}
```

---

### TableSection

**Shape**

```json
{
  "type":"table",
  "title":"string?",
  "subtitle":"string?",
  "df": "PLACEHOLDER",
  "drop_columns": ["ColA","ColB"]?,
  "clean_empty_cols": true?,
  "clean_empty_rows": true?,
  "title_suffix_from_column": "ColName"?,   
  "column_widths": [0.25,0.5,0.25]?,        
  "formatting_rules": [ Rule ]?,            
  "column_formats":  ColumnFormats?,
  "cell_formats":    CellFormats?,
  "colors": Colors?
}
```

**Example**

```python
{
  "type":"table","title":"Contracts","df": df_contracts,
  "title_suffix_from_column":"Month",
  "drop_columns":["InternalID"],
  "clean_empty_cols":True,"clean_empty_rows":True,
  "column_formats":{
    "Amount":{"type":"currency","currency_symbol":"$","decimal_places":2,"thousands_separator":True},
    "Date":{"type":"date","format":"YYYY-MM-DD"}
  }
}
```

---

### GroupedTableSection

**Shape**

```json
{
  "type":"table_grouped",
  "title":"string?",
  "subtitle":"string?",
  "df":"PLACEHOLDER",
  "groupby":"CategoryCol",
  "category_order":["A","B","C"]?,
  "drop_columns":["ColA"]?,
  "clean_empty_cols": true?,
  "clean_empty_rows": true?,
  "formatting_rules":[ Rule ]?,
  "column_formats": ColumnFormats?,
  "cell_formats":   CellFormats?,
  "colors": Colors?
}
```

**Example**

```python
{
  "type":"table_grouped","title":"Tickets by Status","df": df_tickets,"groupby":"Status",
  "category_order":["Open","Work In Progress","Resolved"],
  "clean_empty_cols":True,
  "formatting_rules":[
    {"scope":"cell","target_column":"SLA_Days",
     "condition":{"type":"numeric","operator":">","value":7},
     "style":{"bg_color":"#FFD6D6","bold":True}}
  ]
}
```

---

### ImageSection

**Shape**

```json
{
  "type":"image",
  "title":"string?",
  "subtitle":"string?",
  "image_path":"path/to/img.png",
  "caption":"string?",
  "width": number,  
  "colors": Colors?
}
```

**Example**

```python
{"type":"image","title":"Occupancy Map","image_path":"assets/occupancy.png","caption":"As of Oct 31","width":6}
```

---

## 🧪 Formatting Rules Cookbook (PDF)

> Styles support only `bg_color` and `bold`. Text color is not supported.

1. **Cell equals**

```python
{"scope":"cell","target_column":"Status",
 "condition":{"type":"equals","value":"Critical"},
 "style":{"bg_color":"#FFCCCC","bold":True}}
```

2. **Cell contains (case-insensitive)**

```python
{"scope":"cell","target_column":"Notes",
 "condition":{"type":"contains","value":"overdue"},
 "style":{"bg_color":"#FFF0B3","bold":False}}
```

3. **Cell numeric threshold**

```python
{"scope":"cell","target_column":"Amount",
 "condition":{"type":"numeric","operator":">=","value":10000},
 "style":{"bg_color":"#E6F4EA","bold":True}}
```

4. **Row equals**

```python
{"scope":"row","target_column":"Severity",
 "condition":{"type":"equals","value":"High"},
 "style":{"bg_color":"#FFE5CC","bold":False}}
```

5. **Row date vs today (SG time)**

```python
{"scope":"row","target_column":"DueDate",
 "condition":{"type":"date_compare","operator":"<","compare_to":"today"},
 "style":{"bg_color":"#FFD6D6","bold":True}}
```

6. **Row date vs fixed date**

```python
{"scope":"row","target_column":"CreatedAt",
 "condition":{"type":"date_compare","operator":">=","value":"2025-10-01"},
 "style":{"bg_color":"#E8F0FE","bold":False}}
```

7. **Cell date vs other column**

```python
{"scope":"cell","target_column":"ClosedAt",
 "condition":{"type":"date_compare_column","operator":">","compare_column":"OpenedAt"},
 "style":{"bg_color":"#FFF5CC","bold":False}}
```

8. **Categorical color scale (cell)**

```python
{"scope":"cell","target_column":"Status",
 "condition":{"type":"color_scale","scale_type":"categorical",
              "color_map":{"Active":"#D1F7C4","Pending":"#FFE8A3","Inactive":"#FFCCCC"}},
 "style":{"bg_color":"#FFFFFF","bold":False}}
```

9. **Numeric color scale (auto min/mid/max)**

```python
{"scope":"cell","target_column":"Utilization",
 "condition":{"type":"color_scale","scale_type":"numeric","mode":"auto",
              "colors":["#D1F7C4","#FFE8A3","#FFCCCC"]},
 "style":{"bg_color":"#FFFFFF","bold":False}}
```

10. **Date color scale (manual anchors)**

```python
{"scope":"cell","target_column":"InspectionDate",
 "condition":{"type":"color_scale","scale_type":"date","mode":"manual",
              "colors":["#D1F7C4","#FFE8A3","#FFCCCC"],
              "min":"2025-01-01","mid":"2025-06-01","max":"2025-12-31"},
 "style":{"bg_color":"#FFFFFF","bold":False}}
```

*Precedence:* later rules override earlier ones; cell overrides row at the same cell.

---

## 🧯 Error Translation Guide (“When you see this…”)

| Message / Symptom                                                | Meaning (Code Path)                                                                | Fix                                                                   |
| ---------------------------------------------------------------- | ---------------------------------------------------------------------------------- | --------------------------------------------------------------------- |
| `⚠️  ... groups not in category_order (appending at end): [...]` | Data has categories missing from `category_order`.                                 | Add them or accept appended order.                                    |
| `⚠️  ... date_compare ... not found / not parseable`             | `compare_to` references global (`start_date`/`end_date`) missing or unparsable.    | Define those globals in runtime or use `value:"YYYY-MM-DD"`.          |
| `... date comparison: N invalid dates`                           | Target column had unparseable dates.                                               | Normalize upstream or adjust rule/format.                             |
| `... categorical color scale: N unmapped values (...)`           | Some values missing in `color_map`.                                                | Add entries or accept no color for unmapped.                          |
| Image doesn’t render, no crash                                   | `image_path` missing/invalid → section skipped.                                    | Ensure file exists at runtime.                                        |
| Title suffix missing                                             | `title_suffix_from_column` reads from **original df**; column may not exist there. | Ensure column exists pre-drop/clean (or remove the suffix).           |
| Column widths ignored                                            | Fractions didn’t sum ≈ 1.0 or length mismatch.                                     | Provide fractional list of same length as visible columns; sum ≈ 1.0. |

---

## 🖋️ Type Hints (concise)

```python
from typing import Any, Dict, List, Optional, Tuple, Union
import pandas as pd

Colors = Dict[str, str]

Rule = Dict[str, Any]
ColumnFormat = Dict[str, Any]
CellFormat = Dict[str, Any]
ColumnFormats = Dict[str, ColumnFormat]
CellFormats = Dict[Union[Tuple[int, str], str], CellFormat]

TitleSection = Dict[str, Any]         # {"type":"title", ...}
TextSection  = Dict[str, Any]         # {"type":"text", ...}
TableSection = Dict[str, Any]         # {"type":"table","df":pd.DataFrame, ...}
GroupedTableSection = Dict[str, Any]  # {"type":"table_grouped","df":pd.DataFrame,"groupby":str, ...}
ImageSection = Dict[str, Any]         # {"type":"image", ...}

Section = Union[TitleSection, TextSection, TableSection, GroupedTableSection, ImageSection]

def generate_report(
    report_sections: List[Section],
    format: str = "pdf",
    output_filename: str = "report.pdf",
    colors: Optional[Colors] = None,
    header_config: Optional[Dict[str, Any]] = None,
    footer_config: Optional[Dict[str, Any]] = None,
    background_svg: Optional[str] = None
) -> str: ...
```

---

## 🧭 LLM “How-to-Choose” Decision Trees (text)

**Table vs Grouped Table**

* Need per-category blocks (each with its own header)? → **Grouped**
* Single grid, no per-group headers → **Table**

**Rules or no rules**

* Visual cues needed (overdue, thresholds, statuses)? → add **`formatting_rules`** (PDF only)
* No highlights needed → omit for speed

**Cleaning**

* Many blank columns/rows? → `clean_empty_cols/rows: True`
* Keep structure identical to source? → leave them False

**Column widths**

* You want control? → provide **fractions that sum ≈ 1.0** (same length as visible columns)
* You don’t care? → omit → equal widths

**Title suffix**

* Want “(Oct 2025)” after the title? → `title_suffix_from_column:"Month"`
  *(Reads from **original df**; there is no toggle.)*

**Links**

* Need clickable links in PDF? → Use `<link href="...">Text</link>` in any text/cell

**DOCX**

* Need headers/footers, rules, SVG? → **Use PDF**. DOCX is basic export only.

---

## 🧰 What Works Where (Parameter-Support Matrix)

| Parameter / Feature                 | PDF Table |                    PDF Grouped |               DOCX Table | Notes                                                |
| ----------------------------------- | --------: | -----------------------------: | -----------------------: | ---------------------------------------------------- |
| `title`, `subtitle`                 |         ✓ | ✓ (section + per-group header) |                        ✓ |                                                      |
| `colors` cascade                    |         ✓ |                              ✓ | ✓ (header bg + alt rows) | Same keys; DOCX applies a subset visually            |
| `drop_columns`                      |         ✓ |                  ✓ (per group) |                        ✓ |                                                      |
| `clean_empty_cols/rows`             |         ✓ |                  ✓ (per group) |                        ✓ |                                                      |
| `title_suffix_from_column`          |         ✓ |                 (section only) |                        ✓ | Reads from **original df**                           |
| `column_widths` (fractions sum≈1.0) |         ✓ |                              ✓ |                        – | Invalid → equal widths                               |
| `formatting_rules`                  |         ✓ |                              ✓ |                        – | PDF only                                             |
| `column_formats` / `cell_formats`   |         ✓ |                              ✓ |                       ✓* | DOCX uses `format_value` only; no rule visuals/align |
| Header/Footer                       |         ✓ |                              ✓ |                        – | 3-zone footer; page totals; header line/logo/text    |
| SVG background                      |         ✓ |                              ✓ |                        – | All pages; behind content                            |
| Hyperlinks (`<link>`)               |         ✓ |                              ✓ |                        – | PDF only                                             |

* DOCX: number/date/na formatting appears (via `format_value`), but **align** keys are not applied.

---

## ⚠️ Gotchas for Agents (LLM Watch-Outs)

* **DF objects only**: `"df"` must be a **pandas.DataFrame**, not the name of one.
* **Column widths**: only **fractions** are supported; length must match visible columns; sum ≈ 1.0.
* **No text color in rules**: only `bg_color` + `bold`. (Do not invent `text_color`.)
* **Title suffix source**: comes from the **original df** (pre-drop/clean). There’s no toggle.
* **Percentage formatting**: uses value as given (`0.23 → "0.2%"`). Scale yourself if you want `23%`.
* **Large cells**: keep content ≲ 500 chars to avoid layout issues.
* **PDF-only features**: rules, header/footer, SVG, hyperlinks are **not** in DOCX.
* **Date rules context**: `compare_to:"today"` is SG (UTC+8). `"start_date"/"end_date"` rely on globals if you’ve injected them.
* **Category order**: missing categories are appended with a warning.

---

## 🧱 Complete Template Examples

### Example 1 — Minimal KPI (PDF)

```python
import pandas as pd
from reportlabcustom import generate_report

df = pd.DataFrame([
  {"Metric":"Total SRs","Value":128},
  {"Metric":"Resolved","Value":117},
  {"Metric":"Avg Close (days)","Value":2.3},
])

template = [
  {"type":"title","title":"Condo KPI Snapshot","subtitle":"October 2025"},
  {"type":"text","title":"Summary","content":"Performance remains stable month-on-month."},
  {"type":"table","title":"Key Metrics","df":df,
   "column_formats":{"Value":{"type":"number","decimal_places":1,"thousands_separator":True}},
   "clean_empty_cols":True,"clean_empty_rows":True}
]

generate_report(template, format="pdf", output_filename="kpi.pdf")
```

---

### Example 2 — Grouped Tickets + Rules + Header/Footer + SVG (PDF)

```python
import pandas as pd
from reportlabcustom import generate_report

df = pd.DataFrame([
  {"Status":"Open","SLA_Days":3,"Title":"Gate light issue","OpenedAt":"2025-10-29","ClosedAt":None},
  {"Status":"Work In Progress","SLA_Days":9,"Title":"Lift noise","OpenedAt":"2025-10-20","ClosedAt":None},
  {"Status":"Resolved","SLA_Days":2,"Title":"Pool pump","OpenedAt":"2025-10-10","ClosedAt":"2025-10-12"},
])

template = [
  {"type":"title","title":"Service Requests","subtitle":"October 2025"},
  {"type":"table_grouped","title":"By Status","subtitle":"SLA highlights","df":df,"groupby":"Status",
   "category_order":["Open","Work In Progress","Resolved"],
   "formatting_rules":[
     {"scope":"cell","target_column":"SLA_Days",
      "condition":{"type":"numeric","operator":">","value":7},
      "style":{"bg_color":"#FFD6D6","bold":True}},
     {"scope":"cell","target_column":"Title",
      "condition":{"type":"contains","value":"lift"},
      "style":{"bg_color":"#FFF0B3","bold":False}}
   ],
   "column_formats":{
     "SLA_Days":{"type":"number","decimal_places":0},
     "OpenedAt":{"type":"date","format":"YYYY-MM-DD"},
     "ClosedAt":{"type":"date","format":"YYYY-MM-DD"}
   },
   "clean_empty_cols":True,"clean_empty_rows":True
  }
]

head = {"text":"Monthly Report","text_position":"right","draw_line":True}
foot = {"text_left":"© 2025 Ohmyhome","page_numbers":{"position":"center"},"draw_line":True}

generate_report(
  template, format="pdf", output_filename="tickets.pdf",
  header_config=head, footer_config=foot, background_svg="assets/letterhead_background.svg"
)
```

---

### Example 3 — Links, Money Formats, Alt Rows (PDF)

```python
import pandas as pd
from reportlabcustom import generate_report

df = pd.DataFrame([
  {"Vendor":"ACME","Contract":"<link href=\"https://example.com/c/1001\" color=\"blue\">#1001</link>","Amount":12345.6,"Date":"2025-10-03","Status":"Active"},
  {"Vendor":"Bolt","Contract":"<link href=\"https://example.com/c/1002\" color=\"blue\">#1002</link>","Amount":980.0,"Date":"2025-10-11","Status":"Pending"}
])

template = [
  {"type":"title","title":"Contracts Summary","subtitle":"As at Oct 31, 2025"},
  {"type":"table","title":"Active Contracts","df":df,
   "column_formats":{
     "Amount":{"type":"currency","currency_symbol":"$","decimal_places":2,"thousands_separator":True},
     "Date":{"type":"date","format":"YYYY-MM-DD"}
   },
   "formatting_rules":[{
     "scope":"cell","target_column":"Status",
     "condition":{"type":"color_scale","scale_type":"categorical",
                  "color_map":{"Active":"#D1F7C4","Pending":"#FFE8A3"}},
     "style":{"bg_color":"#FFFFFF","bold":False}
   }],
   "clean_empty_cols":True,"clean_empty_rows":True
  }
]

generate_report(template, format="pdf", output_filename="contracts.pdf")
```

---

## 📏 Core Behavior & Defaults

* **Deterministic order:** sections render in the array’s order.
* **Two-pass PDF build:** proper `{n}/{total}` page numbers in footer.
* **Header/Footer (PDF):** three zones; if page numbers occupy a zone, that zone’s text is ignored.
* **Smart orphan control:** ~2″ threshold avoids orphaned titles/subtitles/group headers.
* **Grouped tables:** missing categories appended with a warning; no subtotals.
* **Title suffix:** `title_suffix_from_column` reads from **original df** (pre-drop/clean). No toggle exists.
* **Links (PDF):** use `<link href="..." color="blue">Text</link>` inside text or cells.
* **DOCX:** basic renderer (no header/footer, no rules, no SVG, no column widths enforcement). Formats via `format_value` only.

### Theme defaults (`theme.py`)

```python
report_colors = {
  'header_bg':'#FF8C00','header_text':'#FFFFFF',
  'row_alt':'#FFE5CC','row_normal':'#FFFFFF',
  'separator':'#FF8C00','subtitle':'#666666','section_subtitle':'#888888',
}
```

### SVG Background (PDF)

* `background_svg="path/to/file.svg"`
* Loads once, scaled to letter, aspect preserved & centered, drawn **behind** content/header/footer.
* Invalid/missing file → warning, continue without background.

---

**End of SPEC.md (v2.6)**

---

## ➕ Addenda (v2.6)

### 🖇️ Type Hints — Autocomplete‑Friendly Stubs (.pyi‑style)

> Drop this block into `reportlabcustom/_types.pyi` (or keep in the SPEC) to guide LLMs/IDEs.

```python
from typing import Any, Dict, List, Optional, Tuple, Union, Literal, TypedDict, NotRequired
import pandas as pd

# ---------- Visual theme ----------
class Colors(TypedDict, total=False):
    header_bg: str
    header_text: str
    row_alt: str
    row_normal: str
    separator: str
    subtitle: str
    section_subtitle: str

# ---------- Header / Footer (PDF) ----------
class PageNumbers(TypedDict, total=False):
    position: Literal['left','center','right']
    format: NotRequired[str]

class FooterConfig(TypedDict, total=False):
    text_left: NotRequired[str]
    text_center: NotRequired[str]
    text_right: NotRequired[str]
    page_numbers: NotRequired[PageNumbers]
    font_size: NotRequired[int]
    text_color: NotRequired[str]
    draw_line: NotRequired[bool]
    line_color: NotRequired[str]
    height: NotRequired[float]  # inches

class HeaderConfig(TypedDict, total=False):
    text: NotRequired[str]
    text_position: NotRequired[Literal['left','center','right']]
    font_size: NotRequired[int]
    text_color: NotRequired[str]
    logo_path: NotRequired[str]
    logo_width: NotRequired[float]  # inches
    logo_height: NotRequired[float] # inches
    logo_position: NotRequired[Literal['left','center','right']]
    draw_line: NotRequired[bool]
    line_color: NotRequired[str]
    height: NotRequired[float]      # inches

# ---------- Formatting ----------
class Style(TypedDict, total=False):
    bg_color: str
    bold: bool

class CondEquals(TypedDict):
    type: Literal['equals']
    value: Any

class CondContains(TypedDict):
    type: Literal['contains']
    value: str

class CondNumeric(TypedDict):
    type: Literal['numeric']
    operator: Literal['>','>=','<','<=','==','!=']
    value: float

class CondDateCompare(TypedDict, total=False):
    type: Literal['date_compare']
    operator: Literal['>','>=','<','<=','==']
    compare_to: NotRequired[Literal['today','start_date','end_date']]
    value: NotRequired[str]  # 'YYYY-MM-DD'

class CondDateCompareColumn(TypedDict):
    type: Literal['date_compare_column']
    operator: Literal['>','>=','<','<=','==']
    compare_column: str

class CondColorScaleCategorical(TypedDict):
    type: Literal['color_scale']
    scale_type: Literal['categorical']
    color_map: Dict[str, str]

class CondColorScaleNumeric(TypedDict, total=False):
    type: Literal['color_scale']
    scale_type: Literal['numeric']
    mode: Literal['auto','manual']
    colors: List[str]  # exactly 3
    min: NotRequired[float]
    mid: NotRequired[float]
    max: NotRequired[float]

class CondColorScaleDate(TypedDict, total=False):
    type: Literal['color_scale']
    scale_type: Literal['date']
    mode: Literal['auto','manual']
    colors: List[str]  # exactly 3
    min: NotRequired[str]
    mid: NotRequired[str]
    max: NotRequired[str]

Condition = Union[
    CondEquals, CondContains, CondNumeric,
    CondDateCompare, CondDateCompareColumn,
    CondColorScaleCategorical, CondColorScaleNumeric, CondColorScaleDate
]

class Rule(TypedDict, total=False):
    scope: Literal['row','cell']
    target_column: str
    condition: Condition
    style: Style

class ColumnFormat(TypedDict, total=False):
    type: Literal['number','currency','percentage','date']
    decimal_places: NotRequired[int]
    thousands_separator: NotRequired[bool]
    currency_symbol: NotRequired[str]
    format: NotRequired[str]  # for dates
    align: NotRequired[Literal['left','center','right']]
    na: NotRequired[str]

ColumnFormats = Dict[str, ColumnFormat]
# CellFormats are applied via (row_index, col_name) or direct mapping; kept flexible in code.
CellFormats = Dict[Any, ColumnFormat]

# ---------- Sections ----------
class TitleSection(TypedDict, total=False):
    type: Literal['title']
    title: str
    subtitle: NotRequired[str]
    separator_color: NotRequired[str]
    subtitle_color: NotRequired[str]
    colors: NotRequired[Colors]

class TextSection(TypedDict, total=False):
    type: Literal['text']
    title: NotRequired[str]
    subtitle: NotRequired[str]
    content: str
    style: NotRequired[Literal['normal','bold','italic']]
    alignment: NotRequired[Literal['left','center','right']]
    font_size: NotRequired[int]
    colors: NotRequired[Colors]

class TableSection(TypedDict, total=False):
    type: Literal['table']
    title: NotRequired[str]
    subtitle: NotRequired[str]
    df: pd.DataFrame
    drop_columns: NotRequired[List[str]]
    clean_empty_cols: NotRequired[bool]
    clean_empty_rows: NotRequired[bool]
    title_suffix_from_column: NotRequired[str]
    column_widths: NotRequired[List[float]]  # fractions, sum≈1.0
    formatting_rules: NotRequired[List[Rule]]
    column_formats: NotRequired[ColumnFormats]
    cell_formats: NotRequired[CellFormats]
    colors: NotRequired[Colors]

class GroupedTableSection(TypedDict, total=False):
    type: Literal['table_grouped']
    title: NotRequired[str]
    subtitle: NotRequired[str]
    df: pd.DataFrame
    groupby: str
    category_order: NotRequired[List[str]]
    drop_columns: NotRequired[List[str]]
    clean_empty_cols: NotRequired[bool]
    clean_empty_rows: NotRequired[bool]
    formatting_rules: NotRequired[List[Rule]]
    column_formats: NotRequired[ColumnFormats]
    cell_formats: NotRequired[CellFormats]
    colors: NotRequired[Colors]

class ImageSection(TypedDict, total=False):
    type: Literal['image']
    title: NotRequired[str]
    subtitle: NotRequired[str]
    image_path: str
    caption: NotRequired[str]
    width: NotRequired[float]  # inches
    colors: NotRequired[Colors]

Section = Union[TitleSection, TextSection, TableSection, GroupedTableSection, ImageSection]

# ---------- Public API ----------

def generate_report(
    report_sections: List[Section],
    format: Literal['pdf','docx'] = 'pdf',
    output_filename: str = 'report.pdf',
    colors: Optional[Colors] = None,
    header_config: Optional[HeaderConfig] = None,
    footer_config: Optional[FooterConfig] = None,
    background_svg: Optional[str] = None
) -> str: ...

# ---------- Utils (signatures) ----------

def prepare_dataframe(df: pd.DataFrame) -> pd.DataFrame: ...

def format_value(value: Any, format_spec: Optional[ColumnFormat] = None) -> str: ...

def evaluate_formatting_rules(df: pd.DataFrame, rules: List[Rule]) -> Dict[str, Any]: ...
```

---

### 🧭 Decision Tree — Picking the Right Rule (textual flow)

1. **What do you want to highlight?**

   * Entire records → use `scope: "row"`
   * Single cells → use `scope: "cell"`

2. **What’s the data type?**

   * Text keyword/pattern → `condition.type: "contains"` (case‑insensitive)
   * Text exact value → `"equals"`
   * Numbers (>, <, thresholds) → `"numeric"` with `operator` + `value`
   * Single date vs **today/fixed date** → `"date_compare"`
   * **Date vs date in another column** → `"date_compare_column"`
   * Color by **category** → `"color_scale"` + `scale_type: "categorical"` + `color_map`
   * Color by **magnitude (numbers)** → `"color_scale"` + `scale_type: "numeric"` (auto or manual anchors)
   * Color by **recency/time** → `"color_scale"` + `scale_type: "date"` (auto or manual anchors)

3. **What style to apply?**

   * Background only: `style: {"bg_color":"#RRGGBB"}`
   * Emphasis: add `"bold": true`
   * *(Text color is not supported.)*

4. **Multiple rules?**

   * Order matters: later rules **override** earlier ones
   * Cell‑scope overrides row‑scope for the same cell

5. **Sanity checks**

   * Target column exists?
   * Date values parse? (use `prepare_dataframe` or a date format in `column_formats`)
   * Categorical map covers the main values? (warnings show unmapped values)

---

### 🧹 Cleaning Flags — Before/After Example

**Input DataFrame (`df`)**

| idx | A    | B  | C  |
| --: | :--- | :- | :- |
|   0 | x    | '' | 1  |
|   1 | ''   | '' | '' |
|   2 | None | '' | 3  |
|   3 | ''   | '' | '' |

*(Empty string shown as `''`; `None` stands for missing/NaN.)*

```python
section = {
  "type": "table",
  "title": "Cleaning Demo",
  "df": df,
}
```

**Case A — `clean_empty_cols=True` (columns only)**

* Drops any column that is entirely NA/`''`.
* Here, **B** is all empty → dropped.

**Rendered columns:** A, C

**Case B — `clean_empty_rows=True` (rows only)**

* Drops any row whose cells are all NA/`''`.
* Here, rows **1** and **3** are fully empty → dropped.

**Remaining rows:** idx 0 and 2

**Case C — both flags True**

* First apply column drop, then row drop on the remaining data.
* Result: columns **A, C** with rows **0, 2**.

**Notes**

* Numeric zeros (`0`) are **kept** (non‑empty after `astype(str)`); only NA/`''` collapse.
* Order of user‑provided `drop_columns` is respected **before** suffix/formatting.
* `title_suffix_from_column` reads from the **original df** even if that column is later dropped.

---
