"""Create a minimal valid ICO file for Tauri development."""
import struct
import os

# Create icons directory
os.makedirs('src-tauri/icons', exist_ok=True)

# Minimal 16x16 ICO file structure
# ICO header (6 bytes) + Image directory (16 bytes) + BMP data
ico_data = bytearray([
    # ICO header
    0x00, 0x00,  # Reserved (must be 0)
    0x01, 0x00,  # Type (1 = ICO)
    0x01, 0x00,  # Number of images
    
    # Image directory entry (16 bytes)
    0x10,        # Width (16 pixels)
    0x10,        # Height (16 pixels)
    0x00,        # Color palette (0 = no palette)
    0x00,        # Reserved
    0x01, 0x00,  # Color planes
    0x20, 0x00,  # Bits per pixel (32-bit)
    0x00, 0x04, 0x00, 0x00,  # Size of image data (1024 bytes)
    0x16, 0x00, 0x00, 0x00,  # Offset to image data (22 bytes)
])

# BMP header for 16x16 32-bit image
bmp_header = bytearray([
    0x28, 0x00, 0x00, 0x00,  # Header size (40 bytes)
    0x10, 0x00, 0x00, 0x00,  # Width (16)
    0x20, 0x00, 0x00, 0x00,  # Height (32 = 16*2 for ICO format)
    0x01, 0x00,              # Planes
    0x20, 0x00,              # Bits per pixel (32)
    0x00, 0x00, 0x00, 0x00,  # Compression (none)
    0x00, 0x04, 0x00, 0x00,  # Image size
    0x00, 0x00, 0x00, 0x00,  # X pixels per meter
    0x00, 0x00, 0x00, 0x00,  # Y pixels per meter
    0x00, 0x00, 0x00, 0x00,  # Colors used
    0x00, 0x00, 0x00, 0x00,  # Important colors
])

# Create blue 16x16 image data (BGRA format)
# 16x16 pixels * 4 bytes (BGRA) = 1024 bytes
image_data = bytearray()
for y in range(16):
    for x in range(16):
        # BGRA: Blue, Green, Red, Alpha
        image_data.extend([0xFF, 0x00, 0x00, 0xFF])  # Blue pixel

# AND mask (all transparent) - 16x16 bits = 32 bytes
and_mask = bytearray([0x00] * 32)

# Combine all parts
ico_file = ico_data + bmp_header + image_data + and_mask

# Write to file
with open('src-tauri/icons/icon.ico', 'wb') as f:
    f.write(ico_file)

print("✓ Created icon.ico successfully")
