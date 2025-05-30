from PIL import Image, ImageDraw, ImageFont
from pathlib import Path

FONT_NAME = "CourierPrimeCode.ttf"
FONT_SIZE = 45
IMAGE_WIDTH = 1920
IMAGE_HEIGHT = 1080
START_X = 710
START_Y = 160
COL_WIDTH = 340

important_augs = ('Speed Enhancement', 'Power Recirculator')
short_augs =     ('Speed',             'Power Recirc'      )
all_skills =     ('Weapons: Heavy', 'Weapons: Pistol', 'Weapons: Rifle', 'Weapons: Low-Tech', 'Weapons: Demolition', 'Environmental Training', 'Lockpicking', 'Electronics', 'Medicine', 'Computer', 'Swimming')
short_skills =   ('Heavy',          'Pistol',          'Rifle',          'Low-Tech',          'Demolition',          'Enviro',                 'Lockpicking', 'Electronics', 'Medicine', 'Computer', 'Swimming')

skill_levels =   ['UNTRAINED', 'TRAINED', 'ADVANCED', 'MASTER']

font = ImageFont.truetype(FONT_NAME, FONT_SIZE)

def MakeLayout():
    global short_augs, short_skills
    img = Image.open('baselayout.png')
    assert img.width == IMAGE_WIDTH
    assert img.height == IMAGE_HEIGHT
    gc = ImageDraw.Draw(img)
    text = '\n'.join(short_augs)
    if short_augs:
        text += '\n'
    text += '\n'.join(short_skills)
    DrawColumn(gc, -1.2, '', text) # HACK: this column -1.2 for better positioning
    outname = Path('out') / 'layout.png'
    img.save(outname)


def MakePlayerImage(col, player, timestamp, state):
    img = Image.new("RGBA", (IMAGE_WIDTH, IMAGE_HEIGHT))#, 'black')
    gc = ImageDraw.Draw(img)
    DrawPlayer(gc, col, player, state)
    outname = player + ' ' + timestamp.replace(':', '-') + '.png'
    outpath = Path('out') / outname
    img.save(outpath)

def DrawPlayer(gc, col, name, state:dict):
    global important_augs, all_skills
    text = ''
    for aug in important_augs:
        lvl = state.get(aug)
        if lvl is None:
            text += 'N/A\n'
            continue
        text += str(lvl+1) + '\n'
    for skill in all_skills:
        lvl = state.get(skill, 0)
        text += skill_levels[int(lvl)] + '\n'
    #print(text)
    DrawColumn(gc, col, name, text, align='center')


def DrawColumn(gc:ImageDraw.ImageDraw, col, header, text, align='left'):
    coords = (START_X + col * COL_WIDTH, START_Y)
    #print('DrawColumn', header)
    #print(text)
    text = header + '\n' + text
    gc.text(coords, text, font=font, align=align, spacing=30)
