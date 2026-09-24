#!/usr/bin/env python3
"""
vance_ascii — make fun of DJ Vance with ASCII art animations in your Linux terminal.

Generates or sources dancing DJ Vance frames and animates them in the terminal
with retro VT-100 vibes (ANSI colors, ASCII art).

Supports multiple frame sources:
- YouTube storyboard scraping
- AI-generated frames (unsloth)
- Direct ASCII art generation

Usage:
    just-dance-vance-terminal youtube --url https://youtube.com/shorts/S2GC9PxDWPI
    just-dance-vance-terminal generate --frames 30 --ai
    just-dance-vance-terminal ascii --text "VANCE IS DANCING"
    just-dance-vance-terminal play frames/ --fps 12 --loop

Press Ctrl+C to stop.
"""

import argparse
import sys
import time
from pathlib import Path

from .generators.ascii_generator import generate_and_save

# Lazy imports for optional dependencies
PIL = None
CHAFA = None


def parse_args():
    parser = argparse.ArgumentParser(
        description="AI-powered ASCII art roasting of DJ Vance"
    )
    subparsers = parser.add_subparsers(dest="command", help="Operation mode")

    # YouTube storyboard scraping
    youtube_parser = subparsers.add_parser(
        "youtube", help="Scrape YouTube storyboard and render as ASCII"
    )
    youtube_parser.add_argument("--url", required=True, help="YouTube video URL")
    youtube_parser.add_argument("--fps", type=int, default=12, help="Playback FPS")
    youtube_parser.add_argument("--width", type=int, default=None, help="Terminal width")
    youtube_parser.add_argument("--height", type=int, default=None, help="Terminal height")
    youtube_parser.add_argument("--loop", action="store_true", default=True, help="Loop animation")
    youtube_parser.add_argument("--charset", default="standard", help="ASCII charset: simple, standard, blocks")

    # AI generation
    ai_parser = subparsers.add_parser("generate", help="AI-generate Vance frames")
    ai_parser.add_argument("--frames", type=int, default=30, help="Number of frames to generate")
    ai_parser.add_argument("--prompt", default="DJ Vance dancing", help="Generation prompt")
    ai_parser.add_argument("--output", default="vance_frames", help="Output directory")
    ai_parser.add_argument("--model", default="unsloth", help="Generation model")

    # Direct ASCII art
    ascii_parser = subparsers.add_parser("ascii", help="Create ASCII art directly")
    ascii_parser.add_argument("--text", default="VANCE", help="Text to render")
    ascii_parser.add_argument("--style", default="dancing", help="Style: dancing, roasting, etc.")

    # Play existing frames
    play_parser = subparsers.add_parser("play", help="Play frames from directory")
    play_parser.add_argument("frames_dir", help="Directory containing frames")
    play_parser.add_argument("--fps", type=int, default=12, help="Playback FPS")
    play_parser.add_argument("--loop", action="store_true", default=True, help="Loop animation")
    play_parser.add_argument("--width", type=int, default=None, help="Terminal width")
    play_parser.add_argument("--charset", default="standard", help="ASCII charset")

    return parser.parse_args()


def ensure_pil():
    """Lazy-load PIL."""
    global PIL
    if PIL is None:
        try:
            import PIL as _PIL
            PIL = _PIL
        except ImportError:
            print("ERROR: Pillow required: pip install Pillow", file=sys.stderr)
            sys.exit(1)
    return PIL


def get_terminal_size():
    """Get terminal dimensions."""
    import shutil
    cols, rows = shutil.get_terminal_size()
    return cols, rows


def image_to_ascii(image_path, width=None, height=None, charset="standard"):
    """Convert an image to ASCII art."""
    PIL = ensure_pil()
    from PIL import Image

    if width is None or height is None:
        width, height = get_terminal_size()
        height = max(height - 2, 10)  # Leave room for status line

    # Load and resize image
    img = Image.open(image_path).convert("RGB")
    aspect_ratio = img.height / img.width
    new_height = int(width * aspect_ratio * 0.55)  # Terminal cells are ~2:1 height:width
    img = img.resize((width, new_height), Image.Resampling.LANCZOS)

    # Brightness to ASCII mapping
    ascii_chars = {
        "simple": " .:-=+*#%@",
        "standard": " .'`^\",:;Il!i><~+_-?][}{1)(|\\/tfjrxnuvczXYUJCLQ0OZmwqpdbkhao*#MW&8%B@$",
        "blocks": " ░▒▓█",
    }
    chars = ascii_chars.get(charset, ascii_chars["standard"])

    result = []
    pixels = img.getdata()
    width_img = img.width
    for i, pixel in enumerate(pixels):
        if i % width_img == 0:
            result.append("\n")
        # Calculate brightness (0-255)
        brightness = sum(pixel) / 3
        char_idx = int((brightness / 255) * (len(chars) - 1))
        result.append(chars[char_idx])

    return "".join(result)


def animate_frames(frames_dir, fps=12, loop=True, width=None, height=None, charset="standard"):
    """Play ASCII frames in terminal with animation (supports image and text frames)."""
    frames_path = Path(frames_dir)

    # Look for either image files (.png, .jpg) or text files (.txt)
    image_frames = sorted(frames_path.glob("*.png")) + sorted(frames_path.glob("*.jpg"))
    text_frames = sorted(frames_path.glob("*.txt"))

    # Use whichever type we found
    if text_frames:
        frames = text_frames
        is_text = True
    elif image_frames:
        frames = image_frames
        is_text = False
    else:
        print(f"No frames found in {frames_dir}", file=sys.stderr)
        sys.exit(1)

    frame_delay = 1.0 / fps
    frame_count = len(frames)
    print(f"Playing {frame_count} frames at {fps} FPS")

    try:
        while loop:
            for frame_path in frames:
                # Clear screen (VT-100 style)
                print("\033[2J\033[H", end="", flush=True)

                # Render frame
                if is_text:
                    # Safe: frames are generated internally by ascii_generator, not from untrusted input
                    ascii_art = frame_path.read_text()
                else:
                    ascii_art = image_to_ascii(str(frame_path), width, height, charset)

                print(ascii_art, flush=True)
                time.sleep(frame_delay)

            if not loop:
                break

    except KeyboardInterrupt:
        print("\n\n✌️ Vance out.", flush=True)


def main():
    args = parse_args()

    if args.command == "youtube":
        from generators.youtube_scraper import scrape_youtube
        frames_dir = scrape_youtube(args.url)
        animate_frames(
            frames_dir,
            fps=args.fps,
            loop=args.loop,
            width=args.width,
            charset=args.charset,
        )

    elif args.command == "generate":
        frames_dir = generate_and_save(
            frames=args.frames,
            output_dir=args.output,
        )
        print(f"\nGenerated frames in {frames_dir}")
        print(f"Play with: just-dance-vance-terminal play {frames_dir} --fps 12")

    elif args.command == "ascii":
        from .interactive import interactive_dance
        interactive_dance()

    elif args.command == "play":
        animate_frames(
            args.frames_dir,
            fps=args.fps,
            loop=args.loop,
            width=args.width,
            charset=args.charset,
        )

    else:
        print("Usage: just-dance-vance-terminal {youtube,generate,ascii,play} ...", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
