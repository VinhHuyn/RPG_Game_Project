# Changelog

## 2026-08-16 22:30 PDT - Five-Second Streaming Window Update

### Changed
- Added a 5-second Testing world-stream update instead of regenerating map content every frame.
- Rebuilds local boundary tiles, nature/filler, CSV monsters, grouped monsters, and ambient monster groups around the current player tile.
- Clears old streamed tiles/enemies before rebuilding so sprite counts stay bounded.
- Added ambient monster groups so enemies are not limited to one CSV-heavy location.
- Updated `docs/UPDATE_DOC.md` with the streaming cadence and smoke-test evidence.

### Verified
- `SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy .venv/bin/python -B -m pytest Testing/tests/test_map_window_performance.py -q` passed: 21 tests.
- Smoke test confirmed no update at `4999ms`, update at `5000ms`, and streamed window moved to `<rect(200, 185, 50, 50)>`.

## 2026-08-16 21:38 PDT - Chunked Safe Fill and Monster Groups

### Changed
- Changed Testing texture fill from evenly spaced single tiles to seeded chunk/group placement.
- Reserved a player/spawn escape corridor so generated or CSV nature tiles do not block the active 50 x 50 window into a dead end.
- Kept generated nature chunks destroyable through the existing attackable nature path.
- Added companion monster group spawning around CSV monster anchors while avoiding the player tile and blocked/reserved tiles.
- Updated `docs/UPDATE_DOC.md` with the safe-fill and grouped-monster behavior.

### Verified
- `SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy .venv/bin/python -B -m pytest Testing/tests/test_map_window_performance.py -q` passed: 18 tests.
- Headless smoke test confirmed `blocked_corridor_nature 0`, `enemy_sprites_grouped 15`, and `moved_enemy_sprites_grouped 42`.

## 2026-08-16 21:23 PDT - Player-Centered Spawns and Destroyable Nature

### Changed
- Recentered Testing enemy and nature respawn windows around the current player position instead of only the original spawn.
- Added deterministic nature texture fill inside the active 50 x 50 window to reduce sparse empty space.
- Made nature tiles attackable/destroyable through the existing grass-like attack path.
- Made Testing enemy sprite/audio loading path-independent for respawn tests.
- Updated `docs/UPDATE_DOC.md` with the player-centered spawn and destroyable nature fill details.

### Verified
- `SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy .venv/bin/python -B -m pytest Testing/tests/test_map_window_performance.py -q` passed: 14 tests.
- Headless smoke test confirmed the moved player window `<rect(200, 185, 50, 50)>`, 14 moved-window enemies, and 458 moved-window nature sprites.

## 2026-08-16 19:30 PDT - Global Nature/Monster Tile IDs

### Changed
- Added Tiled global/local ID helpers for the Testing nature and monster tilesets.
- Renamed the active entity mapping to `MONSTER_IDS` / `IGNORED_MONSTER_TILE_IDS` while keeping compatibility aliases.
- Re-enabled Testing nature tile creation using `Tileset/nature/nature.png` instead of the incomplete split-image folder.
- Updated `docs/UPDATE_DOC.md` with the global nature/monster ID audit and verification output.

### Verified
- `SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy .venv/bin/python -B -m pytest Testing/tests/test_map_window_performance.py -q` passed: 11 tests.
- Headless smoke test created 726 nature sprites, 5 enemies, and 935 obstacle sprites in the 50 x 50 player window.

## 2026-08-16 19:12 PDT - CSV ID Audit

### Changed
- Updated `Testing/code/level.py` entity handling so IDs `17`, `32`, and `33` are ignored as duplicate parts of the `16/17/32/33` 2x2 creature.
- Added a regression test confirming only `16` spawns from that 2x2 entity block.
- Updated `docs/UPDATE_DOC.md` with the CSV entity/nature ID audit and spawn-window positions.

### Verified
- `pytest Testing/tests/test_map_window_performance.py -q` passed: 9 tests.

## 2026-08-16 19:00 PDT - Testing Gameplay Regression Fix

### Changed
- Fixed `Testing/code/level.py` spatial indexing so collision tiles created through `Tile(...)` are indexed after map creation.
- Limited active boundary collision to boundary tile ID `768` instead of treating every non-empty boundary tile as solid.
- Added Testing entity ID mappings for the new map IDs (`0`, `1`, `2`, `16`, `17`, `18`, `32`, `33`, `50`) so enemies spawn again.
- Reduced `Testing/code/player.py` debug movement speed from `100` to `5`.

### Verified
- `pytest Testing/tests/test_map_window_performance.py -q` passed: 8 tests.
- Headless smoke test: player speed `5`, enemy count `5`, obstacle sprites `209`, spatial cells `281`.

## 2026-08-16 18:37 PDT - Python Runtime Install

### Added
- Installed project `.venv` with Python 3.12.13 via `uv`.
- Added `.python-version` set to `3.12.13`.
- Updated `runtime.txt` to `python-3.12.13`.

### Changed
- Updated `requirements.txt` runtime comments to recommend Python 3.12.13 for long-term compatibility.

### Verified
- `.venv` reports `Python 3.12.13`.
- `python -m pip --version` works inside `.venv`.
- `pytest Testing/tests/test_map_window_performance.py -q` passed: 5 tests.

## 2026-08-16 18:37 PDT - Requirements Runtime Note

### Added
- Added Python runtime guidance comments to `requirements.txt`.
- Added `runtime.txt` declaring `python-3.11` for hosts that read a Python runtime file.

### Notes
- Python itself cannot be installed by `pip install -r requirements.txt`; install Python first, then install package dependencies.

## 2026-08-16 18:37 PDT - README Update

### Changed
- Rewrote `README.md` with current setup, run commands, test command, large-map performance notes, main file overview, and future refactor list.

## 2026-08-16 18:08 PDT - Testing Map Window Performance

### Added
- Added `Testing/tests/test_map_window_performance.py` with performance-focused unit tests for 50 x 50 map-window creation, camera culling, and spatial obstacle lookup.

### Changed
- Refactored `Testing/code/level.py` to create only a 50 x 50 tile window around the player spawn at startup.
- Kept `Working/code` as the baseline; no Working code changes are part of this Testing-only refactor.
- Updated `docs/UPDATE_DOC.md` with the Testing-only performance results.

### Verified
- `pytest Testing/tests/test_map_window_performance.py -q` passed: 5 tests.
- Headless smoke test for `Testing/code` created 2,491 obstacle sprites instead of the previous 65,433.

## 2026-08-16 18:08 PDT - Performance Refactor

### Added
- Added `[SUGGESTION]` refactor candidates to `docs/UPDATE_DOC.md`.
- Added initial performance tests for camera culling and spatial obstacle lookup; later moved the active tests under `Testing/tests/`.
- Added `requirements.txt` with `pygame` and `pytest` versions used for verification.

### Changed
- Initially tested camera culling and `SpatialObstacleGroup`; active implementation is now limited to `Testing/code`.
- Active collision spatial lookup implementation is now limited to `Testing/code/entity.py`.

### Verified
- `pytest tests/test_big_map_performance.py -q` passed: 3 tests.
- Headless smoke tests instantiated both `Testing/code` and `Working/code` levels with the project venv.

## 2026-08-16 18:08 PDT - Doc Sync

### Added
- Added `docs/UPDATE_DOC.md` with architecture notes, map-pipeline findings, and root-cause analysis for the new 256 x 256 map issue.
- Added `docs/PROJECT_TREE.md` with the current repository structure.

### Notes
- Static inspection found current Git modifications are line-ending-only when compared with `--ignore-space-at-eol`.
- Game execution was not run because `pygame` is not installed in this WSL environment.

