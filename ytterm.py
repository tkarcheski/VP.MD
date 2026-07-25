#!/usr/bin/env python3
"""
ytterm — play any YouTube video's storyboard as ASCII art in your terminal.

No video download required: YouTube exposes publicly accessible "storyboard"
preview images (the thumbnails you see when hovering the seek bar). This tool
fetches those, slices them into frames, and animates them in your terminal
with ANSI colors.

Nothing is bundled or redistributed — frames are fetched from YouTube at
runtime, on your machine, from the same public endpoint your browser uses.

Usage:
    python3 ytterm.py https://www.youtube.com/watch?v=VIDEO_ID
    python3 ytterm.py https://www.youtube.com/shorts/VIDEO_ID --fps 8 --width 100

Requirements:
    - Python 3.8+
    - Pillow  (pip install Pillow)
    - chafa   (optional, used automatically for higher-quality rendering)

Press Ctrl+C to stop.
"""

import argparse
import io
import json
import os
import re
import shutil
import subprocess
import sys
import time
import urllib.parse
import urllib.request

try:
    from PIL import Image
except ImportError:
    print("Pillow is required: pip install Pillow", file=sys.stderr)
    sys.exit(1)

UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)


# --------------------------------------------------------------------------
# Fetching
# --------------------------------------------------------------------------

def http_get(url: str, timeout: int = 20) -> bytes:
    req = urllib.request.Request(url, headers={
        "User-Agent": UA,
        "Referer": "https://www.youtube.com/",
        "Accept-Language": "en-US,en;q=0.9",
    })
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read()


def extract_video_id(url: str) -> str:
    patterns = [
        r"(?:v=|/shorts/|/embed/|youtu\.be/)([A-Za-z0-9_-]{11})",
    ]
    for p in patterns:
        m = re.search(p, url)
        if m:
            return m.group(1)
    if re.fullmatch(r"[A-Za-z0-9_-]{11}", url):
        return url
    raise ValueError(f"Could not extract a video ID from: {url}")


def fetch_metadata(video_id: str) -> dict:
    """Get title/author from YouTube's public oEmbed endpoint (no API key)."""
    oembed = (
        "https://www.youtube.com/oembed?format=json&url="
        + urllib.parse.quote(f"https://www.youtube.com/watch?v={video_id}")
    )
    try:
        data = json.loads(http_get(oembed).decode())
        return {"title": data.get("title", video_id),
                "author": data.get("author_name", "unknown")}
    except Exception:
        return {"title": video_id, "author": "unknown"}


def fetch_storyboard_spec(video_id: str) -> str:
    """Extract the storyboard spec string from the watch page."""
    for page_url in (
        f"https://www.youtube.com/watch?v={video_id}",
        f"https://www.youtube.com/shorts/{video_id}",
    ):
        try:
            html = http_get(page_url).decode("utf-8", errors="replace")
        except Exception:
            continue
        m = re.search(
            r'"playerStoryboardSpecRenderer"\s*:\s*\{\s*"spec"\s*:\s*"([^"]+)"',
            html,
        )
        if m:
            return m.group(1).encode().decode("unicode_escape")
    raise RuntimeError(
        "Could not find a storyboard spec. The video may be private, "
        "age-restricted, or YouTube served a consent/captcha page."
    )


def parse_storyboard_spec(spec: str) -> dict:
    """
    Spec format:  BASE_URL|level0|level1|...
    Each level:   width#height#quality#cols#rows#duration#name#sigh   (8 fields)
    $L in the URL is the level index, $N is the image name ($M = image index).
    """
    parts = spec.split("|")
    base_url = parts[0]
    levels = []
    for i, level_spec in enumerate(parts[1:]):
        f = level_spec.split("#")
        if len(f) < 8:
            continue
        levels.append({
            "level": i,
            "frame_w": int(f[0]),
            "frame_h": int(f[1]),
            "cols": int(f[3]),
            "rows": int(f[4]),
            "name": f[6],
            "sigh": f[7],
        })
    return {"base_url": base_url, "levels": levels}


def download_frames(sb: dict, level_idx: int = -1, max_images: int = 50) -> list:
    """Download storyboard images for a level and slice into PIL frames."""
    levels = sb["levels"]
    if not levels:
        raise RuntimeError("No storyboard levels available.")
    level = levels[level_idx] if 0 <= level_idx < len(levels) else levels[-1]

    frames = []
    for seg in range(max_images):
        name = level["name"].replace("$M", str(seg))
        url = (sb["base_url"]
               .replace("$L", str(level["level"]))
               .replace("$N", name))
        url += ("&" if "?" in url else "?") + "sigh=" + level["sigh"]

        try:
            data = http_get(url, timeout=15)
        except Exception:
            break  # no more segments

        img = Image.open(io.BytesIO(data)).convert("RGB")
        w, h = img.size
        fw = w // level["cols"]
        fh = h // level["rows"]
        for row in range(level["rows"]):
            for col in range(level["cols"]):
                frame = img.crop((col * fw, row * fh,
                                  (col + 1) * fw, (row + 1) * fh))
                # skip empty (all-black) padding frames
                if frame.convert("L").getextrema() != (0, 0):
                    frames.append(frame)

        if "$M" not in level["name"]:
            break  # single-image level

    if not frames:
        raise RuntimeError("Downloaded storyboard but extracted no frames.")
    return frames


# --------------------------------------------------------------------------
# Rendering
# --------------------------------------------------------------------------

def render_chafa(frame: Image.Image, width: int, height: int) -> str:
    """Render via chafa (best quality)."""
    buf = io.BytesIO()
    frame.save(buf, format="PNG")
    result = subprocess.run(
        ["chafa", "--colors=240", "--symbols=block+border+space",
         f"--size={width}x{height}", "-"],
        input=buf.getvalue(), capture_output=True,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.decode()[:200])
    return result.stdout.decode()


def render_halfblock(frame: Image.Image, width: int, height: int) -> str:
    """Built-in truecolor renderer using U+2580 half blocks (no chafa needed)."""
    # each text row shows two pixel rows
    px_h = height * 2
    src_w, src_h = frame.size
    scale = min(width / src_w, px_h / src_h)
    w = max(1, int(src_w * scale))
    h = max(2, int(src_h * scale) // 2 * 2)
    img = frame.resize((w, h))
    px = img.load()

    lines = []
    for y in range(0, h, 2):
        row = []
        for x in range(w):
            r1, g1, b1 = px[x, y]
            r2, g2, b2 = px[x, y + 1]
            row.append(f"\x1b[38;2;{r1};{g1};{b1}m\x1b[48;2;{r2};{g2};{b2}m\u2580")
        row.append("\x1b[0m")
        lines.append("".join(row))
    return "\n".join(lines)


def render_frames(frames: list, width: int, height: int, use_chafa: bool) -> list:
    rendered = []
    total = len(frames)
    for i, frame in enumerate(frames):
        sys.stderr.write(f"\rRendering frame {i + 1}/{total}...")
        sys.stderr.flush()
        if use_chafa:
            rendered.append(render_chafa(frame, width, height))
        else:
            rendered.append(render_halfblock(frame, width, height))
    sys.stderr.write("\n")
    return rendered


# --------------------------------------------------------------------------
# Playback
# --------------------------------------------------------------------------

def play(rendered: list, meta: dict, fps: float, loop: bool):
    delay = 1.0 / fps
    sys.stdout.write("\x1b[?25l")  # hide cursor
    try:
        while True:
            for i, frame in enumerate(rendered):
                sys.stdout.write("\x1b[2J\x1b[H")
                sys.stdout.write(
                    f"\x1b[1;36m{meta['title']}\x1b[0m "
                    f"\x1b[90mby {meta['author']} | "
                    f"frame {i + 1}/{len(rendered)} | Ctrl+C to stop\x1b[0m\n"
                )
                sys.stdout.write(frame)
                sys.stdout.write("\n")
                sys.stdout.flush()
                time.sleep(delay)
            if not loop:
                break
            time.sleep(0.3)
    except KeyboardInterrupt:
        pass
    finally:
        sys.stdout.write("\x1b[2J\x1b[H\x1b[?25h\x1b[0m")
        sys.stdout.flush()
        print(f"{meta['title']} — stopped.")


def main():
    parser = argparse.ArgumentParser(
        description="Play a YouTube video's storyboard as ASCII art in the terminal.")
    parser.add_argument("url", help="YouTube URL or 11-character video ID")
    parser.add_argument("--fps", type=float, default=8.0,
                        help="playback frames per second (default: 8)")
    parser.add_argument("--width", type=int, default=0,
                        help="output width in columns (default: terminal width)")
    parser.add_argument("--height", type=int, default=0,
                        help="output height in rows (default: terminal height)")
    parser.add_argument("--level", type=int, default=-1,
                        help="storyboard quality level (default: highest)")
    parser.add_argument("--no-loop", action="store_true", help="play once and exit")
    parser.add_argument("--no-chafa", action="store_true",
                        help="force built-in renderer even if chafa is installed")
    args = parser.parse_args()

    term = shutil.get_terminal_size((80, 42))
    width = args.width or term.columns
    height = args.height or max(10, term.lines - 3)

    video_id = extract_video_id(args.url)
    print(f"Video ID: {video_id}")

    meta = fetch_metadata(video_id)
    print(f"Title:    {meta['title']}")
    print(f"Author:   {meta['author']}")

    print("Fetching storyboard spec...")
    spec = fetch_storyboard_spec(video_id)
    sb = parse_storyboard_spec(spec)
    print(f"Found {len(sb['levels'])} storyboard levels: "
          + ", ".join(f"L{l['level']} {l['frame_w']}x{l['frame_h']}"
                      for l in sb["levels"]))

    print("Downloading frames...")
    frames = download_frames(sb, level_idx=args.level)
    print(f"Extracted {len(frames)} frames.")

    use_chafa = (not args.no_chafa) and shutil.which("chafa") is not None
    print(f"Renderer: {'chafa' if use_chafa else 'built-in half-block'}")
    rendered = render_frames(frames, width, height, use_chafa)

    play(rendered, meta, fps=args.fps, loop=not args.no_loop)


if __name__ == "__main__":
    main()
