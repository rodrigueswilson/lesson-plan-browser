import sys
import os

# Add tools/scraper to path
scraper_dir = r'd:\LP\tools\scraper'
sys.path.append(scraper_dir)

from docs_client import DocsClient

def main():
    doc_id = "1hBoK4uk0Z_GBEixY4wFHXtFi1gLOXarytFhKamftSOE"
    output_path = r'd:\LP\temp_u2\unit2_export.md'
    
    print(f"Testing Markdown export for {doc_id}...")
    client = DocsClient()
    
    # MIME type for Markdown is text/markdown
    success = client.export_document(doc_id, output_path, mime_type='text/markdown')
    if success:
        print(f"Successfully exported to {output_path}")
        # Show first 500 chars
        with open(output_path, 'r', encoding='utf-8') as f:
            print(f"--- PREVIEW ---\n{f.read(1000)}\n--- END PREVIEW ---")
    else:
        print("Markdown export failed. Likely not supported by this API version or account.")

if __name__ == '__main__':
    main()
