import pyray as rl
import math
import random
import sys
import os

def resource_path(relative_path):
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

# Constants
_B = 1.0
_A = 0.0

SCREEN_WIDTH = 800
SCREEN_HEIGHT = 450
TEXTURE_SCALE = 2.0

shootSFX = None
deadSFX = None


class Bullet:
    def __init__(self, x, y, dir_vec):
        self.x = x
        self.y = y
        self.dir = dir_vec  # Vector2 with speed applied

    def update(self, dt):
        self.x += self.dir.x * dt
        self.y += self.dir.y * dt

    def draw(self):
        rl.draw_circle(int(self.x), int(self.y), 5, rl.ORANGE)


class Enemy:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.speed = 45.0
        self.max_health = 30
        self.health = self.max_health
        self.contact_damage = 5
        self.hit_timer = _A

        self.texture = rl.load_texture(resource_path("assets/enemy.png"))
        max_dim = max(self.texture.width, self.texture.height)
        self.radius = 0.5 * max_dim * TEXTURE_SCALE

    def update(self, dt, player):
        dx = player.x + player.width * 0.5 - self.x
        dy = player.y + player.height * 0.5 - self.y
        dist_sq = dx * dx + dy * dy

        if dist_sq > 0.0001:
            inv_len = _B / math.sqrt(dist_sq)
            self.x += dx * inv_len * self.speed * dt
            self.y += dy * inv_len * self.speed * dt

        if self.hit_timer > _A:
            self.hit_timer -= dt

    def draw(self):
        pos = rl.Vector2(
            self.x - self.texture.width * TEXTURE_SCALE * 0.5,
            self.y - self.texture.height * TEXTURE_SCALE * 0.5
        )
        rl.draw_texture_ex(self.texture, pos, 0.0, TEXTURE_SCALE, rl.WHITE)

        bar_w, bar_h = 30, 4
        bx = int(self.x - bar_w * 0.5)
        by = int(self.y - self.radius - 10)

        rl.draw_rectangle(bx, by, bar_w, bar_h, rl.LIGHTGRAY)
        if self.health > 0:
            fill = int(bar_w * (self.health / self.max_health))
            rl.draw_rectangle(bx, by, fill, bar_h, rl.GREEN)

    def quit(self):
        rl.unload_texture(self.texture)


class Player:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.speed = 220.0
        self.bullet_speed = 600.0
        self.bullets = []
        self.dir = rl.Vector2(_A, -_B)
        self.score = 0
        self.max_health = 100
        self.health = self.max_health
        self.dead = False

        self.texture = rl.load_texture(resource_path("assets/player.png"))
        self.width = int(self.texture.width * TEXTURE_SCALE)
        self.height = int(self.texture.height * TEXTURE_SCALE)

    def update(self, dt):
        dx = dy = _A

        if rl.is_key_down(rl.KEY_A):
            dx -= _B
            self.x -= self.speed * dt
        if rl.is_key_down(rl.KEY_D):
            dx += _B
            self.x += self.speed * dt
        if rl.is_key_down(rl.KEY_W):
            dy -= _B
            self.y -= self.speed * dt
        if rl.is_key_down(rl.KEY_S):
            dy += _B
            self.y += self.speed * dt

        if dx != _A or dy != _A:
            inv_len = _B / math.sqrt(dx * dx + dy * dy)
            self.dir.x = dx * inv_len
            self.dir.y = dy * inv_len

        self.x = max(_A, min(self.x, SCREEN_WIDTH - self.width))
        self.y = max(_A, min(self.y, SCREEN_HEIGHT - self.height))

        if rl.is_key_pressed(rl.KEY_SPACE) or rl.is_mouse_button_pressed(rl.MOUSE_BUTTON_LEFT):
            rl.play_sound(shootSFX)
            bx = self.x + self.width * 0.5
            by = self.y + self.height * 0.5

            m = rl.get_mouse_position()
            dxm = m.x - bx
            dym = m.y - by
            dist_sq = dxm * dxm + dym * dym

            if dist_sq > 0.0001:
                inv_len = _B / math.sqrt(dist_sq)
                self.dir.x = dxm * inv_len
                self.dir.y = dym * inv_len
                self.bullets.append(
                    Bullet(bx, by,
                           rl.Vector2(self.dir.x * self.bullet_speed,
                                      self.dir.y * self.bullet_speed))
                )

        for b in self.bullets:
            b.update(dt)

        i = 0
        while i < len(self.bullets):
            b = self.bullets[i]
            if (b.x < -40 or b.x > SCREEN_WIDTH + 40 or
                b.y < -40 or b.y > SCREEN_HEIGHT + 40):
                self.bullets[i] = self.bullets[-1]
                self.bullets.pop()
            else:
                i += 1

    def draw(self):
        for b in self.bullets:
            b.draw()
        rl.draw_texture_ex(self.texture, rl.Vector2(self.x, self.y), 0.0, TEXTURE_SCALE, rl.WHITE)

    def quit(self):
        rl.unload_texture(self.texture)


def main():
    global shootSFX, deadSFX

    rl.init_window(SCREEN_WIDTH, SCREEN_HEIGHT, "Shooter Game")
    rl.init_audio_device()

    shootSFX = rl.load_sound(resource_path("assets/shoot.mp3"))
    rl.set_sound_volume(shootSFX, 0.1)
    deadSFX = rl.load_sound(resource_path("assets/dead.mp3"))

    player = Player(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2)
    enemies = []

    icon = rl.load_image(resource_path("assets/favicon.png"))
    rl.set_window_icon(icon)
    rl.unload_image(icon)
    
    spawn_timer = _A
    bullet_damage = 20
    show_fps = False
    game_over = False

    music = rl.load_music_stream(resource_path("assets/ambient.mp3"))
    music_volume = 0.25
    rl.set_music_volume(music, music_volume)
    rl.play_music_stream(music)

    while not rl.window_should_close():
        rl.update_music_stream(music)
        dt = rl.get_frame_time()

        if rl.is_key_pressed(rl.KEY_F3):
            show_fps = not show_fps

        if not game_over:
            spawn_timer -= dt
            if spawn_timer <= _A:
                enemies.append(
                    Enemy(random.randint(0, SCREEN_WIDTH),
                          random.randint(0, SCREEN_HEIGHT))
                )
                spawn_timer = random.randint(16, 32) / 10.0

            player.update(dt)

            i = 0
            while i < len(enemies):
                e = enemies[i]
                e.update(dt, player)

                hit = False
                rr = (e.radius + 5.0) ** 2

                j = 0
                while j < len(player.bullets):
                    b = player.bullets[j]
                    dx = b.x - e.x
                    dy = b.y - e.y
                    if dx * dx + dy * dy <= rr:
                        player.bullets[j] = player.bullets[-1]
                        player.bullets.pop()
                        e.health -= bullet_damage
                        if e.health <= 0:
                            hit = True
                        break
                    j += 1

                dxp = player.x + player.width * 0.5 - e.x
                dyp = player.y + player.height * 0.5 - e.y
                if (dxp * dxp + dyp * dyp <=
                    (e.radius + player.width * 0.5) ** 2 and
                        e.hit_timer <= _A):
                    player.health = max(0, player.health - e.contact_damage)
                    e.hit_timer = 0.6

                if hit:
                    enemies[i] = enemies[-1]
                    enemies.pop()
                    player.score += 1
                else:
                    i += 1

            if player.health <= 0:
                game_over = True
                rl.play_sound(deadSFX)

        rl.begin_drawing()
        rl.clear_background(rl.WHITE)

        rl.draw_text("Use WASD to move & SPACE/click to shoot", 10, SCREEN_HEIGHT - 20, 20, rl.BLACK)

        if show_fps:
            rl.draw_text(f"{rl.get_fps()} FPS", SCREEN_WIDTH - 90, 10, 20, rl.DARKGRAY)

        rl.draw_rectangle(10, 10, 200, 12, rl.LIGHTGRAY)
        if player.health > 0:
            rl.draw_rectangle(10, 10, int(200 * player.health / player.max_health), 12, rl.GREEN)

        rl.draw_text(f"Score: {player.score}", 10, 28, 20, rl.GREEN)

        player.draw()
        for e in enemies:
            e.draw()

        if game_over:
            msg = "GAME OVER"
            size = 40
            rl.draw_text(msg,
                         SCREEN_WIDTH // 2 - rl.measure_text(msg, size) // 2,
                         SCREEN_HEIGHT // 2 - size // 2,
                         size, rl.RED)
            rl.stop_music_stream(music)

        rl.end_drawing()

    for e in enemies:
        e.quit()
    player.quit()

    rl.unload_music_stream(music)
    rl.unload_sound(shootSFX)
    rl.unload_sound(deadSFX)
    rl.close_audio_device()
    rl.close_window()


if __name__ == "__main__":
    main()
