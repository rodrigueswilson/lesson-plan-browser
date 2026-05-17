import re
from typing import Set, List, Dict
from tools.scraper.docs_client import DocsClient

class CurriculumCrawler:
    """Crawls Google Docs recursively to discover curriculum content."""
    
    # regex for Google Docs: docs.google.com/document/d/[DOC_ID]/...
    DOC_REGEX = r'https://docs\.google\.com/document/d/([a-zA-Z0-9-_]+)'
    # regex for Google Drive files (usually PDFs): drive.google.com/file/d/[FILE_ID]/...
    DRIVE_FILE_REGEX = r'https://drive\.google\.com/file/d/([a-zA-Z0-9-_]+)'
    # regex for Google Slides: docs.google.com/presentation/d/[ID]/...
    SLIDES_REGEX = r'https://docs\.google\.com/presentation/d/([a-zA-Z0-9-_]+)'
    # regex for PowerPoint files
    PPTX_REGEX = r'https?://[^\s<>"]+\.pptx'
    # generic PDF link: any URL ending in .pdf
    PDF_URL_REGEX = r'https?://[^\s<>"]+\.pdf'
    # generic HTML link (excluding common non-HTML extensions)
    HTML_URL_REGEX = r'https?://[^\s<>"]+(?<!\.pdf)(?<!\.docx)(?<!\.zip)(?<!\.png)(?<!\.jpg)'

    def __init__(self, client: DocsClient):
        self.client = client
        self.visited_docs: Set[str] = set()
        self.discovered_pdfs: Set[str] = set()
        self.discovered_slides: Set[str] = set()
        self.discovered_pptxs: Set[str] = set()
        self.discovered_htmls: Set[str] = set()
        # Maps doc_id -> tab_title -> link_type -> list of links
        self.doc_resource_map: Dict[str, Dict[str, Dict[str, List[str]]]] = {}

    def crawl_root(self, root_doc_id: str, max_depth: int = 3):
        """Starts recursive crawling from a root document."""
        print(f"Starting crawl from Doc ID: {root_doc_id} (max_depth={max_depth})")
        self._crawl_recursive(root_doc_id, depth=0, max_depth=max_depth)
        
        print("\nCrawl Complete!")
        print(f"Visited Docs: {len(self.visited_docs)}")
        print(f"Discovered PDFs: {len(self.discovered_pdfs)}")
        print(f"Discovered Slides: {len(self.discovered_slides)}")
        print(f"Discovered PPTXs: {len(self.discovered_pptxs)}")
        print(f"Discovered HTMLs: {len(self.discovered_htmls)}")
        return self.doc_resource_map

    def _crawl_recursive(self, doc_id: str, depth: int, max_depth: int):
        if doc_id in self.visited_docs or depth > max_depth:
            return
        
        self.visited_docs.add(doc_id)
        print(f"{'  ' * depth}Crawling Doc: {doc_id}")
        
        try:
            doc = self.client.get_document(doc_id)
            self.doc_resource_map[doc_id] = self._extract_links_from_doc(doc)
            
            # Recursive crawling for discovered Docs
            for tab_links in self.doc_resource_map[doc_id].values():
                for linked_doc_id in tab_links.get('doc', []):
                    self._crawl_recursive(linked_doc_id, depth + 1, max_depth)
                
                # Populating global sets for separate processing if needed
                self.discovered_pdfs.update(tab_links.get('pdf', []))
                self.discovered_slides.update(tab_links.get('slides', []))
                self.discovered_pptxs.update(tab_links.get('pptx', []))
                self.discovered_htmls.update(tab_links.get('html', []))
                
        except Exception as e:
            print(f"{'  ' * depth}Error crawling {doc_id}: {e}")

    def _extract_links_from_doc(self, doc: Dict) -> Dict[str, Dict[str, List[str]]]:
        """Extracts all links from a Google Doc structure, mapped by tab title."""
        tab_links = {}
        
        if 'tabs' in doc:
            for tab in doc['tabs']:
                self._extract_links_from_tabs_recursive(tab, tab_links)
        else:
            # Fallback for docs without tabs
            tab_links['Main Content'] = {}
            body = doc.get('body', {})
            content = body.get('content', [])
            for element in content:
                self._process_element(element, tab_links['Main Content'])
            
        return tab_links

    def _extract_links_from_tabs_recursive(self, tab: Dict, tab_links: Dict):
        """Recursively search for links in all tabs."""
        doc_tab = tab.get('documentTab', {})
        tab_props = tab.get('tabProperties', {})
        title = tab_props.get('title') or (doc_tab.get('title') if doc_tab else 'Untitled Tab')
        
        if title not in tab_links:
            tab_links[title] = {}
            
        body = doc_tab.get('body', {})
        for element in body.get('content', []):
            self._process_element(element, tab_links[title])
            
        for child in tab.get('childTabs', []):
            self._extract_links_from_tabs_recursive(child, tab_links)

    def _process_element(self, element: Dict, found_links: Dict):
        """Recursively search for paragraph links (text + rich links)."""
        if 'paragraph' in element:
            for run in element['paragraph'].get('elements', []):
                text_run = run.get('textRun')
                if text_run and 'link' in text_run.get('textStyle', {}):
                    url = text_run['textStyle']['link'].get('url')
                    if url:
                        self._categorize_and_add_link(url, found_links)
                # Google Docs "smart chips" / rich links (e.g., Cool-down PDFs)
                rich_link = run.get('richLink')
                if rich_link:
                    rich_props = rich_link.get('richLinkProperties', {})
                    rich_url = rich_props.get('uri')
                    if rich_url:
                        self._categorize_and_add_link(rich_url, found_links)
        elif 'table' in element:
            for row in element['table'].get('tableRows', []):
                for cell in row.get('tableCells', []):
                    for cell_element in cell.get('content', []):
                        self._process_element(cell_element, found_links)

    def _categorize_and_add_link(self, url: str, found_links: Dict[str, List[str]]):
        # Check for Google Docs
        doc_match = re.search(self.DOC_REGEX, url)
        if doc_match:
            doc_id = doc_match.group(1)
            if 'doc' not in found_links: found_links['doc'] = []
            if doc_id not in found_links['doc']: found_links['doc'].append(doc_id)
            return

        # Check for Drive Files (PDFs)
        drive_match = re.search(self.DRIVE_FILE_REGEX, url)
        if drive_match:
            if 'pdf' not in found_links: found_links['pdf'] = []
            if url not in found_links['pdf']: found_links['pdf'].append(url)
            return

        # Check for direct PDF links
        if re.search(self.PDF_URL_REGEX, url):
            if 'pdf' not in found_links: found_links['pdf'] = []
            if url not in found_links['pdf']: found_links['pdf'].append(url)
            return

        # Check for Google Slides
        slides_match = re.search(self.SLIDES_REGEX, url)
        if slides_match:
            slides_id = slides_match.group(1)
            if 'slides' not in found_links: found_links['slides'] = []
            if slides_id not in found_links['slides']: found_links['slides'].append(slides_id)
            return

        # Check for PPTX
        if re.search(self.PPTX_REGEX, url):
            if 'pptx' not in found_links: found_links['pptx'] = []
            if url not in found_links['pptx']: found_links['pptx'].append(url)
            return

        # Check for HTML
        if re.search(self.HTML_URL_REGEX, url):
            if 'html' not in found_links: found_links['html'] = []
            if url not in found_links['html']: found_links['html'].append(url)

if __name__ == '__main__':
    # Test crawler with a dummy ID (will fail without credentials.json)
    from tools.scraper.docs_client import DocsClient
    try:
        client = DocsClient()
        crawler = CurriculumCrawler(client)
        # crawler.crawl_root('MY_ROOT_DOC_ID')
    except Exception as e:
        print(f"Setup error for crawler: {e}")
