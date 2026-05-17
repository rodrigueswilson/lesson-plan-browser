import re

class StyleParser:
    """
    Parses Google Docs HTML export CSS to identify semantic styles.
    Maps obfuscated class names (e.g. .c0, .c1) to semantic flags.
    """
    def __init__(self, html_content: str):
        self.style_map = {}
        self._parse_styles(html_content)

    def _parse_styles(self, html_content: str):
        # Extract <style> block
        style_match = re.search(r'<style[^>]*>(.*?)</style>', html_content, re.DOTALL | re.IGNORECASE)
        if not style_match:
            return

        css = style_match.group(1)
        # Find all class definitions: .name{props}
        # Note: GDocs often combines classes like .c1,.c2{props}
        rule_pattern = re.compile(r'\.([a-zA-Z0-9_-]+(?:,\.[a-zA-Z0-9_-]+)*)\s*\{([^\}]*)\}')
        
        for match in rule_pattern.finditer(css):
            selector_str, props = match.groups()
            selectors = [s.strip().lstrip('.') for s in selector_str.split(',')]
            
            flags = set()
            
            # Check for bold
            if 'font-weight:700' in props or 'font-weight:bold' in props:
                flags.add('bold')
            
            # Check for italic
            if 'font-style:italic' in props:
                flags.add('italic')
                
            # Check for font size (headings)
            size_match = re.search(r'font-size:(\d+)pt', props)
            if size_match:
                size = int(size_match.group(1))
                if size >= 20: flags.add('h1')
                elif size >= 16: flags.add('h2')
                elif size >= 14: flags.add('h3')
                elif size >= 12: flags.add('h4')

            if flags:
                for s in selectors:
                    if s not in self.style_map:
                        self.style_map[s] = set()
                    self.style_map[s].update(flags)

    def get_flags(self, class_name: str) -> set:
        """Returns the semantic flags for a given class name."""
        return self.style_map.get(class_name, set())

    def get_flags_from_inline(self, style_str: str) -> set:
        """Parses an inline style string for semantic flags."""
        if not style_str:
            return set()
        
        flags = set()
        if 'font-weight:700' in style_str or 'font-weight:bold' in style_str:
            flags.add('bold')
        if 'font-style:italic' in style_str:
            flags.add('italic')
            
        size_match = re.search(r'font-size:(\d+)pt', style_str)
        if size_match:
            size = int(size_match.group(1))
            if size >= 20: flags.add('h1')
            elif size >= 16: flags.add('h2')
            elif size >= 14: flags.add('h3')
            elif size >= 12: flags.add('h4')
        return flags

    def transform_element(self, tag: str, classes: list, inline_style: str = "") -> str:
        """
        Determines the semantic tag for an element.
        Combines class-based flags and inline-style flags.
        """
        all_flags = set()
        for c in classes:
            all_flags.update(self.get_flags(c))
            
        all_flags.update(self.get_flags_from_inline(inline_style))
            
        if tag == 'span':
            if 'bold' in all_flags: return 'strong'
            if 'italic' in all_flags: return 'em'
            
        if tag == 'p':
            if 'h1' in all_flags: return 'h1'
            if 'h2' in all_flags: return 'h2'
            if 'h3' in all_flags: return 'h3'
            if 'h4' in all_flags: return 'h4'
            
        return tag
