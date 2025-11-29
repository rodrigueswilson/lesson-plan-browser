"""Create a valid ICO file that Tauri can decode."""
from PIL import Image
import os

# Create icons directory
os.makedirs('src-tauri/icons', exist_ok=True)

# Create a simple 32x32 blue image
img = Image.new('RGBA', (32, 32), color=(0, 0, 255, 255))

# Save as ICO
img.save('src-tauri/icons/icon.ico', format='ICO', sizes=[(32, 32)])

print("✓ Created valid icon.ico")
