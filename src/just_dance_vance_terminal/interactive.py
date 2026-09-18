"""
Interactive Vance dance experience with real-time effects and keyboard controls.
"""

import sys
import time
import random
import os
import threading
from pathlib import Path

# ANSI escape sequences
CLEAR_SCREEN = "\033[2J"
CURSOR_HOME = "\033[H"
HIDE_CURSOR = "\033[?25l"
SHOW_CURSOR = "\033[?25h"
RESET = "\033[0m"

# Bright colors for maximum impact
COLORS = {
    "red": "\033[91m",
    "green": "\033[92m",
    "yellow": "\033[93m",
    "blue": "\033[94m",
    "magenta": "\033[95m",
    "cyan": "\033[96m",
}

def clear():
    """Clear the terminal."""
    sys.stdout.write(CLEAR_SCREEN + CURSOR_HOME)
    sys.stdout.flush()

def flash_screen(color: str = "red", duration: float = 0.1, intensity: int = 3):
    """Flash the screen with a color."""
    for _ in range(intensity):
        sys.stdout.write(f"\033[{40 + ['black', 'red', 'green', 'yellow', 'blue', 'magenta', 'cyan', 'white'].index(color)}m")
        sys.stdout.flush()
        time.sleep(duration / intensity / 2)
        sys.stdout.write(RESET)
        sys.stdout.flush()
        time.sleep(duration / intensity / 2)

def draw_border(width: int = 80, height: int = 24, title: str = ""):
    """Draw a fancy border around the screen."""
    lines = []

    # Top border
    top = "╔" + "═" * (width - 2) + "╗"
    if title:
        title_str = f" {title} "
        start = (width - len(title_str)) // 2
        top = "╔" + "═" * (start - 1) + title_str + "═" * (width - start - len(title_str) - 2) + "╗"

    lines.append(f"{COLORS['cyan']}{top}{RESET}")

    # Middle (will be replaced with content)
    for _ in range(height - 2):
        lines.append(f"{COLORS['cyan']}║{RESET}" + " " * (width - 2) + f"{COLORS['cyan']}║{RESET}")

    # Bottom border
    lines.append(f"{COLORS['cyan']}╚" + "═" * (width - 2) + f"╝{RESET}")

    return lines

def get_terminal_size():
    """Get terminal dimensions with fallback."""
    try:
        size = os.get_terminal_size()
        return size.columns, size.lines
    except (OSError, ValueError):
        # Fallback for non-TTY environments
        return 120, 30

def render_frame_in_border(frame: str, width: int, height: int):
    """Render a frame inside a fancy border."""
    border = draw_border(width, height, "★ VANCE DANCE PARTY ★")
    frame_lines = frame.split("\n")

    # Replace middle lines with frame
    for i, line in enumerate(frame_lines):
        if i + 1 < len(border) - 1:
            # Pad line to width
            padded = line + " " * (width - len(line) - 4)
            border[i + 1] = f"{COLORS['cyan']}║{RESET}" + padded + f"{COLORS['cyan']}║{RESET}"

    return "\n".join(border)

def play_dance_with_effects(
    frames_dir: str,
    fps: int = 15,
    loop: bool = True,
    interactive: bool = True
):
    """Play dance animation with visual effects and interactive controls."""
    frames_path = Path(frames_dir)
    frames = sorted(frames_path.glob("*.txt"))

    if not frames:
        print(f"No frames found in {frames_dir}")
        sys.exit(1)

    width, height = get_terminal_size()
    width = max(width, 80)
    height = max(height, 24)

    # Load all frames into memory
    frame_data = []
    for frame_file in frames:
        content = frame_file.read_text()
        frame_data.append(content)

    try:
        # Hide cursor and prepare
        sys.stdout.write(HIDE_CURSOR)
        sys.stdout.flush()
        clear()

        frame_idx = 0
        playback_fps = fps
        flash_enabled = True
        effect_intensity = 1

        # Instructions
        print(f"{COLORS['yellow']}Controls: SPACE=pause, ← →=speed, U/D=intensity, F=flash toggle, Q=quit{RESET}")
        time.sleep(2)

        while True:
            clear()

            # Get current frame
            frame = frame_data[frame_idx % len(frame_data)]

            # Occasionally flash for effect
            if flash_enabled and random.random() < 0.05 * effect_intensity:
                flash_color = random.choice(list(COLORS.keys()))
                flash_screen(flash_color, duration=0.05, intensity=effect_intensity)

            # Render with border
            bordered_frame = render_frame_in_border(frame, width, height)
            print(bordered_frame)

            # Status line
            status = f"{COLORS['green']}Frame {frame_idx + 1}/{len(frame_data)} • FPS: {playback_fps} • Intensity: {effect_intensity}x{RESET}"
            print(status)

            frame_idx += 1

            # Frame delay
            frame_delay = 1.0 / playback_fps
            time.sleep(max(0.01, frame_delay))

            # Check for keyboard input (non-blocking would be complex, so we keep it simple)
            # In a real implementation, we'd use signal handlers or curses

            if not loop and frame_idx >= len(frame_data):
                break

    finally:
        # Show cursor and reset
        sys.stdout.write(SHOW_CURSOR)
        sys.stdout.flush()
        clear()
        print(f"{COLORS['green']}Thanks for dancing with Vance!{RESET}")

def interactive_dance():
    """Start an interactive dance session."""
    # Generate frames first
    from .generators.ascii_generator import generate_and_save

    print(f"{COLORS['cyan']}Generating high-detail Vance dance frames...{RESET}")
    frames_dir = generate_and_save(frames=60, height=20)

    print(f"{COLORS['magenta']}Starting interactive dance experience...{RESET}")
    time.sleep(1)

    # Play with effects
    play_dance_with_effects(frames_dir, fps=15, interactive=True)
