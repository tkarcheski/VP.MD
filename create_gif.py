#!/usr/bin/env python3
"""Convert ASCII frames to an animated GIF."""

import re
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

# ANSI color to RGB mapping
ANSI_COLORS = {
    "91": (255, 85, 85),    # bright red
    "92": (85, 255, 85),    # bright green
    "93": (255, 255, 85),   # bright yellow
    "94": (85, 85, 255),    # bright blue
    "95": (255, 85, 255),   # bright magenta
    "96": (85, 255, 255),   # bright cyan
    "0": (255, 255, 255),   # reset (white)
}

def parse_ansi_text(text):
    """Parse ANSI-colored text into segments of (color, text)."""
    segments = []
    pattern = r'\033\[([0-9]+)m'
    current_color = "0"
    last_end = 0

    for match in re.finditer(pattern, text):
        # Add text before this code
        if match.start() > last_end:
            segments.append((current_color, text[last_end:match.start()]))

        # Update current color
        current_color = match.group(1)
        last_end = match.end()

    # Add remaining text
    if last_end < len(text):
        segments.append((current_color, text[last_end:]))

    return segments

def render_frame_to_image(frame_text, width=1200, height=600, bg_color=(20, 20, 40)):
    """Render an ASCII frame to an image."""
    img = Image.new("RGB", (width, height), bg_color)
    draw = ImageDraw.Draw(img)

    # Use monospace font
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 12)
    except:
        font = ImageFont.load_default()

    char_width = 7
    line_height = 16

    y = 10
    for line in frame_text.split("\n"):
        x = 10
        segments = parse_ansi_text(line)

        for color_code, text in segments:
            color = ANSI_COLORS.get(color_code, (255, 255, 255))
            draw.text((x, y), text, fill=color, font=font)
            x += len(text) * char_width

        y += line_height

    return img

def create_gif():
    """Create animated GIF from ASCII frames."""
    frames_dir = Path("vance_dance_frames")
    frame_files = sorted(frames_dir.glob("frame_*.txt"))

    if not frame_files:
        print("No frames found. Run the CLI first to generate frames.")
        return

    print(f"Rendering {len(frame_files)} frames to images...")
    images = []

    for i, frame_file in enumerate(frame_files):
        frame_text = frame_file.read_text()
        img = render_frame_to_image(frame_text)
        images.append(img)

        if (i + 1) % 15 == 0:
            print(f"  Rendered {i + 1}/{len(frame_files)}")

    # Create animated GIF
    gif_path = Path("assets/vance_dance.gif")
    gif_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"Creating GIF at {gif_path}...")
    images[0].save(
        gif_path,
        save_all=True,
        append_images=images[1:],
        duration=67,  # ~15 FPS
        loop=0,
        optimize=False,
    )

    print(f"✓ GIF created: {gif_path}")
    print(f"  Size: {gif_path.stat().st_size / 1024:.1f} KB")

if __name__ == "__main__":
    create_gif()
