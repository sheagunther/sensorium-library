#!/usr/bin/env python3
"""
Sensorium Library — Resize Pipeline
Loop MMT™ · Run locally against your clone of the sensorium-library repo.

Usage:
    python3 resize.py [--repo-path /path/to/sensorium-library]

What it does:
    1. Reads manifest.json for tier assignments (source vs standard)
    2. Creates /standard/ and /source/ directories
    3. Standard-tier images → resized to 1024px long edge, JPEG q85
    4. Source-tier images → resized to 1536px long edge, JPEG q90
       (originals preserved in repo root for archival)
    5. Updates manifest.json with resized paths and dimensions
    6. Skips images already resized (idempotent)

After running:
    git add . && git commit -m "Resize pass v1" && git push
"""

import os
import sys
import json
from PIL import Image

STANDARD_LONG_EDGE = 1024
SOURCE_LONG_EDGE = 1536
STANDARD_QUALITY = 85
SOURCE_QUALITY = 90

# Images where high-res detail is the information
SOURCE_TIER_KEYWORDS = [
    "mandelbrot", "fractal", "mandel_zoom", "electron-microscope",
    "cell_explainer", "biomedical", "hubble", "deep_field",
    "discretegeometry", "graph_bounds"
]


def is_source_tier(filename, manifest_entry=None):
    """Determine if an image should be source tier."""
    if manifest_entry and manifest_entry.get("tier") == "source":
        return True
    lower = filename.lower()
    return any(kw in lower for kw in SOURCE_TIER_KEYWORDS)


def resize_image(src_path, dst_path, long_edge, quality):
    """Resize image so long edge = target. Skip if already done."""
    if os.path.exists(dst_path):
        return "skipped"
    try:
        img = Image.open(src_path)
    except Exception as e:
        return f"error: {e}"

    w, h = img.size
    if max(w, h) <= long_edge:
        # Already small enough — just copy
        img.save(dst_path, "JPEG", quality=quality)
        return "copied"

    if w >= h:
        new_w = long_edge
        new_h = int(h * (long_edge / w))
    else:
        new_h = long_edge
        new_w = int(w * (long_edge / h))

    img = img.convert("RGB")  # handle RGBA, palette, etc.
    img = img.resize((new_w, new_h), Image.LANCZOS)
    img.save(dst_path, "JPEG", quality=quality)
    return f"resized {w}x{h} → {new_w}x{new_h}"


def main():
    repo_path = sys.argv[1] if len(sys.argv) > 1 else "."
    manifest_path = os.path.join(repo_path, "manifest.json")

    if not os.path.exists(manifest_path):
        print(f"No manifest.json found at {repo_path}")
        sys.exit(1)

    with open(manifest_path) as f:
        manifest = json.load(f)

    # Create output dirs
    standard_dir = os.path.join(repo_path, "standard")
    source_dir = os.path.join(repo_path, "source")
    os.makedirs(standard_dir, exist_ok=True)
    os.makedirs(source_dir, exist_ok=True)

    stats = {"standard": 0, "source": 0, "skipped": 0, "errors": 0}

    for entry in manifest.get("images", []):
        filename = entry.get("file", "")
        if entry.get("is_folder"):
            continue

        src_path = os.path.join(repo_path, filename)
        if not os.path.exists(src_path):
            print(f"  MISSING: {filename}")
            stats["errors"] += 1
            continue

        # Determine tier
        source = is_source_tier(filename, entry)
        tier = "source" if source else "standard"
        long_edge = SOURCE_LONG_EDGE if source else STANDARD_LONG_EDGE
        quality = SOURCE_QUALITY if source else STANDARD_QUALITY
        out_dir = source_dir if source else standard_dir

        # Build output path (always .jpg)
        base = os.path.splitext(os.path.basename(filename))[0]
        dst_path = os.path.join(out_dir, f"{base}.jpg")

        result = resize_image(src_path, dst_path, long_edge, quality)

        # Update manifest entry
        entry["tier"] = tier
        entry["resized_path"] = os.path.relpath(dst_path, repo_path)

        if "error" in result:
            stats["errors"] += 1
            print(f"  ERROR: {filename} — {result}")
        elif result == "skipped":
            stats["skipped"] += 1
        else:
            stats[tier] += 1
            print(f"  {tier.upper()}: {filename} — {result}")

    # Handle FWW(C) folder
    fwwc_dir = os.path.join(repo_path, "FWW(C)")
    if os.path.isdir(fwwc_dir):
        fwwc_standard = os.path.join(standard_dir, "fwwc")
        os.makedirs(fwwc_standard, exist_ok=True)
        for fname in os.listdir(fwwc_dir):
            if fname.startswith("."):
                continue
            src = os.path.join(fwwc_dir, fname)
            base = os.path.splitext(fname)[0]
            dst = os.path.join(fwwc_standard, f"{base}.jpg")
            result = resize_image(src, dst, STANDARD_LONG_EDGE, STANDARD_QUALITY)
            if "error" not in result and result != "skipped":
                stats["standard"] += 1
                print(f"  FWWC: {fname} — {result}")

    # Write updated manifest
    manifest["version"] = manifest.get("version", 0) + 1
    manifest["updated"] = "auto-resize"
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)

    print(f"\nDone. Standard: {stats['standard']}, Source: {stats['source']}, "
          f"Skipped: {stats['skipped']}, Errors: {stats['errors']}")
    print(f"Manifest updated at {manifest_path}")
    print(f"\nNext: git add . && git commit -m 'Resize pass' && git push")


if __name__ == "__main__":
    main()
