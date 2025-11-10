# src/yourpkg/__init__.py

# Re-export only the public entry points you want callers to use.
# Keep this file light to avoid circular imports and heavy import time.

from .pdf import generate_report  # unified entry point that handles format='pdf' or 'docx'

# (Optional) also expose the format-specific builders if you want:
from .pdf import _generate_pdf_report as generate_pdf_report  # optional public alias
from .docx import _generate_docx_report as generate_docx_report  # optional public alias

# (Optional) expose theme tokens for customization:
from .theme import report_colors

__all__ = [
    "generate_report",
    "generate_pdf_report",
    "generate_docx_report",
    "report_colors",
]
