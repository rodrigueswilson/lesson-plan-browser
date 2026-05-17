from typing import Dict, List, Any

class GoogleDocsProcessor:
    """Converts a Google Doc JSON structure into clean Markdown."""

    def __init__(self):
        self._list_counters = {}
        self.inline_objects = {}

    def process(self, doc: Dict[str, Any]) -> Dict[str, Any]:
        """Processes a document JSON into a dictionary of {tab_title: {'content': md, 'images': {id: uri}}}."""
        results = {}
        # Root inline objects (for no-tabs documents)
        self.inline_objects = doc.get('inlineObjects', {})
        
        # Check for new 'tabs' structure
        if 'tabs' in doc:
            tabs = doc['tabs']
            print(f"  Found {len(tabs)} top-level tabs.")
            for tab in tabs:
                self._process_tab_to_dict_recursive(tab, results)
        else:
            # Fallback to flat document structure
            print("  No tabs found, processing as flat document.")
            body = doc.get('body', {})
            content = body.get('content', [])
            markdown_lines = []
            for element in content:
                markdown_lines.extend(self._process_element(element))
            results['main'] = "\n".join(markdown_lines)
            
        return results

    def _process_tab_to_dict_recursive(self, tab: Dict[str, Any], results: Dict[str, Any], prefix: str = ""):
        """Recursively processes tabs into a flat dictionary with path-like keys."""
        doc_tab = tab.get('documentTab')
        tab_props = tab.get('tabProperties', {})
        
        # The title is in tabProperties for newer API versions
        title = tab_props.get('title') or (doc_tab.get('title') if doc_tab else 'Untitled Tab')
        print(f"    Processing Tab: {title}")
        
        # Create a path-like key for nested tabs
        full_title = f"{prefix} - {title}" if prefix else title
        
        # Get this tab's specific inline objects
        tab_inline_objects = doc_tab.get('inlineObjects', {}) if doc_tab else {}
        
        # Process this tab's body if it exists
        markdown_lines = []
        if doc_tab and 'body' in doc_tab:
            # Temporarily set inline_objects for this tab's elements
            old_inline_objects = self.inline_objects
            self.inline_objects = tab_inline_objects
            body = doc_tab.get('body', {})
            for element in body.get('content', []):
                markdown_lines.extend(self._process_element(element))
            
            # Extract ALL images from THIS tab
            used_images = {}
            for obj_id, obj_data in self.inline_objects.items():
                props = obj_data.get('inlineObjectProperties', {})
                uri = props.get('embeddedObject', {}).get('imageProperties', {}).get('contentUri')
                if uri:
                    used_images[obj_id] = uri
            
            content_str = "\n".join(markdown_lines)
            results[full_title] = {"markdown": content_str, "images": used_images}
            
            # Restore previous inline_objects
            self.inline_objects = old_inline_objects
            
        # Process Child Tabs
        child_tabs = tab.get('childTabs', [])
        if child_tabs:
            print(f"      Found {len(child_tabs)} child tabs for {title}")
            for child in child_tabs:
                self._process_tab_to_dict_recursive(child, results, prefix=full_title)

    def _process_element(self, element: Dict[str, Any]) -> List[str]:
        """Processes top-level body elements."""
        lines = []
        
        if 'paragraph' in element:
            lines.append(self._process_paragraph(element['paragraph']))
        elif 'table' in element:
            lines.extend(self._process_table(element['table']))
        elif 'sectionBreak' in element:
            lines.append("\n---\n")
            
        return lines

    def _process_paragraph(self, paragraph: Dict[str, Any]) -> str:
        """Processes a paragraph including headers, lists, and links."""
        text = ""
        for run in paragraph.get('elements', []):
            if 'textRun' in run:
                content = run['textRun'].get('content', '')
                link = run['textRun'].get('textStyle', {}).get('link')
                if link and 'url' in link:
                    url = link['url']
                    # If text is empty/whitespace, use "Link" as visible text so it's clickable
                    if content.strip():
                        text += f"[{content.strip()}]({url})"
                        if content.endswith(' '): text += ' '
                    else:
                        text += f"[Link]({url}){content}"
                else:
                    text += content
            elif 'inlineObjectElement' in run:
                obj_id = run['inlineObjectElement'].get('inlineObjectId')
                text += f"\n\n[IMAGE:{obj_id}]\n\n"
        
        # Handle Headers
        style = paragraph.get('paragraphStyle', {}).get('namedStyleType', 'NORMAL_TEXT')
        if style.startswith('HEADING_'):
            level = int(style.split('_')[1])
            text = f"{'#' * level} {text.strip()}"
        
        # Handle Bullet/Numbered Lists (Simplistic)
        if 'bullet' in paragraph:
            text = f"* {text.strip()}"
            
        return text

    def _process_table(self, table: Dict[str, Any]) -> List[str]:
        """Converts a Google Doc table to a Markdown table."""
        md_table = []
        rows = table.get('tableRows', [])
        
        for i, row in enumerate(rows):
            cells = row.get('tableCells', [])
            cell_contents = []
            for cell in cells:
                # Recursively process cell content
                content = []
                for element in cell.get('content', []):
                    content.extend(self._process_element(element))
                cell_contents.append(" ".join(content).replace("\n", " ").strip())
            
            md_table.append("| " + " | ".join(cell_contents) + " |")
            
            # Add separator after header row
            if i == 0:
                md_table.append("| " + " | ".join(["---"] * len(cells)) + " |")
                
        return md_table + [""] # Add empty line after table
