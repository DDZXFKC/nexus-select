#!/usr/bin/env python3
"""Foot Locker Cow Print IO0442-200: untouched originals on white square.

No cutout, alpha matting, sharpening, saturation, edge repair, resizing or crop.
Reads only approved image ids _01, _03, _04. Writes PNGs and provenance.json.
"""
import argparse
import hashlib
import json
from pathlib import Path
from PIL import Image

STYLE = "IO0442-200"
SOURCE_IDS = ("O0442200_01", "O0442200_03", "O0442200_04")
ORIGINAL_SHA256 = {
    "O0442200_01": "fe885340165c579753676bbea0adbf577e7438a33321f15fc727eca179075dfd",
    "O0442200_03": "aeb5cf783e43c8b21f15e9db62fcc41c9e4b14a73f79720238e08cf45ac14b50",
    "O0442200_04": "d0bfdf7f44c3a1b6ef3abf1e98628160ccb40c45574109b4bffc0b701e703273",
}
BASE = "https://images.footlocker.com/is/image/EBFL2/"


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def square_without_cutout(original: Path, dest: Path):
    with Image.open(original) as source:
        source.load()
        # Preserve native pixel dimensions and compositing pixel coordinates.
        rgba = source.convert("RGBA")
        w, h = rgba.size
        if w <= 0 or h <= 0 or max(w, h) > 6000:
            raise ValueError("Unacceptable original image dimensions")
        size = max(w, h)
        canvas = Image.new("RGBA", (size, size), (255, 255, 255, 255))
        at = ((size - w) // 2, (size - h) // 2)
        canvas.alpha_composite(rgba, at)
        # Do not change original opaque pixels. Transparent pixels only
        # display on the white base; no edge blur or masks are introduced.
        for y in range(h):
            for x in range(w):
                pixel = rgba.getpixel((x, y))
                if pixel[3] == 255 and canvas.getpixel((x + at[0], y + at[1])) != pixel:
                    raise ValueError("Opaque source pixel was modified")
        rgb = canvas.convert("RGB")
        if any(rgb.getpixel(p) != (255, 255, 255) for p in
               ((0, 0), (size - 1, 0), (0, size - 1), (size - 1, size - 1))):
            raise ValueError("Original has nonwhite opaque corners; needs a different source")
        dest.parent.mkdir(parents=True, exist_ok=True)
        rgb.save(dest, format="PNG", optimize=True)
        return {"source_width": w, "source_height": h,
                "square_size": size, "offset_x": at[0], "offset_y": at[1],
                "output_sha256": sha256(dest)}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--original-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    report = []
    for image_id in SOURCE_IDS:
        original = args.original_dir / (image_id + ".webp")
        if not original.is_file() or sha256(original) != ORIGINAL_SHA256[image_id]:
            raise ValueError(f"Foot Locker source mismatch: {image_id}")
        target = args.output_dir / (image_id + "-white-square.png")
        info = square_without_cutout(original, target)
        report.append({"image_id": image_id, "maker_style": STYLE,
                       "source_url": BASE + image_id,
                       "original_sha256": ORIGINAL_SHA256[image_id],
                       "output_file": target.name, **info})
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "provenance.json").write_text(
        json.dumps({"style": STYLE, "sku": "FL-O0442200",
                    "source_is_original": True,
                    "cutout": False, "resize": False, "crop": False,
                    "images": report}, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"completed": len(report), "images": report}, indent=2))


if __name__ == "__main__":
    main()
