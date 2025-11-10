def test_imports():
    import reportlabcustom
    from reportlabcustom import generate_report, report_colors
    from reportlabcustom.pdf import _generate_pdf_report
    from reportlabcustom.docx import _generate_docx_report
    assert callable(generate_report)
    assert isinstance(report_colors, dict)
