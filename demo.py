#!/usr/bin/env python3
"""Quick demo of Vance dancing - no loops, just show the frames."""

import sys
import time
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from just_dance_vance_terminal.generators.ascii_generator import generate_and_save

def demo():
    """Generate and display a few frames without looping."""
    print("Generating Vance dance frames...")
    frames_dir = generate_and_save(frames=6, height=20)

    frames = sorted(Path(frames_dir).glob("*.txt"))

    print("\n" + "="*80)
    print("DISPLAYING DANCE FRAMES")
    print("="*80 + "\n")

    for i, frame_file in enumerate(frames):
        print(f"\n{'='*80}")
        print(f"Frame {i+1}/6")
        print(f"{'='*80}\n")

        content = frame_file.read_text()
        print(content)

        time.sleep(0.8)

if __name__ == "__main__":
    demo()
