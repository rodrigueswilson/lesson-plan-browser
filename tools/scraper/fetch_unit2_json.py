import sys
import os
import json

# Add tools/scraper to path
scraper_dir = r'd:\LP\tools\scraper'
sys.path.append(scraper_dir)

from docs_client import DocsClient

def main():
    doc_id = "1hBoK4uk0Z_GBEixY4wFHXtFi1gLOXarytFhKamftSOE"
    output_path = r'd:\LP\temp_u2\unit2_api_raw.json'
    
    print(f"Connecting to Google Docs API for {doc_id}...")
    client = DocsClient()
    
    success = client.get_document_json(doc_id, output_path)
    if success:
        print(f"Successfully saved raw JSON to {output_path}")
    else:
        print("Failed to save JSON.")

if __name__ == '__main__':
    main()
