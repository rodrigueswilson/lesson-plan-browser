import argparse
import sys
import os
import re
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))
import datetime
import json
from typing import Any, Callable, Dict, List, Set, cast
import requests # type: ignore
import google.auth # type: ignore
from tools.scraper.docs_client import DocsClient # type: ignore
from tools.scraper.crawler import CurriculumCrawler # type: ignore
from tools.scraper.pdf_processor import PDFProcessor # type: ignore
from tools.scraper.html_processor import HTMLProcessor # type: ignore
from tools.scraper.slides_processor import SlidesProcessor # type: ignore
from tools.scraper.ocr_processor import OCRProcessor # type: ignore
from tools.scraper.ingestion import IngestionService # type: ignore
from tools.scraper.docs_processor import GoogleDocsProcessor # type: ignore
from tools.scraper.gdoc_docx_export import export_docx_full_or_tab_fallback # type: ignore

# Global logger setup
log_file = None

def setup_logging(out_dir):
    global log_file
    os.makedirs(out_dir, exist_ok=True)
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    log_name = f"scraped_{timestamp}.log"
    log_path = os.path.join(out_dir, log_name)
    log_file = open(log_path, 'a', encoding='utf-8')
    return log_path

def log(message, level="INFO"):
    global log_file
    timestamp = datetime.datetime.now().strftime("%H:%M:%S")
    msg = f"[{timestamp}] [{level}] {message}"
    print(msg)
    if log_file:
        log_file.write(msg + "\n")
        log_file.flush()

def sanitize_name(name: str) -> str:
    """Creates a filesystem-safe version of a string."""
    return "".join([c if c.isalnum() else "_" for c in name]).strip("_")

def extract_nested_keys(d):
    keys = set()
    if isinstance(d, dict):
        for k, v in d.items():
            if isinstance(v, str):
                keys.add(k)
            else:
                keys.update(extract_nested_keys(v))
    return keys

def load_registry(filepath: str) -> set:
    if os.path.exists(filepath):
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if "scraped_ids" in data and isinstance(data["scraped_ids"], list):
                    return set(data["scraped_ids"])
                return extract_nested_keys(data)
        except Exception as e:
            log(f"Error loading registry: {e}", "WARNING")
    return set()

def save_registry_hierarchical(filepath: str, doc_id: str, title: str, parent_dir: str):
    try:
        from tools.scraper.organizer import guess_grade_and_subject, parse_unit_name
        grade, subject = guess_grade_and_subject(title, parent_dir)
        unit_name = parse_unit_name(title, os.path.basename(parent_dir))
        
        # Fallback naming cleanup
        if unit_name == os.path.basename(parent_dir) and not title.lower().startswith("unit"):
            safe_title = "".join([c if c.isalnum() or c in " _-" else "" for c in title]).strip()
            unit_name = safe_title.replace(" ", "_").strip("_")
            
        data = {}
        if os.path.exists(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                try: data = json.load(f)
                except: pass
                
        # Clean up old structure if it somehow still exists
        if "scraped_ids" in data:
            del data["scraped_ids"]
            
        if grade not in data: data[grade] = {}
        if subject not in data[grade]: data[grade][subject] = {}
        if unit_name not in data[grade][subject]: data[grade][subject][unit_name] = {}
        
        data[grade][subject][unit_name][doc_id] = title
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        log(f"Error saving registry hierarchically: {e}", "WARNING")
        
def get_cached_asset(asset_name: str, target_path: str) -> bool:
    import shutil
    cache_dir = "reference_docs/.asset_cache"
    cache_path = os.path.join(cache_dir, asset_name)
    if os.path.exists(cache_path) and os.path.getsize(cache_path) > 0:
        os.makedirs(os.path.dirname(target_path), exist_ok=True)
        shutil.copy2(cache_path, target_path)
        return True
    return False

def cache_asset(asset_name: str, source_path: str):
    import shutil
    cache_dir = "reference_docs/.asset_cache"
    os.makedirs(cache_dir, exist_ok=True)
    cache_path = os.path.join(cache_dir, asset_name)
    if os.path.exists(source_path) and os.path.getsize(source_path) > 0:
        shutil.copy2(source_path, cache_path)


def _tab_links_nonempty(links: Dict[str, Any]) -> bool:
    return bool(links) and any(links.get(k) for k in ("doc", "pdf", "slides", "pptx", "html"))


def process_tab_linked_resources(
    links: Dict[str, Any],
    res_rel_dir: str,
    abs_res_dir: str,
    abs_originals_dir: str,
    recurse_linked_doc: Callable[[str], None],
    client: Any,
    crawler: CurriculumCrawler,
    pdf_proc: PDFProcessor,
    html_proc: HTMLProcessor,
    slides_proc: SlidesProcessor,
    ocr_proc: OCRProcessor,
    ingestion: IngestionService,
    log_depth: int,
) -> None:
    """Downloads linked Google Docs (via recurse), PDFs, Slides, PPTX, and HTML for one tab."""
    if not _tab_links_nonempty(links):
        return
    os.makedirs(abs_res_dir, exist_ok=True)
    os.makedirs(abs_originals_dir, exist_ok=True)
    li = "  " * log_depth

    for linked_id in links.get("doc", []):
        recurse_linked_doc(linked_id)

    for pdf_url in links.get("pdf", []):
        try:
            drive_match = re.search(crawler.DRIVE_FILE_REGEX, pdf_url)
            raw_pdf_name = str(pdf_url).split("/")[-1]
            file_id = str(drive_match.group(1)) if drive_match else sanitize_name(cast(str, raw_pdf_name)[:50])  # type: ignore
            orig_pdf = os.path.join(abs_originals_dir, f"PDF_{file_id}.pdf")

            if os.path.exists(orig_pdf) and os.path.getsize(orig_pdf) > 0:
                log(f"{li}Skipping existing PDF: {file_id}")
                continue
            if not get_cached_asset(f"PDF_{file_id}.pdf", orig_pdf):
                if drive_match:
                    log(f"{li}Downloading Drive PDF: {file_id}")
                    client.download_drive_file(file_id, orig_pdf)
                else:
                    display_url = cast(str, pdf_url)[:40]  # type: ignore
                    log(f"{li}Downloading Web PDF: {display_url}...")
                    resp = requests.get(pdf_url, timeout=15)
                    resp.raise_for_status()
                    with open(orig_pdf, "wb") as f:
                        f.write(resp.content)
                cache_asset(f"PDF_{file_id}.pdf", orig_pdf)
            else:
                log(f"{li}Copied cached PDF: {file_id}")

            pdf_text = str(pdf_proc.extract_text(orig_pdf))
            file_id_short = cast(str, file_id)[:8]  # type: ignore
            save_path = str(os.path.join(res_rel_dir, f"PDF_{file_id_short}"))
            ingestion.save_as_markdown(
                save_path,
                pdf_text,
                {"source": pdf_url, "type": "pdf"},
            )
        except Exception as e:
            log(f"{li}  Error processing PDF {pdf_url}: {e}", "ERROR")

    for slide_id in links.get("slides", []):
        try:
            slide_id_str = str(slide_id)
            log(f"{li}Processing Google Slides: {slide_id_str}")
            presentation = client.get_presentation(slide_id_str)
            res = slides_proc.process_google_slides(presentation)
            slides_md = res["markdown"]

            for obj_id, uri in res["images"].items():
                try:
                    img_path = os.path.join(abs_originals_dir, f"SLIDE_IMG_{obj_id}.png")
                    if not os.path.exists(img_path):
                        if not get_cached_asset(f"SLIDE_IMG_{obj_id}.png", img_path):
                            resp = requests.get(uri, timeout=10)
                            resp.raise_for_status()
                            with open(img_path, "wb") as f:
                                f.write(resp.content)
                            cache_asset(f"SLIDE_IMG_{obj_id}.png", img_path)
                        else:
                            log(f"{li}  Copied cached Slide image: {obj_id}")

                    ocr_text = ocr_proc.process_file(img_path)
                    if ocr_text:
                        slides_md = str(slides_md).replace(
                            f"[IMAGE:{obj_id}]",
                            f"\n> **[Slide Image OCR]**\n> {ocr_text.replace(chr(10), chr(10) + '> ')}\n",
                        )
                except Exception as img_e:
                    log(f"{li}  Slide image error {obj_id}: {img_e}", "WARNING")

            slide_id_short = cast(str, slide_id_str)[:8]  # type: ignore
            save_path_slides = str(os.path.join(res_rel_dir, f"Slides_{slide_id_short}"))
            ingestion.save_as_markdown(
                save_path_slides,
                slides_md,
                {"source": slide_id, "type": "google_slides"},
            )
        except Exception as e:
            log(f"{li}  Error processing Slides {slide_id}: {e}", "ERROR")

    for pptx_url in links.get("pptx", []):
        try:
            drive_match = re.search(crawler.DRIVE_FILE_REGEX, pptx_url)
            raw_pptx_name = str(pptx_url).split("/")[-1]
            file_id = str(drive_match.group(1)) if drive_match else sanitize_name(cast(str, raw_pptx_name)[:50])  # type: ignore
            orig_pptx = os.path.join(abs_originals_dir, f"PPTX_{file_id}.pptx")

            if not os.path.exists(orig_pptx):
                if not get_cached_asset(f"PPTX_{file_id}.pptx", orig_pptx):
                    if drive_match:
                        log(f"{li}Downloading Drive PPTX: {file_id}")
                        client.download_drive_file(file_id, orig_pptx)
                    else:
                        display_pptx_url = cast(str, pptx_url)[:40]  # type: ignore
                        log(f"{li}Downloading Web PPTX: {display_pptx_url}...")
                        resp = requests.get(pptx_url, timeout=15)
                        resp.raise_for_status()
                        with open(orig_pptx, "wb") as f:
                            f.write(resp.content)
                    cache_asset(f"PPTX_{file_id}.pptx", orig_pptx)
                else:
                    log(f"{li}Copied cached PPTX: {file_id}")
            else:
                log(f"{li}Skipping existing PPTX: {file_id}")

            res = slides_proc.process_pptx(orig_pptx)
            pptx_md = res["markdown"]
            for obj_id, shape in res["images"].items():
                try:
                    img_path = os.path.join(abs_originals_dir, f"PPTX_IMG_{obj_id}.png")
                    if not os.path.exists(img_path):
                        if not get_cached_asset(f"PPTX_IMG_{obj_id}.png", img_path):
                            with open(img_path, "wb") as f:
                                f.write(shape.image.blob)
                            cache_asset(f"PPTX_IMG_{obj_id}.png", img_path)
                        else:
                            log(f"{li}  Copied cached PPTX image: {obj_id}")
                    ocr_text = ocr_proc.process_file(img_path)
                    if ocr_text:
                        pptx_md = str(pptx_md).replace(
                            f"[IMAGE:{obj_id}]",
                            f"\n> **[PPTX Image OCR]**\n> {ocr_text.replace(chr(10), chr(10) + '> ')}\n",
                        )
                except Exception as img_e:
                    log(f"{li}  PPTX image error {obj_id}: {img_e}", "WARNING")

            file_id_pptx_short = cast(str, file_id)[:8]  # type: ignore
            save_path_pptx = str(os.path.join(res_rel_dir, f"PPTX_{file_id_pptx_short}"))
            ingestion.save_as_markdown(
                save_path_pptx,
                pptx_md,
                {"source": pptx_url, "type": "pptx"},
            )
        except Exception as e:
            log(f"{li}  Error processing PPTX {pptx_url}: {e}", "ERROR")

    for html_url in links.get("html", []):
        try:
            html_url_str = str(html_url)
            log(f"{li}Scraping HTML: {cast(str, html_url_str)[:30]}...")  # type: ignore
            html_text = html_proc.extract_content(html_url_str, google_client=client)
            safe_html_name = sanitize_name(cast(str, html_url_str)[:20])  # type: ignore
            ingestion.save_as_markdown(
                os.path.join(res_rel_dir, f"HTML_{safe_html_name}"),
                html_text,
                {"source": html_url, "type": "html"},
            )
        except Exception as e:
            log(f"{li}  Error processing HTML {html_url}: {e}", "ERROR")


def process_doc_recursive(
    doc_id,
    client,
    crawler,
    doc_proc,
    pdf_proc,
    html_proc,
    slides_proc,
    ocr_proc,
    ingestion,
    table_parser,
    parent_dir,
    output_root,
    depth,
    max_depth,
    visited_docs,
    target_unit=None,
    registry_path=None,
    force=False,
    user_id=None,
    entry_root_id=None,
    incremental_root=False,
):
    """Recursively processes a Google Doc and its discovered resources."""
    root_resync = bool(
        incremental_root
        and entry_root_id
        and doc_id == entry_root_id
        and doc_id in visited_docs
        and not force
    )

    if not force and doc_id in visited_docs and not root_resync:
        log(f"{'  ' * depth}Skipping already scraped Doc: {doc_id}")
        return

    # Mark as visited early to prevent circular loops within a single run
    visited_docs.add(doc_id)

    try:
        doc = client.get_document(doc_id)
        if not doc:
            return

        title = doc.get("title", doc_id)
        log(f"{'  ' * depth}Processing Doc: {title} ({doc_id})")
        safe_doc_title = sanitize_name(title)

        # Current doc root directory within the parent (relative to output_root)
        current_doc_dir = os.path.join(parent_dir, safe_doc_title)

        # Absolute path for creating directories
        abs_doc_dir = os.path.join(output_root, current_doc_dir)

        if root_resync:
            log(
                f"{'  ' * depth}Incremental root pass: following new links only "
                f"(skipping full export for this doc; registry unchanged).",
                "INFO",
            )
            doc_links_map = crawler._extract_links_from_doc(doc)
            for tab_title, links in doc_links_map.items():
                if target_unit and target_unit.lower() not in tab_title.lower():
                    continue
                if not _tab_links_nonempty(links):
                    continue
                log(f"{'  ' * (depth + 1)}Unit: {tab_title}")
                path_parts = [sanitize_name(p.strip()) for p in tab_title.split(" - ")]
                unit_rel_dir = os.path.join(current_doc_dir, *path_parts)
                res_rel_dir = os.path.join(unit_rel_dir, "resources")
                abs_res_dir = os.path.join(output_root, res_rel_dir)
                abs_originals_dir = os.path.join(abs_res_dir, "originals")

                def recurse_linked(lid: str) -> None:
                    process_doc_recursive(
                        lid,
                        client,
                        crawler,
                        doc_proc,
                        pdf_proc,
                        html_proc,
                        slides_proc,
                        ocr_proc,
                        ingestion,
                        table_parser,
                        unit_rel_dir,
                        output_root,
                        depth + 1,
                        max_depth,
                        visited_docs,
                        target_unit,
                        registry_path,
                        force=False,
                        user_id=user_id,
                        entry_root_id=entry_root_id,
                        incremental_root=incremental_root,
                    )

                process_tab_linked_resources(
                    links,
                    res_rel_dir,
                    abs_res_dir,
                    abs_originals_dir,
                    recurse_linked,
                    client,
                    crawler,
                    pdf_proc,
                    html_proc,
                    slides_proc,
                    ocr_proc,
                    ingestion,
                    depth + 2,
                )
            return

        # Processor returns tab titles -> {'markdown': ..., 'images': {id: uri}}
        tab_data_map = doc_proc.process(doc)

        # NEW: Export doc-wide high-fidelity assets (HTML, DOCX, JSON)
        # We do this once per Doc ID in the root of its folder
        doc_originals_dir = os.path.join(abs_doc_dir, "originals")
        os.makedirs(doc_originals_dir, exist_ok=True)
        log(f"{'  ' * depth}Exporting high-fidelity assets for: {title}")
        
        # 1. HTML Export (may fail on very large native Google Docs)
        html_path = os.path.join(doc_originals_dir, f"{safe_doc_title}.html")
        if not client.export_document(doc_id, html_path, "text/html"):
            log(f"{'  ' * depth}HTML export failed for: {title}", "WARNING")

        # 2. DOCX: Drive full export, or per-tab synthesis when exportSizeLimitExceeded
        export_result = export_docx_full_or_tab_fallback(
            client,
            doc_id,
            doc,
            doc_originals_dir,
            safe_doc_title,
            log_fn=lambda m: log(f"{'  ' * depth}{m}"),
        )

        # 3. Raw JSON (same payload as tab fallback; avoids a second documents.get)
        json_path = os.path.join(doc_originals_dir, f"{safe_doc_title}.json")
        with open(json_path, "w", encoding="utf-8") as jf:
            json.dump(doc, jf, ensure_ascii=False, indent=2)
        log(f"{'  ' * depth}Wrote API JSON: {json_path}")

        # NEW: Ingest single DOCX into original_lesson_plans (tab-split leaves multiple files; skip)
        if table_parser and user_id:
            try:
                docx_path = export_result.get("full_docx")
                if docx_path and os.path.isfile(docx_path) and os.path.getsize(docx_path) > 0:
                    week_of = "unknown"
                    date_match = re.search(r"(\d{1,2}-\d{1,2})", title)
                    if date_match:
                        week_of = date_match.group(1)

                    metadata = {
                        "user_id": user_id,
                        "week_of": week_of,
                        "slot_number": depth,
                        "subject": "Scraped",
                        "grade": "N/A",
                    }
                    log(f"{'  ' * depth}Ingesting DOCX to DB for: {title}")
                    table_parser.ingest_to_db(docx_path, metadata)
                elif export_result.get("mode") == "tabs":
                    log(
                        f"{'  ' * depth}ingest_to_db skipped: document exported as "
                        f"{len(export_result.get('tab_docx_paths') or [])} tab DOCX files under "
                        f"{export_result.get('tab_dir')}",
                        "WARNING",
                    )
            except Exception as e:
                log(f"{'  ' * depth}Database ingestion failed for {title}: {e}", "WARNING")

        # Get links found by the crawler for this specific doc
        doc_links_map = crawler._extract_links_from_doc(doc)

        for tab_title, data in tab_data_map.items():
            if target_unit and target_unit.lower() not in tab_title.lower():
                continue

            log(f"{'  ' * (depth+1)}Unit: {tab_title}")
            content = data.get('markdown', '')
            doc_images = data.get('images', {})
            
            # Use nested structure based on splits string
            path_parts = [sanitize_name(p.strip()) for p in tab_title.split(" - ")]
            unit_rel_dir = os.path.join(current_doc_dir, *path_parts)
            safe_tab_title = path_parts[-1]
            
            # Paths relative to output_root
            res_rel_dir = os.path.join(unit_rel_dir, "resources")
            
            # Absolute paths for saving originals
            abs_unit_dir = os.path.join(output_root, unit_rel_dir)
            abs_res_dir = os.path.join(output_root, res_rel_dir)
            abs_originals_dir = os.path.join(abs_res_dir, "originals")
            abs_img_dir = os.path.join(abs_res_dir, "images")

            # A. Process Inline Images for this tab (OCR & File Retention)
            if doc_images:
                os.makedirs(abs_img_dir, exist_ok=True)
                os.makedirs(abs_originals_dir, exist_ok=True)
                for obj_id, uri in doc_images.items():
                    try:
                        img_path = os.path.join(abs_originals_dir, f"IMG_{obj_id}.png")
                        
                        # Incremental check
                        if not os.path.exists(img_path):
                            if not get_cached_asset(f"IMG_{obj_id}.png", img_path):
                                log(f"    Downloading Image: {obj_id}")
                                r = requests.get(uri, timeout=10)
                                r.raise_for_status()
                                with open(img_path, 'wb') as f: f.write(r.content)
                                cache_asset(f"IMG_{obj_id}.png", img_path)
                            else:
                                log(f"    Copied cached image: {obj_id}")
                        else:
                            log(f"    Skipping existing image: {obj_id}")

                        # OCR processing
                        log(f"    OCR-ing Image: {obj_id}")
                        ocr_text = ocr_proc.process_file(img_path)
                        if ocr_text:
                            content = str(content).replace(f"[IMAGE:{obj_id}]", f"\n> **[Image OCR Text]**\n> {ocr_text.replace(chr(10), chr(10)+'> ')}\n")
                        else:
                            content = content.replace(f"[IMAGE:{obj_id}]", f"* [Image {obj_id} (No text detected)] *")
                    except Exception as e:
                        log(f"      Error OCR-ing Image {obj_id}: {e}", "WARNING")

            # B. Process Linked Resources for this tab (linked Docs respect scraped_registry.json;
            # PDFs/PPTX skip when originals already on disk).
            links = doc_links_map.get(tab_title, {})

            def recurse_linked(lid: str) -> None:
                process_doc_recursive(
                    lid,
                    client,
                    crawler,
                    doc_proc,
                    pdf_proc,
                    html_proc,
                    slides_proc,
                    ocr_proc,
                    ingestion,
                    table_parser,
                    unit_rel_dir,
                    output_root,
                    depth + 1,
                    max_depth,
                    visited_docs,
                    target_unit,
                    registry_path,
                    force=False,
                    user_id=user_id,
                    entry_root_id=entry_root_id,
                    incremental_root=incremental_root,
                )

            process_tab_linked_resources(
                links,
                res_rel_dir,
                abs_res_dir,
                abs_originals_dir,
                recurse_linked,
                client,
                crawler,
                pdf_proc,
                html_proc,
                slides_proc,
                ocr_proc,
                ingestion,
                depth + 2,
            )

            # C. Save the final Unit Markdown
            ingestion.save_as_markdown(
                os.path.join(unit_rel_dir, cast(str, safe_tab_title)), # type: ignore
                content,
                {"doc_title": title, "tab_title": tab_title, "type": "google_doc", "id": doc_id}
            )

        # Create localized index.md based on what's physically downloaded
        index_content = f"# {title} Index\n\n**Source ID**: {doc_id}\n\n## Contents\n\n"
        for t_title in tab_data_map.keys():
            path_parts = [sanitize_name(p.strip()) for p in t_title.split(" - ")]
            abs_t_dir = os.path.join(abs_doc_dir, *path_parts)
            safe_t_title = path_parts[-1]
            t_md_file = os.path.join(abs_t_dir, f"{safe_t_title}.md")
            
            if os.path.exists(t_md_file):
                t_rel_path = "/".join(path_parts) + f"/{safe_t_title}.md"
                indent = "  " * (len(path_parts) - 1)
                index_content += f"{indent}- [{t_title.split(' - ')[-1]}]({t_rel_path})\n"
        
        # Determine index placement: inside the doc folder if depth > 0 or if we have a title to work with
        index_dir = current_doc_dir if current_doc_dir else sanitize_name(title)
        ingestion.save_as_markdown(
            os.path.join(index_dir, "index"),
            index_content,
            {"title": title, "type": "index", "id": doc_id}
        )
        
        # Save to registry immediately after successfully processing this document
        if registry_path:
            save_registry_hierarchical(registry_path, doc_id, title, index_dir)

    except Exception as e:
        log(f"{'  ' * depth}Error processing {doc_id}: {e}", "ERROR")

def main():
    parser = argparse.ArgumentParser(description="Hierarchical Curriculum Scraper")
    parser.add_argument("root_id", help="Root Google Doc ID")
    parser.add_argument("--depth", type=int, default=1, help="Max recursion depth")
    parser.add_argument("--out", default="reference_docs/scraped", help="Output directory")
    parser.add_argument("--unit", type=str, default=None, help="Optional: Unit to download (e.g. 'Unit 6'). Also downloads sub-tabs.")
    parser.add_argument("--force", action="store_true", help="Force re-scraping even if ID is in registry")
    parser.add_argument(
        "--incremental-root",
        action="store_true",
        help=(
            "When the root doc ID is already in scraped_registry.json, fetch it once to follow "
            "links and download only missing resources (skip full root HTML/DOCX/JSON export and "
            "tab markdown). Linked Google Docs are still skipped if their IDs are in the registry; "
            "PDFs/PPTX skip when the original file already exists."
        ),
    )
    parser.add_argument("--user_id", type=str, default=None, help="User ID for database ingestion")
    parser.add_argument("--db_path", type=str, default=None, help="Path to SQLite database")

    args = parser.parse_args()

    # Initialize Logging
    log_path = setup_logging(args.out)
    log(f"Initializing Hierarchical Scraper (Output: {args.out})")
    log(f"Logs: {log_path}")

    try:
        client = DocsClient()
        crawler = CurriculumCrawler(client)
        pdf_proc = PDFProcessor()
        html_proc = HTMLProcessor()
        slides_proc = SlidesProcessor()
        doc_proc = GoogleDocsProcessor()
        ocr_proc = OCRProcessor()
        ingestion = IngestionService(args.out)
        
        registry_path = "reference_docs/scraped_registry.json"
        visited_docs = load_registry(registry_path)
        incremental_root = bool(args.incremental_root and args.root_id in visited_docs)
        if args.incremental_root and args.root_id not in visited_docs:
            log(
                "Note: --incremental-root ignored (root ID not in scraped_registry.json); "
                "running a full scrape for the root.",
                "INFO",
            )
        if args.user_id:
            from tools.scraper.table_extractor import RecursiveTableParser  # type: ignore

            table_parser = RecursiveTableParser(db_path=args.db_path)
        else:
            table_parser = None
        
        # Start hierarchical processing from root
        process_doc_recursive(
            args.root_id,
            client,
            crawler,
            doc_proc,
            pdf_proc,
            html_proc,
            slides_proc,
            ocr_proc,
            ingestion,
            table_parser,
            "",
            args.out,
            0,
            args.depth,
            visited_docs,
            args.unit,
            registry_path,
            force=args.force,
            user_id=args.user_id,
            entry_root_id=args.root_id,
            incremental_root=incremental_root,
        )

        log(f"All done. Organized files are in {args.out}")

    except Exception as e:
        log(f"Unexpected Error: {e}", "ERROR")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        if log_file:
            log_file.close()

if __name__ == "__main__":
    main()
