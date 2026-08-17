# RPG Game Project

A Python/Pygame top-down RPG prototype built as a learning project for pixel-art game development. The project started from guided Zelda-style Pygame tutorials and was customized with new maps, characters, enemies, UI, save/load logic, magic, and experimental larger Tiled maps.

## Project Status

This is an older personal project with two main runtime folders:

- `Working/` — the known-good baseline using the smaller original map.
- `Testing/` — the experimental large-map version using the newer 256 x 256 Tiled export.

Recent maintenance focused on documenting the codebase and improving the `Testing/` large-map performance path without changing the `Working/` baseline.

## Requirements

- Python 3.11+ or Python 3.12+
- Pygame
- Pytest, for tests

Install dependencies with the included requirements file:

```bash
python -m venv .venv
source .venv/bin/activate  # Windows PowerShell: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

If using `uv`:

```bash
uv venv .venv
source .venv/bin/activate
uv pip install -r requirements.txt
```

## How to Run

Run the known-good baseline:

```bash
cd Working/code
python main.py
```

Run the large-map testing version:

```bash
cd Testing/code
python main.py
```

Important: the game uses relative asset paths, so run `main.py` from inside either `Working/code` or `Testing/code`.

## How to Test

From the repository root:

```bash
source .venv/bin/activate
pytest Testing/tests/test_map_window_performance.py -q
```

Current verified result:

```text
5 passed
```

## Large Map Performance Notes

The new `Testing/` map is 256 x 256 tiles. The original code tried to create too many map/collision sprites at startup, especially from `Testing/map/Boundary.csv`, which contains 65,433 non-empty cells.

Implemented in `Testing/code`:

- A 50 x 50 tile startup creation window around the player spawn.
- `SpatialObstacleGroup` for faster nearby obstacle lookup.
- Camera culling so offscreen sprites are not sorted/drawn every frame.
- Unknown entity IDs are skipped instead of defaulting to squid.

Observed headless smoke-test result after the change:

```text
level_created_seconds 2.279
map_window <rect(68, 138, 50, 50)>
visible_sprites 1
obstacle_sprites 2491
draw_seconds 0.0004
```

Before the 50 x 50 map-window change, the testing map created 65,433 obstacle sprites and took about 12 seconds to instantiate in the same headless environment.

## Main Files

- `Working/code/main.py` — entry point for the baseline game.
- `Testing/code/main.py` — entry point for the large-map testing version.
- `Testing/code/level.py` — map loading, sprite groups, camera drawing, save/load, combat hooks, and large-map performance changes.
- `Testing/code/entity.py` — shared movement/collision behavior using spatial obstacle lookup when available.
- `Testing/tests/test_map_window_performance.py` — performance-focused regression tests.
- `docs/UPDATE_DOC.md` — detailed architecture, map issue diagnosis, and refactor suggestions.
- `docs/CHANGELOG.md` — documentation and maintenance log.
- `docs/PROJECT_TREE.md` — repository structure overview.

## Known Issues / Future Refactors

See `docs/UPDATE_DOC.md` for detailed notes. High-value follow-ups:

- Merge duplicated `Working/code` and `Testing/code` into one configurable codebase.
- Replace hardcoded relative paths with a `paths.py` helper.
- Add a real Tiled GID resolver for building/nature layers.
- Re-export `Boundary.csv` as a sparse collision layer.
- Split `Level.create_map()` further into loader/factory modules.
- Replace raw `pickle` save/load with JSON later.

## Credits

Created as a learning project using Python, Pygame, pixel-art assets, and tutorial-guided RPG mechanics, then customized with original project changes.
