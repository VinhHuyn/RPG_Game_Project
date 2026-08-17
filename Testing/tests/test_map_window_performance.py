import os
import sys
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame

TESTING_ROOT = Path(__file__).resolve().parents[1]
TESTING_CODE = TESTING_ROOT / "code"
if str(TESTING_CODE) not in sys.path:
    sys.path.insert(0, str(TESTING_CODE))


class DummyBlitter:
    def __init__(self):
        self.calls = []

    def get_size(self):
        return (1280, 720)

    def blit(self, image, pos):
        self.calls.append((image, pos))


class DummySprite(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((64, 64))
        self.rect = self.image.get_rect(topleft=(x, y))
        self.hitbox = self.rect.copy()


def setup_module():
    pygame.init()
    pygame.display.set_mode((1280, 720))


def teardown_module():
    pygame.quit()


def build_level():
    from level import Level

    cwd = os.getcwd()
    os.chdir(TESTING_CODE)
    try:
        return Level()
    finally:
        os.chdir(cwd)


def test_map_creation_is_limited_to_50_by_50_window_around_player():
    level = build_level()

    assert level.map_creation_size_tiles == 50
    assert len(level.obstacle_sprites.sprites()) <= 50 * 50
    assert level.player is not None

    window = level.map_creation_window
    for sprite in level.obstacle_sprites.sprites():
        tile_x = sprite.hitbox.x // 64
        tile_y = sprite.hitbox.y // 64
        assert window.left <= tile_x < window.right
        assert window.top <= tile_y < window.bottom


def test_big_map_level_startup_stays_under_reasonable_sprite_count():
    level = build_level()

    # The old path created 65,433 obstacle sprites from Boundary.csv.
    # The windowed path should keep startup sprite creation bounded.
    assert len(level.obstacle_sprites.sprites()) < 3_000
    assert len(level.visible_sprites.sprites()) < 3_000


def test_windowed_map_creates_indexed_collision_tiles():
    level = build_level()

    assert len(level.obstacle_sprites.sprites()) > 0
    assert len(level.obstacle_sprites.spatial_index) > 0

    obstacle = level.obstacle_sprites.sprites()[0]
    assert obstacle in level.obstacle_sprites.get_nearby(obstacle.hitbox)


def test_windowed_map_spawns_nearby_enemies():
    from enemy import Enemy

    level = build_level()

    enemies = [sprite for sprite in level.visible_sprites.sprites() if isinstance(sprite, Enemy)]

    assert enemies


def test_monster_id_mapping_ignores_2x2_duplicate_tiles():
    from level import MONSTER_IDS, IGNORED_MONSTER_TILE_IDS

    assert '16' in MONSTER_IDS
    assert {'17', '32', '33'} <= IGNORED_MONSTER_TILE_IDS
    assert not ({'17', '32', '33'} & set(MONSTER_IDS))


def test_tiled_global_ids_resolve_to_local_nature_and_monster_ids():
    from level import nature_tile_index, monster_name_for_tile, tile_global_id

    assert tile_global_id('49', 'nature') == 2098
    assert nature_tile_index('2098') == 49
    assert nature_tile_index('49') == 49
    assert tile_global_id('16', 'monster') == 8849
    assert monster_name_for_tile('8849') == 'squid'
    assert monster_name_for_tile('8850') is None


def test_windowed_map_creates_resolved_nature_tiles():
    level = build_level()

    nature_tiles = [
        sprite for sprite in level.visible_sprites.sprites()
        if getattr(sprite, 'sprite_type', None) == 'nature'
    ]
    assert nature_tiles
    assert all(sprite.image.get_size() == (64, 64) for sprite in nature_tiles)


def test_testing_player_speed_is_not_debug_fast():
    level = build_level()

    assert level.player.stats['speed'] <= level.player.max_stats['speed']
    assert level.player.speed <= 10


def test_camera_draw_culls_offscreen_sprites():
    from level import YSortCameraGroup

    cwd = os.getcwd()
    os.chdir(TESTING_CODE)
    try:
        group = YSortCameraGroup()
    finally:
        os.chdir(cwd)

    near = DummySprite(0, 0)
    far = DummySprite(100_000, 100_000)
    player = DummySprite(640, 360)
    group.add(near, far)
    group.display_surface = DummyBlitter()

    group.custom_draw(player)

    drawn_sprites = [call[0] for call in group.display_surface.calls]
    assert near.image in drawn_sprites
    assert far.image not in drawn_sprites


def test_spatial_obstacle_group_returns_nearby_subset():
    from level import SpatialObstacleGroup

    group = SpatialObstacleGroup(cell_size=64)
    near = DummySprite(0, 0)
    far = DummySprite(10_000, 10_000)
    group.add(near, far)

    nearby = set(group.get_nearby(pygame.Rect(0, 0, 64, 64)))

    assert near in nearby
    assert far not in nearby
    assert len(nearby) < len(group.sprites())


def test_entity_collision_uses_spatial_obstacle_lookup():
    from entity import Entity

    class SpatialGroup:
        def __init__(self):
            self.calls = 0
            self.near = DummySprite(32, 0)

        def get_nearby(self, rect):
            self.calls += 1
            return [self.near]

        def __iter__(self):
            raise AssertionError("collision should use get_nearby() when available")

    entity = Entity([])
    entity.image = pygame.Surface((64, 64))
    entity.rect = entity.image.get_rect(topleft=(0, 0))
    entity.hitbox = entity.rect.copy()
    entity.direction.x = 1
    entity.obstacle_sprites = SpatialGroup()

    entity.collision("horizontal")

    assert entity.obstacle_sprites.calls == 1


def test_respawn_enemy_uses_current_player_centered_window():
    from enemy import Enemy
    from settings import TILESIZE

    level = build_level()
    level.player.rect.center = (225 * TILESIZE + TILESIZE // 2, 210 * TILESIZE + TILESIZE // 2)
    level.player.hitbox.center = level.player.rect.center

    level.clear_enemy()
    level.respawn_enemy()

    window = level.map_creation_window
    assert window.left == 200
    assert window.top == 185
    enemies = [sprite for sprite in level.visible_sprites.sprites() if isinstance(sprite, Enemy)]
    assert enemies
    for enemy in enemies:
        tile_x = enemy.rect.x // TILESIZE
        tile_y = enemy.rect.y // TILESIZE
        assert window.left <= tile_x < window.right
        assert window.top <= tile_y < window.bottom


def test_nature_tiles_are_destroyable_attackable_entities():
    level = build_level()

    nature_tiles = [
        sprite for sprite in level.visible_sprites.sprites()
        if getattr(sprite, 'sprite_type', None) == 'nature'
    ]

    assert nature_tiles
    assert any(sprite in level.attackable_sprites for sprite in nature_tiles)


def test_texture_fill_adds_destroyable_tiles_to_sparse_empty_window():
    from level import iter_texture_fill_tiles

    layouts = {
        'nature': [['-1' for _ in range(10)] for _ in range(10)],
        'boundary': [['-1' for _ in range(10)] for _ in range(10)],
    }
    window = pygame.Rect(0, 0, 10, 10)

    fills = list(iter_texture_fill_tiles(layouts, window))

    assert fills
    assert len(fills) >= 5
    assert all(0 <= col < 10 and 0 <= row < 10 for col, row, _ in fills)


def test_texture_fill_chunks_leave_player_escape_corridors_open():
    from level import iter_texture_fill_tiles, is_reserved_walkway_tile

    layouts = {
        'nature': [['-1' for _ in range(20)] for _ in range(20)],
        'boundary': [['-1' for _ in range(20)] for _ in range(20)],
    }
    window = pygame.Rect(0, 0, 20, 20)
    center = (10, 10)

    fills = list(iter_texture_fill_tiles(layouts, window, center))
    fill_positions = {(col, row) for col, row, _ in fills}

    assert fills
    assert not any(is_reserved_walkway_tile(col, row, window, center) for col, row in fill_positions)
    # At least one adjacent pair proves texture fill is chunk/group based, not isolated dots.
    assert any((col + 1, row) in fill_positions or (col, row + 1) in fill_positions for col, row in fill_positions)


def test_runtime_texture_fill_keeps_player_spawn_escape_route_open():
    from level import is_reserved_walkway_tile
    from settings import TILESIZE

    level = build_level()
    center = level.player_tile_position()
    blocked_nature = {
        (sprite.rect.x // TILESIZE, sprite.rect.y // TILESIZE)
        for sprite in level.visible_sprites.sprites()
        if getattr(sprite, 'sprite_type', None) == 'nature'
    }

    assert not any(is_reserved_walkway_tile(col, row, level.map_creation_window, center) for col, row in blocked_nature)


def test_monster_group_spawns_add_companions_near_anchor_monsters():
    from level import iter_monster_group_spawns

    layouts = {
        'entities': [['-1' for _ in range(10)] for _ in range(10)],
        'boundary': [['-1' for _ in range(10)] for _ in range(10)],
        'nature': [['-1' for _ in range(10)] for _ in range(10)],
    }
    layouts['entities'][5][5] = '0'
    window = pygame.Rect(0, 0, 10, 10)

    group_spawns = list(iter_monster_group_spawns(layouts, window, (2, 2)))

    assert group_spawns
    assert len(group_spawns) >= 2
    assert all(monster_name == 'bamboo' for _, _, monster_name in group_spawns)
    assert all(abs(col - 5) <= 2 and abs(row - 5) <= 2 for col, row, _ in group_spawns)


def test_respawn_enemy_creates_grouped_monsters_without_spawning_on_player():
    from enemy import Enemy
    from settings import TILESIZE

    level = build_level()
    center = level.player_tile_position()
    level.clear_enemy()
    level.respawn_enemy()

    enemies = [sprite for sprite in level.visible_sprites.sprites() if isinstance(sprite, Enemy)]
    enemy_tiles = {(enemy.rect.x // TILESIZE, enemy.rect.y // TILESIZE) for enemy in enemies}

    assert len(enemies) > 5
    assert center not in enemy_tiles


def test_streaming_world_interval_is_five_seconds_not_every_frame():
    from level import MAP_STREAM_UPDATE_INTERVAL

    level = build_level()
    calls = []
    level.stream_world_window = lambda: calls.append('stream')
    level.last_stream_update_time = 1000

    level.update_streaming_world(5999)
    assert calls == []

    level.update_streaming_world(6000)
    assert calls == ['stream']
    assert level.last_stream_update_time == 6000
    assert MAP_STREAM_UPDATE_INTERVAL == 5000


def test_streaming_world_moves_window_and_regenerates_local_content():
    from enemy import Enemy
    from settings import TILESIZE

    level = build_level()
    initial_window = level.map_creation_window.copy()

    level.player.rect.center = (225 * TILESIZE + TILESIZE // 2, 210 * TILESIZE + TILESIZE // 2)
    level.player.hitbox.center = level.player.rect.center
    level.stream_world_window()

    assert level.map_creation_window != initial_window
    assert level.map_creation_window.left == 200
    assert level.map_creation_window.top == 185

    nature_tiles = [sprite for sprite in level.visible_sprites.sprites() if getattr(sprite, 'sprite_type', None) == 'nature']
    enemies = [sprite for sprite in level.visible_sprites.sprites() if isinstance(sprite, Enemy)]
    assert nature_tiles
    assert enemies
    for sprite in nature_tiles + enemies:
        tile_x = sprite.rect.x // TILESIZE
        tile_y = sprite.rect.y // TILESIZE
        assert level.map_creation_window.left <= tile_x < level.map_creation_window.right
        assert level.map_creation_window.top <= tile_y < level.map_creation_window.bottom


def test_streaming_world_clears_old_window_tiles_to_keep_sprite_count_bounded():
    level = build_level()
    initial_visible = len(level.visible_sprites.sprites())
    initial_obstacles = len(level.obstacle_sprites.sprites())

    level.stream_world_window()
    level.stream_world_window()

    assert len(level.visible_sprites.sprites()) <= initial_visible + 200
    assert len(level.obstacle_sprites.sprites()) <= initial_obstacles + 200
