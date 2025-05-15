import pygame
import sys
import random
import os
from pygame.locals import *

# Inicialización
pygame.init()
pygame.mixer.init()  # Initialize the mixer for audio

# Constantes
WIDTH = 800
HEIGHT = 600
GRAVITY = 0.8
PLAYER_SPEED = 5
JUMP_FORCE = -15
FPS = 60
BULLET_SPEED = 10
ENEMY_MOVE_SPEED = 2
WORLD_WIDTH = 3000
GROUND_LEVEL = 560

# Colores
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BLUE = (0, 0, 255)
RED = (255, 0, 0)
YELLOW = (255, 255, 0)
GREEN = (0, 255, 0)
PURPLE = (128, 0, 128)
ORANGE = (255, 165, 0)
DARK_ORANGE = (200, 100, 0)
CYAN = (0, 255, 255)
DARK_BROWN = (139, 69, 19)
SKY_BLUE = (100, 150, 255)
GRAY = (150, 150, 150)
DARK_GRAY = (100, 100, 100)
GLOW_YELLOW = (255, 255, 0, 128)  # Semi-transparent yellow for glow
DARK_PURPLE = (50, 0, 100)  # For gradient sky
RED_ORANGE = (200, 50, 50)  # For gradient sky
DESERT_RED = (150, 50, 50)  # For desert ground


class Player(pygame.sprite.Sprite):
    def __init__(self, x, y, game):
        super().__init__()
        self.game = game  # Reference to the Game instance
        self.original_image = pygame.image.load(os.path.join("assets", "ninja.png")).convert_alpha()
        self.original_image = pygame.transform.scale(self.original_image, (35, 35))
        self.original_image = pygame.transform.flip(self.original_image, True, False)
        self.image = self.original_image
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.velocity_y = 0
        self.jumping = False
        self.facing_right = False
        self.health = 100
        self.max_health = 100
        self.speed = PLAYER_SPEED
        self.shoot_rate = 10
        self.shoot_timer = 0
        self.shield_active = False

    def update(self, platforms):
        self.velocity_y += GRAVITY
        self.rect.y += self.velocity_y
        collisions = pygame.sprite.spritecollide(self, platforms, False)
        for platform in collisions:
            if self.velocity_y > 0:
                self.rect.bottom = platform.rect.top
                self.velocity_y = 0
                self.jumping = False
            elif self.velocity_y < 0:
                self.rect.top = platform.rect.bottom
                self.velocity_y = 0
        self.rect.clamp_ip(pygame.Rect(0, 0, WIDTH, HEIGHT))

    def jump(self):
        if not self.jumping:
            self.velocity_y = JUMP_FORCE
            self.jumping = True

    def move(self, dx, dy):
        self.rect.x += dx * self.speed
        self.rect.y += dy * self.speed
        if dx > 0 and not self.facing_right:
            self.facing_right = True
            self.image = pygame.transform.flip(self.original_image, True, False)
        elif dx < 0 and self.facing_right:
            self.facing_right = False
            self.image = self.original_image

    def shoot(self, bullets, all_sprites):
        if self.shoot_timer <= 0:
            bullet = Bullet(self.rect.right if self.facing_right else self.rect.left,
                            self.rect.centery, 1 if self.facing_right else -1, is_player_bullet=True)
            bullets.add(bullet)
            all_sprites.add(bullet)
            # Play shoot sound if loaded
            if self.game.shoot_sound_loaded:
                self.game.shoot_sound.play()
            self.shoot_timer = self.shoot_rate
        else:
            self.shoot_timer -= 1

    def draw_health_bar(self, screen):
        bar_width = 30
        bar_height = 5
        fill = (self.health / self.max_health) * bar_width
        pygame.draw.rect(screen, RED, (self.rect.x, self.rect.y - 10, bar_width, bar_height))
        pygame.draw.rect(screen, GREEN, (self.rect.x, self.rect.y - 10, fill, bar_height))
        pygame.draw.rect(screen, BLACK, (self.rect.x, self.rect.y - 10, bar_width, bar_height), 1)
        if self.shield_active:
            pygame.draw.rect(screen, CYAN, (self.rect.x - 2, self.rect.y - 2, 39, 39), 2)

    def activate_shield(self):
        self.shield_active = True

    def take_damage(self):
        if self.shield_active:
            self.shield_active = False
            return False
        return True


class Platform(pygame.sprite.Sprite):
    def __init__(self, x, y, width, height):
        super().__init__()
        self.image = pygame.Surface((width, height))
        self.image.fill(DARK_BROWN)
        pygame.draw.rect(self.image, (100, 50, 0), (0, 0, width, height), 4)
        for i in range(0, width, 15):
            pygame.draw.line(self.image, (120, 60, 0), (i, 0), (i, height), 2)
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y


class Enemy(pygame.sprite.Sprite):
    def __init__(self, x, y, shoot_rate=120):
        super().__init__()
        try:
            self.image = pygame.image.load(os.path.join("assets", "sherif.png")).convert_alpha()
            self.image = pygame.transform.scale(self.image, (35, 35))
            self.use_image = True
        except pygame.error as e:
            print(f"Warning: Couldn't load assets/sherif.png, using fallback graphic. Error: {e}")
            self.image = pygame.Surface((30, 30), pygame.SRCALPHA)
            pygame.draw.polygon(self.image, RED, [(15, 0), (0, 30), (30, 30)])
            pygame.draw.circle(self.image, BLACK, (10, 10), 4)
            pygame.draw.circle(self.image, BLACK, (20, 10), 4)
            self.use_image = False
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.health = 30
        self.max_health = 30
        self.velocity_y = 0
        self.shoot_timer = 0
        self.shoot_rate = shoot_rate
        self.can_move = random.choice([True, False])
        self.move_direction = 1
        self.move_speed = ENEMY_MOVE_SPEED
        self.platform = None

    def update(self, platforms, player, enemy_bullets, all_sprites):
        self.velocity_y += GRAVITY
        self.rect.y += self.velocity_y
        collisions = pygame.sprite.spritecollide(self, platforms, False)
        for platform in collisions:
            if self.velocity_y > 0:
                self.rect.bottom = platform.rect.top
                self.velocity_y = 0
                self.platform = platform
            elif self.velocity_y < 0:
                self.rect.top = platform.rect.bottom
                self.velocity_y = 0
        if self.can_move and self.platform:
            self.rect.x += self.move_direction * self.move_speed
            if self.rect.right > self.platform.rect.right:
                self.move_direction = -1
            elif self.rect.left < self.platform.rect.left:
                self.move_direction = 1
        self.shoot_timer += 1
        if self.shoot_timer >= self.shoot_rate:
            direction = -1 if player.rect.x < self.rect.x else 1
            bullet = Bullet(self.rect.centerx, self.rect.centery, direction, is_player_bullet=False)
            bullet.image.fill(RED)
            enemy_bullets.add(bullet)
            all_sprites.add(bullet)
            self.shoot_timer = 0

    def draw_health_bar(self, screen):
        bar_width = 30
        bar_height = 5
        fill = (self.health / self.max_health) * bar_width
        pygame.draw.rect(screen, RED, (self.rect.x, self.rect.y - 10, bar_width, bar_height))
        pygame.draw.rect(screen, GREEN, (self.rect.x, self.rect.y - 10, fill, bar_height))
        pygame.draw.rect(screen, BLACK, (self.rect.x, self.rect.y - 10, bar_width, bar_height), 1)


class Bullet(pygame.sprite.Sprite):
    def __init__(self, x, y, direction, is_player_bullet=False):
        super().__init__()
        if is_player_bullet:
            try:
                self.image = pygame.image.load(os.path.join("assets", "balaninja.png")).convert_alpha()
                self.image = pygame.transform.scale(self.image, (10, 5))
            except pygame.error as e:
                print(f"Warning: Couldn't load assets/balaninja.png, using fallback graphic. Error: {e}")
                self.image = pygame.Surface((10, 5))
                self.image.fill(YELLOW)
        else:
            self.image = pygame.Surface((10, 5))
            self.image.fill(YELLOW)
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.direction = direction

    def update(self):
        self.rect.x += self.direction * BULLET_SPEED
        if self.rect.right < 0 or self.rect.left > WIDTH:
            self.kill()


class Goal(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((40, 60))
        self.image.fill(GREEN)
        pygame.draw.rect(self.image, YELLOW, (0, 0, 40, 60), 4)
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y


class Menu:
    def __init__(self, screen, font, small_font):
        self.screen = screen
        self.font = pygame.font.Font(None, 100)  # Larger font for title
        self.small_font = small_font
        try:
            self.background = pygame.image.load(os.path.join("assets", "naranja.png")).convert()
            self.background = pygame.transform.scale(self.background, (WIDTH, HEIGHT))
            self.use_background = True
        except pygame.error as e:
            print(f"Warning: Couldn't load assets/naranja.png, using fallback background. Error: {e}")
            self.background = pygame.Surface((WIDTH, HEIGHT))
            self.background.fill(SKY_BLUE)
            self.use_background = False
        self.buttons = [
            {"text": "Play", "action": "Play", "rect": pygame.Rect(WIDTH // 2 - 100, 200, 200, 50)},
            {"text": "Levels", "action": "Levels", "rect": pygame.Rect(WIDTH // 2 - 100, 270, 200, 50)},
            {"text": "Shop", "action": "Shop", "rect": pygame.Rect(WIDTH // 2 - 100, 340, 200, 50)},
            {"text": "Credits", "action": "Credits", "rect": pygame.Rect(WIDTH // 2 - 100, 410, 200, 50)},
            {"text": "Context", "action": "Context", "rect": pygame.Rect(WIDTH // 2 - 100, 480, 200, 50)},
            {"text": "Quit", "action": "Quit", "rect": pygame.Rect(WIDTH // 2 - 100, 550, 200, 50)},
        ]
        self.title_text = self.font.render("Shuriken Sundown", True, WHITE)
        self.title_shadow = self.font.render("Shuriken Sundown", True, BLACK)
        self.title_glow = self.font.render("Shuriken Sundown", True, GLOW_YELLOW)

    def draw(self):
        if self.use_background:
            self.screen.blit(self.background, (0, 0))
        else:
            self.screen.fill(SKY_BLUE)
        title_x = WIDTH // 2 - self.title_text.get_width() // 2
        title_y = 100
        for dx, dy in [(2, 2), (3, 3), (-2, 2), (2, -2)]:
            self.screen.blit(self.title_shadow, (title_x + dx, title_y + dy))
        for dx, dy in [(1, 1), (-1, -1), (1, -1), (-1, 1), (2, 0), (-2, 0), (0, 2), (0, -2)]:
            self.screen.blit(self.title_glow, (title_x + dx, title_y + dy))
        self.screen.blit(self.title_text, (title_x, title_y))
        pygame.draw.line(self.screen, YELLOW, (title_x, title_y - 10),
                         (title_x + self.title_text.get_width(), title_y - 10), 3)
        pygame.draw.line(self.screen, YELLOW, (title_x, title_y + self.title_text.get_height() + 10),
                         (title_x + self.title_text.get_width(), title_y + self.title_text.get_height() + 10), 3)
        for x in [title_x, title_x + self.title_text.get_width()]:
            pygame.draw.line(self.screen, YELLOW, (x, title_y - 10), (x, title_y - 20), 3)
            pygame.draw.line(self.screen, YELLOW, (x, title_y + self.title_text.get_height() + 10),
                             (x, title_y + self.title_text.get_height() + 20), 3)
        mouse_pos = pygame.mouse.get_pos()
        for button in self.buttons:
            is_hovered = button["rect"].collidepoint(mouse_pos)
            button_color = GRAY if is_hovered else DARK_BROWN
            border_color = CYAN if is_hovered else YELLOW
            shadow_rect = button["rect"].copy()
            shadow_rect.x += 4
            shadow_rect.y += 4
            pygame.draw.rect(self.screen, DARK_GRAY, shadow_rect)
            pygame.draw.rect(self.screen, button_color, button["rect"])
            pygame.draw.rect(self.screen, border_color, button["rect"], 4)
            text_surface = self.small_font.render(button["text"], True, WHITE)
            text_shadow = self.small_font.render(button["text"], True, BLACK)
            text_rect = text_surface.get_rect(center=button["rect"].center)
            shadow_rect = text_rect.copy()
            shadow_rect.x += 2
            shadow_rect.y += 2
            self.screen.blit(text_shadow, shadow_rect)
            self.screen.blit(text_surface, text_rect)

    def update(self, event):
        if event.type == MOUSEBUTTONDOWN and event.button == 1:
            mouse_pos = event.pos
            for button in self.buttons:
                if button["rect"].collidepoint(mouse_pos):
                    return button["action"]
        return None


class LevelSelect:
    def __init__(self, screen, font, small_font):
        self.screen = screen
        self.font = font
        self.small_font = small_font
        try:
            self.background = pygame.image.load(os.path.join("assets", "naranja.png")).convert()
            self.background = pygame.transform.scale(self.background, (WIDTH, HEIGHT))
            self.use_background = True
        except pygame.error as e:
            print(f"Warning: Couldn't load assets/naranja.png, using fallback background. Error: {e}")
            self.background = pygame.Surface((WIDTH, HEIGHT))
            self.background.fill(SKY_BLUE)
            self.use_background = False
        self.buttons = [
            {"text": "Level 1", "action": "Level1", "rect": pygame.Rect(WIDTH // 2 - 150, 250, 100, 100)},
            {"text": "Level 2", "action": "Level2", "rect": pygame.Rect(WIDTH // 2 + 50, 250, 100, 100)},
            {"text": "Back", "action": "Back", "rect": pygame.Rect(WIDTH // 2 - 100, 400, 200, 50)},
        ]
        self.title_text = self.font.render("Select Level", True, WHITE)
        self.title_shadow = self.font.render("Select Level", True, BLACK)
        self.title_glow = self.font.render("Select Level", True, GLOW_YELLOW)

    def draw(self):
        if self.use_background:
            self.screen.blit(self.background, (0, 0))
        else:
            self.screen.fill(SKY_BLUE)
        title_x = WIDTH // 2 - self.title_text.get_width() // 2
        title_y = 100
        for dx, dy in [(2, 2), (3, 3), (-2, 2), (2, -2)]:
            self.screen.blit(self.title_shadow, (title_x + dx, title_y + dy))
        for dx, dy in [(1, 1), (-1, -1), (1, -1), (-1, 1), (2, 0), (-2, 0), (0, 2), (0, -2)]:
            self.screen.blit(self.title_glow, (title_x + dx, title_y + dy))
        self.screen.blit(self.title_text, (title_x, title_y))
        pygame.draw.line(self.screen, YELLOW, (title_x, title_y - 10),
                         (title_x + self.title_text.get_width(), title_y - 10), 3)
        pygame.draw.line(self.screen, YELLOW, (title_x, title_y + self.title_text.get_height() + 10),
                         (title_x + self.title_text.get_width(), title_y + self.title_text.get_height() + 10), 3)
        for x in [title_x, title_x + self.title_text.get_width()]:
            pygame.draw.line(self.screen, YELLOW, (x, title_y - 10), (x, title_y - 20), 3)
            pygame.draw.line(self.screen, YELLOW, (x, title_y + self.title_text.get_height() + 10),
                             (x, title_y + self.title_text.get_height() + 20), 3)
        mouse_pos = pygame.mouse.get_pos()
        for button in self.buttons:
            is_hovered = button["rect"].collidepoint(mouse_pos)
            button_color = GRAY if is_hovered else DARK_BROWN
            border_color = CYAN if is_hovered else YELLOW
            shadow_rect = button["rect"].copy()
            shadow_rect.x += 4
            shadow_rect.y += 4
            pygame.draw.rect(self.screen, DARK_GRAY, shadow_rect)
            pygame.draw.rect(self.screen, button_color, button["rect"])
            pygame.draw.rect(self.screen, border_color, button["rect"], 4)
            text_surface = self.small_font.render(button["text"], True, WHITE)
            text_shadow = self.small_font.render(button["text"], True, BLACK)
            text_rect = text_surface.get_rect(center=button["rect"].center)
            shadow_rect = text_rect.copy()
            shadow_rect.x += 2
            shadow_rect.y += 2
            self.screen.blit(text_shadow, shadow_rect)
            self.screen.blit(text_surface, text_rect)

    def update(self, event):
        if event.type == MOUSEBUTTONDOWN and event.button == 1:
            mouse_pos = event.pos
            for button in self.buttons:
                if button["rect"].collidepoint(mouse_pos):
                    return button["action"]
        return None


class Context:
    def __init__(self, screen, small_font):
        self.screen = screen
        self.context_font = pygame.font.Font(None, 20)
        self.small_font = small_font
        self.background = pygame.Surface((WIDTH, HEIGHT))
        self.create_background()
        self.story_text = [
            "Año desconocido. Tiempo colapsado. Historia rota.",
            "",
            "El experimento fallido de una megacorporación conocida como KairoTech rompió el flujo del tiempo. Ahora, samuráis del pasado, pistoleros del oeste y tecnología del futuro existen en un mismo mundo: el Territorio Péndulo.",
            "",
            "En este caos surgieron dos fuerzas:",
            "",
            "🥷 El Clan del Eclipse — antiguos ninjas, adaptados al presente, maestros del sigilo y del disparo preciso. Buscan restaurar el equilibrio a su modo: rápido, silencioso y letal.",
            "",
            "🤠 Los Sheriffs del Reloj — guardianes del orden, hombres y mujeres del viejo oeste con armas potentes y reglas claras. Su ley es dura, su justicia más aún.",
            "",
            "Ambos bandos luchan por controlar el Núcleo Cronal, un artefacto que podría reparar la línea del tiempo... o destruirla por completo.",
            "",
            "El reloj corre. Las balas silban. Las sombras se mueven.",
            "",
            "¿De qué lado estás tú?"
        ]
        self.wrapped_lines = []
        self.chars_per_line = []
        self.wrap_text()
        self.current_char = 0
        self.current_line = 0
        self.timer = 0
        self.char_delay = 50
        self.animation_complete = False
        self.text_surfaces = []
        self.text_positions = []
        self.prepare_text()
        print("Context initialized with wrapped lines:", self.wrapped_lines)

    def create_background(self):
        for y in range(HEIGHT // 2):
            t = y / (HEIGHT // 2)
            r = int(DARK_PURPLE[0] * (1 - t) + RED_ORANGE[0] * t)
            g = int(DARK_PURPLE[1] * (1 - t) + RED_ORANGE[1] * t)
            b = int(DARK_PURPLE[2] * (1 - t) + RED_ORANGE[2] * t)
            pygame.draw.line(self.background, (r, g, b), (0, y), (WIDTH, y))

    def wrap_text(self):
        max_width = 700
        for line in self.story_text:
            if not line:
                self.wrapped_lines.append("")
                self.chars_per_line.append([])
                continue
            words = line.split()
            current_line = ""
            current_chars = []
            for word in words:
                test_line = current_line + word + " "
                test_surface = self.context_font.render(test_line, True, WHITE)
                if test_surface.get_width() <= max_width:
                    current_line = test_line
                    current_chars.extend(list(word + " "))
                else:
                    if current_line:
                        self.wrapped_lines.append(current_line.strip())
                        self.chars_per_line.append(current_chars)
                    current_line = word + " "
                    current_chars = list(word + " ")
            if current_line:
                self.wrapped_lines.append(current_line.strip())
                self.chars_per_line.append(current_chars)
        print("Wrapped lines:", self.wrapped_lines)

    def prepare_text(self):
        self.text_surfaces = []
        self.text_positions = []
        line_height = 25
        total_height = len(self.wrapped_lines) * line_height
        start_y = (HEIGHT - total_height) // 2
        for i in range(len(self.wrapped_lines)):
            if i < self.current_line:
                text_to_show = self.wrapped_lines[i]
            elif i == self.current_line and not self.animation_complete:
                chars_to_show = self.chars_per_line[i][:self.current_char]
                text_to_show = "".join(chars_to_show)
            else:
                text_to_show = ""
            try:
                text_surface = self.context_font.render(text_to_show, True, WHITE)
                text_shadow = self.context_font.render(text_to_show, True, BLACK)
                text_rect = text_surface.get_rect(center=(WIDTH // 2, start_y + i * line_height))
                self.text_surfaces.append((text_surface, text_shadow))
                self.text_positions.append(text_rect)
                print(f"Line {i}: Rendering '{text_to_show}' at {text_rect}")
            except Exception as e:
                print(f"Error rendering line {i}: {e}")

    def update(self):
        if self.animation_complete:
            return
        self.timer += 1000 / FPS
        if self.timer >= self.char_delay:
            self.timer = 0
            if self.current_line < len(self.wrapped_lines):
                total_chars = sum(len(chars) for chars in self.chars_per_line)
                if self.current_char < len(self.chars_per_line[self.current_line]):
                    self.current_char += 1
                    print(
                        f"Line {self.current_line}, Char {self.current_char}: {self.chars_per_line[self.current_line][self.current_char - 1]}")
                elif self.current_line + 1 < len(self.wrapped_lines):
                    self.current_line += 1
                    self.current_char = 0
                    print(f"Moving to line {self.current_line}")
                if self.current_char >= total_chars:
                    self.animation_complete = True
                    print("Animation complete")
            self.prepare_text()

    def draw(self):
        self.screen.blit(self.background, (0, 0))
        for (text_surface, text_shadow), text_rect in zip(self.text_surfaces, self.text_positions):
            shadow_rect = text_rect.copy()
            shadow_rect.x += 2
            shadow_rect.y += 2
            self.screen.blit(text_shadow, shadow_rect)
            self.screen.blit(text_surface, text_rect)
        if self.animation_complete:
            instruction = self.small_font.render("Presiona ENTER para volver al menú", True, WHITE)
            instruction_shadow = self.small_font.render("Presiona ENTER para volver al menú", True, BLACK)
            instruction_rect = instruction.get_rect(center=(WIDTH // 2, HEIGHT - 30))
            shadow_rect = instruction_rect.copy()
            shadow_rect.x += 2
            shadow_rect.y += 2
            self.screen.blit(instruction_shadow, shadow_rect)
            self.screen.blit(instruction, instruction_rect)


class Shop:
    def __init__(self, screen, font, small_font, total_score, upgrades):
        self.screen = screen
        self.font = font
        self.small_font = small_font
        self.total_score = total_score
        self.upgrades = upgrades
        self.options = [
            {"name": "Disparar más rápido", "cost": 1400, "purchased": "faster_shooting" in self.upgrades,
             "action": "faster_shooting"},
            {"name": "Moverse más rápido", "cost": 1200, "purchased": "faster_movement" in self.upgrades,
             "action": "faster_movement"},
            {"name": "Escudo temporal", "cost": 1600, "purchased": "shield" in self.upgrades, "action": "shield"}
        ]
        self.buttons = []
        y_start = 225
        vertical_spacing = 10
        padding_x = 20
        padding_y = 10
        current_y = y_start
        for i, option in enumerate(self.options):
            status = "Comprado" if option["purchased"] else f"Costo: {option['cost']}"
            text_str = f"✨ {i + 1}. {option['name']} - {status} ✨"
            text_surface = self.small_font.render(text_str, True, WHITE)
            text_rect = text_surface.get_rect()
            button_width = text_rect.width + padding_x * 2
            button_height = text_rect.height + padding_y * 2
            button_rect = pygame.Rect(WIDTH // 2 - button_width // 2, current_y, button_width, button_height)
            self.buttons.append({"rect": button_rect, "action": option["action"], "index": i, "text": text_str})
            current_y += button_height + vertical_spacing
        return_text = "Volver al Menú"
        return_surface = self.small_font.render(return_text, True, WHITE)
        return_rect = return_surface.get_rect()
        button_width = return_rect.width + padding_x * 2
        button_height = return_rect.height + padding_y * 2
        return_button_rect = pygame.Rect(WIDTH // 2 - button_width // 2, current_y, button_width, button_height)
        self.buttons.append({"rect": return_button_rect, "action": "menu", "index": None, "text": return_text})

    def draw(self):
        try:
            shop_background = pygame.image.load(os.path.join("assets", "menutienda.png")).convert_alpha()
            shop_background = pygame.transform.scale(shop_background, (WIDTH, HEIGHT))
            self.screen.blit(shop_background, (0, 0))
        except pygame.error as e:
            print(f"Warning: Couldn't load assets/menutienda.png, using fallback. Error: {e}")
            self.screen.fill(DARK_BROWN)
        score_text = self.small_font.render(f"★ Puntos totales: {self.total_score} ★", True, YELLOW)
        score_rect = score_text.get_rect(center=(WIDTH // 2, 150))
        pygame.draw.rect(self.screen, BLACK,
                         (score_rect.x - 10, score_rect.y - 5, score_rect.width + 20, score_rect.height + 10), 2)
        self.screen.blit(score_text, score_rect)
        mouse_pos = pygame.mouse.get_pos()
        for button in self.buttons:
            is_hovered = button["rect"].collidepoint(mouse_pos)
            button_color = GRAY if is_hovered else DARK_BROWN
            border_color = CYAN if is_hovered else YELLOW
            shadow_rect = button["rect"].copy()
            shadow_rect.x += 4
            shadow_rect.y += 4
            pygame.draw.rect(self.screen, DARK_GRAY, shadow_rect)
            pygame.draw.rect(self.screen, button_color, button["rect"])
            pygame.draw.rect(self.screen, border_color, button["rect"], 4)
            text_str = button["text"]
            if button["action"] == "menu":
                text = self.small_font.render(text_str, True, WHITE)
            else:
                option = self.options[button["index"]]
                text = self.small_font.render(text_str, True, PURPLE if option["purchased"] else WHITE)
            text_shadow = self.small_font.render(text_str, True, BLACK)
            text_rect = text.get_rect(center=button["rect"].center)
            shadow_rect = text_rect.copy()
            shadow_rect.x += 2
            shadow_rect.y += 2
            self.screen.blit(text_shadow, shadow_rect)
            self.screen.blit(text, text_rect)

    def update(self, event):
        if event.type == MOUSEBUTTONDOWN and event.button == 1:
            mouse_pos = event.pos
            for button in self.buttons:
                if button["rect"].collidepoint(mouse_pos):
                    action = button["action"]
                    if action == "menu":
                        return "menu"
                    else:
                        index = button["index"]
                        option = self.options[index]
                        if not option["purchased"] and self.total_score >= option["cost"]:
                            self.upgrades[action] = True
                            self.total_score -= option["cost"]
                            option["purchased"] = True
        return None


class Game:
    def __init__(self):
        # Initialize display
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Shuriken Sundown")

        # Display loading screen
        try:
            loading_image = pygame.image.load(os.path.join("assets", "loading.png")).convert_alpha()
            loading_image = pygame.transform.scale(loading_image, (WIDTH, HEIGHT))
            self.screen.blit(loading_image, (0, 0))
            pygame.display.flip()
        except pygame.error as e:
            print(f"Warning: Couldn't load assets/loading.png, using fallback background. Error: {e}")
            self.screen.fill(BLACK)
            loading_text = pygame.font.Font(None, 80).render("Loading...", True, WHITE)
            loading_rect = loading_text.get_rect(center=(WIDTH // 2, HEIGHT // 2))
            self.screen.blit(loading_text, loading_rect)
            pygame.display.flip()

        # Wait for 4 seconds
        pygame.time.wait(4000)

        # Initialize rest of the game
        self.clock = pygame.time.Clock()
        self.state = "menu"
        self.all_sprites = pygame.sprite.Group()
        self.platforms = pygame.sprite.Group()
        self.enemies = pygame.sprite.Group()
        self.bullets = pygame.sprite.Group()
        self.enemy_bullets = pygame.sprite.Group()
        self.goals = pygame.sprite.Group()
        self.player = None
        self.font = pygame.font.Font(None, 80)
        self.small_font = pygame.font.Font(None, 40)
        self.menu = Menu(self.screen, self.font, self.small_font)
        self.shop = None
        self.context = None
        self.level_select = None
        self.score = 0
        self.total_score = 0
        self.upgrades = {}
        self.lives = 3
        self.scroll_x = 0
        try:
            self.background = pygame.image.load(os.path.join("assets", "desert.png")).convert()
            self.background = pygame.transform.scale(self.background, (WIDTH, HEIGHT))
        except pygame.error as e:
            print(f"Warning: Couldn't load assets/desert.png, using fallback background. Error: {e}")
            self.background = pygame.Surface((WIDTH, HEIGHT))
            self.background.fill(SKY_BLUE)
            pygame.draw.rect(self.background, RED, (0, HEIGHT - 40, WIDTH, 40))
        try:
            self.heart_image = pygame.image.load(os.path.join("assets", "vida1.png")).convert_alpha()
            self.heart_image = pygame.transform.scale(self.heart_image, (32, 32))
        except pygame.error as e:
            print(f"Warning: Couldn't load assets/vida1.png, using fallback heart. Error: {e}")
            self.heart_image = pygame.Surface((32, 32), pygame.SRCALPHA)
            pygame.draw.polygon(self.heart_image, RED,
                                [(16, 8), (8, 0), (0, 8), (8, 16), (16, 24), (24, 16), (32, 8), (24, 0)])
        try:
            self.gameover_image = pygame.image.load(os.path.join("assets", "gameover.png")).convert_alpha()
            self.gameover_image = pygame.transform.scale(self.gameover_image, (WIDTH, HEIGHT))
            self.use_gameover_image = True
        except pygame.error as e:
            print(f"Warning: Couldn't load assets/gameover_image.png, using fallback text screen. Error: {e}")
            self.use_gameover_image = False
        try:
            self.credits_image = pygame.image.load(os.path.join("assets", "creditsns.png")).convert_alpha()
            self.credits_image = pygame.transform.scale(self.credits_image, (WIDTH, HEIGHT))
            self.use_credits_image = True
        except pygame.error as e:
            print(f"Warning: Couldn't load assets/creditsns.png, using fallback text screen. Error: {e}")
            self.use_credits_image = False
        try:
            self.win_image = pygame.image.load(os.path.join("assets", "win.png")).convert_alpha()
            self.win_image = pygame.transform.scale(self.win_image, (WIDTH, HEIGHT))
            self.use_win_image = True
        except pygame.error as e:
            print(f"Warning: Couldn't load assets/win.png, using fallback text screen. Error: {e}")
            self.use_win_image = False
        # Initialize menu music
        self.menu_music_loaded = False
        try:
            pygame.mixer.music.load(os.path.join("assets", "musicamenu.mp3"))
            self.menu_music_loaded = True
        except pygame.error as e:
            print(f"Warning: Couldn't load assets/musicamenu.mp3. Error: {e}")
        # Initialize play music
        self.play_music_loaded = False
        try:
            pygame.mixer.music.load(os.path.join("assets", "musicaplay.mp3"))
            self.play_music_loaded = True
        except pygame.error as e:
            print(f"Warning: Couldn't load assets/musicaplay.mp3. Error: {e}")
        # Initialize context music
        self.context_music_loaded = False
        try:
            pygame.mixer.music.load(os.path.join("assets", "teclado.mp3"))
            self.context_music_loaded = True
        except pygame.error as e:
            print(f"Warning: Couldn't load assets/teclado.mp3. Error: {e}")
        # Initialize shoot sound
        self.shoot_sound_loaded = False
        try:
            self.shoot_sound = pygame.mixer.Sound(os.path.join("assets", "disparo.mp3"))
            self.shoot_sound.set_volume(0.5)
            self.shoot_sound_loaded = True
        except pygame.error as e:
            print(f"Warning: Couldn't load assets/disparo.mp3. Error: {e}")

    def reset_game(self):
        self.all_sprites.empty()
        self.platforms.empty()
        self.enemies.empty()
        self.bullets.empty()
        self.enemy_bullets.empty()
        self.goals.empty()
        self.scroll_x = 0
        if self.player:
            self.player.rect.x = 100
            self.player.rect.y = 100
            self.player.velocity_y = 0
            self.player.health = self.player.max_health
            self.player.shoot_rate = 5 if "faster_shooting" in self.upgrades else 10
            self.player.speed = 7 if "faster_movement" in self.upgrades else PLAYER_SPEED
            if "shield" in self.upgrades:
                self.player.activate_shield()
            self.all_sprites.add(self.player)
        else:
            self.player = Player(100, 100, self)
            self.player.shoot_rate = 5 if "faster_shooting" in self.upgrades else 10
            self.player.speed = 7 if "faster_movement" in self.upgrades else PLAYER_SPEED
            if "shield" in self.upgrades:
                self.player.activate_shield()
            self.all_sprites.add(self.player)
        platforms = [
            Platform(100, 150, 150, 20),
            Platform(300, 200, 150, 20),
            Platform(500, 150, 150, 20),
            Platform(700, 250, 150, 20),
            Platform(900, 200, 150, 20),
            Platform(1100, 300, 150, 20),
            Platform(1300, 250, 150, 20),
            Platform(1500, 200, 150, 20),
            Platform(1700, 300, 150, 20),
            Platform(1900, 250, 150, 20),
            Platform(2100, 350, 150, 20),
            Platform(2300, 300, 150, 20),
            Platform(2500, 400, 150, 20),
            Platform(2800, 500, 150, 20),
        ]
        for platform in platforms:
            self.platforms.add(platform)
            self.all_sprites.add(platform)
        enemies = [
            Enemy(300, 160),
            Enemy(500, 110),
            Enemy(700, 210),
            Enemy(900, 160),
            Enemy(1100, 260),
            Enemy(1300, 210),
            Enemy(1500, 160),
            Enemy(1700, 260),
            Enemy(1900, 210),
            Enemy(2100, 310),
            Enemy(2300, 260),
            Enemy(2500, 360),
        ]
        for enemy in enemies:
            self.enemies.add(enemy)
            self.all_sprites.add(enemy)
        goal = Goal(2800, 450)
        self.goals.add(goal)
        self.all_sprites.add(goal)
        print(f"Goal created at x={goal.rect.x}, y={goal.rect.y}")

    def reset_final_level(self):
        self.all_sprites.empty()
        self.platforms.empty()
        self.enemies.empty()
        self.bullets.empty()
        self.enemy_bullets.empty()
        self.goals.empty()
        self.scroll_x = 0
        if self.player:
            self.player.rect.x = 100
            self.player.rect.y = 100
            self.player.velocity_y = 0
            self.player.health = self.player.max_health
            self.player.shoot_rate = 5 if "faster_shooting" in self.upgrades else 10
            self.player.speed = 7 if "faster_movement" in self.upgrades else PLAYER_SPEED
            if "shield" in self.upgrades:
                self.player.activate_shield()
            self.all_sprites.add(self.player)
        else:
            self.player = Player(100, 100, self)
            self.player.shoot_rate = 5 if "faster_shooting" in self.upgrades else 10
            self.player.speed = 7 if "faster_movement" in self.upgrades else PLAYER_SPEED
            if "shield" in self.upgrades:
                self.player.activate_shield()
            self.all_sprites.add(self.player)
        platforms = [
            Platform(100, 200, 200, 20),
            Platform(350, 180, 200, 20),
            Platform(600, 220, 200, 20),
            Platform(850, 200, 200, 20),
            Platform(1100, 240, 200, 20),
            Platform(1400, 220, 200, 20),
            Platform(1700, 260, 200, 20),
            Platform(2000, 240, 200, 20),
            Platform(2300, 280, 200, 20),
            Platform(2600, 300, 200, 20),
            Platform(2900, 450, 200, 20),
        ]
        for platform in platforms:
            self.platforms.add(platform)
            self.all_sprites.add(platform)
        enemies = [
            Enemy(350, 140, shoot_rate=60),
            Enemy(600, 180, shoot_rate=60),
            Enemy(850, 160, shoot_rate=60),
            Enemy(1100, 200, shoot_rate=60),
            Enemy(1400, 180, shoot_rate=60),
            Enemy(1700, 220, shoot_rate=60),
            Enemy(2000, 200, shoot_rate=60),
            Enemy(2300, 240, shoot_rate=60),
        ]
        for enemy in enemies:
            self.enemies.add(enemy)
            self.all_sprites.add(enemy)
        goal = Goal(2900, 400)
        self.goals.add(goal)
        self.all_sprites.add(goal)
        print(f"Final level goal created at x={goal.rect.x}, y={goal.rect.y}")

    def run(self):
        while True:
            if self.state == "menu":
                self.run_menu()
            elif self.state == "levels":
                self.run_levels()
            elif self.state == "playing":
                self.run_game()
            elif self.state == "final_level":
                self.run_final_level()
            elif self.state == "game_over":
                self.run_game_over()
            elif self.state == "win":
                self.run_win()
            elif self.state == "credits":
                self.run_credits()
            elif self.state == "shop":
                self.run_shop()
            elif self.state == "context":
                self.run_context()

    def run_menu(self):
        if self.menu_music_loaded and not pygame.mixer.music.get_busy():
            pygame.mixer.music.load(os.path.join("assets", "musicamenu.mp3"))
            pygame.mixer.music.set_volume(0.5)
            pygame.mixer.music.play(-1)
        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                sys.exit()
            result = self.menu.update(event)
            if result:
                if result == "Play":
                    if self.menu_music_loaded:
                        pygame.mixer.music.stop()
                    self.state = "playing"
                    self.score = 0
                    self.lives = 3
                    self.scroll_x = 0
                    self.reset_game()
                elif result == "Levels":
                    self.state = "levels"
                    self.level_select = LevelSelect(self.screen, self.font, self.small_font)
                elif result == "Shop":
                    self.state = "shop"
                    self.shop = Shop(self.screen, self.font, self.small_font, self.total_score, self.upgrades)
                elif result == "Credits":
                    if self.menu_music_loaded:
                        pygame.mixer.music.stop()
                    self.state = "credits"
                elif result == "Context":
                    if self.menu_music_loaded:
                        pygame.mixer.music.stop()
                    self.state = "context"
                    self.context = Context(self.screen, self.small_font)
                elif result == "Quit":
                    if self.menu_music_loaded:
                        pygame.mixer.music.stop()
                    pygame.quit()
                    sys.exit()
        self.menu.draw()
        pygame.display.flip()
        self.clock.tick(FPS)

    def run_levels(self):
        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                sys.exit()
            result = self.level_select.update(event)
            if result:
                if result == "Level1":
                    if self.menu_music_loaded:
                        pygame.mixer.music.stop()
                    self.state = "playing"
                    self.score = 0
                    self.lives = 3
                    self.scroll_x = 0
                    self.reset_game()
                elif result == "Level2":
                    if self.menu_music_loaded:
                        pygame.mixer.music.stop()
                    self.state = "final_level"
                    self.score = 0
                    self.lives = 3
                    self.scroll_x = 0
                    if self.player is None:
                        self.player = Player(100, 100, self)
                        self.player.shoot_rate = 5 if "faster_shooting" in self.upgrades else 10
                        self.player.speed = 7 if "faster_movement" in self.upgrades else PLAYER_SPEED
                        if "shield" in self.upgrades:
                            self.player.activate_shield()
                        self.all_sprites.add(self.player)
                    self.reset_final_level()
                elif result == "Back":
                    self.state = "menu"
        self.level_select.draw()
        pygame.display.flip()
        self.clock.tick(FPS)

    def run_context(self):
        if self.context_music_loaded and not pygame.mixer.music.get_busy():
            pygame.mixer.music.load(os.path.join("assets", "teclado.mp3"))
            pygame.mixer.music.set_volume(0.5)
            pygame.mixer.music.play(-1)
        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                sys.exit()
            if event.type == KEYDOWN:
                if event.key == K_RETURN:
                    if self.context_music_loaded:
                        pygame.mixer.music.stop()
                    self.state = "menu"
                    print("ENTER pressed, returning to menu")
        self.context.update()
        self.context.draw()
        pygame.display.flip()
        self.clock.tick(FPS)

    def run_shop(self):
        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                sys.exit()
            result = self.shop.update(event)
            if result == "menu":
                self.state = "menu"
        self.shop.draw()
        pygame.display.flip()
        self.clock.tick(FPS)

    def run_credits(self):
        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                sys.exit()
            if event.type == KEYDOWN:
                if event.key == K_RETURN:
                    self.state = "menu"
        if self.use_credits_image:
            self.screen.blit(self.credits_image, (0, 0))
        else:
            self.screen.fill((50, 50, 150))
            pygame.draw.circle(self.screen, WHITE, (50, 50), 3)
            pygame.draw.circle(self.screen, WHITE, (700, 100), 4)
            pygame.draw.circle(self.screen, WHITE, (200, 150), 2)
            pygame.draw.circle(self.screen, WHITE, (600, 200), 3)
            pygame.draw.circle(self.screen, WHITE, (300, 300), 4)
            pygame.draw.ellipse(self.screen, (200, 200, 200), (100, 50, 80, 40))
            pygame.draw.ellipse(self.screen, (200, 200, 200), (500, 80, 100, 50))
            pygame.draw.ellipse(self.screen, (200, 200, 200), (300, 120, 90, 45))
        pygame.display.flip()
        self.clock.tick(FPS)

    def run_game(self):
        if self.play_music_loaded and not pygame.mixer.music.get_busy():
            pygame.mixer.music.load(os.path.join("assets", "musicaplay.mp3"))
            pygame.mixer.music.set_volume(0.5)
            pygame.mixer.music.play(-1)
        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                sys.exit()
            if event.type == KEYDOWN:
                if event.key == K_w:
                    self.player.jump()
                if event.key == K_ESCAPE:
                    if self.play_music_loaded:
                        pygame.mixer.music.stop()
                    self.state = "menu"
        keys = pygame.key.get_pressed()
        dx, dy = 0, 0
        if keys[K_a]:
            dx -= 1
        if keys[K_d]:
            dx += 1
        if keys[K_s]:
            dy += 1
        if keys[K_SPACE]:
            self.player.shoot(self.bullets, self.all_sprites)
        if dx > 0 and self.player.rect.x > WIDTH // 2 and self.scroll_x < WORLD_WIDTH - WIDTH:
            self.scroll_x += self.player.speed
            self.player.rect.x = WIDTH // 2
            for sprite in self.all_sprites:
                if sprite != self.player:
                    sprite.rect.x -= self.player.speed
        else:
            self.player.move(dx, dy)
        if self.scroll_x < 0:
            self.scroll_x = 0
            for sprite in self.all_sprites:
                if sprite != self.player:
                    sprite.rect.x -= self.scroll_x
            self.scroll_x = 0
        elif self.scroll_x > WORLD_WIDTH - WIDTH:
            self.scroll_x = WORLD_WIDTH - WIDTH
            for sprite in self.all_sprites:
                if sprite != self.player:
                    sprite.rect.x -= self.scroll_x
            self.scroll_x = WORLD_WIDTH - WIDTH
        self.player.update(self.platforms)
        for enemy in self.enemies:
            enemy.update(self.platforms, self.player, self.enemy_bullets, self.all_sprites)
        self.bullets.update()
        self.enemy_bullets.update()
        for sprite in self.enemies.sprites() + self.bullets.sprites() + self.enemy_bullets.sprites():
            if sprite.rect.right < 0:
                sprite.kill()
        if self.player.rect.bottom >= GROUND_LEVEL or pygame.sprite.spritecollide(self.player, self.enemies, False):
            if self.player.take_damage():
                self.lives -= 1
                self.player.health = self.player.max_health
                self.player.rect.x = 100
                self.player.rect.y = 100
                self.player.velocity_y = 0
                self.scroll_x = 0
                for sprite in self.all_sprites:
                    if sprite != self.player:
                        sprite.rect.x += self.scroll_x
                self.reset_game()
                if self.lives <= 0:
                    if self.play_music_loaded:
                        pygame.mixer.music.stop()
                    self.total_score += self.score
                    self.state = "game_over"
        enemy_bullet_hits = pygame.sprite.spritecollide(self.player, self.enemy_bullets, True)
        for hit in enemy_bullet_hits:
            if self.player.take_damage():
                self.player.health -= 10
                if self.player.health <= 0:
                    self.lives -= 1
                    self.player.health = self.player.max_health
                    self.player.rect.x = 100
                    self.player.rect.y = 100
                    self.player.velocity_y = 0
                    self.scroll_x = 0
                    for sprite in self.all_sprites:
                        if sprite != self.player:
                            sprite.rect.x += self.scroll_x
                    self.reset_game()
                    if self.lives <= 0:
                        if self.play_music_loaded:
                            pygame.mixer.music.stop()
                        self.total_score += self.score
                        self.state = "game_over"
        for bullet in self.bullets:
            hits = pygame.sprite.spritecollide(bullet, self.enemies, False)
            for enemy in hits:
                enemy.health -= 20
                bullet.kill()
                if enemy.health <= 0:
                    enemy.kill()
                    self.score += 50
        print(f"Goals active: {len(self.goals.sprites())}")
        if self.goals:
            print(
                f"Player: x={self.player.rect.x}, y={self.player.rect.y}, Goal: x={self.goals.sprites()[0].rect.x}, y={self.goals.sprites()[0].rect.y}")
        if self.goals and pygame.sprite.spritecollide(self.player, self.goals, True):
            print("Goal collided! Transitioning to final_level")
            self.state = "final_level"
            self.reset_final_level()
        self.screen.blit(self.background, (0, 0))
        self.all_sprites.draw(self.screen)
        for enemy in self.enemies:
            enemy.draw_health_bar(self.screen)
        self.player.draw_health_bar(self.screen)
        score_text = self.small_font.render(f"Score: {self.score}", True, BLACK)
        self.screen.blit(score_text, (10, 10))
        for i in range(self.lives):
            self.screen.blit(self.heart_image, (10 + i * 42, 50))
        pygame.display.flip()
        self.clock.tick(FPS)

    def run_final_level(self):
        print("Entered final_level state")
        if self.play_music_loaded and not pygame.mixer.music.get_busy():
            pygame.mixer.music.load(os.path.join("assets", "musicaplay.mp3"))
            pygame.mixer.music.set_volume(0.5)
            pygame.mixer.music.play(-1)
        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                sys.exit()
            if event.type == KEYDOWN:
                if event.key == K_w:
                    self.player.jump()
                if event.key == K_ESCAPE:
                    if self.play_music_loaded:
                        pygame.mixer.music.stop()
                    self.state = "menu"
        keys = pygame.key.get_pressed()
        dx, dy = 0, 0
        if keys[K_a]:
            dx -= 1
        if keys[K_d]:
            dx += 1
        if keys[K_s]:
            dy += 1
        if keys[K_SPACE]:
            self.player.shoot(self.bullets, self.all_sprites)
        if dx > 0 and self.player.rect.x > WIDTH // 2 and self.scroll_x < WORLD_WIDTH - WIDTH:
            self.scroll_x += self.player.speed
            self.player.rect.x = WIDTH // 2
            for sprite in self.all_sprites:
                if sprite != self.player:
                    sprite.rect.x -= self.player.speed
        else:
            self.player.move(dx, dy)
        if self.scroll_x < 0:
            self.scroll_x = 0
            for sprite in self.all_sprites:
                if sprite != self.player:
                    sprite.rect.x -= self.scroll_x
            self.scroll_x = 0
        elif self.scroll_x > WORLD_WIDTH - WIDTH:
            self.scroll_x = WORLD_WIDTH - WIDTH
            for sprite in self.all_sprites:
                if sprite != self.player:
                    sprite.rect.x -= self.scroll_x
            self.scroll_x = WORLD_WIDTH - WIDTH
        self.player.update(self.platforms)
        for enemy in self.enemies:
            enemy.update(self.platforms, self.player, self.enemy_bullets, self.all_sprites)
        self.bullets.update()
        self.enemy_bullets.update()
        for sprite in self.enemies.sprites() + self.bullets.sprites() + self.enemy_bullets.sprites():
            if sprite.rect.right < 0:
                sprite.kill()
        if self.player.rect.bottom >= GROUND_LEVEL or pygame.sprite.spritecollide(self.player, self.enemies, False):
            if self.player.take_damage():
                self.lives -= 1
                self.player.health = self.player.max_health
                self.player.rect.x = 100
                self.player.rect.y = 100
                self.player.velocity_y = 0
                self.scroll_x = 0
                for sprite in self.all_sprites:
                    if sprite != self.player:
                        sprite.rect.x += self.scroll_x
                self.reset_final_level()
                if self.lives <= 0:
                    if self.play_music_loaded:
                        pygame.mixer.music.stop()
                    self.total_score += self.score
                    self.state = "game_over"
        enemy_bullet_hits = pygame.sprite.spritecollide(self.player, self.enemy_bullets, True)
        for hit in enemy_bullet_hits:
            if self.player.take_damage():
                self.player.health -= 10
                if self.player.health <= 0:
                    self.lives -= 1
                    self.player.health = self.player.max_health
                    self.player.rect.x = 100
                    self.player.rect.y = 100
                    self.player.velocity_y = 0
                    self.scroll_x = 0
                    for sprite in self.all_sprites:
                        if sprite != self.player:
                            sprite.rect.x += self.scroll_x
                    self.reset_final_level()
                    if self.lives <= 0:
                        if self.play_music_loaded:
                            pygame.mixer.music.stop()
                        self.total_score += self.score
                        self.state = "game_over"
        for bullet in self.bullets:
            hits = pygame.sprite.spritecollide(bullet, self.enemies, False)
            for enemy in hits:
                enemy.health -= 10  # Level 2: 3 shots to kill (30 health / 10 damage = 3)
                bullet.kill()
                if enemy.health <= 0:
                    enemy.kill()
                    self.score += 50
        print(f"Goals active: {len(self.goals.sprites())}")
        if self.goals:
            print(
                f"Player: x={self.player.rect.x}, y={self.player.rect.y}, Goal: x={self.goals.sprites()[0].rect.x}, y={self.goals.sprites()[0].rect.y}")
        if self.goals and pygame.sprite.spritecollide(self.player, self.goals, True):
            print("Goal collided! You win!")
            if self.play_music_loaded:
                pygame.mixer.music.stop()
            self.total_score += self.score
            self.state = "win"
        self.screen.blit(self.background, (0, 0))
        self.all_sprites.draw(self.screen)
        for enemy in self.enemies:
            enemy.draw_health_bar(self.screen)
        self.player.draw_health_bar(self.screen)
        score_text = self.small_font.render(f"Score: {self.score}", True, BLACK)
        self.screen.blit(score_text, (10, 10))
        for i in range(self.lives):
            self.screen.blit(self.heart_image, (10 + i * 42, 50))
        pygame.display.flip()
        self.clock.tick(FPS)

    def run_win(self):
        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                sys.exit()
            if event.type == KEYDOWN:
                if event.key == K_RETURN:
                    self.state = "menu"
        if self.use_win_image:
            self.screen.blit(self.win_image, (0, 0))
        else:
            self.screen.fill((0, 150, 0))
            win_text = self.font.render("WIN!", True, WHITE)
            score_text = self.font.render(f"Final Score: {self.score}", True, WHITE)
            win_text_rect = win_text.get_rect(center=(WIDTH // 2, 200))
            score_text_rect = score_text.get_rect(center=(WIDTH // 2, 300))
            self.screen.blit(win_text, win_text_rect)
            self.screen.blit(score_text, score_text_rect)
        instruction = self.small_font.render("Press ENTER to return to menu", True, WHITE)
        instruction_shadow = self.small_font.render("Press ENTER to return to menu", True, BLACK)
        instruction_rect = instruction.get_rect(center=(WIDTH // 2, HEIGHT - 30))
        shadow_rect = instruction_rect.copy()
        shadow_rect.x += 2
        shadow_rect.y += 2
        self.screen.blit(instruction_shadow, shadow_rect)
        self.screen.blit(instruction, instruction_rect)
        pygame.display.flip()
        self.clock.tick(FPS)

    def run_game_over(self):
        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                sys.exit()
            if event.type == KEYDOWN:
                if event.key == K_RETURN:
                    self.state = "menu"
        if self.use_gameover_image:
            self.screen.blit(self.gameover_image, (0, 0))
        else:
            self.screen.fill(BLACK)
            game_over = self.font.render("Game Over!", True, WHITE)
            score_text = self.font.render(f"Final Score: {self.score}", True, WHITE)
            instruction = self.font.render("Press ENTER to return to menu", True, WHITE)
            game_over_rect = game_over.get_rect(center=(WIDTH // 2, 200))
            score_text_rect = score_text.get_rect(center=(WIDTH // 2, 300))
            instruction_rect = instruction.get_rect(center=(WIDTH // 2, 450))
            self.screen.blit(game_over, game_over_rect)
            self.screen.blit(score_text, score_text_rect)
            self.screen.blit(instruction, instruction_rect)
        pygame.display.flip()
        self.clock.tick(FPS)


if __name__ == "__main__":
    game = Game()
    game.run()
