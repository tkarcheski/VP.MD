"""
ASCII art generation for DJ Vance animations with full ANSI color support.

Creates detailed, colorized dance frames with smooth animations and visual effects.
"""

import random
from pathlib import Path

# ANSI color codes
class Colors:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"

    # Foreground
    BLACK = "\033[30m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"

    # Bright
    BRIGHT_RED = "\033[91m"
    BRIGHT_GREEN = "\033[92m"
    BRIGHT_YELLOW = "\033[93m"
    BRIGHT_BLUE = "\033[94m"
    BRIGHT_MAGENTA = "\033[95m"
    BRIGHT_CYAN = "\033[96m"
    BRIGHT_WHITE = "\033[97m"

    # Background
    BG_BLACK = "\033[40m"
    BG_RED = "\033[41m"
    BG_GREEN = "\033[42m"
    BG_YELLOW = "\033[43m"
    BG_BLUE = "\033[44m"
    BG_MAGENTA = "\033[45m"
    BG_CYAN = "\033[46m"

# High-detail Vance with color markup: {color_name}text{reset}
VANCE_POSES_COLORED = [
    # Pose 1: Left sweep with raised arms
    """
              {cyan}╔═══╗{reset}
              {cyan}║{reset} {bright_yellow}●{reset} {cyan}│ │{reset}
              {cyan}╚═══╝{reset}
              {red}│╱│╲{reset}
             {red}│{reset}  {bright_magenta}│{reset}  {red}│{reset}
             {red}│{reset} {bright_magenta}╱{reset} {bright_magenta}╲{reset} {red}│{reset}
            {red}│{reset} {bright_magenta}│{reset}   {bright_magenta}│{reset} {red}│{reset}
           {red}╱{reset} {bright_magenta}│{reset}     {bright_magenta}│{reset} {red}╲{reset}
          {red}│{reset}  {bright_magenta}│{reset}     {bright_magenta}│{reset}  {red}│{reset}
         {green}╱{reset}   {bright_magenta}╲{reset}     {bright_magenta}╱{reset}   {green}╲{reset}
        {green}│{reset}     {bright_magenta}╲{reset}   {bright_magenta}╱{reset}     {green}│{reset}
        {green}│{reset}      {bright_magenta}╲{reset} {bright_magenta}╱{reset}      {green}│{reset}
        {green}│{reset}       {bright_yellow}╲{reset}       {green}│{reset}
        {green}│{reset}        {bright_yellow}║{reset}       {green}│{reset}
       {blue}╱{reset}         {bright_yellow}║{reset}         {blue}╲{reset}
      {blue}│╱╲{reset}        {bright_yellow}║{reset}        {blue}╱╲│{reset}
     {blue}│{reset}   {bright_cyan}╲{reset}       {bright_yellow}║{reset}       {bright_cyan}╱{reset}   {blue}│{reset}
     {blue}│{reset}   {bright_cyan}╱╲{reset}      {bright_yellow}║{reset}      {bright_cyan}╱╲{reset}   {blue}│{reset}
     {blue}│{reset}  {bright_cyan}╱{reset}  {bright_cyan}╲╱╲╱╲╱╲╱╱╲╱╲╱{reset}  {bright_cyan}╲{reset}  {blue}│{reset}
    """,
    # Pose 2: Right sweep
    """
               {cyan}╔═══╗{reset}
               {cyan}║{reset} {bright_yellow}●{reset} {cyan}│ │{reset}
               {cyan}╚═══╝{reset}
               {red}│╲│╱{reset}
              {red}│{reset}  {bright_magenta}│{reset}  {red}│{reset}
              {red}│{reset} {bright_magenta}╱{reset} {bright_magenta}╲{reset} {red}│{reset}
             {red}│{reset} {bright_magenta}│{reset}   {bright_magenta}│{reset} {red}│{reset}
            {red}╱{reset} {bright_magenta}│{reset}     {bright_magenta}│{reset} {red}╲{reset}
           {red}│{reset}  {bright_magenta}│{reset}     {bright_magenta}│{reset}  {red}│{reset}
          {green}╱{reset}   {bright_magenta}╲{reset}     {bright_magenta}╱{reset}   {green}╲{reset}
         {green}│{reset}     {bright_magenta}╲{reset}   {bright_magenta}╱{reset}     {green}│{reset}
         {green}│{reset}      {bright_magenta}╲{reset} {bright_magenta}╱{reset}      {green}│{reset}
         {green}│{reset}       {bright_yellow}║{reset}       {green}│{reset}
         {green}│{reset}       {bright_yellow}║{reset}       {green}│{reset}
        {blue}╱{reset}        {bright_yellow}║{reset}        {blue}╲{reset}
       {blue}│╱╲{reset}       {bright_yellow}║{reset}        {blue}╱╲│{reset}
      {blue}│{reset}   {bright_cyan}╲{reset}      {bright_yellow}║{reset}       {bright_cyan}╱{reset}   {blue}│{reset}
      {blue}│{reset}   {bright_cyan}╱╲{reset}     {bright_yellow}║{reset}      {bright_cyan}╱╲{reset}   {blue}│{reset}
      {blue}│{reset}  {bright_cyan}╱{reset}  {bright_cyan}╲╱╲╱╲╲╱╱╲╱╲╱{reset}  {bright_cyan}╲{reset}  {blue}│{reset}
    """,
    # Pose 3: Jump with hands up
    """
               {cyan}╔═══╗{reset}
              {bright_yellow}╱{cyan}║{reset} {bright_yellow}●{reset} {cyan}│{reset} {bright_yellow}│╲{reset}
             {bright_yellow}╱{reset} {cyan}╚═══╝{reset}  {bright_yellow}╲{reset}
            {red}│{reset}  {red}│{reset} {bright_yellow}║{reset} {red}│{reset}   {red}│{reset}
            {red}│{reset}  {red}│{reset} {bright_yellow}║{reset} {red}│{reset}   {red}│{reset}
           {red}│{reset}   {red}│{reset} {bright_yellow}║{reset} {red}│{reset}   {red}│{reset}
          {red}╱{reset}    {red}│{reset} {bright_yellow}║{reset} {red}│{reset}    {red}╲{reset}
         {red}│{reset}     {red}│{reset} {bright_yellow}║{reset} {red}│{reset}     {red}│{reset}
         {red}│{reset}  {bright_magenta}╱╲{reset} {red}│{reset} {bright_yellow}║{reset} {red}│{reset} {bright_magenta}╱╲{reset}  {red}│{reset}
        {green}│{reset}  {bright_magenta}│{reset}  {bright_magenta}│╱╲║╱╲{reset}{bright_magenta}│{reset}  {bright_magenta}│{reset}  {green}│{reset}
        {green}│{reset}  {bright_magenta}│{reset}  {bright_magenta}│{reset}  {bright_yellow}║{reset}  {bright_magenta}│{reset}  {bright_magenta}│{reset}  {green}│{reset}
        {green}│{reset}  {bright_magenta}╲╱{reset}  {bright_magenta}╱{reset} {bright_yellow}║{reset} {bright_magenta}╲{reset}  {bright_magenta}╲╱{reset}  {green}│{reset}
         {green}╲{reset}      {green}╱{reset}  {bright_yellow}║{reset}  {green}╲{reset}      {green}╱{reset}
          {green}╲{reset}    {green}╱{reset}   {bright_yellow}║{reset}   {green}╲{reset}    {green}╱{reset}
           {green}╲{reset}  {green}╱{reset}    {bright_yellow}║{reset}    {green}╲{reset}  {green}╱{reset}
            {green}╲╱╱╱╱╱╱║╱╱╱╱╲╱╱{reset}
    """,
    # Pose 4: Hip thrust forward
    """
                {cyan}╔═══╗{reset}
                {cyan}║{reset} {bright_yellow}●{reset} {cyan}│{reset}
                {cyan}╚═══╝{reset}
               {bright_yellow}╱{red}│{reset} {bright_yellow}║{reset} {red}│{bright_yellow}╲{reset}
              {red}│{reset} {red}│{reset} {bright_yellow}║{reset} {red}│{reset} {red}│{reset}
              {red}│{reset} {red}│{reset} {bright_yellow}║{reset} {red}│{reset} {red}│{reset}
             {red}│{reset}  {red}│{reset} {bright_yellow}║{reset} {red}│{reset}  {red}│{reset}
            {red}╱{reset}   {red}│{reset} {bright_yellow}║{reset} {red}│{reset}   {red}╲{reset}
           {red}│{reset}    {red}│{reset} {bright_yellow}║{reset} {red}│{reset}    {red}│{reset}
          {green}╱{reset}    {bright_magenta}╱╲║╱╲{reset}    {green}╲{reset}
         {green}│{reset}    {bright_magenta}│{reset}  {bright_yellow}║{reset}  {bright_magenta}│{reset}    {green}│{reset}
         {green}│{reset}   {bright_magenta}╱╲{reset} {bright_yellow}║{reset} {bright_magenta}╱╲{reset}   {green}│{reset}
        {blue}│{reset}    {bright_magenta}│{reset}  {bright_yellow}║{reset}  {bright_magenta}│{reset}    {blue}│{reset}
        {blue}│{reset}   {bright_magenta}╱{reset} {bright_magenta}╲{reset} {bright_yellow}║{reset} {bright_magenta}╱{reset} {bright_magenta}╲{reset}   {blue}│{reset}
        {blue}│{reset}  {bright_magenta}│{reset}   {bright_magenta}╲║╱{reset}   {bright_magenta}│{reset}  {blue}│{reset}
         {blue}╲{reset} {bright_magenta}│{reset}    {bright_yellow}║{reset}    {bright_magenta}│{reset} {blue}╱{reset}
          {blue}╲{blue}│{reset}   {bright_yellow}╱{reset} {bright_yellow}╲{reset}   {blue}│{blue}╱{reset}
           {blue}╲{reset}  {blue}╱{reset}   {blue}╲{reset}  {blue}╱{reset}
            {blue}╲╱{reset}     {blue}╲╱{reset}
    """,
]

ROAST_LINES = [
    "{bright_yellow}★ VANCE IS DANCING ★{reset}",
    "{bright_cyan}>>> DJ VANCE MOMENT <<<{reset}",
    "{bright_magenta}╔═ THE LEGEND HIMSELF ═╗{reset}",
    "{bright_red}!!! ABSOLUTELY UNHINGED !!!{reset}",
    "{bright_green}☆ VIBE CHECK: PASSED ☆{reset}",
    "{bright_blue}>>> RESPECT THE RHYTHM <<<{reset}",
    "{bright_yellow}§§§ BUSSIN BUSSIN §§§{reset}",
    "{bright_magenta}>>> THIS IS PURE ART <<<{reset}",
    "{bright_cyan}★ CERTIFIED DANCER ★{reset}",
    "{bright_red}!!! MOVES ARE FIRE !!!{reset}",
]

def colorize_string(text: str, color_map: dict) -> str:
    """Replace {color_name} placeholders with ANSI codes."""
    result = text
    for color_name, code in color_map.items():
        result = result.replace(f"{{{color_name}}}", code)
    return result

def generate_vance_frame(
    pose_idx: int = 0, roast: str = "", width: int = 80, height: int = 24
) -> str:
    """Generate a colorized Vance ASCII frame."""
    color_map = {
        "reset": Colors.RESET,
        "cyan": Colors.BRIGHT_CYAN,
        "yellow": Colors.BRIGHT_YELLOW,
        "red": Colors.BRIGHT_RED,
        "magenta": Colors.BRIGHT_MAGENTA,
        "green": Colors.BRIGHT_GREEN,
        "blue": Colors.BRIGHT_BLUE,
        "bright_yellow": Colors.BRIGHT_YELLOW,
        "bright_magenta": Colors.BRIGHT_MAGENTA,
        "bright_cyan": Colors.BRIGHT_CYAN,
        "bright_red": Colors.BRIGHT_RED,
        "bright_green": Colors.BRIGHT_GREEN,
        "bright_blue": Colors.BRIGHT_BLUE,
    }

    pose = VANCE_POSES_COLORED[pose_idx % len(VANCE_POSES_COLORED)]
    pose_colored = colorize_string(pose, color_map)
    pose_lines = pose_colored.strip().split("\n")

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
        roast_colored = colorize_string(roast, color_map)
        frame_lines.append(roast_colored.center(width))

    # Ensure we fill the frame
    while len(frame_lines) < height:
        frame_lines.append("")

    return "\n".join(frame_lines[:height])

def generate_animation(
    frames: int = 60,
    width: int = 80,
    height: int = 24,
    roast: bool = True,
) -> list[str]:
    """Generate a sequence of colorized ASCII frames with smooth transitions."""
    animation = []

    for i in range(frames):
        pose_idx = i % len(VANCE_POSES_COLORED)
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
    output_dir: str = "vance_dance_frames",
) -> str:
    """Save ASCII frames as text files."""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    for i, frame in enumerate(frames):
        frame_file = output_path / f"frame_{i:04d}.txt"
        frame_file.write_text(frame)

        if (i + 1) % 15 == 0:
            print(f"Generated {i + 1}/{len(frames)} ASCII frames")

    print(f"All frames saved to {output_dir}")
    return output_dir

def generate_and_save(
    frames: int = 60,
    output_dir: str = "vance_dance_frames",
    width: int = 80,
    height: int = 24,
) -> str:
    """Generate ASCII animation and save to directory."""
    print(f"Generating {frames} colorized ASCII frames for Vance...")
    animation = generate_animation(frames=frames, width=width, height=height)
    return save_ascii_frames(animation, output_dir)
