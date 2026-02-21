#!/usr/bin/env python3
"""Convert icon2.svg to Android app icon PNGs at all required sizes."""

import cairosvg
import os

# Icon sizes for different Android densities
SIZES = {
    'mdpi': 48,
    'hdpi': 72,
    'xhdpi': 96,
    'xxhdpi': 144,
    'xxxhdpi': 192,
}

# Base paths
RES_PATH = 'android/app/src/main/res'
SVG_FILE = 'icon2.svg'

def convert_icon():
    """Convert SVG to PNG at all required sizes."""
    print(f"Converting {SVG_FILE} to Android icon resources...")
    
    # Create launcher icons
    for density, size in SIZES.items():
        output_dir = f"{RES_PATH}/mipmap-{density}"
        launcher_path = f"{output_dir}/ic_launcher.png"
        foreground_path = f"{output_dir}/ic_launcher_foreground.png"
        
        print(f"  Creating {density} ({size}x{size}px)...")
        
        # Create ic_launcher.png
        cairosvg.svg2png(
            url=SVG_FILE,
            write_to=launcher_path,
            output_width=size,
            output_height=size
        )
        
        # Create ic_launcher_foreground.png (same size for now)
        cairosvg.svg2png(
            url=SVG_FILE,
            write_to=foreground_path,
            output_width=size,
            output_height=size
        )
    
    print("✓ Icon conversion complete!")
    print(f"  Created icons in: {RES_PATH}/mipmap-*/")

if __name__ == '__main__':
    convert_icon()

