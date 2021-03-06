import pygame
import random
from os import path

from settings import WIDTH, HEIGHT, FPS, Color, PLATFORM_LIST, FONT_NAME, HS_FILE, SPRITESHEET, WORLD_ACC, POW_STR
from sprites import Player, game_elements, art, hitbox


class Game:

    def __init__(self):
        #  Basic flow control
        self.running = True
        self.playing = True
        self.mob_timer = 0

        #  Basic pygame vars
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        self.clock = pygame.time.Clock()
        self.font = pygame.font.match_font(FONT_NAME)

        # Basic py game initializations
        pygame.init()
        pygame.mixer.init()
        pygame.display.set_caption('Suriland')

        # Paths
        self.path = path.dirname(__file__)
        self.highscore_path = path.join(self.path, HS_FILE)
        self.spritesheet_path = path.join(self.path, SPRITESHEET)
        self.snd_path = path.join(self.path, 'snd')

        self._load_data()

    def _load_data(self):
        with open(self.highscore_path, 'r') as f:
            try:
                self.highscore = int(f.read())
            except Exception as e:
                self.highscore = 0
        self.jump_sound = pygame.mixer.Sound(path.join(self.snd_path, 'jump.wav'))
        self.spritesheet = art.Sheet(self.spritesheet_path)

    def new(self):
        self.score = 0
        self.playing = True

        self.all_sprites = pygame.sprite.LayeredUpdates()  # group that lets you specify the order sprites are drawn
        self.platforms = pygame.sprite.Group()
        self.powerups = pygame.sprite.Group()
        self.mobs = pygame.sprite.Group()
        self.clouds = pygame.sprite.Group()

        self.player = Player.Player(self)
        self.hitbox = hitbox.HitBox(self, self.player)

        for platform in PLATFORM_LIST:

            game_elements.BasePlatform(*platform, game=self, _type=2)

        self._run()

    def _run(self):

        while self.playing:

            self.clock.tick(FPS)
            self._events()
            self._update()
            self._draw()

    def _update(self):

        self.all_sprites.update()
        now = pygame.time.get_ticks()

        if now - self.mob_timer > 6000:
            self.mob_timer = now
            game_elements.Mob(self)

        #  Platform collision, TODO: see why sometimes when going down it won't detect collision.
        if self.player.vel.y > 0:
            hits = pygame.sprite.spritecollide(self.hitbox, self.platforms, False)

            if hits:
                lowest = hits[0]
                for hit in hits:
                    if hit.rect.bottom < lowest.rect.bottom:
                        lowest = hit

                if self.player.pos.y < lowest.rect.centery:
                    self.player.pos.y = lowest.rect.top + 1
                    self.player.vel.y = 0
                    self.player.jumping = False
                    self.player.acc.y = WORLD_ACC
        # hits = pygame.sprite.spritecollide(self.player, self.mobs, False, pygame.sprite.collide_mask)

        # Powerups collision.
        powerups_hits = pygame.sprite.spritecollide(self.player, self.powerups, True)
        for powerup in powerups_hits:
            if powerup.type == 'boost':
                self.player.vel.y = -POW_STR
                self.player.jumping = False
        #  platforms moving up if we reach 1/4 height (up) and spawn cloud
        if self.player.rect.top <= HEIGHT / 4:
            if random.randrange(100) < 10:
                game_elements.Cloud(self)

            self.player.pos.y += max(abs(self.player.vel.y), 2)

            for cloud in self.clouds:
                cloud.rect.y += max(abs(self.player.vel.y / 2), 2)

            for platform in self.platforms:
                platform.rect.y += max(abs(self.player.vel.y), 2)
                if platform.rect.top >= HEIGHT:
                    platform.kill()
                    self.score += 10

            for mob in self.mobs:
                mob.rect.y += max(abs(self.player.vel.y), 2)

        if self.player.rect.bottom > HEIGHT:
            for sprite in self.all_sprites:
                sprite.rect.y -= max(self.player.vel.y, 10)
                if sprite.rect.bottom < 0:
                    sprite.kill()

        if len(self.platforms) == 0:
            self.playing = False

        while len(self.platforms) < 4:
            game_elements.BasePlatform(random.randrange(0, WIDTH - random.randrange(60, 100)),
                                       0, self, random.randint(1, 2))

    def _events(self):

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                self.playing = False
            if event.type == pygame.KEYUP:
                if event.key == pygame.K_SPACE:
                    self.player.jump_cut()  # TODO PUt this in to player, not GAME

    def _draw(self):
        if 0 <= self.score < 150:
            self.screen.fill(Color.LIGHT_BLUE)
        if 150 < self.score < 250:
            self.screen.fill(Color.LIGHT_BLUE2)
        if 250 < self.score < 350:
            self.screen.fill(Color.LIGHT_BLUE3)
        if 350 < self.score < 450:
            self.screen.fill(Color.LIGHT_BLUE4)
        if 450 < self.score:
            self.screen.fill(Color.LIGHT_BLUE5)

        self.all_sprites.draw(self.screen)
        self._draw_text(str(self.score), 22, Color.WHITE, WIDTH - 25, 15)
        self._draw_text(f'{round(self.clock.get_fps(), 2)}', 22, Color.WHITE, 35, 15)
        self.screen.blit(self.player.image, self.player.rect)  # makes the player to be in front of the platform
        pygame.display.flip()

    def show_start_screen(self):

        self.screen.fill(Color.LIGHT_PURPLE)
        self._draw_text('super juego increible', 25, Color.WHITE, WIDTH / 2, HEIGHT / 4)
        self._draw_text('Arrows to move, space to jump', 22, Color.RED, WIDTH / 2, HEIGHT * 3 / 4)
        self._draw_text(f'Higher score: {self.highscore}', 10, Color.GREEN, WIDTH / 2, HEIGHT / 2)
        pygame.display.flip()
        self._wait_for_key()

    def show_go_screen(self):
        if not self.running:
            return

        self.screen.fill(Color.BLUE)
        self._draw_text('YOU ARE DEAD', 48, Color.RED, WIDTH / 2, HEIGHT / 4)
        self._draw_text(f'You score score: {self.score}', 10, Color.GREEN, WIDTH / 2, HEIGHT / 2)

        pygame.display.flip()
        self._save_score()

        self._wait_for_key()

    def _save_score(self):
        if self.score > self.highscore:
            with open(f'{self.path}/{HS_FILE}', 'w') as f:
                f.write(str(self.score))

    def _draw_text(self, text, size, color, x, y):
        font = pygame.font.Font(self.font, size)
        text_surface = font.render(text, True, color)
        text_rect = text_surface.get_rect()
        text_rect.midtop = (x, y)
        self.screen.blit(text_surface, text_rect)

    def _wait_for_key(self):
        waiting = True
        while waiting:
            self.clock.tick(FPS/2)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    waiting = False
                    self.running = False
                if event.type == pygame.KEYUP:
                    waiting = False
