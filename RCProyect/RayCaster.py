import pygame
from pygame.sprite import collide_circle_ratio
from math import cos, sin, pi, atan2
from pygame.locals import *


RAY_AMOUNT = 100
SPRITE_BACKGROUND = (152, 0, 136, 255)

width = 1000
height = 500

wallTextures = {
    '1': pygame.image.load('pared1.png'),
    '2': pygame.image.load('pared2.png'),
    '3': pygame.image.load('pared3.png'),
    '4': pygame.image.load('pared4.png'),
    '5': pygame.image.load('pared5.png'),
    '6': pygame.image.load('pared6.png'),
    '7': pygame.image.load('pared7.png')
}

enemies = [
    {"x": 50,
     "y": 100,
     "sprite": pygame.image.load('orc.png')},
    {"x": 250,
     "y": 100,
     "sprite": pygame.image.load('mutantelephant.jpg')},
    {"x": 200,
     "y": 350,
     "sprite": pygame.image.load('megaman.png')}
]
class Raycaster(object):
    def __init__(self, screen):
        self.screen = screen
        _, _, self.width, self.height = screen.get_rect()
        self.map = []
        self.zbuffer = [float('inf') for z in range(self.width)]
        self.blocksize = 50
        self.wallheight = 50
        self.maxdistance = 300
        self.stepSize = 5
        self.turnSize = 5
        self.player = {
            'x': 100,
            'y': 70,
            'fov': 60,
            'angle': 0}
        self.hitEnemy = False

    def load_map(self, filename):
        self.map = []
        with open(filename) as file:
            for line in file.readlines():
                self.map.append(list(line.rstrip()))

    def drawMinimap(self):
        minimapWidth = 100
        minimapHeight = 100
        minimapSurface = pygame.Surface((500, 500))
        minimapSurface.fill(pygame.Color("gray"))
        for x in range(0, 500, self.blocksize):
            for y in range(0, 500, self.blocksize):
                i = int(x/self.blocksize)
                j = int(y/self.blocksize)
                if (
                    j < len(self.map)
                    and i < len(self.map[j])
                    and self.map[j][i] != ' '
                ):
                    tex = wallTextures[self.map[j][i]]
                    tex = pygame.transform.scale(
                        tex, (self.blocksize, self.blocksize))
                    rect = tex.get_rect()
                    rect = rect.move((x, y))
                    minimapSurface.blit(tex, rect)
        rect = (int(self.player['x'] - 4), int(self.player['y']) - 4, 10, 10)
        minimapSurface.fill(pygame.Color('black'), rect)

        for enemy in enemies:
            rect = (enemy['x'] - 4, enemy['y'] - 4, 10, 10)
            minimapSurface.fill(pygame.Color('red'), rect)

        minimapSurface = pygame.transform.scale(
            minimapSurface, (minimapWidth, minimapHeight))
        self.screen.blit(minimapSurface, (self.width -
                                          minimapWidth, self.height - minimapHeight))

    def drawBlock(self, x, y, id):
        tex = wallTextures[id].convert()
        tex = pygame.transform.scale(
            tex, (self.blocksize, self.blocksize)).convert()
        rect = tex.get_rect()
        rect = rect.move((x, y))
        self.screen.blit(tex, rect)

    def drawPlayerIcon(self, color):
        if self.player['x'] < self.width / 2:
            rect = (self.player['x'] - 2, self.player['y'] - 2, 5, 5)
            self.screen.fill(color, rect)

    def castRay(self, angle):
        rads = angle * pi / 180
        dist = 0
        stepSize = 1
        stepX = stepSize * cos(rads)
        stepY = stepSize * sin(rads)
        playerPos = (self.player['x'], self.player['y'])
        x = playerPos[0]
        y = playerPos[1]
        while True:
            dist += stepSize
            x += stepX
            y += stepY
            i = int(x/self.blocksize)
            j = int(y/self.blocksize)
            if (
                j < len(self.map)
                and i < len(self.map[j])
                and self.map[j][i] != ' '
            ):
                hitX = x - i*self.blocksize
                hitY = y - j*self.blocksize
                hit = 0
                if 1 < hitX < self.blocksize-1:
                    if hitY < 1:
                        hit = self.blocksize - hitX
                    elif hitY >= self.blocksize-1:
                        hit = hitX
                elif 1 < hitY < self.blocksize-1:
                    if hitX < 1:
                        hit = hitY
                    elif hitX >= self.blocksize-1:
                        hit = self.blocksize - hitY
                tx = hit / self.blocksize
                return dist, self.map[j][i], tx

    def drawSprite(self, obj, size):
        spriteDist = ((self.player['x'] - obj['x']) **
                      2 + (self.player['y'] - obj['y']) ** 2) ** 0.5

        spriteAngle = atan2(obj['y'] - self.player['y'],
                            obj['x'] - self.player['x']) * 180 / pi

        aspectRatio = obj['sprite'].get_width() / obj['sprite'].get_height()
        spriteHeight = (self.height / spriteDist) * size
        spriteWidth = spriteHeight * aspectRatio

        angleDif = (spriteAngle - self.player['angle']) % 360
        angleDif = (angleDif - 360) if angleDif > 180 else angleDif
        startX = angleDif * self.width / self.player['fov']
        startX += (self.width / 2) - (spriteWidth / 2)
        startY = (self.height / 2) - (spriteHeight / 2)
        startX = int(startX)
        startY = int(startY)

        for x in range(startX, startX + int(spriteWidth)):
            if (0 < x < self.width) and self.zbuffer[x] >= spriteDist:
                for y in range(startY, startY + int(spriteHeight)):
                    tx = int((x - startX) *
                             obj['sprite'].get_width() / spriteWidth)
                    ty = int((y - startY) *
                             obj['sprite'].get_height() / spriteHeight)
                    texColor = obj['sprite'].get_at((tx, ty))
                    if texColor != SPRITE_BACKGROUND and texColor[3] > 128:
                        self.screen.set_at((x, y), texColor)

                        if y == self.height / 2:
                            self.zbuffer[x] = spriteDist
                            if x == self.width / 2:
                                self.hitEnemy = True

    def render(self):
        halfHeight = int(self.height / 2)
        for column in range(RAY_AMOUNT):
            angle = self.player['angle'] - (self.player['fov'] / 2) + (self.player['fov'] * column / RAY_AMOUNT)
            dist, id, tx = self.castRay(angle)
            rayWidth = int(( 1 / RAY_AMOUNT) * self.width)
            for i in range(rayWidth):
                self.zbuffer[column * rayWidth + i] = dist
            startX = int(( (column / RAY_AMOUNT) * self.width))
            h = self.height / (dist * cos( (angle - self.player["angle"]) * pi / 180)) * self.wallheight
            startY = int(halfHeight - h/2)
            endY = int(halfHeight + h/2)
            color_k = (1 - min(1, dist / self.maxdistance)) * 255
            tex = wallTextures[id]
            tex = pygame.transform.scale(tex, (tex.get_width() * rayWidth, int(h)))
            tx = int(tx * tex.get_width())
            self.screen.blit(tex, (startX, startY), (tx,0,rayWidth,tex.get_height()))
        self.hitEnemy = False
        for enemy in enemies:
            self.drawSprite(enemy, 50)
        sightRect = (int(self.width / 2 - 2), int(self.height / 2 - 2), 5,5 )
        self.screen.fill(pygame.Color('red') if self.hitEnemy else pygame.Color('white'), sightRect)
        self.drawMinimap()

def menu():
    pygame.mixer.music.load('click.mp3')
    pygame.mixer.music.set_volume(0.45)
    flag = True
    while flag:
        click = False
        for ev in pygame.event.get():
            if ev.type == pygame.MOUSEBUTTONDOWN:
                if ev.button == 1:
                    click = True
            elif ev.type == pygame.QUIT:
                flag = False
        gb = pygame.image.load("fondomenu.png")
        gb = pygame.transform.scale(gb, (width, height))
        gbrect = gb.get_rect()
        screen.blit(gb, gbrect)
        surface, tr = newText("Diego RC", titleFont)
        tr.center = ((width/2), (height/2)-100)
        screen.blit(surface, tr)
        mx, my = pygame.mouse.get_pos()
        boton = crearboton(400, 225, 200, 50, "Jugar", pygame.Color("black"), width/2, 250)
        salirboton = crearboton(400, 290, 200, 50, "Salir", pygame.Color("black"), width/2, 310)
        if boton.collidepoint((mx, my)):
            if click:
                pygame.mixer.music.play()
                flag = False
                elegirmapa()
        elif salirboton.collidepoint((mx, my)):
            if click:
                pygame.mixer.music.play()
                flag = False
                salir()
                firstLoop = False
        pygame.display.update()
        clock.tick(100)

def updateFPS():
    fps = str(int(clock.get_fps()))
    fps = font.render(fps, 1, pygame.Color("white"))
    return fps


def salir():
    pygame.quit()
    quit()




def newText(text, font, colour=pygame.Color("Pink")):
    textSurface = font.render(text, True, colour)
    return textSurface, textSurface.get_rect()




def juego():
    isRunning = True
    maxVol = 0.80
    currentVol = 0.30
    delta = clock.tick(100)
    dTime = 1 / float(delta)
    pygame.mixer.music.load('play.mp3')
    pygame.mixer.music.set_volume(currentVol)
    pygame.mixer.music.play(-1)
    while isRunning:
        keys = pygame.key.get_pressed()
        for ev in pygame.event.get():
            if (
                ev.type != pygame.QUIT
                and ev.type == pygame.KEYDOWN
                and ev.key == pygame.K_ESCAPE
            ):
                isRunning = False
                pygame.mixer.music.fadeout(500)
            elif (ev.type == pygame.QUIT):
                isRunning = False
        newX = rCaster.player['x']
        newY = rCaster.player['y']
        forward = rCaster.player['angle'] * pi / 180
        right = (rCaster.player['angle'] + 90) * pi / 180
        if keys[K_w]:
            newX += cos(forward) * rCaster.stepSize + 0.5 * dTime
            newY += sin(forward) * rCaster.stepSize + 0.5 * dTime
        elif keys[K_s]:
            newX -= cos(forward) * rCaster.stepSize + 0.5 * dTime
            newY -= sin(forward) * rCaster.stepSize + 0.5 * dTime
        elif keys[K_a]:
            newX -= cos(right) * rCaster.stepSize + 0.5 * dTime
            newY -= sin(right) * rCaster.stepSize + 0.5 * dTime
        elif keys[K_d]:
            newX += cos(right) * rCaster.stepSize + 0.5 * dTime
            newY += sin(right) * rCaster.stepSize + 0.5 * dTime
        elif keys[K_q]:
            rCaster.player['angle'] -= rCaster.turnSize + 0.5 * dTime
        elif keys[K_e]:
            rCaster.player['angle'] += rCaster.turnSize + 0.5 * dTime
        i = int(newX/rCaster.blocksize)
        j = int(newY/rCaster.blocksize)
        if rCaster.map[j][i] == ' ':
            rCaster.player['x'] = newX
            rCaster.player['y'] = newY
        screen.fill(pygame.Color("gray"))
        screen.fill(pygame.Color("saddlebrown"),
                    (0, 0,  width, int(height / 2)))
        screen.fill(pygame.Color("dimgray"), (0,
                                              int(height / 2),  width, int(height / 2)))
        rCaster.render()
        screen.fill(pygame.Color("black"), (0, 0, 30, 30))
        screen.blit(updateFPS(), (0, 0))
        clock.tick(100)
        pygame.display.update()

def crearboton(x, y, w, h, text, color, centerx, centery):
    btnTxt = pygame.font.Font('rale.ttf', 30)
    btn = pygame.Rect(x, y, w, h)
    pygame.draw.rect(screen, color, btn)
    bs, br = newText(text, btnTxt)
    br.center = (centerx, centery)
    screen.blit(bs, br)
    return btn

def elegirmapa():
    selecting = True
    while selecting:
        mx, my = pygame.mouse.get_pos()
        click = False
        for ev in pygame.event.get():
            if ev.type == pygame.MOUSEBUTTONDOWN:
                if ev.button == 1:
                    click = True
            elif ev.type == pygame.QUIT:
                selecting = False
        gb = pygame.image.load("fondomenu2.jpg")
        gb = pygame.transform.scale(gb, (width, height))
        gbrect = gb.get_rect()
        screen.blit(gb, gbrect)
        ss, sr = newText("Selecciona el mapa", titleFont)
        sr.center = ((width/2), (height/2)-150)
        screen.blit(ss, sr)
        mapa1 = crearboton(450, 200, 100, 50, "Mapa 1", pygame.Color("black"), width/2, 225)
        mapa3 = crearboton(450, 260, 100, 50, "Mapa 2", pygame.Color("black"), width/2, 285)
        mapa2 = crearboton(450, 320, 100, 50, "Mapa 3", pygame.Color("black"), width/2, 345)


        if mapa1.collidepoint((mx, my)):
            if click:
                FUNCboton("mapa1.txt")
                selecting = False
        elif mapa2.collidepoint((mx, my)):
            if click:
                FUNCboton("mapa2.txt")
                selecting = False
        elif mapa3.collidepoint((mx, my)):
            if click:
                FUNCboton("mapa3.txt")
                selecting = False
        pygame.display.update()
        clock.tick(100)


def FUNCboton(arg0):
    pygame.mixer.music.play()
    rCaster.load_map(arg0)
    juego()




pygame.init()
pygame.mixer.init()

flags = pygame.DOUBLEBUF | pygame.HWACCEL | pygame.HWSURFACE
screen = pygame.display.set_mode((width, height), flags, 16)
screen.set_alpha(None)

pygame.event.set_allowed([QUIT, KEYDOWN, KEYUP, MOUSEBUTTONDOWN])

rCaster = Raycaster(screen)

clock = pygame.time.Clock()
font = pygame.font.SysFont("Arial", 25)
titleFont = pygame.font.Font("rale.ttf", 90)

firstLoop = True
while firstLoop:
    menu()
