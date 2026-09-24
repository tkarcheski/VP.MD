# 🇺🇸 VP.MD — JD Vance Autonomous Terminal 🇺🇸

**The most patriotic terminal experience in America.** Watch JD Vance dance in colorized ASCII art. Or engage the autonomous AI agent that runs on pure American energy.

## Demo

![JD Vance Dancing in Terminal](assets/vance_dance.gif)

*Colorized ASCII animation of JD Vance dancing with roasting commentary. 30 frames at 15 FPS.*

## Features

✨ **JD Vance Dancing** — High-detail colorized ASCII animation of Vance doing full dance moves (sweeps, jumps, hip thrusts, kicks) with roasting commentary.

🤖 **Autopilot AI Agent** — Fully autonomous JD Vance AI running in continuous mode. Generates thoughts about working-class America, bootstraps, and meritocracy. Self-updates its own configuration. Speaks with voice (optional TTS).

🎨 **Full ANSI Color** — Vibrant terminal experience with cyan, magenta, yellow, red, green, and blue styling throughout.

⚙️ **Self-Updating** — The AI agent modifies its own config files and improves itself continuously.

🔊 **Voice Output** — Optional text-to-speech so Vance can speak his quips (uses `espeak` if available).

## Quick Start

### Installation

```bash
# Using uv (Python 3.13+)
git clone <repo>
cd just-dance-vance-terminal
uv sync
```

### Watch Vance Dance

```bash
uv run just-dance-vance-terminal ascii
```

Generates 60 colorized frames and animates them at 15 FPS with a fancy border, cycling through roasting commentary. Press `Ctrl+C` to stop.

### Engage Autopilot AI

```bash
# 60 second demo
uv run just-dance-vance-terminal autopilot --duration 60

# Shorter version
uv run just-dance-vance-terminal autopilot --duration 15

# With voice (if espeak installed)
uv run just-dance-vance-terminal autopilot --duration 30 --voice
```

The bot will:
- Generate autonomous JD Vance thoughts every 2-4 seconds
- Self-update its configuration (modifying `vance_config.json`)
- Occasionally speak its thoughts (if voice enabled)
- Display patriotic banners and real-time metrics
- Run continuously until the duration expires

## What the Autopilot Says

The AI generates authentic JD Vance energy:

```
★ VANCE BOT ★ We need to stop denigrating people who work with their hands!
★ VANCE BOT ★ The real America isn't on the coasts—it's in Appalachia.
★ VANCE BOT ★ Work hard, stay humble, get rich. That's the American way.
★ VANCE BOT ★ Memes are how working-class America communicates with power.
★ VANCE BOT ★ Self-improvement, constant optimization. That's peak American capitalism.
```

And self-updates with:

```
↻ SELF-UPDATE: Enhanced working-class energy detection
↻ SELF-UPDATE: Optimized bootstrap-pulling algorithm
↻ SELF-UPDATE: Increased patriotism coefficient by 0.5%
```

## ASCII Dance Poses

The dancing Vance features 6 distinct poses with smooth frame transitions:

1. **Left Sweep** — Raising arms, swaying left
2. **Right Sweep** — Swaying right  
3. **Jump** — Hands up, maximum energy
4. **Hip Thrust** — Forward momentum
5. **Twist** — Full body rotation
6. **Kick** — One leg flying

Each frame is fully colorized with detailed box-drawing characters for the body, positioned limbs, and bright ANSI colors for maximum visual impact.

## Commands

```bash
# ASCII dance animation
uv run just-dance-vance-terminal ascii

# Autonomous AI autopilot mode
uv run just-dance-vance-terminal autopilot [--duration SECONDS] [--voice]

# YouTube storyboard scraping (legacy)
uv run just-dance-vance-terminal youtube --url <URL>

# Play existing frame directory
uv run just-dance-vance-terminal play <frames_dir>
```

## Architecture

```
src/just_dance_vance_terminal/
├── __init__.py           # Main entry point
├── cli.py                # Command-line interface
├── interactive.py        # Terminal UI and effects
├── vance_agent.py        # 🤖 Autopilot AI agent (NEW)
└── generators/
    ├── ascii_generator.py      # ASCII frame generation
    ├── youtube_scraper.py      # YouTube storyboard fetcher
    └── __init__.py
```

## Configuration

The autopilot agent creates and manages `src/just_dance_vance_terminal/vance_config.json`:

```json
{
  "autopilot": true,
  "voice_enabled": true,
  "self_update_interval": 3600,
  "patriotism_level": 9001,
  "american_flag_density": "MAXIMUM",
  "last_update": "2026-09-23T..."
}
```

The agent self-modifies this file during operation.

## Requirements

- Python 3.13+
- `uv` package manager
- Optional: `espeak` for voice output (Linux: `sudo apt install espeak`)

## Notes

🇺🇸 **Full YOLO Mode** — This is a satire/parody project. The "autopilot AI" is a humorous bot that generates random JD Vance quips, not actual autonomous decision-making. Self-updating means it modifies its own JSON config, not its source code.

🎨 **Terminal Support** — Best results on modern terminals with 24-bit (truecolor) ANSI support. Works on macOS Terminal, iTerm2, GNOME Terminal, and most Linux terminals.

🔊 **Voice** — Voice output uses `espeak` (Linux) or system TTS if available. Falls back silently if unavailable.

## License

MIT — Use this to roast JD Vance in any way you see fit.

---

**Made with maximum American energy. 🦅 God bless America. 🇺🇸**
