"""
YouTube storyboard scraper — fetch and extract frames from YouTube preview thumbnails.

YouTube exposes publicly-accessible storyboard images (the thumbnails you see
when hovering the seek bar). This module fetches and slices them into individual frames.
"""

import io
import json
import re
import urllib.parse
import urllib.request
from pathlib import Path

from PIL import Image

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)


def http_get(url: str, timeout: int = 20) -> bytes:
    """Fetch URL with appropriate headers."""
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Referer": "https://www.youtube.com/",
            "Accept-Language": "en-US,en;q=0.9",
        },
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read()


def extract_video_id(url: str) -> str:
    """Extract YouTube video ID from URL."""
    patterns = [
        r"(?:v=|/shorts/|/embed/|youtu\.be/)([A-Za-z0-9_-]{11})",
    ]
    for p in patterns:
        m = re.search(p, url)
        if m:
            return m.group(1)
    if re.fullmatch(r"[A-Za-z0-9_-]{11}", url):
        return url
    raise ValueError(f"Could not extract video ID from: {url}")


def fetch_video_metadata(video_id: str) -> dict:
    """Get title/author from YouTube's public oEmbed endpoint."""
    oembed_url = (
        "https://www.youtube.com/oembed?format=json&url="
        + urllib.parse.quote(f"https://www.youtube.com/watch?v={video_id}")
    )
    try:
        data = json.loads(http_get(oembed_url).decode())
        return {
            "title": data.get("title", video_id),
            "author": data.get("author_name", "unknown"),
        }
    except Exception as e:
        print(f"Warning: Could not fetch metadata: {e}")
        return {"title": video_id, "author": "unknown"}


def fetch_storyboard_metadata(video_id: str) -> dict:
    """
    Fetch YouTube's internal storyboard config.

    Returns: {
        'url': storyboard image URL template,
        'cols': frames per row,
        'rows': frames per column,
        'frame_width': pixel width of each frame,
        'frame_height': pixel height of each frame,
        'frame_count': total frames,
        'duration': video duration in seconds,
    }
    """
    # Fetch the watch page to extract storyboard config
    watch_url = f"https://www.youtube.com/watch?v={video_id}"
    try:
        html = http_get(watch_url).decode("utf-8", errors="ignore")
    except Exception as e:
        raise RuntimeError(f"Failed to fetch video page: {e}")

    # Extract initial data from the watch page
    match = re.search(r'"storyboards":\s*(\[.*?\])', html)
    if not match:
        raise RuntimeError("Could not find storyboard config in page")

    try:
        storyboards = json.loads(match.group(1))
    except json.JSONDecodeError:
        raise RuntimeError("Failed to parse storyboard config")

    if not storyboards:
        raise RuntimeError("No storyboards found for this video")

    # Use the highest quality storyboard (last one)
    sb = storyboards[-1]

    return {
        "url": sb.get("templateUrl", ""),
        "cols": int(sb.get("columns", 10)),
        "rows": int(sb.get("rows", 10)),
        "frame_width": int(sb.get("width", 160)),
        "frame_height": int(sb.get("height", 90)),
        "frame_count": int(sb.get("frameCount", 0)),
        "duration": int(sb.get("durationSeconds", 0)),
    }


def fetch_frames(video_id: str, max_images: int = 100) -> list[Image.Image]:
    """
    Fetch storyboard images and slice into individual frames.

    Returns list of PIL Image objects.
    """
    print(f"Fetching storyboard metadata for {video_id}...")
    config = fetch_storyboard_metadata(video_id)

    url_template = config["url"]
    cols = config["cols"]
    rows = config["rows"]
    frame_width = config["frame_width"]
    frame_height = config["frame_height"]
    frame_count = config["frame_count"]

    print(
        f"Found {frame_count} frames ({cols}x{rows} grid, "
        f"{frame_width}x{frame_height} each)"
    )

    frames = []
    image_idx = 0

    while len(frames) < frame_count and image_idx < max_images:
        url = url_template.replace("M0", str(image_idx)).replace("M1", str(image_idx))
        print(f"Fetching storyboard image {image_idx}...", end=" ", flush=True)

        try:
            img_data = http_get(url)
            img = Image.open(io.BytesIO(img_data))
            print("OK")
        except Exception as e:
            print(f"FAILED: {e}")
            break

        # Slice into individual frames
        for row in range(rows):
            for col in range(cols):
                if len(frames) >= frame_count:
                    break

                x = col * frame_width
                y = row * frame_height
                frame = img.crop(
                    (x, y, x + frame_width, y + frame_height)
                )
                frames.append(frame)

        image_idx += 1

    print(f"Extracted {len(frames)} frames")
    return frames[:frame_count]


def save_frames(frames: list[Image.Image], output_dir: str):
    """Save frame images to directory."""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    for i, frame in enumerate(frames):
        frame_path = output_path / f"frame_{i:04d}.png"
        frame.save(frame_path)
        if (i + 1) % 10 == 0:
            print(f"Saved {i + 1}/{len(frames)} frames", flush=True)

    print(f"All frames saved to {output_dir}")


def scrape_youtube(url: str, output_dir: str = "vance_frames", max_images: int = 100):
    """Main entry point: scrape YouTube video and save frames."""
    video_id = extract_video_id(url)
    print(f"Video ID: {video_id}")

    metadata = fetch_video_metadata(video_id)
    print(f"Title: {metadata['title']}")
    print(f"Author: {metadata['author']}")

    frames = fetch_frames(video_id, max_images=max_images)
    save_frames(frames, output_dir)

    return output_dir
