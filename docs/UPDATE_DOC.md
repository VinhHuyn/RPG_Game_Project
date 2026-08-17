# RPG Game Project Update Document

_Last updated: 2026-08-16 22:30 PDT_

## Executive Summary

This repository is a Python/Pygame top-down RPG project based on a guided Zelda-style tutorial, then customized with new characters, maps, UI, save/load, magic, enemy respawn, and larger Tiled maps.

There are two active copies of the game code:

- `Working/` — older/stable 50 x 57 map pipeline using tutorial-style layers (`map_FloorBlocks.csv`, `map_Grass.csv`, `map_Objects.csv`, `map_Entities.csv`).
- `Testing/` — experimental/new-map pipeline using 256 x 256 exported layers (`Boundary.csv`, `Building.csv`, `Nature.csv`, `Entities.csv`, `Ground.csv`).

Main finding: the new map broke performance/display because the Tiled layer exports no longer match the assumptions in `level.py`. The game currently treats almost every boundary tile as a collision object, treats unknown entity tile IDs as enemies, does not draw building/nature layers because that code is commented out, and would crash or draw wrong tiles if those layers were simply uncommented because Tiled GIDs are being used as direct Python list indexes.

## How to Run

From the repository root:

```bash
cd Working/code
python main.py
```

Testing/new map version:

```bash
cd Testing/code
python main.py
```

Dependency:

```bash
pip install pygame
```

Note: I could not execute the game in this WSL environment because `pygame` is not currently installed here. The diagnosis below is based on static code and CSV/map inspection.

## Current Repository State Observed

- Branch: `main`
- Latest commit: `861cca7 Modifed code`
- Recent relevant commits:
  - `f0faec5 upscale map to 64` — updated `graphics/Ground/ground.png` to a much larger image.
  - `d483228 added new map` — added new large map image assets.
  - `dc0e4ba Update 2.0` — larger update before current edits.
- `git diff --stat` shows many modified files, but `git diff --stat --ignore-space-at-eol` is empty. That means the current working-tree modifications appear to be line-ending-only churn, not code/content changes.

## Project Architecture

### Main runtime flow

- `main.py` initializes Pygame, creates `Game`, shows `FrontPage`, enters the game loop, and handles menu/save/quit keys.
- `level.py` owns world creation, map loading, sprite groups, camera drawing, combat checks, save/load, and respawn.
- `settings.py` defines screen size, FPS, tile size, UI constants, weapons, magic, enemies, and character stats.
- `player.py`, `enemy.py`, and `entity.py` implement movement, collision, attacks, AI, vulnerability, and cooldowns.
- `tile.py` defines generic map tiles and hitboxes.
- `support.py` loads CSV maps and image folders.
- `ui.py`, `upgrade.py`, `frontpage.py`, `characterSelections.py`, `magic.py`, `particles.py`, and `weapon.py` handle UI/gameplay presentation systems.

### Map/data split

#### `Working/`

`Working/map` has a small 50 x 57 map:

- `map_Floor.csv`: 50 x 57, 2,850 floor cells.
- `map_FloorBlocks.csv`: 325 collision cells.
- `map_Grass.csv`: 137 grass cells.
- `map_Objects.csv`: 91 object cells.
- `map_Entities.csv`: 36 entity cells:
  - 1 player spawn (`394`)
  - 17 bamboo (`390`)
  - 4 spirit (`391`)
  - 2 raccoon (`392`)
  - 12 default/squid (`393`)

This version matches the older tutorial-style assumptions much better.

#### `Testing/`

`Testing/map` has the new 256 x 256 map:

- `Ground.csv`: 256 x 256, 65,536 filled ground cells.
- `Boundary.csv`: 256 x 256, 65,433 non-empty cells.
- `Nature.csv`: 11,698 non-empty cells.
- `Building.csv`: 144 non-empty cells.
- `Entities.csv`: 103 non-empty cells, including 1 player spawn (`394`) plus many IDs the code does not understand (`0`, `1`, `2`, `16`, `17`, `18`, `32`, `33`, `50`).

## Why the New Map Broke the Game

### 1. Boundary layer is effectively the whole map

In `Testing/code/level.py`, every non-`-1` cell in `Boundary.csv` becomes an invisible collision tile:

```python
if style == 'boundary':
    Tile((x,y), [self.obstacle_sprites], 'invisible')
```

But `Testing/map/Boundary.csv` has 65,433 non-empty cells out of 65,536 possible cells.

Impact:

- Almost the entire map becomes collision/obstacle space.
- Player movement can feel blocked or broken.
- Startup creates tens of thousands of obstacle sprites.
- Collision checks become much heavier than the original small map.

Likely cause: the Tiled layer exported as `Boundary.csv` is not a sparse collision layer. It looks like a full tile layer, not just walls/blocked tiles.

### 2. New map is much larger but rendering/collision are not culled

The original working map is 50 x 57 = 2,850 cells. The new map is 256 x 256 = 65,536 cells, about 23x more cells.

The current sprite system was written for the small map. `YSortCameraGroup.custom_draw()` sorts and draws all visible sprites every frame:

```python
for sprite in sorted(self.sprites(), key=lambda sprite: sprite.rect.centery):
    offset_pos = sprite.rect.topleft - self.offset
    self.display_surface.blit(sprite.image, offset_pos)
```

There is no camera-frustum check to skip sprites outside the screen. If many nature/building/enemy sprites are active, the game sorts/draws far more than needed every frame.

Impact:

- Low FPS on the 256 x 256 map.
- Startup/load time increases because CSV loops scan hundreds of thousands of cells across multiple layers.
- If nature/building rendering is enabled without culling, FPS will likely drop harder.

### 3. Building and nature do not display because their rendering code is commented out

In `Testing/code/level.py`, the loading exists:

```python
'building': import_csv_layout('../map/Building.csv'),
'nature': import_csv_layout('../map/Nature.csv')
```

But the actual sprite creation is commented:

```python
# if style == 'building':
#     building_surf = self.graphics['building'][int(col)]
#     Tile(...)

# if style == 'nature':
#     surf = self.graphics['nature'][int(col)]
#     Tile(...)
```

Impact:

- `Building.csv` and `Nature.csv` are read, but no building/nature sprites are created.
- This exactly explains the README note: “Building and nature current not displayed”.

### 4. Simply uncommenting building/nature would not be safe

The code assumes a Tiled CSV value can directly index into an image list:

```python
surf = self.graphics['nature'][int(col)]
building_surf = self.graphics['building'][int(col)]
```

But the new CSV IDs do not match those lists:

- `Nature.csv` IDs range from 49 to 169, but `Testing/graphics/Nature` has 78 files. IDs such as 113, 114, 115, 168, 169 are out of range for `list[int(col)]`.
- `Building.csv` IDs include `1636`, `2309`, `2310`, `2311`, and `-1610611100`, but `Testing/graphics/Building` has 1,121 files. These are also out of range.
- The negative building ID is a Tiled flip-flag encoded global tile ID, not a normal tileset index. It must be decoded/masked before use.

Impact:

- Uncommenting those blocks would likely raise `IndexError` or use the wrong images.
- Tiled global tile IDs need mapping from GID -> tileset local ID -> asset path, not direct list indexing.

### 5. Entity layer IDs no longer match the hardcoded enemy mapping

The old entity map uses IDs the code expects:

- `390` bamboo
- `391` spirit
- `392` raccoon
- `393` default squid
- `394` player spawn

The new `Testing/map/Entities.csv` uses:

```text
0, 1, 2, 16, 17, 18, 32, 33, 50, 394
```

Current logic treats anything other than player spawn `394` as an enemy, defaulting to squid unless it is exactly `390`, `391`, or `392`.

Impact:

- The new map spawns 102 enemies/objects from IDs the code does not actually understand.
- Many non-enemy markers may become squids accidentally.
- Enemy count and behavior will not match the Tiled map design.

### 6. Ground rendering does not use `Ground.csv`

The renderer uses a single pre-rendered floor image:

```python
self.floor_surf = pygame.image.load('../graphics/tilemap/ground.png').convert()
```

The new `Ground.csv` contains 65,536 cells, but it is not used by `level.py` in either `Working` or `Testing`.

Impact:

- Changing `Ground.csv` alone will not change the rendered floor.
- The floor shown depends on `graphics/tilemap/ground.png`.
- Commit `f0faec5` updated `graphics/Ground/ground.png`, but code loads `../graphics/tilemap/ground.png`; these are different paths in the root/Testing asset layout.

## Recommended Fix Plan

Do these one at a time, testing after each step.

### Step 1 — Clean the Git working tree line endings

Current diffs appear to be line-ending-only. Before real fixes, normalize line endings to avoid noisy diffs.

Suggested `.gitattributes`:

```gitattributes
*.py text eol=lf
*.md text eol=lf
*.csv text eol=lf
*.tmx text eol=lf
*.tsx text eol=lf
*.png binary
*.wav binary
*.ttf binary
```

### Step 2 — Fix the collision/boundary export

In Tiled, create/export a sparse collision layer where only blocked tiles have values and walkable space is `-1`.

Target: `Boundary.csv` should contain only walls/solid obstacles, not 65k+ cells.

### Step 3 — Replace hardcoded entity IDs with a map dictionary

Example:

```python
ENTITY_MAP = {
    '390': 'bamboo',
    '391': 'spirit',
    '392': 'raccoon',
    '393': 'squid',
}
PLAYER_SPAWN_ID = '394'
```

For the new map, decide what IDs `0`, `1`, `2`, `16`, `17`, `18`, `32`, `33`, and `50` are supposed to mean. Do not default unknown IDs to squid.

### Step 4 — Decode Tiled GIDs instead of using direct list indexes

Tiled CSV values are global tile IDs. They can also include flip flags. Do not do `graphics[int(col)]` for new tilesets.

Implement a tile resolver that:

1. masks Tiled flip flags,
2. subtracts the tileset `firstgid`,
3. maps the local tile ID to the correct image file.

### Step 5 — Re-enable building/nature only after the ID resolver works

Once GID mapping is correct, uncomment/rewrite the building/nature creation logic.

### Step 6 — Add camera culling

Only draw/update sprites near the screen. At minimum, skip drawing sprites whose rect is outside a padded camera rectangle.

Concept:

```python
camera_rect = pygame.Rect(self.offset.x - 128, self.offset.y - 128, WIDTH + 256, HEIGHT + 256)
for sprite in sorted(self.sprites(), key=lambda sprite: sprite.rect.centery):
    if sprite.rect.colliderect(camera_rect):
        self.display_surface.blit(sprite.image, sprite.rect.topleft - self.offset)
```

### Step 7 — Avoid creating every static map tile as a sprite if possible

For a 256 x 256 map, consider pre-rendering static layers to one/few surfaces, then using sprites only for interactive objects, collision, enemies, and the player.

## Implemented Performance Fix - 2026-08-16

The FPS-focused code fix is now limited to `Testing/code`; `Working/code` is left as the baseline.

- Added `SpatialObstacleGroup` in `Testing/code/level.py`.
  - Static obstacle tiles are indexed by map cell.
  - `Entity.collision()` now asks the obstacle group for nearby obstacles when available instead of scanning every obstacle sprite.
- Added camera culling in `YSortCameraGroup.custom_draw()`.
  - The floor is still drawn normally.
  - Dynamic sprites are only sorted/drawn if their rect intersects the current screen area plus one-tile padding.
- Added 50 x 50 startup map-window creation around the player spawn.
  - `Testing/code/level.py` now finds the player spawn in `Entities.csv` first.
  - It creates a 50 x 50 tile `map_creation_window` around that spawn.
  - Boundary/entity sprite creation is limited to that window instead of the whole 256 x 256 map.
  - Unknown entity IDs are skipped instead of defaulting to squid.
- Added performance regression tests in `Testing/tests/test_map_window_performance.py`.

Verification run:

```text
pytest Testing/tests/test_map_window_performance.py -q
5 passed
```

Headless smoke test result using the project venv:

```text
Testing/code:
level_created_seconds 2.279
map_window <rect(68, 138, 50, 50)>
visible_sprites 1
obstacle_sprites 2491
nearby_obstacles_for_player 0
draw_seconds 0.0004
```

Previous Testing smoke result before the 50 x 50 creation window:

```text
level_created_seconds 12.058
visible_sprites 103
obstacle_sprites 65433
draw_seconds 0.0003
```

Result: startup obstacle creation dropped from 65,433 obstacle sprites to 2,491, and headless level creation dropped from ~12 seconds to ~2.3 seconds in this environment.

## CSV Entity and Nature ID Audit - 2026-08-16

`CSV file/Entities.csv` and `Testing/map/Entities.csv` are identical. The player spawn is ID `394` at tile position `(93, 163)`. The 50 x 50 startup window around that spawn is `(68, 138)` through `(118, 188)`.

Entity IDs in the full CSV:

| ID | Count | Code handling |
|---:|---:|---|
| `0` | 8 | enemy spawn |
| `1` | 24 | enemy spawn |
| `2` | 29 | enemy spawn |
| `16` | 4 | enemy spawn for 2x2 creature top-left only |
| `17` | 4 | ignored; 2x2 creature top-right |
| `18` | 17 | enemy spawn |
| `32` | 4 | ignored; 2x2 creature bottom-left |
| `33` | 4 | ignored; 2x2 creature bottom-right |
| `50` | 8 | enemy spawn |
| `394` | 1 | player spawn |

The 2x2 entity blocks are consistently laid out as `16,17` over `32,33`, so only `16` should create an enemy. `17`, `32`, and `33` must not create separate enemies.

Entities inside the current 50 x 50 startup window:

| ID | Count | Positions |
|---:|---:|---|
| `0` | 2 | `(108,146)`, `(98,187)` |
| `2` | 3 | `(89,148)`, `(85,156)`, `(116,163)` |
| `394` | 1 | `(93,163)` |

Nature IDs inside the current startup window:

| Nature ID | Count |
|---:|---:|
| `113` | 234 |
| `114` | 256 |
| `115` | 218 |
| `128` | 5 |
| `129` | 4 |
| `130` | 6 |
| `131` | 3 |

Nature exists near the player. It is now rendered in `Testing/code/level.py` through a Tiled local/global ID resolver and the source `Tileset/nature/nature.png` tileset image, instead of directly indexing the incomplete `Testing/graphics/Nature` split-image folder.

## Global Nature and Monster Tile ID Fix - 2026-08-16

`Map/map2.tmx` uses Tiled global IDs, while the exported CSV files under `Testing/map/` use local tile IDs with `-1` for empty cells. The relevant `firstgid` values are:

| Tileset | `firstgid` | CSV local ID example | TMX global ID example |
|---|---:|---:|---:|
| `nature` | `2049` | `49` | `2098` |
| `monster` | `8833` | `16` | `8849` |

The full `Nature.csv` local IDs map to these global Tiled IDs:

| Local IDs | Global IDs | Notes |
|---|---|---|
| `49`, `50`, `51` | `2098`, `2099`, `2100` | sparse nature objects |
| `67`, `68`, `69` | `2116`, `2117`, `2118` | sparse nature objects |
| `80`, `81`, `82`, `83` | `2129`, `2130`, `2131`, `2132` | sparse nature objects |
| `113`, `114`, `115` | `2162`, `2163`, `2164` | main grass/nature fill near the player window |
| `118` | `2167` | sparse nature object |
| `128`, `129`, `130`, `131` | `2177`, `2178`, `2179`, `2180` | nature cluster IDs near the player window |
| `134`, `150`, `166`, `167`, `168`, `169` | `2183`, `2199`, `2215`, `2216`, `2217`, `2218` | additional nature cluster IDs |

Code changes made in `Testing/code`:

- Added Tiled ID helpers in `Testing/code/level.py`: `decode_tiled_gid`, `tile_local_id`, `tile_global_id`, `nature_tile_index`, and `monster_name_for_tile`.
- Renamed the runtime enemy mapping to `MONSTER_IDS` / `IGNORED_MONSTER_TILE_IDS` to match the `Monster` tileset/layer naming in `Map/map2.tmx`; `ENEMY_IDS` aliases remain for compatibility.
- Re-enabled nature sprite creation for the 50 x 50 startup window by loading `Tileset/nature/nature.png` as a 256-tile local-ID indexed tileset instead of indexing the incomplete `Testing/graphics/Nature` folder.
- Added `nature` to `HITBOX_OFFSET` so nature tiles can be created as collidable/attackable map tiles without a `KeyError`.
- Kept monster/entity handling windowed and explicit: duplicate 2x2 monster tiles `17`, `32`, and `33` are ignored; unknown IDs do not default to squid.

Verification after the fix:

```text
pytest Testing/tests/test_map_window_performance.py -q
11 passed

Headless smoke test:
level_created_seconds 2.697
map_window <rect(68, 138, 50, 50)>
visible_sprites 732
nature_sprites 726
enemy_sprites 5
obstacle_sprites 935
```

## Player-Centered Spawn Window and Destroyable Nature Fill - 2026-08-16

The active Testing map window is now explicitly centered on the current character/player position when enemies or nature respawn. Initial map creation still starts around the player spawn `(93, 163)`, but runtime respawn calls recalculate the 50 x 50 window from `player.rect.center`.

Behavior changes in `Testing/code`:

- Added `player_tile_position()` and `update_map_creation_window_around_player()` in `Testing/code/level.py`.
- Updated enemy respawn so spawned monsters are constrained to the current player-centered 50 x 50 map window.
- Updated nature respawn so destroyable nature tiles refresh around the current player-centered 50 x 50 map window.
- Added deterministic texture fill through `iter_texture_fill_tiles()`: sparse empty cells inside the active window receive additional nature/grass-like tiles from IDs `113`, `114`, `115`, `128`, `129`, `130`, and `131`. This reduces plain empty space without editing the source CSV by hand.
- Nature tiles are now placed in `attackable_sprites` and are destroyable by the existing attack path, like grass.
- `Testing/code/enemy.py` now resolves monster sprites and audio relative to the code file, so respawn tests do not depend on the shell's current directory for enemy asset loading.

Verification after this update:

```text
SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy .venv/bin/python -B -m pytest Testing/tests/test_map_window_performance.py -q
14 passed

Headless smoke test from Testing/code:
level_created_seconds 2.926
initial_window <rect(68, 138, 50, 50)>
visible_sprites 955
nature_sprites 949
attackable_nature 949
enemy_sprites 5
obstacle_sprites 1158
moved_window <rect(200, 185, 50, 50)>
moved_enemy_sprites 14
moved_nature_sprites 458
```

## Chunked Safe Nature Fill and Monster Groups - 2026-08-16

The texture filler was changed from evenly spaced single tiles into seeded pseudo-random chunks. It now preserves an escape route so the spawn/player area cannot be boxed in by filler.

Behavior changes in `Testing/code/level.py`:

- Added `is_reserved_walkway_tile()` to reserve a cross-shaped corridor through the active 50 x 50 window plus a small safe bubble around the player/spawn.
- Updated `iter_texture_fill_tiles()` to create grouped/chunked destroyable nature clusters instead of isolated dots.
- Skipped both CSV nature tiles and generated filler tiles on the reserved route, so there is always a path out of the player area and no filler-created dead end.
- Kept generated nature tiles destroyable/attackable through the existing nature/grass attack path.
- Added `iter_monster_group_spawns()` and `create_monster_group_spawns()` so each CSV monster anchor can spawn nearby companion monsters in a small group while avoiding the player tile and blocked/reserved tiles.

Verification after this update:

```text
SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy .venv/bin/python -B -m pytest Testing/tests/test_map_window_performance.py -q
18 passed

Headless smoke test from Testing/code:
level_created_seconds 3.668
initial_window <rect(68, 138, 50, 50)>
center (93, 163)
nature_sprites 795
blocked_corridor_nature 0
enemy_sprites_grouped 15
moved_window <rect(200, 185, 50, 50)>
moved_enemy_sprites_grouped 42
```

## Five-Second Streaming Window Update - 2026-08-16

The Testing map now streams local content around the player every 5 seconds instead of relying on the original spawn location or rebuilding content every frame. Updating every frame would be too expensive for the 256 x 256 map; the 5-second cadence keeps movement smooth while still refreshing the active 50 x 50 world window as the player moves.

Behavior changes in `Testing/code/level.py`:

- Added `MAP_STREAM_UPDATE_INTERVAL = 5000`.
- Added `update_streaming_world(current_time)`, which only regenerates content when 5 seconds have elapsed.
- Added `stream_world_window()`, `clear_streamed_world()`, and `populate_current_window()` to rebuild local boundary tiles, nature/filler, CSV monsters, grouped monsters, and ambient monster groups around the current player tile.
- Replaced the old long enemy/nature respawn timers in `run()` with the 5-second streaming update.
- Ambient monster groups now fill active windows even when the CSV entity layer has few or no monster anchors nearby.
- Old streamed tiles/enemies are cleared before rebuilding so sprite counts stay bounded instead of growing every update.

Verification after this update:

```text
SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy .venv/bin/python -B -m pytest Testing/tests/test_map_window_performance.py -q
21 passed

Headless smoke test from Testing/code:
interval_ms 5000
initial_window <rect(68, 138, 50, 50)>
initial_enemies 24
initial_visible 820
before_4999 False <rect(68, 138, 50, 50)>
at_5000 True <rect(200, 185, 50, 50)>
streamed_enemies 51
streamed_visible 320
```

## [SUGGESTION] Refactor Candidates

### [SUGGESTION] Merge duplicate `Working/code` and `Testing/code`

Most code files are identical between both folders. Keep one shared codebase and switch maps through config instead of duplicating Python files.

Suggested direction:

```python
MAP_PROFILE = "working"  # or "testing"
MAP_DIR = f"../maps/{MAP_PROFILE}"
```

### [SUGGESTION] Extract map loading from `Level.create_map()`

`create_map()` currently mixes CSV parsing, tile creation, player spawning, enemy spawning, graphics loading, and Tiled ID handling. Split into:

- `map_loader.py`
- `tile_resolver.py`
- `entity_factory.py`
- slimmer `level.py`

### [SUGGESTION] Replace hardcoded entity IDs with a registry

Current logic hardcodes entity IDs in multiple places and defaults unknown IDs to squid. Use a dictionary and skip/log unknown IDs instead.

```python
ENTITY_IDS = {
    "390": "bamboo",
    "391": "spirit",
    "392": "raccoon",
    "393": "squid",
}
PLAYER_SPAWN_ID = "394"
```

### [SUGGESTION] Add a real Tiled GID resolver

The new map uses Tiled global tile IDs, including flip-flag encoded values. Do not use `graphics[int(col)]` for new tilesets. Decode GIDs, remove flip flags, subtract `firstgid`, then map to the right image file.

### [SUGGESTION] Replace hardcoded relative paths

Many files rely on paths like `../graphics/...` and `../map/...`, which only work when running from `Working/code` or `Testing/code`. Use a `paths.py` helper based on `Path(__file__).resolve()`.

### [SUGGESTION] Split `Player.input()` into smaller handlers

`Player.input()` currently handles movement, attack, magic, weapon switching, and magic switching. Split into helper methods and cache `weapon_names` / `magic_names` instead of repeatedly calling `list(...)`.

### [SUGGESTION] Remove commented-out old code

Clean or convert commented blocks in `player.py`, `level.py`, `main.py`, and `enemy.py` into real feature flags/config. This will make it clearer which systems are intentionally disabled.

### [SUGGESTION] Replace raw `pickle` save/load later

`pickle` is acceptable for a personal local prototype, but JSON save data is safer and easier to inspect/debug.

## Maintenance Notes

- Keep `Working/` as the known-good baseline until the new map works.
- Treat `Testing/` as the new-map migration area.
- Avoid editing both copies unless the change is intentionally being ported.
- The project currently duplicates most code between `Working/code` and `Testing/code`; once stable, consider merging to one codebase with a configurable map path.
