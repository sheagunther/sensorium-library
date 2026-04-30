#!/usr/bin/env python3
"""
Sensorium Load — Instance-side image selector for the Sensorium system.
Loop MMT™ · Run within Claude sessions to select and prepare images.

Usage (from advisory instance):
    python3 sensorium-load.py --preset grove --count 3
    python3 sensorium-load.py --tags fractal,biology --count 4
    python3 sensorium-load.py --preset newhouse --include-fwwc
    python3 sensorium-load.py --random 3
    python3 sensorium-load.py --file chaos.jpg

Workflow:
    1. Reads manifest.json (from local copy or fetched from repo)
    2. Filters images by preset association, tags, or random selection
    3. Copies selected images to /home/claude/sensorium/ for viewing
    4. Prints selection summary for the instance to view images

Integration with The Slice:
    For source-tier images, produces contact thumbnails via The Slice.
    Instance can then zoom into specific regions for detail loading.

Note: This script works with LOCAL files. The instance must have
the manifest.json available (e.g., in /mnt/project/ or uploaded).
Images must be fetchable — either uploaded, in project files, or
the instance uses web_fetch to pull from the GitHub repo.
"""

import os
import sys
import json
import random
import argparse
import subprocess

OUTPUT_DIR = "/home/claude/sensorium"
SLICE_SCRIPT = "/mnt/project/the-slice.py"
MANIFEST_PATH = None  # Set by args

# GitHub raw URL base — for when images aren't local
GITHUB_RAW_BASE = "https://raw.githubusercontent.com/sheagunther/sensorium-library/main/"


def load_manifest(path):
    """Load and return the manifest."""
    with open(path) as f:
        return json.load(f)


def filter_by_preset(manifest, preset_name):
    """Return images associated with a preset."""
    clean = preset_name.lstrip("~")
    target = f"~{clean}"
    return [img for img in manifest["images"]
            if target in img.get("presets", [])
            and "needs-visual-review" not in img.get("tags", [])]


def filter_by_tags(manifest, tags):
    """Return images matching ANY of the given tags."""
    tag_set = set(tags)
    return [img for img in manifest["images"]
            if tag_set & set(img.get("tags", []))
            and "needs-visual-review" not in img.get("tags", [])]


def select_images(candidates, count, include_fwwc=False):
    """Select N images from candidates. Always include 1 FWW(C) if flag set."""
    if not candidates:
        return []

    if include_fwwc:
        fwwc = [c for c in candidates if "fwwc" in c.get("tags", [])]
        non_fwwc = [c for c in candidates if "fwwc" not in c.get("tags", [])]

        selected = []
        if fwwc:
            selected.append(random.choice(fwwc))
            count -= 1
        if non_fwwc and count > 0:
            selected.extend(random.sample(non_fwwc, min(count, len(non_fwwc))))
        return selected
    else:
        return random.sample(candidates, min(count, len(candidates)))


def prepare_image(entry, manifest, output_dir):
    """Prepare an image for viewing. Returns the output path."""
    filename = entry["file"]
    tier = entry.get("tier", "standard")

    # Check for resized version first
    resized = entry.get("resized_path")
    if resized:
        filename = resized

    # For now, just report what to fetch — the instance will use
    # web_fetch or view tool to actually load the image
    base_url = manifest.get("base_url", GITHUB_RAW_BASE)
    url = base_url + filename.replace(" ", "%20")

    return {
        "file": entry["file"],
        "tier": tier,
        "url": url,
        "tags": entry.get("tags", []),
        "description": entry.get("description", ""),
        "presets": entry.get("presets", []),
        "action": "slice_contact" if tier == "source" else "fetch_whole"
    }


def main():
    parser = argparse.ArgumentParser(description="Sensorium image selector")
    parser.add_argument("--manifest", default="/mnt/project/manifest.json",
                        help="Path to manifest.json")
    parser.add_argument("--preset", help="Select images for a preset (e.g., grove)")
    parser.add_argument("--tags", help="Comma-separated tags to filter by")
    parser.add_argument("--count", type=int, default=3, help="Number of images")
    parser.add_argument("--include-fwwc", action="store_true",
                        help="Always include one FWW(C) image")
    parser.add_argument("--random", type=int, help="Select N random classified images")
    parser.add_argument("--file", help="Select a specific file by name")
    parser.add_argument("--list-presets", action="store_true",
                        help="List all presets and their image counts")

    args = parser.parse_args()

    # Try multiple manifest locations
    manifest_paths = [
        args.manifest,
        "/mnt/project/manifest.json",
        "/mnt/user-data/uploads/manifest.json",
        "./manifest.json"
    ]

    manifest = None
    for mp in manifest_paths:
        if os.path.exists(mp):
            manifest = load_manifest(mp)
            break

    if not manifest:
        print("ERROR: No manifest.json found. Upload it or add to project.")
        sys.exit(1)

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # List presets mode
    if args.list_presets:
        preset_map = manifest.get("presets", {})
        for preset, cats in sorted(preset_map.items()):
            images = filter_by_preset(manifest, preset)
            print(f"  {preset}: {len(images)} images (categories: {', '.join(cats)})")
        return

    # Select images
    if args.file:
        candidates = [img for img in manifest["images"]
                      if args.file in img["file"]]
    elif args.preset:
        candidates = filter_by_preset(manifest, args.preset)
    elif args.tags:
        candidates = filter_by_tags(manifest, args.tags.split(","))
    elif args.random:
        classified = [img for img in manifest["images"]
                      if "needs-visual-review" not in img.get("tags", [])]
        candidates = classified
        args.count = args.random
    else:
        print("Specify --preset, --tags, --random, --file, or --list-presets")
        sys.exit(1)

    selected = select_images(candidates, args.count, args.include_fwwc)

    if not selected:
        print("No images matched the criteria.")
        sys.exit(0)

    # Prepare and report
    print(f"\n{'='*60}")
    print(f"SENSORIUM IMAGE LOAD — {len(selected)} images selected")
    print(f"{'='*60}\n")

    for i, entry in enumerate(selected, 1):
        result = prepare_image(entry, manifest, OUTPUT_DIR)
        print(f"  [{i}] {result['file']}")
        print(f"      Tier: {result['tier']} | Action: {result['action']}")
        print(f"      Tags: {', '.join(result['tags'])}")
        print(f"      Desc: {result['description']}")
        print(f"      URL:  {result['url']}")
        if result['action'] == 'slice_contact':
            print(f"      → Use The Slice: python3 {SLICE_SCRIPT} contact <local_path>")
        print()

    print(f"{'='*60}")
    print("Fetch these URLs with web_fetch, then view with the view tool.")
    print("For source-tier images, run The Slice for detail exploration.")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
