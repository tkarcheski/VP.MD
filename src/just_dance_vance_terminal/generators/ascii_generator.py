"""
ASCII art generation for DJ Vance animations.

Generates ASCII frames procedurally and can be enhanced with unsloth-based fine-tuning.
"""

import random
from pathlib import Path


# Vance ASCII templates - high-detail animated dance poses
VANCE_POSES = [
    # Pose 1: Left sweep with raised arms
    """
              ╔═══╗
              ║ • │ │
              ╚═══╝
              │╱│╲
             │  │  │
             │ ╱ ╲ │
            │ │   │ │
           ╱ │     │ ╲
          │  │     │  │
         ╱   ╲     ╱   ╲
        │     ╲   ╱     │
        │      ╲ ╱      │
        │       ╲       │
        │        ║       │
       ╱         ║         ╲
      │╱╲        ║        ╱╲│
     │   ╲       ║       ╱   │
     │   ╱╲      ║      ╱╲   │
     │  ╱  ╲╱╲╱╲╱╲╱╱╲╱╲╱  ╲  │
    """,
    # Pose 2: Right sweep
    """
               ╔═══╗
               ║ • │ │
               ╚═══╝
               │╲│╱
              │  │  │
              │ ╱ ╲ │
             │ │   │ │
            ╱ │     │ ╲
           │  │     │  │
          ╱   ╲     ╱   ╲
         │     ╲   ╱     │
         │      ╲ ╱      │
         │       ║       │
         │       ║       │
        ╱        ║        ╲
       │╱╲       ║        ╱╲│
      │   ╲      ║       ╱   │
      │   ╱╲     ║      ╱╲   │
      │  ╱  ╲╱╲╱╲╲╱╱╲╱╲╱  ╲  │
    """,
    # Pose 3: Jump with hands up
    """
               ╔═══╗
              ╱║ • │ │╲
             ╱ ╚═══╝  ╲
            │  │ ║ │   │
            │  │ ║ │   │
           │   │ ║ │   │
          ╱    │ ║ │    ╲
         │     │ ║ │     │
         │  ╱╲ │ ║ │ ╱╲  │
        │  │  │╱╲║╱╲│  │  │
        │  │  │  ║  │  │  │
        │  ╲╱  ╱ ║ ╲  ╲╱  │
         ╲      ╱  ║  ╲      ╱
          ╲    ╱   ║   ╲    ╱
           ╲  ╱    ║    ╲  ╱
            ╲╱╱╱╱╱╱║╱╱╱╱╲╱╱
    """,
    # Pose 4: Hip thrust forward
    """
                ╔═══╗
                ║ • │
                ╚═══╝
               ╱│ ║ │╲
              │ │ ║ │ │
              │ │ ║ │ │
             │  │ ║ │  │
            ╱   │ ║ │   ╲
           │    │ ║ │    │
          ╱    ╱╲║╱╲    ╲
         │    │  ║  │    │
         │   ╱╲ ║ ╱╲   │
        │    │  ║  │    │
        │   ╱ ╲ ║ ╱ ╲   │
        │  │   ╲║╱   │  │
         ╲ │    ║    │ ╱
          ╲│   ╱ ╲   │╱
           ╲  ╱   ╲  ╱
            ╲╱     ╲╱
    """,
    # Pose 5: Full body twist
    """
              ╔═══╗
             ╱║ • │║╲
            │ ╚═══╝ │
            │  ╱║╲  │
           │  ╱ ║ ╲  │
          │  │  ║  │  │
         │   │  ║  │   │
        │    │╱╲║╱╲│    │
       ╱     │  ║  │     ╲
      │     ╱   ║   ╲     │
      │    │    ║    │    │
     │    ╱     ║     ╲    │
     │   │      ║      │   │
     │   │      ║      │   │
      ╲  │╱╲   ╱╱╲   ╱╲│  ╱
       ╲ │  │  │  │  │  │ ╱
        ╲│  │╱ ║ ╲│  │  │╱
         ╲ ╱  ╱ ║ ╲  ╲ ╱
          ╱  ╱   ║   ╲  ╲
    """,
    # Pose 6: One leg up kick
    """
              ╔═══╗
              ║ • │
              ╚═══╝
             │╱ ║ ╲│
            │   ║   │
           │    ║    │
          │  ╱╲║╱╲  │
         │  │  ║  │  │
         │  │  ║  │  │
        │   ╲ ║ ╱   │
        │    ╲║╱    │
        │     ║     │
         │    ║    │
         │   ╱╲   │
          ╲ ╱  ╲ ╱
           │    │
           │    │  ← FLYING
           │    │
          ╱╲╱╲╱╲╱╲
    """,
]

ROAST_LINES = [
    "VANCE IS DANCING",
    "DJ VANCE MOMENT",
    "THE LEGEND HIMSELF",
    "ABSOLUTELY UNHINGED",
    "VIBE CHECK: FAILED",
    "RESPECT THE RHYTHM",
    "TOUCH GRASS VANCE",
    "THIS IS ART",
    "CERTIFIED DANCER",
    "BUSSIN BUSSIN",
]


def generate_text_frame(text: str, width: int = 80, height: int = 20) -> str:
    """Generate a simple text-based ASCII frame."""
    lines = []

    # Top padding
    lines.extend([""] * (height // 2 - 2))

    # Centered text
    for word in text.split():
        centered = word.center(width)
        lines.append(centered)

    # Bottom padding
    lines.extend([""] * (height // 2))

    return "\n".join(lines[:height])


def generate_vance_frame(
    pose_idx: int = 0, roast: str = "", width: int = 80, height: int = 20
) -> str:
    """
    Generate a Vance ASCII art frame.

    Args:
        pose_idx: Which pose to use (0-3)
        roast: Optional roast text to include
        width: Terminal width
        height: Terminal height
    """
    pose = VANCE_POSES[pose_idx % len(VANCE_POSES)]
    pose_lines = pose.strip().split("\n")

    frame_lines = []

    # Top padding
    padding_top = max(0, (height - len(pose_lines) - 3) // 2)
    frame_lines.extend([""] * padding_top)

    # Add the pose
    for line in pose_lines:
        frame_lines.append(line.center(width))

    # Add roast text below
    if roast:
        frame_lines.append("")
        frame_lines.append(roast.center(width))

    # Ensure we fill the frame
    while len(frame_lines) < height:
        frame_lines.append("")

    return "\n".join(frame_lines[:height])


def generate_animation(
    frames: int = 30,
    width: int = 80,
    height: int = 20,
    roast: bool = True,
) -> list[str]:
    """
    Generate a sequence of ASCII frames for animation.

    Args:
        frames: Number of frames to generate
        width: Terminal width
        height: Terminal height
        roast: Include roast text

    Returns:
        List of ASCII frame strings
    """
    animation = []

    for i in range(frames):
        pose_idx = i % len(VANCE_POSES)
        roast_text = random.choice(ROAST_LINES) if roast else ""

        frame = generate_vance_frame(
            pose_idx=pose_idx,
            roast=roast_text,
            width=width,
            height=height,
        )
        animation.append(frame)

    return animation


def save_ascii_frames(
    frames: list[str],
    output_dir: str = "vance_ascii_frames",
) -> str:
    """
    Save ASCII frames as text files (for animation playback).

    Args:
        frames: List of ASCII frame strings
        output_dir: Directory to save frames

    Returns:
        Path to output directory
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    for i, frame in enumerate(frames):
        frame_file = output_path / f"frame_{i:04d}.txt"
        frame_file.write_text(frame)

        if (i + 1) % 10 == 0:
            print(f"Generated {i + 1}/{len(frames)} ASCII frames")

    print(f"All frames saved to {output_dir}")
    return output_dir


def generate_and_save(
    frames: int = 30,
    output_dir: str = "vance_ascii_frames",
    width: int = 80,
    height: int = 20,
) -> str:
    """Generate ASCII animation and save to directory."""
    print(f"Generating {frames} ASCII frames for Vance...")
    animation = generate_animation(frames=frames, width=width, height=height)
    return save_ascii_frames(animation, output_dir)
