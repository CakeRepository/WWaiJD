"""
Generate favicon files from the meta image
Requires: pip install Pillow
"""

from PIL import Image
import os

def generate_favicons():
    """Generate various favicon sizes from the meta image."""
    
    # Input image
    input_image = 'img/wwaijd-metaimage.png'
    output_dir = 'static'
    
    if not os.path.exists(input_image):
        print(f"❌ Error: {input_image} not found!")
        return
    
    print(f"📸 Opening image: {input_image}")
    img = Image.open(input_image)
    
    # Convert to RGBA if needed
    if img.mode != 'RGBA':
        img = img.convert('RGBA')
    
    # Define favicon sizes
    sizes = [
        (16, 16, 'favicon-16x16.png'),
        (32, 32, 'favicon-32x32.png'),
        (180, 180, 'apple-touch-icon.png'),
    ]
    
    print("\n🎨 Generating favicon files...")
    
    for width, height, filename in sizes:
        output_path = os.path.join(output_dir, filename)
        resized = img.resize((width, height), Image.Resampling.LANCZOS)
        resized.save(output_path, 'PNG', optimize=True)
        print(f"  ✅ Created {filename} ({width}x{height})")
    
    # Generate .ico file (contains multiple sizes)
    print("\n🖼️  Generating favicon.ico with multiple sizes...")
    ico_path = os.path.join(output_dir, 'favicon.ico')
    
    # Create ICO with multiple sizes
    ico_sizes = [(16, 16), (32, 32), (48, 48)]
    ico_images = []
    
    for width, height in ico_sizes:
        resized = img.resize((width, height), Image.Resampling.LANCZOS)
        ico_images.append(resized)
    
    # Save as ICO
    ico_images[0].save(
        ico_path,
        format='ICO',
        sizes=[(img.width, img.height) for img in ico_images],
        append_images=ico_images[1:]
    )
    print(f"  ✅ Created favicon.ico (multi-size)")
    
    print("\n✨ All favicons generated successfully!")
    print(f"📁 Output location: {output_dir}/")
    print("\n📋 Generated files:")
    print("  - favicon.ico (16x16, 32x32, 48x48)")
    print("  - favicon-16x16.png")
    print("  - favicon-32x32.png")
    print("  - apple-touch-icon.png (180x180)")

if __name__ == '__main__':
    try:
        generate_favicons()
    except ImportError:
        print("❌ Error: Pillow library not found!")
        print("📦 Install it with: pip install Pillow")
    except Exception as e:
        print(f"❌ Error generating favicons: {e}")
