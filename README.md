# ytterm — YouTube storyboards as terminal ASCII art

Play any YouTube video's storyboard as a colored ASCII art animation, right in your terminal.

## Demo

`ytterm` playing [*Just Dance Vance*](https://youtube.com/shorts/S2GC9PxDWPI) by NostromoCore as truecolor half-block art:

![ytterm playing Just Dance Vance in the terminal](assets/demo.gif)

> The demo is rendered from the video's public storyboard frames — the same low-resolution seek-bar previews `ytterm` fetches at runtime. That's why it's pixelated: it's ~1 frame per second of source, blown up into terminal blocks. Want it smoother, sharper, or as pure text? See [Higher quality & more frames](#higher-quality--more-frames), [ASCII rendering](#ascii-rendering), and [Subject isolation](#subject-isolation).

## How it works

YouTube exposes publicly accessible **storyboard images** — the little preview thumbnails you see when hovering over the seek bar. `ytterm` fetches those from YouTube at runtime, slices them into frames, converts them to ANSI-colored character art, and animates them in your terminal.

**No video is downloaded, and no video content is stored in this repository.** Frames are fetched on your machine, from the same public endpoint your browser uses, each time you run the tool.

## Quick start

```bash
pip install Pillow

python3 ytterm.py https://www.youtube.com/watch?v=VIDEO_ID
python3 ytterm.py https://www.youtube.com/shorts/VIDEO_ID --fps 10
```

### The best-looking example

Everything turned up at once — smooth interpolated motion, an upscaled and sharpened source, punchier color, and the detailed ASCII ramp at a high frame rate:

```bash
python3 ytterm.py https://youtube.com/shorts/S2GC9PxDWPI \
    --ascii --charset standard \
    --interpolate 4 --upscale 2 --sharpen \
    --saturation 1.3 --contrast 1.1 \
    --fps 24
```

Prefer colored blocks over text? Swap `--ascii --charset standard` for `--renderer chafa` (or just drop those flags to auto-detect chafa). To drop the background entirely and loop just the dancer:

```bash
pip install rembg onnxruntime
python3 ytterm.py https://youtube.com/shorts/S2GC9PxDWPI \
    --isolate --alpha-matting --feather 1.5 \
    --interpolate 4 --upscale 2 --fps 24
```

Press **Ctrl+C** to stop.

## Options

| Flag | Description | Default |
|------|-------------|---------|
| `--fps N` | Playback speed in frames per second | 8 |
| `--width N` | Output width in columns | terminal width |
| `--height N` | Output height in rows | terminal height |
| `--level N` | Storyboard quality level (0 = lowest) | highest available |
| `--max-images N` | Max storyboard tile images to fetch | 100 |
| `--no-loop` | Play once and exit | loops forever |
| **Rendering** | | |
| `--renderer MODE` | `auto`, `chafa`, `halfblock`, or `ascii` | auto |
| `--ascii` | Shortcut for `--renderer ascii` (true ASCII text) | off |
| `--charset NAME` | ASCII ramp: `simple`, `standard`, or `blocks` | standard |
| `--no-color` | Monochrome ASCII output | color |
| `--no-chafa` | Force the built-in renderer | uses chafa if installed |
| **Quality & frames** | | |
| `--interpolate N` | Synthesize N frames per source frame (smoother motion) | 1 (off) |
| `--upscale F` | LANCZOS-upscale source frames by factor F | 1.0 |
| `--sharpen` | Unsharp mask to recover apparent detail | off |
| `--contrast M` | Contrast multiplier | 1.0 |
| `--saturation M` | Color saturation multiplier | 1.0 |
| **Isolation** | | |
| `--isolate` | Remove background, keep only the largest person/subject | off |
| `--isolate-model M` | rembg model (`u2net`, `u2netp`, `isnet-general-use`, …) | u2net_human_seg |
| `--alpha-matting` | Refine cutout edges (cleaner hair/soft edges) | off |
| `--feather R` | Feather the mask edge by Gaussian radius R | 0 |
| `--keep-all` | Keep every foreground blob, not just the largest | off |

## Higher quality & more frames

Storyboards are tiny and arrive at roughly one frame per second, so `ytterm` can rebuild both the resolution and the motion:

- **More frames** — `--interpolate N` synthesizes `N-1` crossfaded in-between frames for every pair of source frames, turning a slideshow into fluid animation. `--interpolate 3` triples the frame count; combine with `--fps` to taste.
- **Sharper picture** — `--upscale 2 --sharpen` LANCZOS-upscales each frame and applies an unsharp mask before it's knocked down to character cells, recovering a surprising amount of apparent detail. `--contrast` and `--saturation` grade the colors.
- **Best backend** — when [chafa](https://hpjansson.org/chafa/) is present it now renders in full truecolor with ordered dithering; otherwise the built-in truecolor half-block renderer is used.

## ASCII rendering

Pass `--ascii` (or `--renderer ascii`) for the classic text-art look: each cell's brightness is mapped to a character on a dark→light ramp and tinted with that cell's truecolor. Pick the ramp with `--charset`:

- `simple` — ` .:-=+*#%@` (10 levels, bold and readable)
- `standard` — a 70-character ramp with fine tonal gradation (default)
- `blocks` — Unicode shade blocks ` ░▒▓█` for a denser fill

Add `--no-color` for monochrome terminals. The renderer accounts for the ~2:1 height/width of terminal cells so the picture keeps its proportions.

## Subject isolation

With `--isolate`, each frame is run through [rembg](https://github.com/danielgatis/rembg)'s human-segmentation model (U²-Net). The largest connected foreground blob is kept and everything else becomes transparent, so the terminal background shows through and you see just the subject looping.

For cleaner cutouts:

- `--alpha-matting` refines soft edges like hair.
- `--feather R` blurs the mask edge by radius `R` so the subject composites onto the terminal background without a hard, aliased fringe.
- `--isolate-model` swaps in a different rembg model (e.g. `isnet-general-use` for non-human subjects).
- `--keep-all` retains every foreground blob instead of only the largest subject.

First run downloads the model (~176 MB) to `~/.u2net/`. Subsequent runs are instant.

## Rendering

Three renderers are supported (pick with `--renderer`, or let `auto` decide):

- **[chafa](https://hpjansson.org/chafa/)** (optional, auto-detected) — highest quality, uses block/border symbols with full truecolor and ordered dithering. Install with `sudo apt install chafa` or `brew install chafa`.
- **Built-in half-block renderer** — zero extra dependencies beyond Pillow, renders with truecolor U+2580 half blocks.
- **Built-in ASCII renderer** (`--ascii`) — maps brightness to text characters, tinted with truecolor. See [ASCII rendering](#ascii-rendering).

## Requirements

- Python 3.8+
- [Pillow](https://pypi.org/project/Pillow/) (`pip install Pillow`)
- [chafa](https://hpjansson.org/chafa/) (optional, for nicer output)
- [rembg](https://pypi.org/project/rembg/) + onnxruntime (optional, only for `--isolate`)

## Notes & limitations

- Storyboards are low-resolution preview images (~1 frame per second of source video), so playback has a stylized, pixelated aesthetic — that's the charm. `--interpolate`, `--upscale`, and `--sharpen` smooth and sharpen it if you want more.
- Works for most public videos. Private, age-restricted, or region-locked videos won't expose a storyboard.
- This tool does not download, decrypt, or redistribute video streams. It only reads the public seek-bar preview images YouTube serves to every visitor.

## License

MIT — see [LICENSE](LICENSE). Video content referenced belongs to its respective creators.
