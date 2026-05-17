import os
import yaml
from typing import Dict, Any

class IngestionService:
    """Manages storage of scraped content as structured Markdown."""
    
    def __init__(self, output_dir: str):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def save_as_markdown(self, filename: str, content: str, metadata: Dict[str, Any]):
        """Saves content as a Markdown file with YAML frontmatter."""
        # Allow filename to be a relative path for folder structuring
        full_path = os.path.join(self.output_dir, f"{filename}.md")
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        
        # Ensure metadata has at least some basic info
        metadata.setdefault("source", "scraped")
        metadata.setdefault("status", "raw")
        
        yaml_frontmatter = yaml.dump(metadata, default_flow_style=False)
        
        markdown_content = f"---\n{yaml_frontmatter}---\n\n{content}"
        
        with open(full_path, "w", encoding="utf-8") as f:
            f.write(markdown_content)
        
        print(f"Saved: {full_path}")

    def generate_document_id(self, url_or_id: str) -> str:
        """Simple helper to create a safe filename from a URL or ID."""
        import hashlib
        return hashlib.md5(url_or_id.encode()).hexdigest()

if __name__ == "__main__":
    # Test ingestion
    service = IngestionService("output/test")
    service.save_as_markdown("test_doc", "Hello Curriculum", {"grade": "3-5", "subject": "Math"})
