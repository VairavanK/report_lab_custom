import os
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import Paragraph, Spacer, Table, TableStyle, KeepTogether, BaseDocTemplate, PageTemplate, Frame
from reportlab.platypus.flowables import Flowable
from reportlab.graphics import renderPDF

from .utils import prepare_dataframe, format_value, evaluate_formatting_rules, load_and_scale_svg
from .theme import report_colors

# ==================== HEADER AND FOOTER DRAWING ====================

def draw_footer(canvas, doc, footer_config):
    """Draw three-zone footer with flexible positioning"""
    canvas.saveState()
    
    page_width = letter[0]
    footer_y = 0.5 * inch
    
    font_size = footer_config.get('font_size', 9)
    text_color = footer_config.get('text_color', '#666666')
    
    canvas.setFont("Helvetica", font_size)
    canvas.setFillColor(colors.HexColor(text_color))
    
    # Get page number config
    page_num_config = footer_config.get('page_numbers', {})
    page_num_position = page_num_config.get('position', 'center')
    page_num_format = page_num_config.get('format', 'Page {n} of {total}')
    
    # Get total page count from doc (stored by two-pass rendering)
    current_page = canvas.getPageNumber()
    total_pages = getattr(doc, '_total_page_count', current_page)  # ← FIX: Use stored total
    
    # Build page number text
    page_num_text = page_num_format.format(
        n=current_page,
        total=total_pages
    )
    
    # Define zones (page numbers take priority)
    zones = {'left': None, 'center': None, 'right': None}
    zones[page_num_position] = page_num_text
    
    # Add custom text to remaining zones
    if zones['left'] is None:
        zones['left'] = footer_config.get('text_left')
    if zones['center'] is None:
        zones['center'] = footer_config.get('text_center')
    if zones['right'] is None:
        zones['right'] = footer_config.get('text_right')
    
    # Draw each zone
    if zones['left']:
        canvas.drawString(0.75 * inch, footer_y, str(zones['left']))
    if zones['center']:
        canvas.drawCentredString(page_width / 2.0, footer_y, str(zones['center']))
    if zones['right']:
        canvas.drawRightString(page_width - 0.75 * inch, footer_y, str(zones['right']))
    
    # Optional separator line above footer
    if footer_config.get('draw_line', False):
        line_color = footer_config.get('line_color', '#CCCCCC')
        canvas.setStrokeColor(colors.HexColor(line_color))
        canvas.setLineWidth(0.5)
        canvas.line(
            0.75 * inch,
            footer_y + 0.2 * inch,
            page_width - 0.75 * inch,
            footer_y + 0.2 * inch
        )
    
    canvas.restoreState()


def draw_header(canvas, doc, header_config):
    """Draw header with optional logo and text"""
    canvas.saveState()
    
    page_width = letter[0]
    page_height = letter[1]
    header_height = header_config.get('height', 0.75) * inch
    header_y = page_height - 0.5 * inch
    
    font_size = header_config.get('font_size', 10)
    text_color = header_config.get('text_color', '#333333')
    
    # Draw logo if provided
    logo_path = header_config.get('logo_path')
    if logo_path and os.path.exists(logo_path):
        logo_width = header_config.get('logo_width', 1.0) * inch
        logo_height = header_config.get('logo_height', 0.4) * inch
        logo_position = header_config.get('logo_position', 'left')
        
        # Calculate logo X position
        if logo_position == 'left':
            logo_x = 0.75 * inch
        elif logo_position == 'center':
            logo_x = (page_width - logo_width) / 2.0
        else:  # right
            logo_x = page_width - 0.75 * inch - logo_width
        
        logo_y = header_y - logo_height
        
        try:
            canvas.drawImage(logo_path, logo_x, logo_y, 
                           width=logo_width, height=logo_height, 
                           preserveAspectRatio=True, mask='auto')
        except Exception as e:
            print(f"⚠️ Warning: Could not load logo '{logo_path}': {e}")
    
    # Draw header text if provided
    header_text = header_config.get('text')
    if header_text:
        text_position = header_config.get('text_position', 'right')
        canvas.setFont("Helvetica", font_size)
        canvas.setFillColor(colors.HexColor(text_color))
        
        text_y = header_y - 0.3 * inch
        
        if text_position == 'left':
            canvas.drawString(0.75 * inch, text_y, str(header_text))
        elif text_position == 'center':
            canvas.drawCentredString(page_width / 2.0, text_y, str(header_text))
        else:  # right
            canvas.drawRightString(page_width - 0.75 * inch, text_y, str(header_text))
    
    # Optional separator line below header
    if header_config.get('draw_line', True):
        line_color = header_config.get('line_color', '#CCCCCC')
        canvas.setStrokeColor(colors.HexColor(line_color))
        canvas.setLineWidth(0.5)
        line_y = header_y - header_height + 0.2 * inch
        canvas.line(
            0.75 * inch,
            line_y,
            page_width - 0.75 * inch,
            line_y
        )
    
    canvas.restoreState()


def create_header_footer_callback(header_config, footer_config, background_drawing=None):
    """
    Factory function to create onPage callback for headers/footers
    
    Args:
        header_config: Header configuration dict
        footer_config: Footer configuration dict
        background_drawing: Optional ReportLab Drawing object (from load_and_scale_svg)
    """
    def on_page(canvas, doc):
        """Called for each page - draws background, header and footer"""
        canvas.saveState()
        
        # *** DRAW BACKGROUND FIRST (if provided) ***
        if background_drawing:
            # Center the drawing on page
            from reportlab.graphics import renderPDF
            x = (letter[0] - background_drawing.width) / 2
            y = (letter[1] - background_drawing.height) / 2
            renderPDF.draw(background_drawing, canvas, x, y)
        
        # Draw header if configured
        if header_config:
            draw_header(canvas, doc, header_config)
        
        # Draw footer (always present with at least page numbers)
        if footer_config:
            draw_footer(canvas, doc, footer_config)
        
        canvas.restoreState()
    
    return on_page


class ConditionalPageBreak(Flowable):
    """
    A flowable that forces a page break only if remaining space is below threshold.
    Checks available height at render time (during wrap), not at story-building time.
    """
    
    def __init__(self, threshold_inches=2.0):
        """
        Args:
            threshold_inches: Minimum space needed to continue on current page
        """
        Flowable.__init__(self)
        self.threshold = threshold_inches * inch
        self.width = 0
        self.height = 0
    
    def wrap(self, availWidth, availHeight):
        """
        Check available height and decide whether to force page break.
        
        This is called at render time, so availHeight is accurate.
        If availHeight < threshold, we return dimensions that exceed available space,
        forcing ReportLab to move to the next page.
        """
        if availHeight < self.threshold:
            # Force page break by requesting more height than available
            # This causes ReportLab to move this (and following content) to next page
            return (availWidth, availHeight + 1)
        else:
            # Don't force break - take no space
            return (0, 0)
    
    def draw(self):
        """Nothing to draw - this is just a conditional spacer"""
        pass


# ==================== BASIC RENDERING FUNCTIONS ====================

def render_pdf_title(story, section_config, styles, available_width, theme):
    """Render title section in PDF"""
    from reportlab.graphics.shapes import Drawing, Line

    title = section_config.get('title', '')
    subtitle = section_config.get('subtitle', '')

    if title:
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Title'],
            fontSize=18,
            textColor=colors.black,
            alignment=TA_CENTER,
            spaceAfter=6
        )
        story.append(Paragraph(title, title_style))

    if subtitle:
        subtitle_style = ParagraphStyle(
            'CustomSubtitle',
            parent=styles['Normal'],
            fontSize=14,
            textColor=colors.HexColor(section_config.get('subtitle_color', theme['subtitle'])),
            alignment=TA_CENTER,
            spaceAfter=20
        )
        story.append(Paragraph(subtitle, subtitle_style))

    # Add separator line
    separator_color = section_config.get('separator_color', theme['separator'])
    d = Drawing(available_width, 1)
    line = Line(0, 0, available_width, 0)
    line.strokeColor = colors.HexColor(separator_color)
    line.strokeWidth = 2
    d.add(line)
    story.append(d)
    story.append(Spacer(1, 0.2*inch))

def render_pdf_text(story, section_config, styles, theme):
    """Render text section in PDF"""
    content = section_config.get('content', '')
    if not content:
        return

    title = section_config.get('title')
    if title:
        section_title_style = ParagraphStyle(
            'SectionTitle',
            parent=styles['Heading2'],
            fontSize=14,
            spaceAfter=10
        )
        story.append(Paragraph(title, section_title_style))

    subtitle = section_config.get('subtitle')
    if subtitle:
        subtitle_style = ParagraphStyle(
            'SectionSubtitle',
            parent=styles['Normal'],
            fontSize=12,
            textColor=colors.HexColor(theme['section_subtitle']),
            fontName='Helvetica-Oblique',
            spaceAfter=10
        )
        story.append(Paragraph(subtitle, subtitle_style))

    style_name = section_config.get('style', 'normal')
    font_name = 'Helvetica'
    if style_name == 'bold':
        font_name = 'Helvetica-Bold'
    elif style_name == 'italic':
        font_name = 'Helvetica-Oblique'

    alignment = TA_CENTER if section_config.get('alignment') == 'center' else 0
    font_size = section_config.get('font_size', 11)

    para_style = ParagraphStyle(
        'CustomPara',
        parent=styles['Normal'],
        fontSize=font_size,
        fontName=font_name,
        alignment=alignment
    )

    story.append(Paragraph(content, para_style))
    story.append(Spacer(1, 0.2*inch))

def render_pdf_image(story, section_config, available_width, theme):
    """Render image section in PDF"""
    from reportlab.platypus import Image, KeepTogether, PageBreak
    from PIL import Image as PILImage

    image_path = section_config.get('image_path', '')
    if not image_path or not os.path.exists(image_path):
        return

    # Check if we should force page break before title
    # (prevents orphaned titles at bottom of page)
    title = section_config.get('title')
    if title:
        story.append(ConditionalPageBreak(threshold_inches=2.0))

    # Collect all elements to keep together
    elements = []
    
    title = section_config.get('title')
    if title:
        elements.append(Paragraph(title, getSampleStyleSheet()['Heading2']))

    subtitle = section_config.get('subtitle')
    if subtitle:
        styles = getSampleStyleSheet()
        subtitle_style = ParagraphStyle(
            'SectionSubtitle',
            parent=styles['Normal'],
            fontSize=12,
            textColor=colors.HexColor(theme['section_subtitle']),
            fontName='Helvetica-Oblique',
            spaceAfter=10
        )
        elements.append(Paragraph(subtitle, subtitle_style))

    caption = section_config.get('caption')
    if caption:
        styles = getSampleStyleSheet()
        caption_style = ParagraphStyle(
            'Caption',
            parent=styles['Normal'],
            fontSize=10,
            fontName='Helvetica-Oblique'
        )
        elements.append(Paragraph(caption, caption_style))

    width_inches = section_config.get('width', 6)
    target_width = width_inches * inch
    
    # Calculate height based on image aspect ratio
    with PILImage.open(image_path) as img:
        img_width, img_height = img.size
        aspect_ratio = img_height / img_width
        target_height = target_width * aspect_ratio
    
    elements.append(Image(image_path, width=target_width, height=target_height))
    
    # Wrap title + image together to prevent orphaning
    # Falls back to splitting if content exceeds page height
    story.append(KeepTogether(elements))
    story.append(Spacer(1, 0.2*inch))

print("✅ C04: Header/footer functions loaded (BaseDocTemplate ready)")


def render_pdf_table(story, section_config, available_width, styles, theme):
    """Render table section in PDF"""
    from reportlab.platypus import PageBreak
    from reportlab.lib import colors as rl_colors
    
    df = section_config['df']
    if len(df) == 0:
        return

    df_work = df.copy()

    if section_config.get('clean_empty_cols'):
        df_work = df_work.dropna(axis=1, how='all')
        df_work = df_work.loc[:, (df_work != '').any(axis=0)]

    if section_config.get('clean_empty_rows'):
        df_work = df_work.dropna(axis=0, how='all')
        df_work = df_work[(df_work.astype(str) != '').any(axis=1)]

    if 'drop_columns' in section_config:
        drop_cols = section_config['drop_columns']
        df_work = df_work.drop(columns=[c for c in drop_cols if c in df_work.columns])

    if len(df_work) == 0:
        return

    df_work = prepare_dataframe(df_work)

    title = section_config.get('title', '')
    
    # Check if we should force page break before title (prevents orphaning)
    if title:
        story.append(ConditionalPageBreak(threshold_inches=2.0))
    if 'title_suffix_from_column' in section_config:
        col = section_config['title_suffix_from_column']
        if col in df.columns:
            val = df[col].iloc[0]
            title = f"{title} ({val})"

    if title:
        section_title_style = ParagraphStyle(
            'SectionTitle',
            parent=styles['Heading2'],
            fontSize=14,
            spaceAfter=10,
            keepWithNext=True  # Keep title with next element (table)
        )
        story.append(Paragraph(title, section_title_style))

    subtitle = section_config.get('subtitle')
    if subtitle:
        subtitle_style = ParagraphStyle(
            'SectionSubtitle',
            parent=styles['Normal'],
            fontSize=12,
            textColor=colors.HexColor(theme['section_subtitle']),
            fontName='Helvetica-Oblique',
            spaceAfter=10,
            keepWithNext=True  # Keep subtitle with next element (table)
        )
        story.append(Paragraph(subtitle, subtitle_style))

    section_colors = section_config.get('colors', theme)

    # Evaluate formatting rules if provided
    formatting_rules = section_config.get('formatting_rules', [])
    style_map = evaluate_formatting_rules(df_work, formatting_rules)

    # Get column and cell format specifications (Phase 5.1)
    column_formats = section_config.get('column_formats', {})
    cell_formats = section_config.get('cell_formats', {})

    # Display warnings if any
    if style_map.get('warnings'):
        print("⚠️  Formatting warnings:")
        for warning in style_map['warnings']:
            print(f"   • {warning}")

    # Create paragraph style for table cells (enables text wrapping)
    cell_style = ParagraphStyle(
        'TableCell',
        parent=styles['Normal'],
        fontSize=10,
        leading=12
    )

    cell_style_bold = ParagraphStyle(
        'TableCellBold',
        parent=styles['Normal'],
        fontSize=10,
        leading=12,
        fontName='Helvetica-Bold'
    )

    header_style = ParagraphStyle(
        'TableHeader',
        parent=styles['Normal'],
        fontSize=11,
        fontName='Helvetica-Bold',
        leading=13
    )

    # Wrap all cell content in Paragraphs for auto-wrapping
    table_data = [[Paragraph(str(col), header_style) for col in df_work.columns]]
    for row_idx, (_, row) in enumerate(df_work.iterrows()):
        # Check if entire row should be bold
        row_style = style_map['rows'].get(row_idx, {})
        use_bold = row_style.get('bold', False)

        row_cells = []
        for col_idx, value in enumerate(row):
            # Check for cell-specific styling
            cell_key = (row_idx + 1, col_idx)  # +1 for header row
            cell_specific_style = style_map['cells'].get(cell_key, {})

            # Get format specification (Phase 5.1)
            # Priority: cell_formats > column_formats
            format_spec = cell_formats.get(cell_key)
            if not format_spec:
                col_name = df_work.columns[col_idx]
                format_spec = column_formats.get(col_name)

            # Format the value
            formatted_value = format_value(value, format_spec)

            # Determine which base style to use
            if use_bold or cell_specific_style.get('bold', False):
                base_style = cell_style_bold
            else:
                base_style = cell_style

            # Text color not supported per documentation - only bg_color and bold
            row_cells.append(Paragraph(formatted_value, base_style))

        table_data.append(row_cells)

    col_widths = None
    if 'column_widths' in section_config:
        widths = section_config['column_widths']
        if len(widths) == len(df_work.columns) and abs(sum(widths) - 1.0) < 0.01:
            col_widths = [w * available_width for w in widths]

    if col_widths is None:
        col_widths = [available_width / len(df_work.columns)] * len(df_work.columns)

    table = Table(table_data, colWidths=col_widths, repeatRows=1)

    style_list = [
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor(section_colors['header_bg'])),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor(section_colors['header_text'])),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONT SIZE', (0, 1), (-1, -1), 11),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('WORDWRAP', (0, 0), (-1, -1), True),
    ]

    # Apply alternating row colors to all rows
    for i in range(1, len(table_data)):
        if i % 2 == 0:
            style_list.append(('BACKGROUND', (0, i), (-1, i), colors.HexColor(section_colors['row_alt'])))

    # Apply row-level formatting (overrides alternating colors)
    for row_idx, row_style in style_map['rows'].items():
        actual_row = row_idx + 1  # +1 for header
        if 'bg_color' in row_style:
            style_list.append(('BACKGROUND', (0, actual_row), (-1, actual_row), colors.HexColor(row_style['bg_color'])))

    # Apply cell-level formatting (no text color support per documentation)
    for (row_idx, col_idx), cell_style_data in style_map['cells'].items():
        if 'bg_color' in cell_style_data:
            style_list.append(('BACKGROUND', (col_idx, row_idx), (col_idx, row_idx), colors.HexColor(cell_style_data['bg_color'])))

    table.setStyle(TableStyle(style_list))

    # Add table normally (can break across pages naturally)
    # keepWithNext on title/subtitle ensures they stay with table start
    story.append(table)
    story.append(Spacer(1, 0.3*inch))

def render_pdf_table_grouped(story, section_config, available_width, styles, theme):
    """Render grouped tables to PDF using regular table rendering for each group"""
    from reportlab.platypus import KeepTogether, PageBreak
    
    df = section_config['df']
    groupby_col = section_config['groupby']
    
    # Return early if empty
    if df.empty or groupby_col not in df.columns:
        return
    
    # Get category order if provided, else use natural order
    category_order = section_config.get('category_order', sorted(df[groupby_col].unique()))
    drop_columns = section_config.get('drop_columns', [])
    
    section_colors = section_config.get('colors', theme)
    
    # Extract formatting configs (Phase 5.2 - pass through to regular table)
    formatting_rules = section_config.get('formatting_rules', [])
    column_formats = section_config.get('column_formats', {})
    cell_formats = section_config.get('cell_formats', {})
    
    # Render section-level title if provided
    section_title = section_config.get('title')
    section_subtitle = section_config.get('subtitle')
    
    # Check if we should force page break before section title (prevents orphaning)
    if section_title:
        story.append(ConditionalPageBreak(threshold_inches=2.0))
    
    group_elements = []
    
    if section_title:
        title_style = ParagraphStyle(
            'GroupedTableTitle',
            parent=styles['Heading2'],
            fontSize=14,
            spaceAfter=10,
            keepWithNext=True
        )
        group_elements.append(Paragraph(section_title, title_style))
    
    if section_subtitle:
        subtitle_style = ParagraphStyle(
            'GroupedTableSubtitle',
            parent=styles['Normal'],
            fontSize=12,
            textColor=colors.HexColor(theme['section_subtitle']),
            fontName='Helvetica-Oblique',
            spaceAfter=10,
            keepWithNext=True
        )
        group_elements.append(Paragraph(section_subtitle, subtitle_style))
    
    # Create section title style for group headers
    category_header_style = ParagraphStyle(
        'CategoryHeader',
        parent=styles['Heading2'],
        fontSize=12,
        textColor=colors.HexColor('#333333'),
        spaceAfter=6,
        keepWithNext=True
    )
    
    # Process each category
    first_group = True
    for category in category_order:
        category_df = df[df[groupby_col] == category].copy()
        
        # Skip if empty
        if category_df.empty:
            continue
        
        # Clean columns
        if drop_columns:
            category_df = category_df.drop(columns=[col for col in drop_columns if col in category_df.columns])
        
        # Apply clean options from config
        if section_config.get('clean_empty_cols', False):
            category_df = category_df.dropna(axis=1, how='all')
        if section_config.get('clean_empty_rows', False):
            category_df = category_df.dropna(axis=0, how='all')
        
        # Skip if nothing left
        if category_df.empty:
            continue
        
        # Collect current group elements
        current_group_elements = []
        
        # Check if we should force page break before category header (prevents orphaning)
        if not first_group:
            current_group_elements.append(ConditionalPageBreak(threshold_inches=2.0))
        
        current_group_elements.append(Paragraph(str(category), category_header_style))
        current_group_elements.append(Spacer(1, 6))
        
        # Create a temporary story to capture table output
        temp_story = []
        
        # Create a sub-section config for this group and call regular table renderer
        group_section_config = {
            'df': category_df,
            'colors': section_colors,
            'formatting_rules': formatting_rules,
            'column_formats': column_formats,
            'cell_formats': cell_formats
        }
        
        # Only add column_widths if explicitly provided
        if 'column_widths' in section_config and section_config['column_widths'] is not None:
            group_section_config['column_widths'] = section_config['column_widths']
        
        # Call regular table renderer
        render_pdf_table(temp_story, group_section_config, available_width, styles, theme)
        current_group_elements.extend(temp_story)
        
        # For first group, add to group_elements to keep with section title
        if first_group:
            group_elements.extend(current_group_elements)
            first_group = False
        else:
            # Subsequent groups: add naturally, keepWithNext on headers prevents orphaning
            if group_elements:
                story.extend(group_elements)
                group_elements = []
            story.extend(current_group_elements)
    
    # Add final group naturally
    if group_elements:
        story.extend(group_elements)


def _generate_pdf_report(report_sections, output_filename, theme, 
                         header_config=None, footer_config=None, background_svg=None):
    """
    Generate PDF report with optional headers, footers, and SVG background
    
    Args:
        background_svg: Optional path to SVG file for page background
    """
    
    # *** LOAD BACKGROUND ONCE (before creating doc) ***
    background_drawing = None
    if background_svg:
        background_drawing = load_and_scale_svg(background_svg)
        if not background_drawing:
            print(f"⚠️ Warning: Could not load background SVG: {background_svg}")
    
    # Ensure footer always exists (mandatory page numbers)
    if footer_config is None:
        footer_config = {
            'page_numbers': {'position': 'center', 'format': 'Page {n} of {total}'},
            'height': 0.5,
            'draw_line': False
        }
    else:
        # Ensure page_numbers config exists
        if 'page_numbers' not in footer_config:
            footer_config['page_numbers'] = {'position': 'center', 'format': 'Page {n} of {total}'}
        # Set default height if not specified
        if 'height' not in footer_config:
            has_custom_text = (footer_config.get('text_left') or 
                             footer_config.get('text_center') or 
                             footer_config.get('text_right'))
            footer_config['height'] = 0.75 if has_custom_text else 0.5
    
    # Calculate margins based on header/footer presence
    top_margin = 0.75 * inch
    bottom_margin = 0.75 * inch
    
    if header_config:
        header_height = header_config.get('height', 0.75)
        top_margin = (0.5 + header_height) * inch
    
    footer_height = footer_config.get('height', 0.5)
    bottom_margin = (0.5 + footer_height) * inch
    
    # STEP 1: Build document WITHOUT header/footer to count pages
    doc_temp = BaseDocTemplate(
        output_filename,
        pagesize=letter,
        topMargin=top_margin,
        bottomMargin=bottom_margin,
        leftMargin=0.75*inch,
        rightMargin=0.75*inch
    )
    
    frame_temp = Frame(
        x1=0.75*inch,
        y1=bottom_margin,
        width=letter[0] - 1.5*inch,
        height=letter[1] - top_margin - bottom_margin,
        id='normal'
    )
    
    template_temp = PageTemplate(id='temp', frames=[frame_temp])
    doc_temp.addPageTemplates([template_temp])
    
    # Build story
    story = []
    available_width = letter[0] - 1.5*inch
    styles = getSampleStyleSheet()

    for section in report_sections:
        section_type = section['type']

        if section_type == 'title':
            render_pdf_title(story, section, styles, available_width, theme)
        elif section_type == 'text':
            render_pdf_text(story, section, styles, theme)
        elif section_type == 'image':
            render_pdf_image(story, section, available_width, theme)
        elif section_type == 'table':
            render_pdf_table(story, section, available_width, styles, theme)
        elif section_type == 'table_grouped':
            render_pdf_table_grouped(story, section, available_width, styles, theme)
    
    # Build temp to count pages
    doc_temp.build(story)
    total_page_count = doc_temp.page
    
    # STEP 2: Rebuild WITH header/footer using correct total
    # Create callback with correct total (including background)
    def later_pages_callback(canvas, doc):
        """Called on each page - draws background, header/footer with correct total"""
        canvas.saveState()
        
        # Inject total page count into doc for footer to use
        doc._total_page_count = total_page_count
        
        # *** DRAW BACKGROUND FIRST (if provided) ***
        if background_drawing:
            x = (letter[0] - background_drawing.width) / 2
            y = (letter[1] - background_drawing.height) / 2
            renderPDF.draw(background_drawing, canvas, x, y)
        
        # Draw header if configured
        if header_config:
            draw_header(canvas, doc, header_config)
        
        # Draw footer
        if footer_config:
            draw_footer(canvas, doc, footer_config)
        
        canvas.restoreState()
    
    # Create new document for final build
    doc_final = BaseDocTemplate(
        output_filename,
        pagesize=letter,
        topMargin=top_margin,
        bottomMargin=bottom_margin,
        leftMargin=0.75*inch,
        rightMargin=0.75*inch
    )
    
    frame_final = Frame(
        x1=0.75*inch,
        y1=bottom_margin,
        width=letter[0] - 1.5*inch,
        height=letter[1] - top_margin - bottom_margin,
        id='normal'
    )
    
    template_final = PageTemplate(
        id='main',
        frames=[frame_final],
        onPage=later_pages_callback
    )
    
    doc_final.addPageTemplates([template_final])
    
    # Rebuild the same story with header/footer
    story = []
    for section in report_sections:
        section_type = section['type']

        if section_type == 'title':
            render_pdf_title(story, section, styles, available_width, theme)
        elif section_type == 'text':
            render_pdf_text(story, section, styles, theme)
        elif section_type == 'image':
            render_pdf_image(story, section, available_width, theme)
        elif section_type == 'table':
            render_pdf_table(story, section, available_width, styles, theme)
        elif section_type == 'table_grouped':
            render_pdf_table_grouped(story, section, available_width, styles, theme)
    
    # Final build with header/footer
    doc_final.build(story)
    
    return output_filename


# ==================== GENERIC REPORT GENERATOR ====================

def generate_report(report_sections, format='pdf', output_filename='report.pdf',
                    colors=None, header_config=None, footer_config=None, background_svg=None):
    """
    TRULY GENERIC report generator - works for any report type
    """
    # Use provided colors or default to report_colors
    theme = colors if colors is not None else report_colors

    # Ensure extension matches format
    ext = 'pdf' if format == 'pdf' else 'docx'
    if not output_filename.endswith(f'.{ext}'):
        output_filename = f'{output_filename}.{ext}'

    if format == 'pdf':
        return _generate_pdf_report(
            report_sections, output_filename, theme,
            header_config, footer_config, background_svg
        )
    elif format == 'docx':
        # ✅ Lazy import to avoid circular imports
        from .docx import _generate_docx_report
        return _generate_docx_report(report_sections, output_filename, theme)
    else:
        raise ValueError("format must be 'pdf' or 'docx'")