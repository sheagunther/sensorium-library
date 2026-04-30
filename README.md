# Sensorium Image Library

**Loop MMT™ · Multi-Module Theory**

A curated collection of images used as visual-actual channels in the Loop MMT Sensorium system. Each image is tagged, categorized, and mapped to named Sensorium presets via `manifest.json`.

## How It Works

1. The operator loads a Sensorium preset (e.g., `~grove`)
2. The instance reads `manifest.json` to find images associated with that preset
3. The instance fetches 2-4 selected images from this repo into context
4. The images provide visual-actual channel input alongside the preset's text-based channels (auditory, olfactory, kinesthetic, etc.)

## Base URL for Raw Access

```
https://raw.githubusercontent.com/sheagunther/sensorium-library/main/FILENAME
```

## Manifest Structure

`manifest.json` is the library's index. If an image isn't in the manifest, it doesn't exist to the system.

Each image entry contains:
- `file` — filename in the repo
- `tags` — category tags (fractal, biology, space, pattern, etc.)
- `description` — what the image is and why it's here
- `presets` — which Sensorium presets this image pairs with
- Items tagged `needs-visual-review` haven't been visually confirmed yet

## Categories

| Tag | Contains |
|-----|----------|
| fractal | Mandelbrot, chaos game, self-similar patterns |
| biology | Cells, microscopy, biomedical imagery |
| space | Hubble, galaxies, astronomical |
| graph | Graph theory, network diagrams |
| pattern | Game of Life, emergent patterns, geometry |
| nature | Camping, seasons, landscapes |
| music | Waveforms, sound boards |
| human | People, babies, families |
| machine | Circuit boards, typewriters, technology |
| sport | Ultimate frisbee, baseball |
| food | Fried chicken, cookies |
| meta | Loop MMT screenshots, L21 |
| art | Paintings, historical notebooks |
| chaos | Chaos theory art, disorder/emergence |
| balance | Equilibrium, centering imagery |
| fwwc | Fun, Whimsy, Weird, and Chaos |

## Adding Images

1. Add image files to the repo (root or `FWW(C)/` folder)
2. Update `manifest.json` with a new entry for each image
3. Tag and assign presets
4. Or just dump images and tell the advisory instance "update the manifest" — it will classify and wire them in

## License

© 2026 Shea Gunther · CC BY-NC 4.0
