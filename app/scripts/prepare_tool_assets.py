#!/usr/bin/env python3
"""
prepare_tool_assets.py

Batch-crop and resize tool images into standardized PNG assets.

Usage:
  python prepare_tool_assets.py <input_dir> <output_dir> <mode>

Modes:
  - thumbnails -> 600x400 (3:2)
  - banners    -> 1200x200 (6:1)

Examples:
  python prepare_tool_assets.py /path/to/raw/thumbnails /path/to/out thumbnails
  python prepare_tool_assets.py /path/to/raw/banners    /path/to/out banners
"""

import argparse
import sys
from pathlib import Path
from PIL import Image, ImageOps

THUMBNAIL_SIZE = (600, 400)   # 3:2
BANNER_SIZE    = (1200, 200)  # 6:1
VALID_EXTS = {".png", ".jpg", ".jpeg", ".webp", ".tif", ".tiff", ".bmp"}


def parse_args():
    p = argparse.ArgumentParser(
        description="Crop and resize tool images to standard assets."
    )
    p.add_argument("input_dir", type=str, help="Directory with raw screenshots")
    p.add_argument("output_dir", type=str, help="Directory to save processed images")
    p.add_argument(
        "mode",
        type=str,
        choices=["thumbnails", "banners"],
        help="Output format/size preset",
    )
    p.add_argument(
        "--centered",
        action="store_true",
        help="(Default) Center-crop to target aspect (ImageOps.fit).",
    )
    # Placeholder for future profiles/qualities; PNG uses lossless compression
    return p.parse_args()


def target_size_for_mode(mode: str):
    if mode == "thumbnails":
        return THUMBNAIL_SIZE
    elif mode == "banners":
        return BANNER_SIZE
    else:
        raise ValueError(f"Unknown mode: {mode}")


def is_image_file(path: Path) -> bool:
    return path.is_file() and (path.suffix.lower() in VALID_EXTS)


def process_image(src: Path, dst_dir: Path, out_size: tuple[int, int]) -> tuple[bool, str]:
    """
    Process a single image:
      - open
      - center-crop to target aspect
      - resize to out_size
      - convert to PNG (RGB)
      - save as <stem>.png
    Returns (success, message)
    """
    try:
        with Image.open(src) as im:
            # Convert to RGB to avoid palette/alpha oddities for PNGs in the site
            if im.mode not in ("RGB", "RGBA"):
                im = im.convert("RGB")

            # Fit/crop to target aspect and size
            # ImageOps.fit does a center crop to the aspect and then resizes using the given method
            fitted = ImageOps.fit(
                im,
                out_size,
                method=Image.Resampling.LANCZOS,
                bleed=0.0,
                centering=(0.5, 0.5),
            )

            dst_path = dst_dir / f"{src.stem}.png"
            # Optimize PNG size a bit; compress_level 0-9 (9 is highest compression)
            fitted.save(dst_path, format="PNG", optimize=True, compress_level=6)
        return True, f"OK   -> {dst_path.name}"
    except Exception as e:
        return False, f"FAIL -> {src.name}: {e}"


def main():
    args = parse_args()
    input_dir = Path(args.input_dir).expanduser().resolve()
    output_dir = Path(args.output_dir).expanduser().resolve()
    out_size = target_size_for_mode(args.mode)

    if not input_dir.exists() or not input_dir.is_dir():
        print(f"[ERROR] Input directory does not exist or is not a directory: {input_dir}")
        sys.exit(1)

    output_dir.mkdir(parents=True, exist_ok=True)

    files = sorted([p for p in input_dir.iterdir() if is_image_file(p)])
    if not files:
        print(f"[WARN] No image files found in {input_dir}. Valid extensions: {sorted(VALID_EXTS)}")
        sys.exit(0)

    print(f"[INFO] Mode: {args.mode} -> size {out_size[0]}x{out_size[1]}")
    print(f"[INFO] Input : {input_dir}")
    print(f"[INFO] Output: {output_dir}")
    print(f"[INFO] Found {len(files)} image(s). Processing...\n")

    ok, fail = 0, 0
    for src in files:
        success, msg = process_image(src, output_dir, out_size)
        if success:
            ok += 1
        else:
            fail += 1
        print(msg)

    print("\n[SUMMARY]")
    print(f"  Success: {ok}")
    print(f"  Failed : {fail}")
    print(f"  Output : {output_dir}")


if __name__ == "__main__":
    main()
