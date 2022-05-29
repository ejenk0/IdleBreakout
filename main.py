from math import ceil, floor, log10
import random
import pygame as pg

pg.init()

# CONFIG
WINWIDTH = 900
WINHEIGHT = 600

GAMEMARGIN = 20
NAVMARGINX = 20
NAVMARGINY = 5
NAVITEMHEIGHT = 60
NAVHEIGHT = NAVMARGINY * 2 + NAVITEMHEIGHT
NAVCOLOR = (232, 220, 174)


GAMEWIDTH = WINWIDTH - 2 * GAMEMARGIN
GAMEHEIGHT = WINHEIGHT - GAMEMARGIN - NAVHEIGHT

SPAWNX = GAMEWIDTH / 2 + GAMEMARGIN
SPAWNY = GAMEHEIGHT / 2 + GAMEMARGIN

BRICKCOLS = 15
BRICKROWS = 20
BRICKWIDTH = GAMEWIDTH / BRICKCOLS
BRICKHEIGHT = GAMEHEIGHT / BRICKROWS

BALLRADIUS = 10

REALSPEEDLIMIT = 16

# COLORS
GREEN = (99, 213, 54)

# FONTS
BRICKFONT = pg.font.SysFont("Arial", 18)
BIGBRICKFONT = pg.font.SysFont("Arial", 26)
PRICEFONT = pg.font.SysFont("Courier", 13)
UIFONT = pg.font.SysFont("Courier", 15)

# GAME VARS
game_data = {
    "balls": {
        "basic": {"speed": 1, "power": 1, "price": 25},
        "plasma": {"speed": 2, "power": 3, "range": 1, "price": 200},
        "sniper": {"speed": 4, "power": 5, "price": 1500},
        "scatter": {"speed": 3, "power": 10, "extra balls": 2, "price": 10000},
        "cannon": {"speed": 4, "power": 50, "price": 75000},
        "poison": {"speed": 5, "power": 5, "price": 75000},
    }
}
# INITIAL GAME VARS
game_vars = {
    "money": 0,
    "level": 20,
    "particles": 1,
    "maxballs": 50,
    "speedlimit": 40,
    "upgrades": {
        "basic": [0, 0],
        "plasma": [0, 0],
        "sniper": [0, 0],
        "scatter": [0, 0],
        "cannon": [0, 0],
        "poison": [0, 0],
    },
    "claimablegold": 0,
    "gold": 0,
    "devtools": False,
}


def get_ball_data(ballname: str):
    if ballname == "oneshot":
        data = get_ball_data("scatter")
        data["speed"] /= 2
        data["power"] /= 2
        return data
    else:
        data = game_data["balls"][ballname].copy()
        for i, upgrade in enumerate(upgrades[ballname]["upgrades"]):
            data[upgrade["type"]] = (
                data[upgrade["type"]]
                + upgrade["increment"] * game_vars["upgrades"][ballname][i]
            )
        return data


# LEVELS
levels = []

FULLCOL = [1 for x in range(BRICKROWS)]
EMPTYCOL = [0 for x in range(BRICKROWS)]

five_cols = (
    [EMPTYCOL for x in range(int((BRICKCOLS - 5) / 2))]
    + [FULLCOL for x in range(5)]
    + [EMPTYCOL for x in range(int((BRICKCOLS - 5) / 2))]
)
levels.append(five_cols)

three_cols = (
    [FULLCOL]
    + [EMPTYCOL for x in range(int((BRICKCOLS - 5) / 2))]
    + [FULLCOL for x in range(3)]
    + [EMPTYCOL for x in range(int((BRICKCOLS - 5) / 2))]
    + [FULLCOL]
)
levels.append(three_cols)

TWOBRICKSLICE = (
    [0 for x in range(int(BRICKROWS / 4))]
    + [1 for x in range(int(BRICKROWS / 2))]
    + [0 for x in range(int(BRICKROWS / 4))]
)
two_bricks = (
    [EMPTYCOL]
    + [TWOBRICKSLICE for x in range(int(BRICKCOLS / 3))]
    + [EMPTYCOL for x in range(int(BRICKCOLS / 5))]
    + [TWOBRICKSLICE for x in range(int(BRICKCOLS / 3))]
    + [EMPTYCOL]
)
levels.append(two_bricks)

FOURBRICKSLICE = (
    [0 for x in range(4)]
    + [1 for x in range(int(BRICKROWS / 3))]
    + [0 for x in range(2)]
    + [1 for x in range(int(BRICKROWS / 3))]
    + [0 for x in range(4)]
)
four_bricks = (
    [EMPTYCOL for x in range(2)]
    + [FOURBRICKSLICE for x in range(int(BRICKCOLS / 3))]
    + [EMPTYCOL]
    + [FOURBRICKSLICE for x in range(int(BRICKCOLS / 3))]
    + [EMPTYCOL for x in range(2)]
)
levels.append(four_bricks)

TENBRICKSLICE = [0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0]
ten_bricks = (
    [EMPTYCOL for x in range(2)]
    + [TENBRICKSLICE for x in range(int(BRICKCOLS / 3))]
    + [EMPTYCOL]
    + [TENBRICKSLICE for x in range(int(BRICKCOLS / 3))]
    + [EMPTYCOL for x in range(2)]
)
levels.append(ten_bricks)

win = pg.display.set_mode((WINWIDTH, WINHEIGHT))


def generate_level(map, level):
    bricks = pg.sprite.Group()
    if not level % 20 == 0:
        for x, col in enumerate(map):
            for y, row in enumerate(col):
                if row:
                    bricks.add(
                        Brick(
                            x * BRICKWIDTH + GAMEMARGIN,
                            y * BRICKHEIGHT + NAVHEIGHT,
                            level,
                        )
                    )
    else:
        bricks.add(GoldBrick(value=level * 100, gold_value=floor(log10(level))))
    return bricks


def count_balls(balls, _class):
    return sum(isinstance(ball, _class) for ball in balls)


def currency_formatter(amount, currency="$"):
    return currency + (
        str(round(amount, 1))
        if amount < 1000
        else str(round(amount / 1000, 1)) + "K"
        if amount < 1000000
        else str(round(amount / 1000000, 1)) + "M"
        if amount < 1000000000
        else str(round(amount / 1000000000, 1)) + "B"
        if amount < 1000000000000
        else str(round(amount / 1000000000000, 1)) + "T"
    )


def determineSide(ball: pg.sprite.Sprite, brick: pg.sprite.Sprite):
    rect1 = ball.rect.copy()
    x = rect1.x
    y = rect1.y
    rect2 = brick.rect.copy()
    for _ in range(30):
        if (
            rect1.centery < rect2.top
            and rect1.centerx > rect2.left
            and rect1.centerx < rect2.right
        ):
            return "top"
        if (
            rect1.centery > rect2.bottom
            and rect1.centerx > rect2.left
            and rect1.centerx < rect2.right
        ):
            return "bottom"
        if (
            rect1.centerx < rect2.left
            and rect1.centery > rect2.top
            and rect1.centery < rect2.bottom
        ):
            return "left"
        if (
            rect1.centerx > rect2.right
            and rect1.centery > rect2.top
            and rect1.centery < rect2.bottom
        ):
            return "right"

        x -= ball.speed.x
        y -= ball.speed.y

        rect1.x = x
        rect1.y = y
    return "diagonal"


# UI


class PurchaseButton(pg.sprite.Sprite):
    def __init__(
        self,
        x,
        y,
        ball=None,
        initial_price=0,
        price_multiplier=1,
        label1="",
        label2="",
        width=NAVITEMHEIGHT,
        upgradetype=None,
        ballname=None,
        upgradeindex=None,
        upgradeincrement=None,
        upgrademax=None,
        height=NAVITEMHEIGHT,
        font=PRICEFONT,
    ):
        super().__init__()
        self.ball = ball
        self.image = pg.Surface((width, height))
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.initial_price = initial_price
        self.price_multiplier = price_multiplier
        self.label1 = label1
        self.label2 = label2
        self.width = width
        self.upgradetype = upgradetype
        self.ballname = ballname
        self.upgradeindex = upgradeindex
        self.upgradeincrement = upgradeincrement
        self.upgrademax = upgrademax
        self.height = height
        self.font = font
        self._layer = 5
        self.update()

    def update(self):
        # BALL ICON / LABELS
        if self.ball:
            ballcount = sum(isinstance(ball, self.ball) for ball in balls)
            self.price = round(
                self.initial_price * (self.price_multiplier**ballcount)
            )
        else:
            self.price = self.initial_price * (
                self.price_multiplier
                ** game_vars["upgrades"][self.ballname][self.upgradeindex]
            )
            self.label1 = self.upgradetype.capitalize()
            count = game_vars["upgrades"][self.ballname][self.upgradeindex]
            self.label2 = (
                str(
                    game_data["balls"][self.ballname][self.upgradetype]
                    + count * self.upgradeincrement
                )
                + " >> "
                + str(
                    game_data["balls"][self.ballname][self.upgradetype]
                    + (count + 1) * self.upgradeincrement
                )
            )

        # bg
        self.image.fill((245, 245, 245))
        # progress bar
        if (
            self.upgrademax
            and game_vars["upgrades"][self.ballname][self.upgradeindex]
            >= self.upgrademax
        ):
            pg.draw.rect(
                self.image,
                (181, 181, 181),
                (
                    0,
                    self.height * 2 / 3 + 1,
                    self.width,
                    self.height / 3,
                ),
            )
        else:
            pg.draw.rect(
                self.image,
                GREEN,
                (
                    0,
                    self.height * 2 / 3 + 1,
                    self.width * (game_vars["money"] / self.price),
                    self.height / 3,
                ),
            )
        # border
        pg.draw.rect(self.image, (0, 0, 0), (0, 0, self.width, self.height), 2)
        pg.draw.line(
            self.image,
            (0, 0, 0),
            (0, self.height * 2 / 3),
            (self.width, self.height * 2 / 3),
            2,
        )
        text = currency_formatter(self.price)
        # PRICE
        if (
            self.upgrademax
            and game_vars["upgrades"][self.ballname][self.upgradeindex]
            >= self.upgrademax
        ):
            text = "SOLD OUT"

        textwidth, textheight = self.font.size(text)
        self.image.blit(
            self.font.render(text, True, (0, 0, 0)),
            (self.width / 2 - textwidth / 2, self.height * 5 / 6 - textheight / 2),
        )
        if self.ball:
            ball = self.ball()
            self.image.blit(
                ball.image,
                (
                    self.width / 2 - ball.image.get_width() / 2,
                    self.height * 2 / 3 / 2 - ball.image.get_height() / 2,
                ),
            )
        else:
            self.image.blit(
                self.font.render(self.label1, True, (0, 0, 0)),
                (self.width / 2 - self.font.size(self.label1)[0] / 2, 5),
            )
            self.image.blit(
                self.font.render(self.label2, True, (0, 0, 0)),
                (self.width / 2 - self.font.size(self.label2)[0] / 2, 24),
            )

    def onClick(self):
        global game_vars
        if self.ball:
            global balls
            if (
                game_vars["money"] >= self.price
                and (len(balls) - len(oneshots)) < game_vars["maxballs"]
            ):
                game_vars["money"] -= self.price
                balls.add(self.ball())
                self.update()
                return True
        else:
            if game_vars["money"] >= self.price and (
                game_vars["upgrades"][self.ballname][self.upgradeindex]
                < self.upgrademax
                or not self.upgrademax
            ):
                game_vars["money"] -= self.price
                game_vars["upgrades"][self.ballname][self.upgradeindex] += 1
                return True
        return False


class DeleteButton(pg.sprite.Sprite):
    def __init__(
        self,
        x,
        y,
        ball,
        width=NAVITEMHEIGHT * 1.5,
        height=NAVITEMHEIGHT / 2,
        font: pg.font.Font = UIFONT,
    ):
        super().__init__()
        self.ball = ball
        self.width = width
        self.height = height
        self.image = pg.Surface((width, height))
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.font = font
        self._layer = 5
        self.update()

    def update(self):
        # bg
        self.image.fill((245, 245, 245))
        # border
        pg.draw.rect(self.image, (0, 0, 0), (0, 0, self.width, self.height), 2)
        # text
        text = Text(0, 0, self.width, self.height, "DELETE 1x")
        self.image.blit(text.image, text.rect)

    def onClick(self):
        global balls
        relevant_balls = list(
            filter(lambda ball: ball.name == self.ball().name, balls.sprites())
        )
        if relevant_balls:
            relevant_balls.pop().kill()
            return True
        return False


class Text(pg.sprite.Sprite):
    def __init__(
        self,
        x,
        y,
        maxwidth,
        maxheight,
        text="",
        textcolor=(0, 0, 0),
        updatefunc=None,
    ):
        super().__init__()
        self.text = text
        self.textcolor = textcolor
        self.maxwidth = maxwidth
        self.maxheight = maxheight
        self.x = x
        self.y = y
        self.updatefunc = updatefunc
        self.update()
        self._layer = 5

    def update(self):
        if self.updatefunc:
            self.updatefunc(self)
        self.image = UIFONT.render(self.text, True, self.textcolor)
        self.rect = self.image.get_rect()
        self.rect.x = self.x + self.maxwidth / 2 - self.rect.width / 2
        self.rect.y = self.y + self.maxheight / 2 - self.rect.height / 2


class Box(pg.sprite.Sprite):
    def __init__(self, x, y, width, height, bordercolor=(0, 0, 0), fillcolor=NAVCOLOR):
        super().__init__()
        self.image = pg.Surface((width, height))
        self.image.fill(fillcolor)
        pg.draw.rect(self.image, bordercolor, (0, 0, width, height), 2)
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self._layer = 2


class Image(pg.sprite.Sprite):
    def __init__(self, x, y, width, height, path):
        super().__init__()
        self.image = pg.image.load(path)
        self.image = pg.transform.scale(self.image, (round(width), round(height)))
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self._layer = 3


class UpgradeMenu(pg.sprite.Sprite):
    """
    The upgrade menu is a sprite that contains a list of upgrade buttons.
    Only one instance is used.
    """

    def __init__(
        self, width=WINWIDTH * 0.8, height=WINHEIGHT * 0.8, font: pg.font.Font = UIFONT
    ):
        super().__init__()
        self.width = width
        self.height = height
        self.image = pg.Surface((width, height))
        self.image.set_colorkey((1, 1, 255))
        self.rect = self.image.get_rect()
        self.rect.x = WINWIDTH / 2 - self.width / 2
        self.rect.y = WINHEIGHT / 2 - self.height / 2
        self.font = font
        self.active_tab = "upgrades"
        self.active = False
        self.tab_buttons = {}
        self.upgrade_buttons = {}
        self._layer = 6
        self.update()

    def update(self):
        if self.active:
            self.image = pg.Surface((self.width, self.height))
            self.image.set_colorkey((1, 1, 255))

            # BG and BORDER

            self.image.fill((1, 1, 255))
            pg.draw.rect(
                self.image, NAVCOLOR, (0, 0, self.width, self.height), border_radius=15
            )
            pg.draw.rect(
                self.image, (0, 0, 0), (0, 0, self.rect.width, self.rect.height), 4, 15
            )

            # GENERATE TAB BUTTONS
            tabs = ["upgrades", "powerups", "achievements", "prestige", "skills"]
            tab_button_width = self.width / len(tabs)
            tab_padding = 10
            self.tab_buttons = {}
            self.delete_buttons = {}
            for i, tab in enumerate(tabs):
                tab_rect = pg.Rect(
                    i * tab_button_width + tab_padding,
                    tab_padding,
                    tab_button_width - tab_padding * 2,
                    30,
                )
                if self.active_tab == tab:
                    pg.draw.rect(self.image, (243, 236, 215), tab_rect, border_radius=5)
                self.tab_buttons[tab] = pg.draw.rect(
                    self.image, (0, 0, 0), tab_rect, 2, border_radius=5
                )
                text = Text(
                    tab_rect.x,
                    tab_rect.y,
                    tab_rect.width,
                    tab_rect.height,
                    tab.upper(),
                )
                self.image.blit(text.image, text.rect)

            if self.active_tab == "upgrades":
                # GENERATE UPGRADE BUTTONS

                column_width = self.width / len(upgrades)
                column_height = self.height - 50
                for i, column in enumerate(upgrades):
                    column_rect = pg.Rect(
                        i * column_width, 50, column_width, column_height
                    )
                    # COUNT
                    count_text = Text(
                        column_rect.x,
                        column_rect.y,
                        column_rect.width,
                        20,
                        "(x" + str(count_balls(balls, upgrades[column]["ball"])) + ")",
                    )
                    self.image.blit(count_text.image, count_text.rect)

                    # NAME
                    name_text = Text(
                        column_rect.x,
                        column_rect.y + 20,
                        column_rect.width,
                        20,
                        column.upper() + " BALL",
                    )
                    self.image.blit(name_text.image, name_text.rect)

                    # BALL
                    self.image.blit(
                        upgrades[column]["ball"]().image,
                        (
                            column_rect.centerx
                            - upgrades[column]["ball"]().rect.width / 2,
                            column_rect.y + 43,
                        ),
                    )

                    # UPGRADE 1
                    initprice = upgrades[column]["upgrades"][0]["initialprice"]
                    pricemult = upgrades[column]["upgrades"][0]["pricemult"]
                    type = upgrades[column]["upgrades"][0]["type"]
                    increment = upgrades[column]["upgrades"][0]["increment"]
                    upgrademax = upgrades[column]["upgrades"][0]["max"]

                    upgrade1_button = PurchaseButton(
                        column_rect.centerx - NAVITEMHEIGHT * 1.5 / 2,
                        column_rect.y + 75,
                        width=NAVITEMHEIGHT * 1.5,
                        initial_price=initprice,
                        price_multiplier=pricemult,
                        upgradetype=type,
                        upgradeincrement=increment,
                        ballname=column,
                        upgradeindex=0,
                        upgrademax=upgrademax,
                    )
                    self.image.blit(upgrade1_button.image, upgrade1_button.rect)

                    # UPGRADE 2
                    initprice = upgrades[column]["upgrades"][1]["initialprice"]
                    pricemult = upgrades[column]["upgrades"][1]["pricemult"]
                    type = upgrades[column]["upgrades"][1]["type"]
                    increment = upgrades[column]["upgrades"][1]["increment"]
                    upgrademax = upgrades[column]["upgrades"][1]["max"]

                    upgrade2_button = PurchaseButton(
                        column_rect.centerx - NAVITEMHEIGHT * 1.5 / 2,
                        column_rect.y + 85 + NAVITEMHEIGHT,
                        width=NAVITEMHEIGHT * 1.5,
                        initial_price=initprice,
                        price_multiplier=pricemult,
                        upgradetype=type,
                        upgradeincrement=increment,
                        ballname=column,
                        upgradeindex=1,
                        upgrademax=upgrademax,
                    )
                    self.image.blit(upgrade2_button.image, upgrade2_button.rect)

                    self.upgrade_buttons[column] = [upgrade1_button, upgrade2_button]

                    # DELETE BUTTON
                    delete_button = DeleteButton(
                        column_rect.centerx - NAVITEMHEIGHT * 1.5 / 2,
                        column_rect.y + 95 + NAVITEMHEIGHT * 2,
                        ball=upgrades[column]["ball"],
                    )
                    self.image.blit(delete_button.image, delete_button.rect)

                    self.delete_buttons[column] = delete_button

            # CLOSE BUTTON

            self.close_rect = pg.Rect(
                self.width / 2 - NAVITEMHEIGHT * 1.5 / 2,
                self.height - 37,
                NAVITEMHEIGHT * 1.5,
                30,
            )
            pg.draw.rect(self.image, (0, 0, 0), self.close_rect, 2, border_radius=5)
            close_text = Text(
                self.close_rect.x,
                self.close_rect.y,
                self.close_rect.width,
                self.close_rect.height,
                "CLOSE",
            )
            self.image.blit(close_text.image, close_text.rect)

        else:
            self.image = pg.Surface((0, 0))
            # self.rect = self.image.get_rect()

    def clicked(self, pos):
        # TAB BUTTONS
        for tab, tabrect in self.tab_buttons.items():
            if tabrect.collidepoint(pos):
                self.active_tab = tab
        # UPGRADE BUTTONS
        for column in self.upgrade_buttons.values():
            for button in column:
                if button.rect.collidepoint(pos):
                    button.onClick()
        # DELETE BUTTONS
        for button in self.delete_buttons.values():
            if button.rect.collidepoint(pos):
                button.onClick()
        # UPGRADE MENU CLOSE BUTTON
        if self.close_rect.collidepoint(pos):
            self.active = False


# BRICKS


class Brick(pg.sprite.Sprite):
    def __init__(self, x, y, value: int, width=BRICKWIDTH, height=BRICKHEIGHT):
        pg.sprite.Sprite.__init__(self)
        self.width = width
        self.height = height
        self.image = pg.Surface((self.width, self.height))
        self.image.set_colorkey((1, 1, 255))
        self.value = value
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.infected = 1
        self.update()

    def update(self):
        if self.value <= 0:
            self.kill()
        random.seed(self.value)
        self.color = (
            random.randint(100, 255),
            random.randint(100, 255),
            random.randint(100, 255),
        )
        self.image.fill((1, 1, 255))
        pg.draw.rect(
            self.image, self.color, (0, 0, BRICKWIDTH, BRICKHEIGHT), border_radius=3
        )
        pg.draw.rect(
            self.image,
            (0, 0, 0) if self.infected == 1 else (201, 0, 10),
            (0, 0, BRICKWIDTH, BRICKHEIGHT),
            width=2,
            border_radius=3,
        )

        textwidth, textheight = BRICKFONT.size(str(self.value))
        self.image.blit(
            BRICKFONT.render(str(self.value), True, (0, 0, 0)),
            (BRICKWIDTH / 2 - textwidth / 2, 2),
        )


class GoldBrick(Brick):
    def __init__(self, value: int, gold_value: int, font=BIGBRICKFONT):
        self.font = font
        self.x = GAMEMARGIN + GAMEWIDTH / 2 - BRICKWIDTH * 5 / 2
        self.y = GAMEMARGIN + NAVHEIGHT + GAMEHEIGHT / 2 - BRICKHEIGHT * 5 / 2
        self.color = (244, 204, 3)
        self.gold_value = gold_value
        self.infected = 0
        super().__init__(
            self.x, self.y, value, width=BRICKWIDTH * 5, height=BRICKHEIGHT * 5
        )

    def update(self):
        global game_vars
        if self.value <= 0:
            game_vars["claimablegold"] += self.gold_value
            self.kill()
        self.image.fill((1, 1, 255))
        pg.draw.rect(
            self.image,
            self.color,
            (0, 0, self.width, self.height),
            border_radius=3,
        )
        pg.draw.rect(
            self.image,
            (0, 0, 0) if self.infected == 1 else (201, 0, 10),
            (0, 0, self.width, self.height),
            width=2,
            border_radius=3,
        )
        textwidth, textheight = self.font.size(str(self.value))
        self.image.blit(
            self.font.render(str(self.value), True, (0, 0, 0)),
            (self.width / 2 - textwidth / 2, self.height / 3 - textheight / 2),
        )
        textwidth, textheight = self.font.size("+" + str(self.gold_value) + " GOLD")
        self.image.blit(
            self.font.render("+" + str(self.gold_value) + " GOLD", True, (0, 0, 0)),
            (self.width / 2 - textwidth / 2, self.height * 2 / 3 - textheight / 2),
        )


# BALLS


class Ball(pg.sprite.Sprite):
    def __init__(self, color, x, y, radius):
        pg.sprite.Sprite.__init__(self)
        self.image = pg.Surface((radius * 2, radius * 2))
        self.image.fill((1, 1, 1))
        self.image.set_colorkey((1, 1, 1))
        pg.draw.circle(self.image, color, (radius, radius), radius)
        pg.draw.circle(self.image, (0, 0, 0), (radius, radius), radius, 2)
        self.rect = self.image.get_rect()
        self.x = x
        self.y = y
        self.rect.x = x
        self.rect.y = y
        self.radius = radius
        self.name = "basic"
        angle = random.randint(0, 360)
        self.speed = pg.math.Vector2(1, 0).rotate(angle).normalize()

    def update(self):
        data = get_ball_data(self.name)
        self.velocity = data["speed"]
        self.speed = self.speed.normalize() * (self.velocity / 60) * REALSPEEDLIMIT
        self.strength = data["power"]

        self.x += self.speed.x
        self.y += self.speed.y

        self.rect.x = self.x
        self.rect.y = self.y

        self.border_bounce()

    def bounce_horizontal(self):
        self.speed.reflect_ip(pg.math.Vector2(random.uniform(0.9, 1.1), 0))

    def bounce_vertical(self):
        self.speed.reflect_ip(pg.math.Vector2(0, random.uniform(0.9, 1.1)))

    def border_bounce(self):
        if self.rect.x < GAMEMARGIN:
            self.bounce_horizontal()
            self.x = GAMEMARGIN
            self.rect.x = GAMEMARGIN
        elif self.rect.x > (GAMEWIDTH + GAMEMARGIN) - 2 * self.radius:
            self.bounce_horizontal()
            self.x = (GAMEWIDTH + GAMEMARGIN) - 2 * self.radius
            self.rect.x = (GAMEWIDTH + GAMEMARGIN) - 2 * self.radius
        elif self.rect.y < NAVHEIGHT:
            self.bounce_vertical()
            self.y = NAVHEIGHT
            self.rect.y = NAVHEIGHT
        elif self.rect.y > GAMEHEIGHT + NAVHEIGHT - 2 * self.radius:
            self.bounce_vertical()
            self.y = GAMEHEIGHT + NAVHEIGHT - 2 * self.radius
            self.rect.y = GAMEHEIGHT + NAVHEIGHT - 2 * self.radius
        else:
            return False
        return True


class BasicBall(Ball):
    def __init__(self):
        super().__init__((249, 254, 2), SPAWNX, SPAWNY, BALLRADIUS)
        self.name = "basic"


class PlasmaBall(Ball):
    def __init__(self):
        super().__init__((242, 2, 254), SPAWNX, SPAWNY, BALLRADIUS)
        pg.draw.circle(self.image, (245, 213, 26), (BALLRADIUS, BALLRADIUS), 2)
        self.name = "plasma"


class PlasmaBlast(pg.sprite.Sprite):
    def __init__(self, ballrect: pg.Rect, ballstrength: int):
        pg.sprite.Sprite.__init__(self)
        self.ballrect = ballrect
        range = get_ball_data("plasma")["range"] * 0.75
        self.image = pg.Surface((BRICKWIDTH * range, BRICKHEIGHT * range))
        self.image.fill((242, 2, 254))
        self.rect = self.image.get_rect()
        self.rect.center = self.ballrect.center
        self.strength = ceil(ballstrength * 0.25)
        self.decay = 1
        self.update()

    def update(self):
        if self.decay <= 0:
            self.kill()
        self.decay -= 0.01
        self.image.set_alpha(self.decay * 140)


class SniperBall(Ball):
    def __init__(self):
        super().__init__((240, 240, 240), SPAWNX, SPAWNY, BALLRADIUS)
        pg.draw.line(
            self.image,
            (0, 0, 0),
            (BALLRADIUS - 1, 4),
            (BALLRADIUS - 1, BALLRADIUS * 2 - 5),
            2,
        )
        pg.draw.line(
            self.image,
            (0, 0, 0),
            (4, BALLRADIUS - 1),
            (BALLRADIUS * 2 - 5, BALLRADIUS - 1),
            2,
        )
        self.name = "sniper"

    def border_bounce(self):
        if (
            self.rect.x < GAMEMARGIN
            or self.rect.x > (GAMEWIDTH + GAMEMARGIN) - 2 * self.radius
            or self.rect.y < NAVHEIGHT
            or self.rect.y > GAMEHEIGHT + NAVHEIGHT - 2 * self.radius
        ):
            mindistance = None
            targetbrick = None
            for brick in bricks:
                vec = pg.math.Vector2(brick.rect.center) - pg.math.Vector2(
                    self.rect.center
                )
                distance = vec.length()
                if mindistance is None or distance < mindistance:
                    mindistance = distance
                    targetbrick = brick

            self.speed = (
                pg.math.Vector2(targetbrick.rect.center)
                - pg.math.Vector2(self.rect.center)
            ).normalize() * ((self.velocity / 60) * REALSPEEDLIMIT)


class ScatterBall(Ball):
    def __init__(self):
        super().__init__((239, 126, 43), SPAWNX, SPAWNY, BALLRADIUS)
        pg.draw.line(
            self.image,
            (0, 0, 0),
            (BALLRADIUS - 3, 6),
            (BALLRADIUS - 3, BALLRADIUS * 2 - 7),
            1,
        )
        pg.draw.line(
            self.image,
            (0, 0, 0),
            (BALLRADIUS, 6),
            (BALLRADIUS, BALLRADIUS * 2 - 7),
            1,
        )
        pg.draw.line(
            self.image,
            (0, 0, 0),
            (BALLRADIUS + 3, 6),
            (BALLRADIUS + 3, BALLRADIUS * 2 - 7),
            1,
        )
        self.name = "scatter"

    def border_bounce(self):
        count = get_ball_data(self.name)["extra balls"]
        if super().border_bounce():
            for i in range(count):
                balls.add(OneShotBall(self.rect.center))


class OneShotBall(Ball):
    def __init__(self, pos):
        super().__init__((239, 126, 43), pos[0], pos[1], BALLRADIUS / 2)
        oneshots.add(self)
        self.name = "oneshot"


class CannonBall(Ball):
    def __init__(self):
        super().__init__((101, 101, 101), SPAWNX, SPAWNY, BALLRADIUS * 1.5)
        self.name = "cannon"


class PoisonBall(Ball):
    def __init__(self):
        super().__init__((236, 1, 5), SPAWNX, SPAWNY, BALLRADIUS)
        img = Image(0, 0, BALLRADIUS * 1.9, BALLRADIUS * 1.9, "images/Skull.png")
        self.image.blit(img.image, img.rect)
        self.name = "poison"


# Upgrade details
# max = 0 = no limit
upgrades = {
    "basic": {
        "ball": BasicBall,
        "upgrades": [
            {
                "type": "speed",
                "increment": 1,
                "max": 9,
                "initialprice": 100,
                "pricemult": 2,
            },
            {
                "type": "power",
                "increment": 1,
                "max": 0,
                "initialprice": 250,
                "pricemult": 1.65,
            },
        ],
    },
    "plasma": {
        "ball": PlasmaBall,
        "upgrades": [
            {
                "type": "range",
                "increment": 1,
                "max": 6,
                "initialprice": 1000,
                "pricemult": 2.5,
            },
            {
                "type": "power",
                "increment": 3,
                "max": 0,
                "initialprice": 1250,
                "pricemult": 1.5,
            },
        ],
    },
    "sniper": {
        "ball": SniperBall,
        "upgrades": [
            {
                "type": "speed",
                "increment": 1,
                "max": 6,
                "initialprice": 7500,
                "pricemult": 1.75,
            },
            {
                "type": "power",
                "increment": 5,
                "max": 0,
                "initialprice": 8000,
                "pricemult": 1.35,
            },
        ],
    },
    "scatter": {
        "ball": ScatterBall,
        "upgrades": [
            {
                "type": "extra balls",
                "increment": 1,
                "max": 8,
                "initialprice": 75000,
                "pricemult": 2.5,
            },
            {
                "type": "power",
                "increment": 10,
                "max": 0,
                "initialprice": 100000,
                "pricemult": 1.3,
            },
        ],
    },
    "cannon": {
        "ball": CannonBall,
        "upgrades": [
            {
                "type": "speed",
                "increment": 2,
                "max": 6,
                "initialprice": 100000,
                "pricemult": 1.5,
            },
            {
                "type": "power",
                "increment": 25,
                "max": 0,
                "initialprice": 150000,
                "pricemult": 1.25,
            },
        ],
    },
    "poison": {
        "ball": PoisonBall,
        "upgrades": [
            {
                "type": "speed",
                "increment": 2,
                "max": 5,
                "initialprice": 120000,
                "pricemult": 1.5,
            },
            {
                "type": "power",
                "increment": 5,
                "max": 0,
                "initialprice": 50000,
                "pricemult": 1.2,
            },
        ],
    },
}

balls = pg.sprite.Group()
oneshots = pg.sprite.Group()

random.seed(game_vars["level"])
bricks = generate_level(random.choice(levels), game_vars["level"])

decayingplasmablasts = pg.sprite.Group()
uielements = pg.sprite.LayeredUpdates()
buttons = pg.sprite.Group()

upgrademenu = UpgradeMenu()
upgrademenu.add(uielements)

# BALL PURCHASE BUTTONS

PurchaseButton(NAVMARGINX, NAVMARGINY, BasicBall, 25, 1.5).add(uielements, buttons)
PurchaseButton(NAVMARGINX + NAVITEMHEIGHT, NAVMARGINY, PlasmaBall, 200, 1.4).add(
    uielements, buttons
)
PurchaseButton(NAVMARGINX + NAVITEMHEIGHT * 2, NAVMARGINY, SniperBall, 1500, 1.35).add(
    uielements, buttons
)
PurchaseButton(
    NAVMARGINX + NAVITEMHEIGHT * 3, NAVMARGINY, ScatterBall, 10000, 1.35
).add(uielements, buttons)
PurchaseButton(NAVMARGINX + NAVITEMHEIGHT * 4, NAVMARGINY, CannonBall, 75000, 1.3).add(
    uielements, buttons
)
PurchaseButton(NAVMARGINX + NAVITEMHEIGHT * 5, NAVMARGINY, PoisonBall, 75000, 1.25).add(
    uielements, buttons
)

# BALL COUNT


def update_ballcount(self):
    self.text = (
        str(len(balls.sprites()) - len(oneshots.sprites()))
        + "/"
        + str(game_vars["maxballs"])
    )


Text(
    NAVMARGINX + NAVITEMHEIGHT * 6,
    NAVMARGINY,
    NAVITEMHEIGHT,
    NAVITEMHEIGHT / 2,
    updatefunc=update_ballcount,
).add(uielements)
Text(
    NAVMARGINX + NAVITEMHEIGHT * 6,
    NAVMARGINY + NAVITEMHEIGHT / 2,
    NAVITEMHEIGHT,
    NAVITEMHEIGHT / 2,
    text="BALLS",
).add(uielements)

# LEVEL DISPLAY

Box(NAVMARGINX + NAVITEMHEIGHT * 7, NAVMARGINY, NAVITEMHEIGHT * 1.5, NAVITEMHEIGHT).add(
    uielements
)
Text(
    NAVMARGINX + NAVITEMHEIGHT * 7,
    NAVMARGINY,
    NAVITEMHEIGHT * 1.5,
    NAVITEMHEIGHT / 2,
    text="LEVEL",
).add(uielements)


def update_level(self):
    self.text = str(game_vars["level"])


Text(
    NAVMARGINX + NAVITEMHEIGHT * 7,
    NAVMARGINY + NAVITEMHEIGHT / 2,
    NAVITEMHEIGHT * 1.5,
    NAVITEMHEIGHT / 2,
    updatefunc=update_level,
).add(uielements)

# UPGRADE BUTTON

open_upgrade_menu = Box(
    NAVMARGINX + NAVITEMHEIGHT * 8.6,
    NAVMARGINY,
    NAVITEMHEIGHT * 2,
    NAVITEMHEIGHT / 2,
    fillcolor=(243, 237, 215),
)
open_upgrade_menu.add(uielements)

Text(
    NAVMARGINX + NAVITEMHEIGHT * 8.6,
    NAVMARGINY,
    NAVITEMHEIGHT * 2,
    NAVITEMHEIGHT / 2,
    text="UPGRADES",
).add(uielements)

# PRESTIGE BUTTON

open_prestige_menu = Box(
    NAVMARGINX + NAVITEMHEIGHT * 8.6,
    NAVMARGINY + NAVITEMHEIGHT / 2,
    NAVITEMHEIGHT * 2,
    NAVITEMHEIGHT / 2,
    fillcolor=(243, 237, 215),
)
open_prestige_menu.add(uielements)

Text(
    NAVMARGINX + NAVITEMHEIGHT * 8.6,
    NAVMARGINY + NAVITEMHEIGHT / 2,
    NAVITEMHEIGHT * 2,
    NAVITEMHEIGHT / 2,
    text="PRESTIGE",
).add(uielements)

# POWERUP BUTTON

open_powerup_menu = Box(
    NAVMARGINX + NAVITEMHEIGHT * 10.7,
    NAVMARGINY,
    NAVITEMHEIGHT,
    NAVITEMHEIGHT,
    fillcolor=GREEN,
)
open_powerup_menu.add(uielements)

Image(
    NAVMARGINX + NAVITEMHEIGHT * 10.7,
    NAVMARGINY,
    NAVITEMHEIGHT * 0.99,
    NAVITEMHEIGHT,
    "images/upgrade.svg",
).add(uielements)

# MONEY DISPLAY

Box(
    NAVMARGINX + NAVITEMHEIGHT * 11.8,
    NAVMARGINY,
    NAVITEMHEIGHT * 2.25,
    NAVITEMHEIGHT,
    fillcolor=(243, 237, 215),
).add(uielements)

Image(
    NAVMARGINX + NAVITEMHEIGHT * 11.8,
    NAVMARGINY + NAVITEMHEIGHT * 0.03,
    NAVITEMHEIGHT * 0.55,
    NAVITEMHEIGHT / 2 - NAVITEMHEIGHT * 0.05,
    path="images/Dollar.png",
).add(uielements)

Box(
    NAVMARGINX + NAVITEMHEIGHT * 12.3,
    NAVMARGINY + NAVITEMHEIGHT * 0.05,
    NAVITEMHEIGHT * 1.7,
    NAVITEMHEIGHT / 2 - NAVITEMHEIGHT * 0.05,
    fillcolor=GREEN,
).add(uielements)


def update_money(self):
    self.text = currency_formatter(game_vars["money"], currency="")


Text(
    NAVMARGINX + NAVITEMHEIGHT * 12.3,
    NAVMARGINY + NAVITEMHEIGHT * 0.05,
    NAVITEMHEIGHT * 1.7,
    NAVITEMHEIGHT / 2 - NAVITEMHEIGHT * 0.05,
    updatefunc=update_money,
).add(uielements)


clock = pg.time.Clock()

# DEV TOOLS

devtools = pg.sprite.Group()
dev_money = Box(WINWIDTH - 20, 0, 20, 20, fillcolor="gold")
dev_money.add(devtools)


def update_fps(self):
    self.text = str(int(clock.get_fps()))


Text(0, WINHEIGHT - 20, 50, 10, updatefunc=update_fps).add(devtools)


def update_gold_count(self):
    self.text = str(game_vars["claimablegold"]) + " | " + str(game_vars["gold"])


Text(0, WINHEIGHT - 35, 50, 10, updatefunc=update_gold_count).add(devtools)

# GAME LOOP

playing = True
while playing:
    clock.tick(60)
    for event in pg.event.get():
        if event.type == pg.QUIT:
            playing = False
        if event.type == pg.MOUSEBUTTONUP:
            pos = pg.mouse.get_pos()
            # BALL BUTTONS
            for button in buttons:
                if button.rect.collidepoint(pos):
                    if button.onClick():
                        break
            if upgrademenu.active:
                upgrademenu_pos = (
                    pos[0] - upgrademenu.rect.left,
                    pos[1] - upgrademenu.rect.top,
                )
                upgrademenu.clicked(upgrademenu_pos)
            # UPGRADE MENU OPEN BUTTON
            if open_upgrade_menu.rect.collidepoint(pos):
                upgrademenu.active = True
                upgrademenu.active_tab = "upgrades"
                break

            # PRESTIGE MENU OPEN BUTTON
            if open_prestige_menu.rect.collidepoint(pos):
                upgrademenu.active = True
                upgrademenu.active_tab = "prestige"
                break

            # POWERUP MENU OPEN BUTTON
            if open_powerup_menu.rect.collidepoint(pos):
                upgrademenu.active = True
                upgrademenu.active_tab = "powerups"
                break

            # BRICKS
            for brick in bricks:
                if brick.rect.collidepoint(pos):
                    brick.value -= 1
                    game_vars["money"] += 1
                    brick.update()

            if game_vars["devtools"]:
                # DEV MONEY
                if dev_money.rect.collidepoint(pos):
                    game_vars["money"] *= 2
                    break

        if event.type == pg.KEYDOWN:
            if event.key == pg.K_d:
                game_vars["devtools"] = not game_vars["devtools"]
    win.fill(NAVCOLOR)

    pg.draw.rect(
        win,
        (226, 243, 214),
        (
            GAMEMARGIN,
            NAVHEIGHT,
            GAMEWIDTH,
            GAMEHEIGHT,
        ),
    )

    bricks.draw(win)

    balls.update()
    balls.draw(win)

    uielements.update()
    uielements.draw(win)

    if game_vars["devtools"]:
        devtools.update()
        devtools.draw(win)

    plasmablasts = pg.sprite.Group()
    collisions = pg.sprite.groupcollide(balls, bricks, False, False)
    for ball in collisions:
        brick = collisions[ball][0]
        if ball.name == "plasma":
            plasmablasts.add(PlasmaBlast(ball.rect, ball.strength))
        game_vars["money"] += max(0, min(brick.value, ball.strength * brick.infected))
        brick.value -= ball.strength * brick.infected

        if ball.name != "cannon" or brick.value > 0:
            side = determineSide(ball, brick)
            if side in ["top", "bottom"]:
                ball.bounce_vertical()
            elif side in ["left", "right"]:
                ball.bounce_horizontal()
            elif side == "diagonal":
                ball.bounce_vertical()
                ball.bounce_horizontal()

        if ball.name == "poison":
            brick.infected = 2

        brick.update()
        if ball.name == "oneshot":
            ball.kill()

    plasmacollisions = pg.sprite.groupcollide(plasmablasts, bricks, False, False)
    for blast in plasmacollisions:
        for brick in plasmacollisions[blast]:
            brick.value -= blast.strength
            game_vars["money"] += max(0, min(brick.value, blast.strength))
            if brick.value <= 0:
                bricks.remove(brick)
            else:
                brick.update()
    if game_vars["particles"]:
        decayingplasmablasts.add(plasmablasts)
        decayingplasmablasts.update()
        decayingplasmablasts.draw(win)

    plasmablasts.empty()

    if len(bricks) == 0:
        game_vars["level"] += 1
        random.seed(game_vars["level"])
        bricks = generate_level(random.choice(levels), game_vars["level"])

    pg.display.update()
