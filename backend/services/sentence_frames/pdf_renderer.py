"""PDF conversion for sentence frame HTML."""

from pathlib import Path

from backend.telemetry import logger


def convert_to_pdf(html_path: str, pdf_path: str, css_template: str) -> str:
    """Convert HTML file to PDF using WeasyPrint with Playwright fallback."""
    html_file = Path(html_path)
    pdf_file = Path(pdf_path)
    pdf_file.parent.mkdir(parents=True, exist_ok=True)
    if pdf_file.exists():
        try:
            pdf_file.unlink()
        except OSError:
            pass

    try:
        import weasyprint

        weasyprint.HTML(filename=str(html_file)).write_pdf(
            str(pdf_file), stylesheets=[weasyprint.CSS(string=css_template)]
        )
        logger.info(
            "sentence_frames_weasyprint_pdf_generated",
            extra={"html_path": str(html_file), "pdf_path": str(pdf_file)},
        )
        return str(pdf_file)
    except Exception as exc:
        logger.warning(
            "sentence_frames_weasyprint_failed",
            extra={
                "html_path": str(html_file),
                "pdf_path": str(pdf_file),
                "error": str(exc),
            },
        )

    try:
        from playwright.sync_api import sync_playwright
    except ImportError as exc:
        logger.error(
            "sentence_frames_playwright_not_installed", extra={"error": str(exc)}
        )
        raise

    with sync_playwright() as p:  # type: ignore[name-defined]
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto(f"file:///{html_file}", wait_until="networkidle")
        page.pdf(
            path=str(pdf_file),
            format="Letter",
            landscape=False,
            print_background=True,
            prefer_css_page_size=True,
            margin={
                "top": "0",
                "right": "0",
                "bottom": "0",
                "left": "0",
            },
        )
        browser.close()

    logger.info(
        "sentence_frames_playwright_pdf_generated",
        extra={"html_path": str(html_file), "pdf_path": str(pdf_file)},
    )
    return str(pdf_file)
