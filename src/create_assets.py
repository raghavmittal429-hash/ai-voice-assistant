from PIL import Image, ImageDraw, ImageFont

# Create assets folder
import os
os.makedirs('assets', exist_ok=True)

# Create icon.png (512x512 - App icon)
icon = Image.new('RGBA', (512, 512), (30, 60, 120, 255))
draw = ImageDraw.Draw(icon)

# Draw circle background
draw.ellipse([50, 50, 462, 462], fill=(100, 150, 255, 255))

# Draw "AI" text
try:
    font = ImageFont.truetype("arial.ttf", 120)
except:
    font = ImageFont.load_default()

draw.text((256, 256), "AI", fill=(255, 255, 255, 255), anchor="mm", font=font)
icon.save('assets/icon.png')
print("✓ Created assets/icon.png (512x512)")

# Create presplash.png (1080x1920 - Splash screen)
presplash = Image.new('RGBA', (1080, 1920), (20, 30, 50, 255))
draw = ImageDraw.Draw(presplash)

# Draw gradient effect
for i in range(0, 1920, 10):
    alpha = int(255 * (1 - i/1920))
    draw.line([(0, i), (1080, i)], fill=(30, 60, 120, alpha))

# Draw title
try:
    font_large = ImageFont.truetype("arial.ttf", 80)
    font_small = ImageFont.truetype("arial.ttf", 40)
except:
    font_large = ImageFont.load_default()
    font_small = ImageFont.load_default()

draw.text((540, 800), "AI Voice", fill=(255, 255, 255, 255), anchor="mm", font=font_large)
draw.text((540, 900), "Assistant", fill=(100, 150, 255, 255), anchor="mm", font=font_large)
draw.text((540, 1000), "Powered by Ollama", fill=(200, 200, 200, 255), anchor="mm", font=font_small)

presplash.save('assets/presplash.png')
print("✓ Created assets/presplash.png (1080x1920)")

print("\n✅ All assets created successfully!")
print("Location: assets/")