import pygame, csv, os, random


class Tile(pygame.sprite.Sprite):
    def __init__(self, image, x, y, spritesheet, type=None, properties=False, info=None):
        pygame.sprite.Sprite.__init__(self)
        self.image = spritesheet.parse_sprite(image)

        if type == 'door':
            self.door_info = info
            self.collider = properties

        if type == 'floor':
            self.spawn = properties

        self.rect = self.image.get_rect()
        self.rect.x, self.rect.y = x, y

    def draw(self, surface):
        surface.blit(self.image, (self.rect.x, self.rect.y))


class TileMap:
    def __init__(self, filename, spritesheet, level):
        self.tile_size = 32
        self.start_x, self.start_y = 0, 0
        self.spritesheet = spritesheet
        self.map_completed = False
        self.level = level
        self.without_enemies = True

        self.floor = pygame.sprite.Group()
        self.fog = []
        self.chest = []
        self.wall = pygame.sprite.Group()
        self.door = []
        self.terminals = []
        self.other = []
        self.just_floor = []

        self.map_h, self.map_w = 0, 0
        self.map = []
        self.read_csv(filename)
        self.load_tiles()
        self.map_surface = pygame.Surface((self.map_w, self.map_h))
        self.load_map()

    def get_level_size(self):
        return self.map_w, self.map_h

    def get_turn_rect(self):
        r = []
        chest_r = []
        turn_rect = []

        for tile in self.chest:
            chest_r.append(tile)
        for tile in self.wall:
            chest_r.append(tile.rect)

        for tile in self.floor:
            if tile.rect not in chest_r:
                r.append(tile.rect)

        for tile in r:
            temp_tile_l = tile.copy()
            temp_tile_r = tile.copy()
            temp_tile_u = tile.copy()
            temp_tile_d = tile.copy()
            temp_tile_l.x -= 32
            temp_tile_r.x += 32
            temp_tile_u.y -= 32
            temp_tile_d.y += 32

            temp_int = 0

            if temp_tile_r in r:
                temp_int += 1
            if temp_tile_l in r:
                temp_int += 1
            if temp_tile_u in r:
                temp_int += 1
            if temp_tile_d in r:
                temp_int += 1

            if temp_int >= 3:
                turn_rect.append(tile)

        return turn_rect

    def wall_destroying(self, explosion_rect):

        r = []
        turns = []
        chests = []

        for tile in explosion_rect:
            for chest in self.chest:
                if chest.rect.collidepoint(tile.center):
                    chests.append(chest.rect)
                    r.append(chest.rect)
                    self.just_floor.append(chest.rect)
                    self.chest.remove(chest)

        if len(chests) != 0:
            new_r = []
            for rect in r:
                temp_tile_l = rect.copy()
                temp_tile_r = rect.copy()
                temp_tile_u = rect.copy()
                temp_tile_d = rect.copy()
                temp_tile_l.x -= 32
                temp_tile_r.x += 32
                temp_tile_u.y -= 32
                temp_tile_d.y += 32
                if temp_tile_l in self.just_floor:
                    new_r.append(temp_tile_l)
                if temp_tile_r in self.just_floor:
                    new_r.append(temp_tile_r)
                if temp_tile_u in self.just_floor:
                    new_r.append(temp_tile_u)
                if temp_tile_d in self.just_floor:
                    new_r.append(temp_tile_d)
                new_r.append(rect)

            for tile in new_r:
                temp_tile_l = tile.copy()
                temp_tile_r = tile.copy()
                temp_tile_u = tile.copy()
                temp_tile_d = tile.copy()
                temp_tile_l.x -= 32
                temp_tile_r.x += 32
                temp_tile_u.y -= 32
                temp_tile_d.y += 32

                temp_int = 0

                if temp_tile_r in self.just_floor:
                    temp_int += 1
                if temp_tile_l in self.just_floor:
                    temp_int += 1
                if temp_tile_u in self.just_floor:
                    temp_int += 1
                if temp_tile_d in self.just_floor:
                    temp_int += 1

                if temp_int >= 3:
                    turns.append(tile)

            self.load_map()

        return turns, chests

    def get_door_rect(self):
        r = []
        for tile in self.door:
            r.append([tile.rect, tile.door_info, tile.collider])
        return r

    def get_terminal_rect(self):
        r = []
        for terminal in self.terminals:
            r.append(terminal.rect)
        return r

    def get_hard_wall(self):
        r = []
        for tile in self.wall:
            r.append(tile.rect)
        for tile in self.door:
            if tile.collider is True:
                r.append(tile.rect)
        return r

    def get_soft_wall(self):
        r = []
        for tile in self.chest:
            r.append(tile.rect)
        return r

    def get_colliders(self):
        r = []
        for tile in self.chest:
            r.append(tile.rect)
        for tile in self.door:
            if tile.collider is True:
                r.append(tile.rect)
        for tile in self.wall:
            r.append(tile.rect)
        return r

    def get_spawn_rect(self):
        r = []

        for tile in self.floor.sprites():
            if tile.spawn is True:
                r.append(tile.rect)
        return r

    def draw_map(self, s, surface):
        surface.blit(self.map_surface, (0 - s[0], 0 - s[1]))

    def load_map(self):
        self.floor.draw(self.map_surface)
        for tile in self.chest:
            tile.draw(self.map_surface)
        for tile in self.door:
            tile.draw(self.map_surface)
        self.wall.draw(self.map_surface)
        for tile in self.terminals:
            tile.draw(self.map_surface)
        for tile in self.other:
            tile.draw(self.map_surface)

    def load_doors(self):
        for tile in self.door:
            if tile.collider is True:
                if self.map_completed is True:
                    tile.image = self.spritesheet.parse_sprite('door_0')

        for tile in self.door:
            tile.draw(self.map_surface)

    def load_floor(self):
        self.floor.draw(self.map_surface)

    def read_csv(self, filename):
        with open(os.path.join(filename)) as data:
            data = csv.reader(data, delimiter=',')
            for row in data:
                self.map.append(list(row))

    def load_tiles(self):
        spawn_points = 0
        floor = ['floor_0', 'floor_1', 'floor_2']
        x, y = 0, 0
        for row in self.map:
            x = 0

            for tile in row:
                if tile == '30':
                    self.floor.add(Tile(random.choice(floor), x * self.tile_size, y * self.tile_size, self.spritesheet, 'floor'))
                    rect = pygame.Rect(x * self.tile_size, y * self.tile_size, 32, 32)
                    self.just_floor.append(rect)
                elif tile[0] == 'd':
                    img = 'background'
                    collider = False
                    if tile[2] == 'n':
                        collider = True
                        img = 'door_1'
                    elif tile[2] == 'd':
                        img = 'door_down'
                    elif tile[2] == 'i':
                        collider = True
                        img = 'door_0'
                    self.door.append(Tile(img, x * self.tile_size, y * self.tile_size,
                                          self.spritesheet, 'door', collider, tile))
                elif tile == '10':
                    self.wall.add(Tile('corner_0', x * self.tile_size, y * self.tile_size, self.spritesheet))
                elif tile == '3':
                    self.wall.add(Tile('wall_up', x * self.tile_size, y * self.tile_size, self.spritesheet))
                elif tile == '11':
                    self.wall.add(Tile('corner_1', x * self.tile_size, y * self.tile_size, self.spritesheet))
                elif tile == '6':
                    self.wall.add(Tile('wall_left', x * self.tile_size, y * self.tile_size, self.spritesheet))
                elif tile == '1':
                    self.wall.add(Tile('wall_1', x * self.tile_size, y * self.tile_size, self.spritesheet))
                elif tile == '5':
                    self.wall.add(Tile('wall_right', x * self.tile_size, y * self.tile_size, self.spritesheet))
                elif tile == '12':
                    self.wall.add(Tile('corner_2', x * self.tile_size, y * self.tile_size, self.spritesheet))
                elif tile == '4':
                    self.wall.add(Tile('wall_down', x * self.tile_size, y * self.tile_size, self.spritesheet))
                elif tile == '13':
                    self.wall.add(Tile('corner_3', x * self.tile_size, y * self.tile_size, self.spritesheet))
                # new
                elif tile == '0':
                    self.wall.add(Tile('wall_0', x * self.tile_size, y * self.tile_size, self.spritesheet))
                elif tile == '2':
                    self.wall.add(Tile('wall_2', x * self.tile_size, y * self.tile_size, self.spritesheet))
                elif tile == '7':
                    self.wall.add(Tile('wall_down_f', x * self.tile_size, y * self.tile_size, self.spritesheet))
                elif tile == '8':
                    self.wall.add(Tile('wall_up_f', x * self.tile_size, y * self.tile_size, self.spritesheet))
                elif tile == '9':
                    self.wall.add(Tile('wall_f', x * self.tile_size, y * self.tile_size, self.spritesheet))
                elif tile == '14':
                    self.wall.add(Tile('corner_4', x * self.tile_size, y * self.tile_size, self.spritesheet))
                elif tile == '15':
                    self.wall.add(Tile('corner_5', x * self.tile_size, y * self.tile_size, self.spritesheet))
                elif tile == '16':
                    self.wall.add(Tile('corner_7', x * self.tile_size, y * self.tile_size, self.spritesheet))
                elif tile == '17':
                    self.wall.add(Tile('corner_6', x * self.tile_size, y * self.tile_size, self.spritesheet))
                elif tile == '31':
                    temp = random.randint(0, 100)
                    if temp % 3 == 0:
                        self.floor.add(
                            Tile(random.choice(floor), x * self.tile_size, y * self.tile_size, self.spritesheet,
                                 'floor'))
                        self.chest.append(Tile('chest', x * self.tile_size, y * self.tile_size, self.spritesheet))
                    else:
                        self.floor.add(
                            Tile(random.choice(floor), x * self.tile_size, y * self.tile_size, self.spritesheet,
                                 'floor', True))
                        rect = pygame.Rect(x * self.tile_size, y * self.tile_size, 32, 32)
                        self.just_floor.append(rect)
                        spawn_points += 1
                elif tile == '32':
                    self.floor.add(Tile(random.choice(floor), x * self.tile_size, y * self.tile_size, self.spritesheet, 'floor', True))
                    rect = pygame.Rect(x * self.tile_size, y * self.tile_size, 32, 32)
                    self.just_floor.append(rect)
                    spawn_points += 1
                elif tile == '33':
                    self.wall.add(Tile('floor_f', x * self.tile_size, y * self.tile_size, self.spritesheet))
                    self.fog.append(pygame.Rect(x * self.tile_size, y * self.tile_size, self.tile_size, self.tile_size))
                elif tile == '37':
                    self.floor.add(Tile('floor_0', x * self.tile_size, y * self.tile_size, self.spritesheet, 'floor'))
                    self.chest.append(Tile('chest', x * self.tile_size, y * self.tile_size, self.spritesheet))
                elif tile == '38':
                    self.floor.add(Tile('floor_0', x * self.tile_size, y * self.tile_size, self.spritesheet, 'floor'))
                    self.wall.add(Tile('kolumn', x * self.tile_size, y * self.tile_size, self.spritesheet))
                elif tile == 't':
                    self.wall.add(Tile('wall_1', x * self.tile_size, y * self.tile_size, self.spritesheet))
                    self.terminals.append(Tile('terminal', x * self.tile_size, y * self.tile_size, self.spritesheet))
                else:
                    self.other.append(Tile('background', x * self.tile_size, y * self.tile_size, self.spritesheet))

                x += 1
            y += 1
        self.map_w, self.map_h = x * self.tile_size, y * self.tile_size

        if spawn_points != 0:
            self.without_enemies = False
