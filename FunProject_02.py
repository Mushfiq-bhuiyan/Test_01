```python
import curses
import random
import time
import os

# ============================================================
# TERMINAL SHOOTER
# A real-time ASCII shooting game
# ============================================================

# Characters
PLAYER = "^"
ENEMY = "V"
BOSS = "W"
BULLET = "|"
ENEMY_BULLET = "!"
EXPLOSION = "*"

# Power-ups
POWER_RAPID = "R"
POWER_TRIPLE = "T"
POWER_HEALTH = "+"

# Game settings
FPS = 30
PLAYER_SPEED = 1
BULLET_SPEED = 1

# Colors
COLOR_PLAYER = 1
COLOR_ENEMY = 2
COLOR_BULLET = 3
COLOR_EXPLOSION = 4
COLOR_POWER = 5
COLOR_BOSS = 6
COLOR_UI = 7


class Game:
    def __init__(self, stdscr):
        self.stdscr = stdscr

        # Terminal dimensions
        self.height, self.width = stdscr.getmaxyx()

        # Game area
        self.game_height = self.height - 3

        # Player
        self.player_x = self.width // 2
        self.player_y = self.game_height - 2

        self.player_health = 100
        self.max_health = 100
        self.lives = 3

        # Objects
        self.bullets = []
        self.enemy_bullets = []
        self.enemies = []
        self.explosions = []
        self.powerups = []

        # Score / level
        self.score = 0
        self.level = 1
        self.kills = 0

        # Boss
        self.boss = None
        self.boss_active = False
        self.boss_defeated = False

        # Power-ups
        self.rapid_fire = 0
        self.triple_shot = 0

        # Timing
        self.last_shot = 0
        self.last_enemy_spawn = 0
        self.last_powerup = 0
        self.last_boss_shot = 0

        self.running = True
        self.paused = False

        # Key state
        self.keys = set()

        self.setup_colors()

    # --------------------------------------------------------
    # Setup
    # --------------------------------------------------------

    def setup_colors(self):
        curses.start_color()
        curses.use_default_colors()

        curses.init_pair(COLOR_PLAYER, curses.CYAN, -1)
        curses.init_pair(COLOR_ENEMY, curses.RED, -1)
        curses.init_pair(COLOR_BULLET, curses.YELLOW, -1)
        curses.init_pair(COLOR_EXPLOSION, curses.MAGENTA, -1)
        curses.init_pair(COLOR_POWER, curses.GREEN, -1)
        curses.init_pair(COLOR_BOSS, curses.RED, -1)
        curses.init_pair(COLOR_UI, curses.WHITE, -1)

    # --------------------------------------------------------
    # Input
    # --------------------------------------------------------

    def read_input(self):
        self.keys.clear()

        while True:
            try:
                key = self.stdscr.getch()

                if key == -1:
                    break

                self.keys.add(key)

            except curses.error:
                break

    # --------------------------------------------------------
    # Player
    # --------------------------------------------------------

    def update_player(self):
        if ord("a") in self.keys or ord("A") in self.keys:
            self.player_x -= 1

        if ord("d") in self.keys or ord("D") in self.keys:
            self.player_x += 1

        # Keep player inside screen
        self.player_x = max(1, min(self.width - 2, self.player_x))

        # Shoot
        if ord(" ") in self.keys:
            self.shoot()

    def shoot(self):
        now = time.time()

        # Rapid fire
        cooldown = 0.08 if self.rapid_fire > 0 else 0.20

        if now - self.last_shot < cooldown:
            return

        self.last_shot = now

        # Triple shot power-up
        if self.triple_shot > 0:
            self.bullets.append(
                [self.player_x, self.player_y - 1, -1]
            )

            self.bullets.append(
                [self.player_x, self.player_y - 1, 0]
            )

            self.bullets.append(
                [self.player_x, self.player_y - 1, 1]
            )

        else:
            self.bullets.append(
                [self.player_x, self.player_y - 1, 0]
            )

    # --------------------------------------------------------
    # Enemy spawning
    # --------------------------------------------------------

    def spawn_enemy(self):
        # Don't spawn normal enemies during boss fight
        if self.boss_active:
            return

        now = time.time()

        # Spawn rate increases with level
        delay = max(0.25, 0.9 - self.level * 0.05)

        if now - self.last_enemy_spawn < delay:
            return

        self.last_enemy_spawn = now

        x = random.randint(2, self.width - 3)

        enemy_type = random.choice(["normal", "normal", "fast"])

        if enemy_type == "fast":
            speed = 0.20
            health = 15
        else:
            speed = 0.10
            health = 25

        self.enemies.append({
            "x": x,
            "y": 1,
            "health": health,
            "speed": speed,
            "last_move": now
        })

    # --------------------------------------------------------
    # Boss
    # --------------------------------------------------------

    def spawn_boss(self):
        self.boss_active = True

        self.boss = {
            "x": self.width // 2,
            "y": 2,
            "health": 500 + self.level * 100,
            "max_health": 500 + self.level * 100,
            "direction": 1,
            "last_move": time.time()
        }

    def update_boss(self):
        if not self.boss:
            return

        now = time.time()

        # Move boss horizontally
        if now - self.boss["last_move"] > 0.10:
            self.boss["x"] += self.boss["direction"]

            if self.boss["x"] <= 5:
                self.boss["direction"] = 1

            if self.boss["x"] >= self.width - 6:
                self.boss["direction"] = -1

            self.boss["last_move"] = now

        # Boss shooting
        if now - self.last_boss_shot > max(0.25, 0.8 - self.level * 0.03):

            self.last_boss_shot = now

            self.enemy_bullets.append([
                self.boss["x"],
                self.boss["y"] + 1
            ])

            # Higher levels get additional shots
            if self.level >= 5:
                self.enemy_bullets.append([
                    self.boss["x"] - 2,
                    self.boss["y"] + 1
                ])

                self.enemy_bullets.append([
                    self.boss["x"] + 2,
                    self.boss["y"] + 1
                ])

    # --------------------------------------------------------
    # Bullets
    # --------------------------------------------------------

    def update_bullets(self):
        new_bullets = []

        for bullet in self.bullets:

            x, y, dx = bullet

            y -= BULLET_SPEED
            x += dx

            if y <= 0:
                continue

            new_bullets.append([x, y, dx])

        self.bullets = new_bullets

    def update_enemy_bullets(self):
        new_bullets = []

        for bullet in self.enemy_bullets:

            x, y = bullet

            y += 1

            if y >= self.game_height:
                continue

            new_bullets.append([x, y])

        self.enemy_bullets = new_bullets

    # --------------------------------------------------------
    # Enemies
    # --------------------------------------------------------

    def update_enemies(self):
        now = time.time()

        for enemy in self.enemies:

            if now - enemy["last_move"] >= enemy["speed"]:

                enemy["y"] += 1
                enemy["last_move"] = now

    # --------------------------------------------------------
    # Collision detection
    # --------------------------------------------------------

    def collisions(self):

        # -------------------------
        # Player bullets vs enemies
        # -------------------------

        remaining_bullets = []

        for bullet in self.bullets:

            bx, by, dx = bullet
            hit = False

            # Normal enemies
            for enemy in self.enemies[:]:

                if abs(bx - enemy["x"]) <= 1 and by == enemy["y"]:

                    enemy["health"] -= 25
                    hit = True

                    if enemy["health"] <= 0:

                        self.score += 10
                        self.kills += 1

                        self.create_explosion(
                            enemy["x"],
                            enemy["y"]
                        )

                        self.enemies.remove(enemy)

                    break

            # Boss
            if self.boss_active and self.boss:

                if (
                    abs(bx - self.boss["x"]) <= 2
                    and by == self.boss["y"]
                ):

                    self.boss["health"] -= 10
                    hit = True

                    if self.boss["health"] <= 0:
                        self.kill_boss()

            if not hit:
                remaining_bullets.append(bullet)

        self.bullets = remaining_bullets

        # -------------------------
        # Enemy bullets vs player
        # -------------------------

        remaining_enemy_bullets = []

        for bullet in self.enemy_bullets:

            bx, by = bullet

            if (
                abs(bx - self.player_x) <= 1
                and by == self.player_y
            ):

                self.player_health -= 10

                self.create_explosion(
                    self.player_x,
                    self.player_y
                )

            else:
                remaining_enemy_bullets.append(bullet)

        self.enemy_bullets = remaining_enemy_bullets

        # -------------------------
        # Enemies reaching player
        # -------------------------

        for enemy in self.enemies[:]:

            if enemy["y"] >= self.player_y:

                self.player_health -= 25

                self.create_explosion(
                    self.player_x,
                    self.player_y
                )

                self.enemies.remove(enemy)

        # -------------------------
        # Player collision with boss
        # -------------------------

        if self.boss_active and self.boss:

            if self.boss["y"] >= self.player_y - 1:

                self.player_health -= 50

        # -------------------------
        # Check health
        # -------------------------

        if self.player_health <= 0:

            self.lives -= 1

            self.player_health = self.max_health

            self.enemies.clear()
            self.enemy_bullets.clear()

            self.player_x = self.width // 2

            if self.lives <= 0:
                self.running = False

    # --------------------------------------------------------
    # Explosions
    # --------------------------------------------------------

    def create_explosion(self, x, y):

        self.explosions.append({
            "x": x,
            "y": y,
            "time": time.time()
        })

    def update_explosions(self):

        now = time.time()

        self.explosions = [
            e for e in self.explosions
            if now - e["time"] < 0.25
        ]

    # --------------------------------------------------------
    # Power-ups
    # --------------------------------------------------------

    def spawn_powerup(self):

        now = time.time()

        if now - self.last_powerup < 8:
            return

        if random.random() > 0.20:
            return

        self.last_powerup = now

        power_type = random.choice([
            POWER_RAPID,
            POWER_TRIPLE,
            POWER_HEALTH
        ])

        self.powerups.append({
            "x": random.randint(2, self.width - 3),
            "y": 1,
            "type": power_type
        })

    def update_powerups(self):

        for power in self.powerups[:]:

            power["y"] += 1

            # Player collects power-up
            if (
                abs(power["x"] - self.player_x) <= 1
                and power["y"] == self.player_y
            ):

                self.collect_powerup(power)

                self.powerups.remove(power)

            elif power["y"] >= self.game_height:

                self.powerups.remove(power)

    def collect_powerup(self, power):

        if power["type"] == POWER_RAPID:
            self.rapid_fire = 8

        elif power["type"] == POWER_TRIPLE:
            self.triple_shot = 8

        elif power["type"] == POWER_HEALTH:
            self.player_health = min(
                self.max_health,
                self.player_health + 40
            )

        self.score += 25

    # --------------------------------------------------------
    # Levels
    # --------------------------------------------------------

    def update_level(self):

        # Every 15 kills = next level
        new_level = self.kills // 15 + 1

        if new_level > self.level:

            self.level = new_level

            # Boss every 3 levels
            if self.level % 3 == 0 and not self.boss_active:
                self.spawn_boss()

    # --------------------------------------------------------
    # Timers
    # --------------------------------------------------------

    def update_timers(self, dt):

        if self.rapid_fire > 0:
            self.rapid_fire -= dt

        if self.triple_shot > 0:
            self.triple_shot -= dt

        self.rapid_fire = max(0, self.rapid_fire)
        self.triple_shot = max(0, self.triple_shot)

    # --------------------------------------------------------
    # Boss defeated
    # --------------------------------------------------------

    def kill_boss(self):

        x = self.boss["x"]
        y = self.boss["y"]

        # Big explosion
        for _ in range(12):
            self.create_explosion(
                x + random.randint(-3, 3),
                y + random.randint(-1, 2)
            )

        self.score += 1000
        self.kills += 15

        self.boss = None
        self.boss_active = False
        self.boss_defeated = True

    # --------------------------------------------------------
    # Drawing
    # --------------------------------------------------------

    def draw_char(self, y, x, char, color):

        if (
            0 <= y < self.game_height
            and 0 <= x < self.width
        ):

            try:
                self.stdscr.addstr(
                    y,
                    x,
                    char,
                    curses.color_pair(color)
                )
            except curses.error:
                pass

    def draw(self):

        self.stdscr.erase()

        # -------------------------
        # Game border
        # -------------------------

        for x in range(self.width):
            self.draw_char(
                0,
                x,
                "-",
                COLOR_UI
            )

        for x in range(self.width):
            self.draw_char(
                self.game_height,
                x,
                "-",
                COLOR_UI
            )

        # -------------------------
        # Player
        # -------------------------

        self.draw_char(
            self.player_y,
            self.player_x,
            PLAYER,
            COLOR_PLAYER
        )

        # -------------------------
        # Player bullets
        # -------------------------

        for x, y, dx in self.bullets:

            self.draw_char(
                y,
                x,
                BULLET,
                COLOR_BULLET
            )

        # -------------------------
        # Enemies
        # -------------------------

        for enemy in self.enemies:

            self.draw_char(
                enemy["y"],
                enemy["x"],
                ENEMY,
                COLOR_ENEMY
            )

        # -------------------------
        # Enemy bullets
        # -------------------------

        for x, y in self.enemy_bullets:

            self.draw_char(
                y,
                x,
                ENEMY_BULLET,
                COLOR_ENEMY
            )

        # -------------------------
        # Boss
        # -------------------------

        if self.boss_active and self.boss:

            self.draw_char(
                self.boss["y"],
                self.boss["x"] - 2,
                "[",
                COLOR_BOSS
            )

            self.draw_char(
                self.boss["y"],
                self.boss["x"] - 1,
                BOSS,
                COLOR_BOSS
            )

            self.draw_char(
                self.boss["y"],
                self.boss["x"],
                BOSS,
                COLOR_BOSS
            )

            self.draw_char(
                self.boss["y"],
                self.boss["x"] + 1,
                BOSS,
                COLOR_BOSS
            )

            self.draw_char(
                self.boss["y"],
                self.boss["x"] + 2,
                "]",
                COLOR_BOSS
            )

        # -------------------------
        # Explosions
        # -------------------------

        for explosion in self.explosions:

            self.draw_char(
                explosion["y"],
                explosion["x"],
                EXPLOSION,
                COLOR_EXPLOSION
            )

        # -------------------------
        # Power-ups
        # -------------------------

        for power in self.powerups:

            self.draw_char(
                power["y"],
                power["x"],
                power["type"],
                COLOR_POWER
            )

        # -------------------------
        # UI
        # -------------------------

        health_bar_length = 15

        health_units = int(
            health_bar_length *
            self.player_health /
            self.max_health
        )

        health_bar = (
            "#" * health_units +
            "-" * (health_bar_length - health_units)
        )

        status = ""

        if self.rapid_fire > 0:
            status += f" RAPID:{self.rapid_fire:.0f}s"

        if self.triple_shot > 0:
            status += f" TRIPLE:{self.triple_shot:.0f}s"

        ui = (
            f" SCORE:{self.score} "
            f" LEVEL:{self.level} "
            f" LIVES:{self.lives} "
            f" HP:[{health_bar}]"
        )

        try:
            self.stdscr.addstr(
                self.game_height + 1,
                0,
                ui[:self.width - 1],
                curses.color_pair(COLOR_UI)
            )

            controls = (
                "A/D: MOVE | SPACE: FIRE | P: PAUSE | Q: QUIT"
            )

            self.stdscr.addstr(
                self.game_height + 2,
                0,
                controls[:self.width - 1],
                curses.color_pair(COLOR_UI)
            )

            if self.boss_active:

                boss_hp = (
                    f"BOSS HP: "
                    f"{self.boss['health']}/"
                    f"{self.boss['max_health']}"
                )

                self.stdscr.addstr(
                    1,
                    max(0, self.width // 2 - len(boss_hp) // 2),
                    boss_hp,
                    curses.color_pair(COLOR_BOSS)
                )

        except curses.error:
            pass

        self.stdscr.refresh()

    # --------------------------------------------------------
    # Pause
    # --------------------------------------------------------

    def pause_screen(self):

        self.stdscr.erase()

        message = "=== PAUSED ==="
        controls = "Press P to continue"

        try:
            self.stdscr.addstr(
                self.height // 2,
                max(0, self.width // 2 - len(message) // 2),
                message
            )

            self.stdscr.addstr(
                self.height // 2 + 1,
                max(0, self.width // 2 - len(controls) // 2),
                controls
            )

            self.stdscr.refresh()

        except curses.error:
            pass

    # --------------------------------------------------------
    # Game loop
    # --------------------------------------------------------

    def run(self):

        previous = time.time()

        while self.running:

            now = time.time()
            dt = now - previous
            previous = now

            self.read_input()

            # Quit
            if (
                ord("q") in self.keys
                or ord("Q") in self.keys
            ):
                break

            # Pause
            if (
                ord("p") in self.keys
                or ord("P") in self.keys
            ):
                self.paused = not self.paused

            if self.paused:

                self.pause_screen()

                time.sleep(0.05)
                continue

            # Update game
            self.update_player()

            self.spawn_enemy()
            self.spawn_powerup()

            self.update_bullets()
            self.update_enemy_bullets()

            self.update_enemies()
            self.update_powerups()

            self.update_boss()

            self.collisions()

            self.update_explosions()

            self.update_level()

            self.update_timers(dt)

            self.draw()

            time.sleep(1 / FPS)

        self.game_over_screen()

    # --------------------------------------------------------
    # Game over
    # --------------------------------------------------------

    def game_over_screen(self):

        self.stdscr.erase()

        messages = [
            "==============================",
            "        GAME OVER",
            "==============================",
            "",
            f"       SCORE : {self.score}",
            f"       LEVEL : {self.level}",
            f"       KILLS : {self.kills}",
            "",
            "      Press any key to exit",
            "=============================="
        ]

        start_y = max(
            1,
            self.height // 2 - len(messages) // 2
        )

        for i, message in enumerate(messages):

            try:

                self.stdscr.addstr(
                    start_y + i,
                    max(0, self.width // 2 - len(message) // 2),
                    message
                )

            except curses.error:
                pass

        self.stdscr.refresh()

        self.stdscr.nodelay(False)
        self.stdscr.getch()


# ============================================================
# Start game
# ============================================================

def main(stdscr):

    # Hide cursor
    curses.curs_set(0)

    # Non-blocking input
    stdscr.nodelay(True)

    # Allow keypad
    stdscr.keypad(True)

    game = Game(stdscr)

    game.run()


if __name__ == "__main__":

    # Windows requires windows-curses:
    # pip install windows-curses

    curses.wrapper(main)
```

### ▶️ Run it

On **Windows**:

```bash
pip install windows-curses
python terminal_shooter.py
```

On **Linux/macOS**:

```bash
python3 terminal_shooter.py
```

### 🎮 Gameplay

| Key     | Action                    |
| ------- | ------------------------- |
| `A`     | Move left                 |
| `D`     | Move right                |
| `SPACE` | Hold to continuously fire |
| `P`     | Pause                     |
| `Q`     | Quit                      |

Power-ups are:

* **R** → Rapid fire
* **T** → Triple shot
* **+** → Health recovery

Every **15 kills** you advance a level. At **levels 3, 6, 9...**, a boss appears with its own health bar and attacks.

**Tip:** Make the terminal window fairly large (e.g. maximize it), because the game uses the terminal dimensions as its play area.
