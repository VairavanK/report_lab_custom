# src/yourpkg/utils.py
import os
from datetime import datetime, timezone, timedelta
import pandas as pd

from reportlab.lib.pagesizes import letter
from svglib.svglib import svg2rlg

# ===== Timezone used by date rules =====
sg_tz = timezone(timedelta(hours=8))

# ===== SVG utilities =====
def load_and_scale_svg(svg_path):
    """
    Load SVG and scale to letter size (8.5\" x 11\").
    Returns a ReportLab Drawing object or None.
    """
    if not os.path.exists(svg_path):
        print(f"⚠️ Warning: SVG background file not found: {svg_path}")
        return None

    try:
        drawing = svg2rlg(svg_path)
        if not drawing:
            print(f"⚠️ Warning: Could not parse SVG file: {svg_path}")
            return None

        target_width = letter[0]   # 612 pt
        target_height = letter[1]  # 792 pt

        scale_x = target_width / drawing.width
        scale_y = target_height / drawing.height
        scale = min(scale_x, scale_y)

        drawing.width *= scale
        drawing.height *= scale
        drawing.scale(scale, scale)
        return drawing
    except Exception as e:
        print(f"⚠️ Warning: Error loading SVG background: {e}")
        return None

# ===== Color helpers =====
def hex_to_rgb(hex_color):
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

def rgb_to_hex(rgb):
    return '#{:02x}{:02x}{:02x}'.format(int(rgb[0]), int(rgb[1]), int(rgb[2]))

def interpolate_color(color1, color2, factor):
    rgb1 = hex_to_rgb(color1)
    rgb2 = hex_to_rgb(color2)
    rgb = tuple(rgb1[i] + (rgb2[i] - rgb1[i]) * factor for i in range(3))
    return rgb_to_hex(rgb)

def get_gradient_color(value, min_val, mid_val, max_val, colors):
    if value <= min_val:
        return colors[0]
    elif value >= max_val:
        return colors[2]
    elif value <= mid_val:
        factor = (value - min_val) / (mid_val - min_val)
        return interpolate_color(colors[0], colors[1], factor)
    else:
        factor = (value - mid_val) / (max_val - mid_val)
        return interpolate_color(colors[1], colors[2], factor)

def calculate_luminance(hex_color):
    r, g, b = [x / 255.0 for x in hex_to_rgb(hex_color)]
    r = r / 12.92 if r <= 0.03928 else ((r + 0.055) / 1.055) ** 2.4
    g = g / 12.92 if g <= 0.03928 else ((g + 0.055) / 1.055) ** 2.4
    b = b / 12.92 if b <= 0.03928 else ((b + 0.055) / 1.055) ** 2.4
    return 0.2126 * r + 0.7152 * g + 0.0722 * b

def get_contrasting_text_color(bg_hex_color):
    return '#FFFFFF' if calculate_luminance(bg_hex_color) < 0.5 else '#000000'

# ===== Formatting & dataframe utilities =====
def format_value(value, format_spec=None):
    """
    Format values for display with optional format_spec:
      {'type': 'date'|'currency'|'percentage'|'number', ...}
    """
    if pd.isna(value) or value is None or str(value) in ['NaT', 'nan', 'None']:
        return ''

    if not format_spec:
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            return str(int(value)) if value == int(value) else f"{value:.2f}"
        return str(value)

    t = format_spec.get('type')

    if t == 'date':
        date_format = format_spec.get('format', 'YYYY-MM-DD')
        try:
            dt = pd.to_datetime(value, errors='coerce') if isinstance(value, str) else pd.Timestamp(value)
            if pd.isna(dt):
                return str(value)
            fmts = {
                'YYYY-MM-DD': '%Y-%m-%d',
                'MM/DD/YYYY': '%m/%d/%Y',
                'DD/MM/YYYY': '%d/%m/%Y',
                'DD MMM YYYY': '%d %b %Y',
                'MMMM DD, YYYY': '%B %d, %Y',
                'DD-MMM-YY': '%d-%b-%y',
            }
            return dt.strftime(fmts.get(date_format, '%Y-%m-%d'))
        except Exception:
            return str(value)

    if t == 'currency':
        try:
            num = float(value)
            dp = format_spec.get('decimal_places', 2)
            sym = format_spec.get('currency_symbol', '$')
            return f"{sym}{num:,.{dp}f}"
        except Exception:
            return str(value)

    if t == 'percentage':
        try:
            num = float(value)
            dp = format_spec.get('decimal_places', 1)
            return f"{num:.{dp}f}%"
        except Exception:
            return str(value)

    if t == 'number':
        try:
            num = float(value)
            dp = format_spec.get('decimal_places', 2)
            ts = format_spec.get('thousands_separator', False)
            return f"{num:,.{dp}f}" if ts else f"{num:.{dp}f}"
        except Exception:
            return str(value)

    return str(value)

def prepare_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    for col in df.columns:
        if pd.api.types.is_datetime64_any_dtype(df[col]):
            df[col] = df[col].dt.strftime('%Y-%m-%d')
        elif df[col].dtype == 'object':
            sample = df[col].dropna().astype(str).head(10)
            if len(sample) > 0 and sample.str.contains(r'[-/:]').any():
                try:
                    temp = pd.to_datetime(df[col], errors='coerce')
                    parsed = temp.notna().sum()
                    total = df[col].notna().sum()
                    if total > 0 and (parsed / total) >= 0.8:
                        df[col] = temp.dt.strftime('%Y-%m-%d')
                except Exception:
                    pass
    return df

def evaluate_formatting_rules(df: pd.DataFrame, rules):
    """
    Returns:
      {'rows': {row_idx: {...}}, 'cells': {(row_idx, col_idx): {...}}, 'warnings': [...]}
    """
    if not rules:
        return {'rows': {}, 'cells': {}, 'warnings': []}

    style_map = {'rows': {}, 'cells': {}, 'warnings': []}

    for rule in rules:
        scope = rule.get('scope', 'cell')
        condition = rule.get('condition', {})
        style = rule.get('style', {})

        # ---- Row-scope ----
        if scope == 'row':
            target_column = rule.get('target_column')
            if not target_column or target_column not in df.columns:
                continue
            cond_type = condition.get('type')

            if cond_type == 'contains':
                search = str(condition.get('value', '')).lower()
                for idx, row in df.iterrows():
                    if search in str(row[target_column]).lower():
                        style_map['rows'][df.index.get_loc(idx)] = style

            elif cond_type == 'equals':
                val = condition.get('value', '')
                for idx, row in df.iterrows():
                    if str(row[target_column]).strip() == str(val):
                        style_map['rows'][df.index.get_loc(idx)] = style

            elif cond_type == 'date_compare':
                op = condition.get('operator', '>')
                compare_to = condition.get('compare_to')
                compare_value = condition.get('value')

                # resolve target_date
                if compare_to == 'today':
                    target_date = datetime.now(sg_tz).date()
                elif compare_to in ['start_date', 'end_date']:
                    try:
                        target_date = globals().get(compare_to)
                        if target_date is None:
                            style_map['warnings'].append(f"compare_to='{compare_to}' not found in context")
                            continue
                        target_date = pd.to_datetime(target_date, errors='coerce')
                        if pd.isna(target_date):
                            style_map['warnings'].append(f"compare_to='{compare_to}' not parseable")
                            continue
                        target_date = target_date.date() if hasattr(target_date, 'date') else target_date
                    except Exception as e:
                        style_map['warnings'].append(f"Error accessing '{compare_to}': {e}")
                        continue
                elif compare_value:
                    target_date = pd.to_datetime(compare_value, errors='coerce')
                    if pd.isna(target_date):
                        style_map['warnings'].append(f"Fixed date '{compare_value}' not parseable")
                        continue
                    target_date = target_date.date() if hasattr(target_date, 'date') else target_date
                else:
                    style_map['warnings'].append("date_compare missing 'compare_to' or 'value'")
                    continue

                parse_failures = 0
                for idx, row in df.iterrows():
                    try:
                        cell_date = pd.to_datetime(row[target_column], errors='coerce')
                        if pd.isna(cell_date):
                            parse_failures += 1
                            continue
                        cell_date = cell_date.date() if hasattr(cell_date, 'date') else cell_date

                        match = (
                            (op == '>' and cell_date > target_date) or
                            (op == '>=' and cell_date >= target_date) or
                            (op == '<' and cell_date < target_date) or
                            (op == '<=' and cell_date <= target_date) or
                            (op == '==' and cell_date == target_date)
                        )
                        if match:
                            style_map['rows'][df.index.get_loc(idx)] = style
                    except Exception:
                        parse_failures += 1
                        continue
                if parse_failures:
                    style_map['warnings'].append(
                        f"date_compare on '{target_column}': {parse_failures} rows unparseable"
                    )

        # ---- Cell-scope ----
        elif scope == 'cell':
            target_column = rule.get('target_column')
            if not target_column or target_column not in df.columns:
                continue
            col_idx = df.columns.get_loc(target_column)
            cond_type = condition.get('type')

            if cond_type == 'equals':
                val = condition.get('value')
                for idx, row in df.iterrows():
                    if str(row[target_column]) == str(val):
                        style_map['cells'][(df.index.get_loc(idx) + 1, col_idx)] = style  # +1 header

            elif cond_type == 'contains':
                val = str(condition.get('value', '')).lower()
                for idx, row in df.iterrows():
                    if val in str(row[target_column]).lower():
                        style_map['cells'][(df.index.get_loc(idx) + 1, col_idx)] = style

            elif cond_type == 'numeric':
                op = condition.get('operator', '>')
                thr = condition.get('value', 0)
                for idx, row in df.iterrows():
                    try:
                        num = float(row[target_column])
                        match = (
                            (op == '>' and num > thr) or
                            (op == '>=' and num >= thr) or
                            (op == '<' and num < thr) or
                            (op == '<=' and num <= thr) or
                            (op == '==' and num == thr)
                        )
                        if match:
                            style_map['cells'][(df.index.get_loc(idx) + 1, col_idx)] = style
                    except Exception:
                        continue

            elif cond_type == 'date_compare':
                op = condition.get('operator', '>')
                compare_to = condition.get('compare_to')
                compare_value = condition.get('value')

                if compare_to == 'today':
                    target_date = datetime.now(sg_tz).date()
                elif compare_to in ['start_date', 'end_date']:
                    try:
                        target_date = globals().get(compare_to)
                        if target_date is None:
                            style_map['warnings'].append(f"compare_to='{compare_to}' not found")
                            continue
                        target_date = pd.to_datetime(target_date, errors='coerce')
                        if pd.isna(target_date):
                            style_map['warnings'].append(f"compare_to='{compare_to}' not parseable")
                            continue
                        target_date = target_date.date() if hasattr(target_date, 'date') else target_date
                    except Exception as e:
                        style_map['warnings'].append(f"Error accessing '{compare_to}': {e}")
                        continue
                elif compare_value:
                    target_date = pd.to_datetime(compare_value, errors='coerce')
                    if pd.isna(target_date):
                        style_map['warnings'].append(f"Fixed date '{compare_value}' not parseable")
                        continue
                    target_date = target_date.date() if hasattr(target_date, 'date') else target_date
                else:
                    style_map['warnings'].append("date_compare missing 'compare_to' or 'value'")
                    continue

                parse_failures = 0
                for idx, row in df.iterrows():
                    try:
                        cell_date = pd.to_datetime(row[target_column], errors='coerce')
                        if pd.isna(cell_date):
                            parse_failures += 1
                            continue
                        cell_date = cell_date.date() if hasattr(cell_date, 'date') else cell_date

                        match = (
                            (op == '>' and cell_date > target_date) or
                            (op == '>=' and cell_date >= target_date) or
                            (op == '<' and cell_date < target_date) or
                            (op == '<=' and cell_date <= target_date) or
                            (op == '==' and cell_date == target_date)
                        )
                        if match:
                            style_map['cells'][(df.index.get_loc(idx) + 1, col_idx)] = style
                    except Exception:
                        parse_failures += 1
                        continue
                if parse_failures:
                    style_map['warnings'].append(
                        f"'{target_column}' date comparison: {parse_failures} invalid dates"
                    )

            elif cond_type == 'date_compare_column':
                op = condition.get('operator', '>')
                compare_column = condition.get('compare_column')
                if not compare_column or compare_column not in df.columns:
                    style_map['warnings'].append(f"Compare column '{compare_column}' not found")
                    continue

                parse_failures = 0
                for idx, row in df.iterrows():
                    try:
                        d1 = pd.to_datetime(row[target_column], errors='coerce')
                        d2 = pd.to_datetime(row[compare_column], errors='coerce')
                        if pd.isna(d1) or pd.isna(d2):
                            parse_failures += 1
                            continue

                        match = (
                            (op == '>' and d1 > d2) or
                            (op == '>=' and d1 >= d2) or
                            (op == '<' and d1 < d2) or
                            (op == '<=' and d1 <= d2) or
                            (op == '==' and d1 == d2)
                        )
                        if match:
                            style_map['cells'][(df.index.get_loc(idx) + 1, df.columns.get_loc(target_column))] = style
                    except Exception:
                        parse_failures += 1
                        continue

                if parse_failures:
                    style_map['warnings'].append(
                        f"'{target_column}' vs '{compare_column}': {parse_failures} invalid dates"
                    )

            elif cond_type == 'color_scale':
                scale_type = condition.get('scale_type', 'numeric')
                if scale_type == 'categorical':
                    color_map = condition.get('color_map', {})
                    if not color_map:
                        style_map['warnings'].append("color_scale categorical missing 'color_map'")
                        continue
                    unmapped = set()
                    for idx, row in df.iterrows():
                        val = str(row[target_column])
                        if val in color_map:
                            bg = color_map[val]
                            style_map['cells'][(df.index.get_loc(idx) + 1, col_idx)] = {
                                'bg_color': bg,
                                # text color calculation is done in PDF renderer if needed
                            }
                        else:
                            unmapped.add(val)
                    if unmapped:
                        head = ', '.join(list(unmapped)[:3])
                        suffix = '...' if len(unmapped) > 3 else ''
                        style_map['warnings'].append(
                            f"'{target_column}' categorical color scale: {len(unmapped)} unmapped values ({head}{suffix})"
                        )

                elif scale_type == 'numeric':
                    mode = condition.get('mode', 'auto')
                    colors3 = condition.get('colors', ['#00FF00', '#FFFF00', '#FF0000'])
                    if len(colors3) != 3:
                        style_map['warnings'].append("color_scale numeric requires exactly 3 colors")
                        continue

                    numeric_values = []
                    for idx, row in df.iterrows():
                        try:
                            v = float(row[target_column])
                            if not pd.isna(v):
                                numeric_values.append((idx, v))
                        except Exception:
                            continue
                    if not numeric_values:
                        style_map['warnings'].append(f"'{target_column}' has no valid numeric values")
                        continue

                    if mode == 'auto':
                        all_vals = [v for _, v in numeric_values]
                        min_val, max_val = min(all_vals), max(all_vals)
                        mid_val = (min_val + max_val) / 2
                    else:
                        min_val = condition.get('min')
                        mid_val = condition.get('mid')
                        max_val = condition.get('max')
                        if None in (min_val, mid_val, max_val) or not (min_val < mid_val < max_val):
                            style_map['warnings'].append("color_scale manual requires valid min < mid < max")
                            continue

                    for idx, value in numeric_values:
                        bg = get_gradient_color(value, min_val, mid_val, max_val, colors3)
                        style_map['cells'][(df.index.get_loc(idx) + 1, col_idx)] = {'bg_color': bg}

                elif scale_type == 'date':
                    mode = condition.get('mode', 'auto')
                    colors3 = condition.get('colors', ['#00FF00', '#FFFF00', '#FF0000'])
                    if len(colors3) != 3:
                        style_map['warnings'].append("color_scale date requires exactly 3 colors")
                        continue

                    date_values, failures = [], 0
                    for idx, row in df.iterrows():
                        try:
                            d = pd.to_datetime(row[target_column], errors='coerce')
                            if pd.isna(d):
                                failures += 1
                                continue
                            date_values.append((idx, d.toordinal()))
                        except Exception:
                            failures += 1
                    if not date_values:
                        style_map['warnings'].append(f"'{target_column}' has no valid dates")
                        continue
                    if failures:
                        style_map['warnings'].append(
                            f"'{target_column}' date color scale: {failures} invalid dates"
                        )

                    if mode == 'auto':
                        vals = [v for _, v in date_values]
                        min_val, max_val = min(vals), max(vals)
                        mid_val = (min_val + max_val) / 2
                    else:
                        try:
                            min_val = pd.to_datetime(condition.get('min')).toordinal()
                            mid_val = pd.to_datetime(condition.get('mid')).toordinal()
                            max_val = pd.to_datetime(condition.get('max')).toordinal()
                            if not (min_val < mid_val < max_val):
                                style_map['warnings'].append("date scale requires min < mid < max")
                                continue
                        except Exception:
                            style_map['warnings'].append("date scale manual: invalid date(s)")
                            continue

                    for idx, ordv in date_values:
                        bg = get_gradient_color(ordv, min_val, mid_val, max_val, colors3)
                        style_map['cells'][(df.index.get_loc(idx) + 1, col_idx)] = {'bg_color': bg}

    return style_map
