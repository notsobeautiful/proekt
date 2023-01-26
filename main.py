import math
import os
import sys
import pygame
import random
import schedule

pygame.font.init()


# загрузка изображений
def load_image(name, colorkey=None):
    fullname = os.path.join('data', name)
    image = pygame.image.load(fullname)
    if colorkey is not None:
        image = image.convert()
        if colorkey == -1:
            colorkey = image.get_at((0, 0))
        image.set_colorkey(colorkey)
    else:
        image = image.convert_alpha()
    return image


# вращение изображений
def rot_center(image, rect, angle):
    rot_image = pygame.transform.rotate(image, angle)
    rot_rect = rot_image.get_rect(center=rect.center)
    return rot_image, rot_rect


# стартовый экран
def start_screen():
    intro_text = ["ЗАСТАВКА", "",
                  "Правила игры",
                  "WASD - управление,",
                  "ЛКМ - начать игру",
                  "Q и E - соответственно уменьшение и увеличение громкости"]

    fon = pygame.transform.scale(load_image('fon.png', colorkey=None), (width, height))
    screen = pygame.display.set_mode((width, height))
    screen.blit(fon, (0, 0))
    font = pygame.font.Font(None, 30)
    text_coord = 50
    for line in intro_text:
        string_rendered = font.render(line, 1, pygame.Color('white'))
        intro_rect = string_rendered.get_rect()
        text_coord += 10
        intro_rect.top = text_coord
        intro_rect.x = 10
        text_coord += intro_rect.height
        screen.blit(string_rendered, intro_rect)

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
            elif event.type == pygame.KEYDOWN or event.type == pygame.MOUSEBUTTONDOWN:
                screen.fill((0, 0, 0))
                return  # начинаем игру
        pygame.display.flip()


# объявление переменных и инициализация pygame
pygame.mixer.pre_init(44100, -16, 1, 512)
pygame.init()
pygame.display.set_caption('Descent')
pygame.mixer.music.load('data/M.O.O.N - Hydrogen.mp3')
pygame.mixer.music.play(-1)
infos = pygame.display.Info()
width = height = infos.current_h - 100
screen = pygame.display.set_mode((width, height))
start_screen()
number_of_clasters = 20
tile_size = 240
state_of_level = 0
difficulty = 10
kill_counter = 0
vol = 1.0
h = 0
p = 1
f1 = pygame.font.Font(None, width // 2 // 20)

# загрузка изображений
player_image = load_image('freak.png', (220, 255, 0))
bullet_image = load_image('bullet.png', (0, 0, 0))
enemy_image = pygame.transform.scale(load_image('enemy.png', (192, 255, 15)), (160, 160))
floor_image = pygame.transform.scale(load_image('floor.png'), (240, 240))
stairs_image = load_image('stairs.png', colorkey=None)
wall1_vert = load_image('1_tile_long_wall.png')
wall2_vert = load_image('2_tile_long_wall.png')
wall1_hor = pygame.transform.rotate(load_image('1_tile_long_wall.png'), 90)
wall2_hor = pygame.transform.rotate(load_image('2_tile_long_wall.png'), 90)
shmurik = pygame.transform.scale(load_image('shmyrovozka.png'), (80, 80))

# загрузка звуков
shot_sound = pygame.mixer.Sound('data/vistrel.ogg')

# загрузка изображений для анимации
animation_ar = []
for i in range(8):
    animation_ar.append(
        pygame.transform.scale(load_image('frame_' + str(i) + '.png', colorkey=(255, 255, 255)), (100, 100)))

# объявление групп
all_sprites = pygame.sprite.Group()
player_group = pygame.sprite.Group()
bullets_group = pygame.sprite.Group()
enemy_bullets_group = pygame.sprite.Group()
enemy_group = pygame.sprite.Group()
walls_group = pygame.sprite.Group()
floor_group = pygame.sprite.Group()

running = True


# класс для замены курсора прицелом
class Cursor(pygame.sprite.Sprite):
    def __init__(self, image):
        super().__init__(all_sprites)
        self.image = image
        self.rect = pygame.Rect(0, 0, 16, 16)


# камера
class Camera:
    def __init__(self):
        self.rect = pygame.Rect(0, 0, width, height)

    def move(self, vector):
        global enemy_counter, difficulty, h, state_of_level, kill_counter

        self.rect[0] += vector[0]
        self.rect[1] += vector[1]

        for i in floor_group:
            i.move_with_camera(vector)

        for i in walls_group:
            i.move_with_camera(vector)

        for i in bullets_group:
            i.move_with_camera([math.sin(math.radians(i.angle)), math.cos(math.radians(i.angle))])
            if pygame.sprite.spritecollideany(i, walls_group):
                i.kill()

        for i in enemy_group:

            i.move_with_camera(vector)

            for j in bullets_group:
                if pygame.sprite.collide_mask(i, j):
                    kill_counter += 1
                    i.kill()
                    j.kill()
                    enemy_counter -= 1
                    break

            i.count += 1
            if i.count == i.danger:
                i.shot()
                i.count = 0

        for i in enemy_bullets_group:
            i.kill_count += 1
            if i.kill_count >= 700:
                i.kill()
            i.move_with_camera([math.sin(math.radians(i.angle)), math.cos(math.radians(i.angle))])
            if pygame.sprite.spritecollideany(i, walls_group):
                i.kill()
            if pygame.sprite.collide_mask(i, player):
                i.kill()
                player.rect[0] += 25
                player.rect[1] += 25
                player.image = shmurik
                with open('data/sth.txt', mode='r') as rt:
                    qw = int(rt.readline())
                    if int(qw < kill_counter):
                        with open("data/sth.txt", "w") as f:
                            f.write(str(kill_counter))
                        text.image = f1.render(str('Новый рекорд! ' + str(kill_counter)), False, (0, 0, 0),
                                               (255, 255, 255))
                    else:
                        text.image = f1.render(str('Рекорд не побит! Текущий рекорд - ' + str(qw)),
                                               False, (0, 0, 0), (255, 255, 255))

                kill_counter = 0
                all_sprites.draw(screen)
                pygame.display.flip()
                state_of_level = 0
                difficulty = 10
                pygame.time.wait(3000)
                generate_level(state_of_level)
                return 0

        mask_object.move_with_camera(vector)

        if (pygame.sprite.collide_mask(player, mask_object) and enemy_counter == 0):
            generate_level(state_of_level)


# игрок, его изображение, маска для пересечений
class Player(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__(player_group, all_sprites)
        self.image = player_image
        self.rect = pygame.Rect(width // 2 - 30, height // 2 - 30, 38, 38)
        self.mask = pygame.mask.from_surface(self.image)
        self.angle = 90


# пуля
class Bullet(pygame.sprite.Sprite):
    def __init__(self, image, x, y, angle):
        super().__init__(all_sprites, bullets_group)
        self.image = image
        self.angle = angle
        self.vector_x = 0
        self.vector_y = 0
        self.bullet_speed = 10
        self.rect = pygame.Rect(width // 2 - 18 - x, height // 2 - 18 - y, 15, 15)

    def move_with_camera(self, vector):
        self.vector_x += vector[0]
        self.vector_y += vector[1]
        while self.vector_x > 1:
            self.rect[0] -= self.bullet_speed
            self.vector_x -= 1
        while self.vector_y > 1:
            self.rect[1] -= self.bullet_speed
            self.vector_y -= 1
        while self.vector_x < -1:
            self.rect[0] += self.bullet_speed
            self.vector_x += 1
        while self.vector_y < -1:
            self.rect[1] += self.bullet_speed
            self.vector_y += 1


# пули противников
class EnemyBullet(pygame.sprite.Sprite):
    def __init__(self, image, x, y, angle):
        super().__init__(all_sprites, enemy_bullets_group)
        self.image = image
        self.angle = angle
        self.kill_count = 0
        self.vector_x = 0
        self.vector_y = 0
        self.bullet_speed = 10
        self.rect = pygame.Rect(width // 2 - 18 - x, height // 2 - 18 - y, 15, 15)

    def move_with_camera(self, vector):
        self.vector_x += vector[0]
        self.vector_y += vector[1]
        while self.vector_x > 1:
            self.rect[0] -= self.bullet_speed
            self.vector_x -= 1
        while self.vector_y > 1:
            self.rect[1] -= self.bullet_speed
            self.vector_y -= 1
        while self.vector_x < -1:
            self.rect[0] += self.bullet_speed
            self.vector_x += 1
        while self.vector_y < -1:
            self.rect[1] += self.bullet_speed
            self.vector_y += 1


# противники
class Enemy(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__(enemy_group, all_sprites)
        self.image = enemy_image
        self.mask = pygame.mask.from_surface(self.image)
        self.rect = pygame.Rect(x, y, 150, 150)
        self.danger = random.randint(10, 100)
        self.count = 0
        self.angle = 0

    def move_with_camera(self, vector):
        self.rect[0] -= vector[0]
        self.rect[1] -= vector[1]

    def shot(self):
        EnemyBullet(bullet_image, self.rect[0] - self.rect[2] // 2, self.rect[1] - self.rect[3] // 2, self.angle + (
            random.randint(-5, 5)))


# стены
class Wall(pygame.sprite.Sprite):
    def __init__(self, image, x, y, wd, hg):
        super().__init__(all_sprites, walls_group)
        self.image = image
        self.rect = pygame.Rect(x, y, wd, hg)
        self.mask = pygame.mask.from_surface(self.image)

    def move_with_camera(self, vector):
        self.rect[0] -= vector[0]
        self.rect[1] -= vector[1]


# пол и его изображение
class Floor(pygame.sprite.Sprite):
    def __init__(self, tile_x, tile_y, fl_image=floor_image):
        super().__init__(all_sprites, floor_group)
        self.image = fl_image
        self.rect = pygame.Rect(tile_x * tile_size, tile_y * tile_size, 240, 240)

    def move_with_camera(self, vector):
        self.rect[0] -= vector[0]
        self.rect[1] -= vector[1]


# объект для пересечения с игроком
class MaskObject(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__(all_sprites)
        self.rect = pygame.Rect(x * 240, y * 240, 240, 160)
        self.image = load_image('example.png', colorkey=None)
        self.mask = pygame.mask.from_surface(self.image)

    def move_with_camera(self, vector):
        self.rect[0] -= vector[0]
        self.rect[1] -= vector[1]


# для анимации
class AnimatedSprite(pygame.sprite.Sprite):
    def __init__(self, ar_of_images):
        super().__init__(all_sprites)
        self.ar = ar_of_images
        self.rect = pygame.Rect(0, 0, 100, 100)
        self.count = 0
        self.image = self.ar[self.count]


# текст
class Text(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__(all_sprites)
        self.image = f1.render(str(kill_counter), False, (0, 0, 0), (255, 255, 255))
        self.rect = pygame.Rect(width - 300, 0, 100, 24)

    def update(self):
        self.image = f1.render(str(kill_counter), False, (0, 0, 0), (255, 255, 255))


# генерация уровня, обновление переменных
def generate_level(state):
    global mask_object, player, state_of_level, cursor, animated_sprite, difficulty, camera, enemy_counter, kill_counter
    global text

    enemy_counter = difficulty

    for i in all_sprites:
        i.kill()

    if state == 1:
        mask_object = MaskObject(4, 4.33333333333333333333333)
    elif state == 0:
        mask_object = MaskObject(0, 0)

    for i in range(5):
        for j in range(5):
            if (i, j) != (0, 0) and (i, j) != (4, 4):
                a = random.randint(1, number_of_clasters)
                eval('claster' + str(a) + '(' + str(i) + ', ' + str(j) + ')')
    Floor(0, 0, stairs_image)
    Wall(wall1_hor, 0, tile_size * 2 // 3, 82, 6)
    Wall(wall2_hor, 82, tile_size * 2 // 3, 164, 6)
    Floor(4, 4, pygame.transform.rotate(stairs_image, 180))
    Wall(wall1_hor, tile_size * 4, tile_size * 4 + tile_size // 3, 82, 6)
    Wall(wall2_hor, tile_size * 4 + 82, tile_size * 4 + tile_size // 3, 164, 6)
    for i in range(5):
        # генерация горизонтальных стен
        Wall(wall1_hor, i * tile_size, -6, 82, 6)
        Wall(wall2_hor, i * tile_size + 81, -6, 164, 6)
        Wall(wall1_hor, i * tile_size, 5 * tile_size, 82, 6)
        Wall(wall2_hor, i * tile_size + 81, 5 * tile_size, 164, 6)

        # генерация вертикальных стен
        Wall(wall1_vert, 0, i * tile_size, 6, 82)
        Wall(wall2_vert, 0, i * tile_size + 82, 6, 164)
        Wall(wall1_vert, 5 * tile_size, i * tile_size, 6, 82)
        Wall(wall2_vert, 5 * tile_size, i * tile_size + 82, 6, 164)

    for i in range(difficulty):
        q = random.randint(0, 179)
        Enemy((q % 15) * 80 - 50, (q // 15) * 80)

    player = Player()
    difficulty += 1
    animated_sprite = AnimatedSprite(animation_ar)
    cursor = Cursor(load_image('cursor_image.png', (255, 255, 255)))

    camera = Camera()
    if state_of_level == 0:
        camera.move([(width) - 50, (height) - 30])
    else:
        camera.move([-(width // 2) + 120, -(height // 2) + 80])

    text = Text()

    state_of_level = 1 - state_of_level


# изменение картинки анимированного спрайта
def animation():
    animated_sprite.count += 1
    animated_sprite.image = animated_sprite.ar[animated_sprite.count % 8]


# следующие 20 функция нужны для генерации уровней
def claster1(tile_x, tile_y):
    Floor(tile_x, tile_y)
    Wall(wall2_vert, tile_x * tile_size + 76, tile_y * tile_size + 76, 6, 164)
    Wall(wall2_vert, tile_x * tile_size + 158, tile_y * tile_size, 6, 164)


def claster2(tile_x, tile_y):
    Floor(tile_x, tile_y)
    Wall(wall1_hor, tile_x * tile_size + 76, tile_y * tile_size + 76, 82, 6)
    Wall(wall1_vert, tile_x * tile_size + 76, tile_y * tile_size + 76, 6, 82)


def claster3(tile_x, tile_y):
    Floor(tile_x, tile_y)
    Wall(wall2_hor, tile_x * tile_size, tile_y * tile_size + 76, 164, 6)
    Wall(wall1_vert, tile_x * tile_size + 164, tile_y * tile_size + 76, 6, 82)


def claster4(tile_x, tile_y):
    Floor(tile_x, tile_y)
    Wall(wall2_hor, tile_x * tile_size + 76, tile_y * tile_size + 76, 164, 6)


def claster5(tile_x, tile_y):
    Floor(tile_x, tile_y)
    Wall(wall2_vert, tile_x * tile_size + 156, tile_y * tile_size + 76, 6, 164)


def claster6(tile_x, tile_y):
    Floor(tile_x, tile_y)
    Wall(wall2_hor, tile_x * tile_size, tile_y * tile_size + 76, 164, 6)


def claster7(tile_x, tile_y):
    Floor(tile_x, tile_y)
    Wall(wall2_hor, tile_x * tile_size, tile_y * tile_size + 158, 164, 6)


def claster8(tile_x, tile_y):
    Floor(tile_x, tile_y)
    Wall(wall2_vert, tile_x * tile_size + 76, tile_y * tile_size, 6, 164)


def claster9(tile_x, tile_y):
    Floor(tile_x, tile_y)
    Wall(wall2_vert, tile_x * tile_size + 76, tile_y * tile_size + 76, 6, 164)


def claster10(tile_x, tile_y):
    Floor(tile_x, tile_y)
    Wall(wall2_hor, tile_x * tile_size + 76, tile_y * tile_size + 158, 164, 6)


def claster11(tile_x, tile_y):
    Floor(tile_x, tile_y)
    Wall(wall2_vert, tile_x * tile_size + 158, tile_y * tile_size, 6, 164)


def claster12(tile_x, tile_y):
    Floor(tile_x, tile_y)
    Wall(wall1_hor, tile_x * tile_size + 78, tile_y * tile_size + 74, 82, 6)
    Wall(wall1_vert, tile_x * tile_size + 158, tile_y * tile_size, 6, 82)
    Wall(wall1_vert, tile_x * tile_size + 78, tile_y * tile_size + 74, 6, 82)


def claster13(tile_x, tile_y):
    Floor(tile_x, tile_y)
    Wall(wall1_hor, tile_x * tile_size + 78, tile_y * tile_size + 74, 82, 6)


def claster14(tile_x, tile_y):
    Floor(tile_x, tile_y)
    Wall(wall1_vert, tile_x * tile_size + 78, tile_y * tile_size + 74, 6, 82)


def claster15(tile_x, tile_y):
    Floor(tile_x, tile_y)
    Wall(wall1_vert, tile_x * tile_size + 78, tile_y * tile_size + 158, 6, 82)


def claster16(tile_x, tile_y):
    Floor(tile_x, tile_y)
    Wall(wall1_vert, tile_x * tile_size + 158, tile_y * tile_size + 74, 6, 82)


def claster17(tile_x, tile_y):
    Floor(tile_x, tile_y)


def claster18(tile_x, tile_y):
    Floor(tile_x, tile_y)


def claster19(tile_x, tile_y):
    Floor(tile_x, tile_y)


def claster20(tile_x, tile_y):
    Floor(tile_x, tile_y)


# задержка между выстрелами
def zadershka():
    global p
    p = 1


cursor_img_rect = (0, 0)
schedule.every(0.1).seconds.do(animation)
schedule.every(1).seconds.do(zadershka)
generate_level(state_of_level)
q, w = player.image, player.rect
cursor_new = (0, 0)
speed = 2
carta = 1
ar = [0, 0]

# главный игровой цикл
while running:
    text.update()

    if pygame.mouse.get_focused():
        pygame.mouse.set_visible(False)
    else:
        pygame.mouse.set_visible(True)

    vector = [0, 0]

    q = pygame.mouse.get_pos()

    if q != cursor_new:

        cursor.rect = (q[0] - 8, q[1] - 8)

        try:
            e = math.degrees(math.atan(((q[0] - width // 2) / (q[1] - height // 2))))
        except Exception:
            e = -90

        if q[1] >= player.rect[1] + 119:
            e = e + 180

        if e < 0 and (-90 <= e <= -77) and (cursor.rect[0] < player.rect[0]):
            e = 180 + e
        elif e > 180:
            e = -180 + (e - 180)

        q, w = player.image, player.rect
        player.image, player.rect = rot_center(player_image, player.rect, e)
        player.mask = pygame.mask.from_surface(player.image)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        if event.type == pygame.MOUSEBUTTONDOWN:
            if p == 1:
                shot_sound.play()
                new_bullet = Bullet(bullet_image, 0, 0, e)
                new_bullet.image, new_bullet.rect = rot_center(new_bullet.image, new_bullet.rect, e)
                p = 0

    vector = [0, 0]

    kpressed = pygame.key.get_pressed()

    boolw = kpressed[pygame.K_w]
    boola = kpressed[pygame.K_a]
    bools = kpressed[pygame.K_s]
    boold = kpressed[pygame.K_d]

    if boolw and boola:
        ar[1] = speed
        ar[0] = speed
        carta = 1
    elif boolw and boold:
        ar[1] = speed
        ar[0] = -speed
        carta = 1
    elif boold and bools:
        ar[1] = -speed
        ar[0] = -speed
        carta = 1
    elif bools and boola:
        ar[1] = -speed
        ar[0] = speed
        carta = 1
    elif boolw:
        ar[1] = speed
        ar[0] = 0
        carta = 1
    elif bools:
        ar[1] = -speed
        ar[0] = 0
        carta = 1
    elif boold:
        ar[0] = -speed
        ar[1] = 0
        carta = 1
    elif boola:
        ar[0] = speed
        ar[1] = 0
        carta = 1

    if kpressed[pygame.K_w]:
        vector[1] -= speed
    elif kpressed[pygame.K_s]:
        vector[1] += speed
    if kpressed[pygame.K_a]:
        vector[0] -= speed
    elif kpressed[pygame.K_d]:
        vector[0] += speed

    if kpressed[pygame.K_q]:
        vol -= 0.1
        pygame.mixer.music.set_volume(vol)
    elif kpressed[pygame.K_e]:
        vol += 0.1
        pygame.mixer.music.set_volume(vol)

    for i in walls_group:
        if pygame.sprite.collide_mask(player, i):
            if carta:
                camera.move([ar[0], ar[1]])
                carta = 0
            player.image, player.rect = q, w
            player.mask = pygame.mask.from_surface(player.image)

    for i in enemy_group:
        try:
            anglee = -math.degrees(math.atan(((i.rect[1] - height // 2) / (i.rect[0] - width // 2))))
            qwe = math.degrees(math.atan(((i.rect[0] - width // 2) / (i.rect[1] - height // 2))))
        except Exception:
            anglee = 0

        if i.rect[1] < player.rect[1] + 119:
            qwe = qwe + 180
            anglee = anglee + 180

        i.angle = anglee

        f, g = rot_center(enemy_image, i.rect, qwe)
        i.image, i.rect = f, g
        i.mask = pygame.mask.from_surface(i.image)

    camera.move(vector)

    screen.fill((255, 255, 255))

    all_sprites.draw(screen)
    cursor_new = q
    schedule.run_pending()
    pygame.display.flip()
