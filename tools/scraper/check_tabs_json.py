import json

path = r'd:\LP\temp_u2\unit2_api_raw.json'
with open(path, 'r', encoding='utf-8') as f:
    doc = json.load(f)

# Check for tabs
if 'tabs' in doc:
    print(f"Document has {len(doc['tabs'])} tabs.")
    for i, tab in enumerate(doc['tabs']):
        tab_properties = tab.get('tabProperties', {})
        print(f"Tab {i}: {tab_properties.get('title')} (ID: {tab_properties.get('tabId')})")
        # Content is in documentTab.body.content
        doc_tab = tab.get('documentTab', {})
        content = doc_tab.get('body', {}).get('content', [])
        print(f"  StructuralElements: {len(content)}")
        
        # Check for tables
        for el in content:
            if 'table' in el:
                t = el['table']
                print(f"  FOUND TABLE: {len(t.get('tableRows', []))} rows")
else:
    print("No tabs found. Checking main body...")
    content = doc.get('body', {}).get('content', [])
    print(f"Main Body StructuralElements: {len(content)}")
