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
    python3 ytterm.py URL --ascii                  # render as true ASCII characters
    python3 ytterm.py URL --interpolate 3          # 3x smoother: synthesize in-between frames
    python3 ytterm.py URL --upscale 2 --sharpen    # crisper, higher-quality frames
    python3 ytterm.py URL --isolate --alpha-matting --feather 1.5   # clean subject cutout

Requirements:
    - Python 3.8+
    - Pillow  (pip install Pillow)
    - chafa   (optional, used automatically for higher-quality block rendering)
    - rembg   (optional, only needed for --isolate:  pip install rembg onnxruntime)

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
    from PIL import Image, ImageFilter, ImageEnhance
except ImportError:
    print("Pillow is required: pip install Pillow", file=sys.stderr)
    sys.exit(1)

# rembg is only imported lazily inside isolate_subject().

UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)

# ASCII luminance ramps, ordered dark -> light. Longer ramps carry more tonal
# detail; "blocks" uses Unicode shade blocks for a denser, higher-quality look.
ASCII_RAMPS = {
    "simple":   " .:-=+*#%@",
    "standard": " .'`^\",:;Il!i><~+_-?][}{1)(|\\/tfjrxnuvczXYUJCLQ0OZmwqpdbkhao*#MW&8%B@$",
    "blocks":   " ░▒▓█",
}


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


def download_frames(sb: dict, level_idx: int = -1, max_images: int = 100) -> list:
    """Download storyboard images for a level and slice into PIL frames.

    The highest level (the default) packs the most tiles per image and the
    largest tile resolution, so it yields both the most frames and the best
    quality source material.
    """
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
# Frame enhancement:  more frames + higher quality
# --------------------------------------------------------------------------

def enhance_frames(frames: list, upscale: float = 1.0, sharpen: bool = False,
                   contrast: float = 1.0, saturation: float = 1.0) -> list:
    """Upscale (LANCZOS), sharpen and punch up frames for a crisper look.

    Storyboards are tiny, so a gentle LANCZOS upscale plus an unsharp mask
    recovers a surprising amount of apparent detail before the frames are
    knocked down to character cells.
    """
    if upscale <= 1.0 and not sharpen and contrast == 1.0 and saturation == 1.0:
        return frames
    out = []
    for fr in frames:
        img = fr
        if upscale > 1.0:
            w, h = img.size
            img = img.resize((max(1, int(w * upscale)),
                              max(1, int(h * upscale))), Image.LANCZOS)
        if contrast != 1.0:
            img = ImageEnhance.Contrast(img).enhance(contrast)
        if saturation != 1.0:
            img = ImageEnhance.Color(img).enhance(saturation)
        if sharpen:
            img = img.filter(ImageFilter.UnsharpMask(radius=2, percent=120,
                                                     threshold=2))
        out.append(img)
    return out


def interpolate_frames(frames: list, factor: int) -> list:
    """Synthesize `factor - 1` crossfaded frames between each pair of source
    frames, multiplying the effective frame count for smoother motion.

    Storyboards are ~1 fps, so this is what turns a slideshow into animation.
    A linear crossfade is cheap and, for the small motions between adjacent
    seek-bar previews, reads as convincing in-between motion.
    """
    if factor <= 1 or len(frames) < 2:
        return frames
    out = []
    for i in range(len(frames) - 1):
        a = frames[i].convert("RGB")
        b = frames[i + 1].convert("RGB")
        if a.size != b.size:
            b = b.resize(a.size, Image.LANCZOS)
        out.append(frames[i])
        for k in range(1, factor):
            out.append(Image.blend(a, b, k / factor))
    out.append(frames[-1])
    return out


# --------------------------------------------------------------------------
# Subject isolation
# --------------------------------------------------------------------------

_REMBG_SESSION = None
_REMBG_MODEL = None


def _get_rembg_session(model: str = "u2net_human_seg"):
    """Lazy-load a rembg session. u2net_human_seg is tuned for people."""
    global _REMBG_SESSION, _REMBG_MODEL
    if _REMBG_SESSION is not None and _REMBG_MODEL == model:
        return _REMBG_SESSION
    try:
        from rembg import new_session  # type: ignore
    except ImportError as e:
        raise RuntimeError(
            "--isolate requires rembg. Install with: pip install rembg onnxruntime"
        ) from e
    _REMBG_SESSION = new_session(model)
    _REMBG_MODEL = model
    return _REMBG_SESSION


def _largest_component_mask(alpha: Image.Image) -> Image.Image:
    """
    Keep only the largest connected foreground blob in an alpha mask.
    Ensures we isolate *one* subject, not scattered background noise.
    Pure-Pillow flood-fill BFS — no numpy/scipy required.
    """
    w, h = alpha.size
    px = alpha.load()
    # Binarize
    thresh = 128
    visited = bytearray(w * h)
    best_pixels: list = []
    best_size = 0

    for start_y in range(h):
        for start_x in range(w):
            idx0 = start_y * w + start_x
            if visited[idx0] or px[start_x, start_y] < thresh:
                continue
            # BFS
            stack = [(start_x, start_y)]
            pixels = []
            visited[idx0] = 1
            while stack:
                x, y = stack.pop()
                pixels.append((x, y))
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < w and 0 <= ny < h:
                        nidx = ny * w + nx
                        if not visited[nidx] and px[nx, ny] >= thresh:
                            visited[nidx] = 1
                            stack.append((nx, ny))
            if len(pixels) > best_size:
                best_size = len(pixels)
                best_pixels = pixels

    if not best_pixels:
        return alpha

    out = Image.new("L", (w, h), 0)
    op = out.load()
    for x, y in best_pixels:
        op[x, y] = px[x, y]  # keep original soft alpha for this blob
    return out


def isolate_subject(frame: Image.Image, keep_largest: bool = True,
                    model: str = "u2net_human_seg",
                    alpha_matting: bool = False, feather: float = 0.0) -> Image.Image:
    """
    Remove background from `frame` using a rembg segmentation model.
    Returns an RGBA image where non-subject pixels have alpha=0.

    alpha_matting refines the cutout edge (great for hair/soft edges); feather
    applies a small Gaussian blur to the alpha channel so the isolated subject
    composites onto the terminal background without a hard, aliased fringe.
    """
    from rembg import remove  # type: ignore
    session = _get_rembg_session(model)
    kwargs = {}
    if alpha_matting:
        kwargs.update(
            alpha_matting=True,
            alpha_matting_foreground_threshold=240,
            alpha_matting_background_threshold=10,
            alpha_matting_erode_size=10,
        )
    result = remove(frame.convert("RGB"), session=session, **kwargs).convert("RGBA")
    if keep_largest or feather > 0:
        r, g, b, a = result.split()
        if keep_largest:
            a = _largest_component_mask(a)
        if feather > 0:
            a = a.filter(ImageFilter.GaussianBlur(feather))
        result = Image.merge("RGBA", (r, g, b, a))
    return result


# --------------------------------------------------------------------------
# Rendering
# --------------------------------------------------------------------------

def render_chafa(frame: Image.Image, width: int, height: int) -> str:
    """Render via chafa (best quality). Preserves alpha if present."""
    buf = io.BytesIO()
    frame.save(buf, format="PNG")
    cmd = ["chafa", "--colors=full", "--symbols=block+border+space",
           "--dither=ordered", f"--size={width}x{height}"]
    if frame.mode == "RGBA":
        cmd += ["--bg=none"]
    cmd.append("-")
    result = subprocess.run(cmd, input=buf.getvalue(), capture_output=True)
    if result.returncode != 0:
        # Older chafa builds reject --colors=full / --dither; retry conservatively.
        cmd_fallback = ["chafa", "--colors=240",
                        "--symbols=block+border+space", f"--size={width}x{height}"]
        if frame.mode == "RGBA":
            cmd_fallback += ["--bg=none"]
        cmd_fallback.append("-")
        result = subprocess.run(cmd_fallback, input=buf.getvalue(),
                                capture_output=True)
        if result.returncode != 0:
            raise RuntimeError(result.stderr.decode()[:200])
    return result.stdout.decode()


def render_halfblock(frame: Image.Image, width: int, height: int) -> str:
    """
    Built-in truecolor renderer using U+2580 half blocks (no chafa needed).
    Honors RGBA alpha: fully-transparent pixels render as a plain space so
    the terminal background shows through.
    """
    has_alpha = frame.mode == "RGBA"
    if not has_alpha:
        frame = frame.convert("RGB")

    px_h = height * 2
    src_w, src_h = frame.size
    scale = min(width / src_w, px_h / src_h)
    w = max(1, int(src_w * scale))
    h = max(2, int(src_h * scale) // 2 * 2)
    img = frame.resize((w, h), Image.LANCZOS)
    px = img.load()

    lines = []
    for y in range(0, h, 2):
        row = []
        for x in range(w):
            if has_alpha:
                r1, g1, b1, a1 = px[x, y]
                r2, g2, b2, a2 = px[x, y + 1]
            else:
                r1, g1, b1 = px[x, y]
                r2, g2, b2 = px[x, y + 1]
                a1 = a2 = 255

            top_vis = a1 >= 128
            bot_vis = a2 >= 128

            if not top_vis and not bot_vis:
                row.append("\x1b[0m ")
            elif top_vis and bot_vis:
                row.append(
                    f"\x1b[38;2;{r1};{g1};{b1}m\x1b[48;2;{r2};{g2};{b2}m▀"
                )
            elif top_vis:
                # top pixel visible, bottom transparent → upper half block, no bg
                row.append(f"\x1b[0m\x1b[38;2;{r1};{g1};{b1}m▀")
            else:
                # bottom pixel visible, top transparent → lower half block, no bg
                row.append(f"\x1b[0m\x1b[38;2;{r2};{g2};{b2}m▄")
        row.append("\x1b[0m")
        lines.append("".join(row))
    return "\n".join(lines)


def render_ascii(frame: Image.Image, width: int, height: int,
                 ramp: str = ASCII_RAMPS["standard"], color: bool = True) -> str:
    """
    Built-in ASCII renderer: maps each cell's luminance to a character from a
    dark→light ramp, optionally tinted with the cell's truecolor.

    This is the "real ASCII" look — text glyphs, not blocks. Terminal cells are
    about twice as tall as they are wide, so the image is sampled at half the
    vertical rate to keep the aspect ratio correct.
    """
    has_alpha = frame.mode == "RGBA"
    if not has_alpha:
        frame = frame.convert("RGB")

    cell_aspect = 0.5  # width/height of a character cell
    src_w, src_h = frame.size
    scale = min(width / src_w, height / (src_h * cell_aspect))
    w = max(1, int(src_w * scale))
    h = max(1, int(src_h * scale * cell_aspect))
    img = frame.resize((w, h), Image.LANCZOS)
    px = img.load()

    n = len(ramp) - 1
    lines = []
    for y in range(h):
        row = []
        for x in range(w):
            if has_alpha:
                r, g, b, a = px[x, y]
                if a < 128:
                    row.append(" ")
                    continue
            else:
                r, g, b = px[x, y]
            lum = (0.2126 * r + 0.7152 * g + 0.0722 * b) / 255.0
            ch = ramp[max(0, min(n, int(lum * n + 0.5)))]
            if color:
                row.append(f"\x1b[38;2;{r};{g};{b}m{ch}")
            else:
                row.append(ch)
        if color:
            row.append("\x1b[0m")
        lines.append("".join(row))
    return "\n".join(lines)


def render_frames(
    frames: list,
    width: int,
    height: int,
    renderer: str,
    ramp: str = ASCII_RAMPS["standard"],
    color: bool = True,
    isolate: bool = False,
    isolate_opts: dict = None,
) -> list:
    isolate_opts = isolate_opts or {}
    rendered = []
    total = len(frames)
    for i, frame in enumerate(frames):
        label = "Isolating" if isolate else "Rendering"
        sys.stderr.write(f"\r{label} frame {i + 1}/{total}...")
        sys.stderr.flush()
        img = isolate_subject(frame, **isolate_opts) if isolate else frame
        if renderer == "chafa":
            rendered.append(render_chafa(img, width, height))
        elif renderer == "ascii":
            rendered.append(render_ascii(img, width, height, ramp=ramp, color=color))
        else:
            rendered.append(render_halfblock(img, width, height))
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
    parser.add_argument("--max-images", type=int, default=100,
                        help="max storyboard tile images to fetch (default: 100)")
    parser.add_argument("--no-loop", action="store_true", help="play once and exit")

    # Renderer selection ----------------------------------------------------
    parser.add_argument("--renderer", choices=["auto", "chafa", "halfblock", "ascii"],
                        default="auto",
                        help="rendering backend (default: auto — chafa if installed, "
                             "else half-block)")
    parser.add_argument("--ascii", dest="ascii_mode", action="store_true",
                        help="shortcut for --renderer ascii (true ASCII characters)")
    parser.add_argument("--charset", choices=list(ASCII_RAMPS.keys()),
                        default="standard",
                        help="ASCII ramp for --ascii (default: standard)")
    parser.add_argument("--no-color", action="store_true",
                        help="monochrome output for the ASCII renderer")
    parser.add_argument("--no-chafa", action="store_true",
                        help="force the built-in renderer even if chafa is installed")

    # Quality / more frames -------------------------------------------------
    parser.add_argument("--interpolate", type=int, default=1, metavar="N",
                        help="synthesize N frames per source frame for smoother "
                             "motion (default: 1 = off; try 2-4)")
    parser.add_argument("--upscale", type=float, default=1.0, metavar="F",
                        help="LANCZOS-upscale source frames by factor F before "
                             "rendering, for a crisper image (default: 1.0)")
    parser.add_argument("--sharpen", action="store_true",
                        help="apply an unsharp mask to recover apparent detail")
    parser.add_argument("--contrast", type=float, default=1.0,
                        help="contrast multiplier (1.0 = unchanged)")
    parser.add_argument("--saturation", type=float, default=1.0,
                        help="color saturation multiplier (1.0 = unchanged)")

    # Subject isolation -----------------------------------------------------
    parser.add_argument("--isolate", action="store_true",
                        help="remove the background and keep only the largest "
                             "foreground person/subject (requires rembg)")
    parser.add_argument("--isolate-model", default="u2net_human_seg",
                        help="rembg model for --isolate (e.g. u2net, u2netp, "
                             "isnet-general-use; default: u2net_human_seg)")
    parser.add_argument("--alpha-matting", action="store_true",
                        help="refine isolation edges with alpha matting "
                             "(cleaner hair/soft edges; slower)")
    parser.add_argument("--feather", type=float, default=0.0, metavar="R",
                        help="feather the isolation mask edge by Gaussian radius R "
                             "for smoother compositing (default: 0)")
    parser.add_argument("--keep-all", action="store_true",
                        help="with --isolate, keep every foreground blob instead "
                             "of only the largest subject")
    args = parser.parse_args()

    # Resolve renderer choice, honoring the legacy flags.
    if args.ascii_mode:
        renderer = "ascii"
    elif args.renderer != "auto":
        renderer = args.renderer
    elif args.no_chafa:
        renderer = "halfblock"
    else:
        renderer = "chafa" if shutil.which("chafa") is not None else "halfblock"

    if renderer == "chafa" and shutil.which("chafa") is None:
        print("chafa not found on PATH; falling back to the built-in half-block "
              "renderer.", file=sys.stderr)
        renderer = "halfblock"

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
    frames = download_frames(sb, level_idx=args.level, max_images=args.max_images)
    print(f"Extracted {len(frames)} source frames.")

    # Higher quality: upscale / sharpen / grade before rendering.
    frames = enhance_frames(frames, upscale=args.upscale, sharpen=args.sharpen,
                            contrast=args.contrast, saturation=args.saturation)

    # More frames: synthesize in-between frames for smoother motion.
    if args.interpolate > 1:
        before = len(frames)
        frames = interpolate_frames(frames, args.interpolate)
        print(f"Interpolated {before} -> {len(frames)} frames "
              f"({args.interpolate}x).")

    renderer_label = {
        "chafa": "chafa (block/border, truecolor)",
        "halfblock": "built-in half-block (truecolor)",
        "ascii": f"built-in ASCII ({args.charset} ramp)",
    }[renderer]
    print(f"Renderer: {renderer_label}"
          + (" + subject isolation (rembg)" if args.isolate else ""))

    isolate_opts = {
        "keep_largest": not args.keep_all,
        "model": args.isolate_model,
        "alpha_matting": args.alpha_matting,
        "feather": args.feather,
    }
    if args.isolate:
        _get_rembg_session(args.isolate_model)  # trigger model download up-front

    rendered = render_frames(
        frames, width, height, renderer,
        ramp=ASCII_RAMPS[args.charset], color=not args.no_color,
        isolate=args.isolate, isolate_opts=isolate_opts,
    )

    play(rendered, meta, fps=args.fps, loop=not args.no_loop)


if __name__ == "__main__":
    main()
