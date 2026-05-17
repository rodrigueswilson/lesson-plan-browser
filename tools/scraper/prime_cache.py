import os
import shutil

def prime_cache():
    cache_dir = "reference_docs/.asset_cache"
    os.makedirs(cache_dir, exist_ok=True)
    search_dirs = ["reference_docs/curriculum", "reference_docs/scraped"]
    
    count = 0
    for s_dir in search_dirs:
        if not os.path.exists(s_dir):
            continue
        for root, _, files in os.walk(s_dir):
            for file in files:
                if file.startswith(("IMG_", "PDF_", "PPTX_", "SLIDE_IMG_")):
                    src = os.path.join(root, file)
                    dst = os.path.join(cache_dir, file)
                    if not os.path.exists(dst):
                        try:
                            shutil.copy2(src, dst)
                            count += 1
                        except Exception as e:
                            print(f"Error copying {file}: {e}")

    print(f"Successfully primed cache with {count} unique media assets.")

if __name__ == "__main__":
    prime_cache()
