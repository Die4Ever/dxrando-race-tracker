from PIL import Image, ImageDraw, ImageFont
#from io import BytesIO
from pathlib import Path
import json
import re

FONT_NAME="CourierPrimeCode.ttf"
FONT_SIZE = 28
IMAGE_WIDTH = 1920
IMAGE_HEIGHT = 1080

augs = set(('Speed Enhancement', 'Power Recirculator'))
skills = set()

skill_levels = ['UNTRAINED', 'TRAINED', 'ADVANCED', 'MASTER']

players = {
    'Nitram': 'testlog.txt',
    #'Ramisme': {},
    #'Voukras': {},
}

font = ImageFont.truetype(FONT_NAME, FONT_SIZE)
Path('out').mkdir(exist_ok=True)

def handlePlayer(idx:int, player:str, logpath:str):
    state_changes = {}
    logtext = Path(logpath).read_text()
    states = {}
    for line in logtext.splitlines():
        (timestamp, newstates) = checkLogLine(line, states)
        if not newstates or newstates == states:
            continue
        #print(timestamp, 'newstates == ', newstates)
        states = newstates
        state_changes[timestamp] = states
    print(state_changes)

    for (timestamp, state) in state_changes.items():
        MakePlayerImage(idx, player, timestamp, state)



def checkLogLine(line:str, states:dict):
    global skill_levels
    # skills/augs are mostly interchangeable here
    m = re.match(r'ClientMessage: (?P<skill>.+) upgraded to (?P<level>\w+) (?P<timestamp>[\d:]+)', line)
    if m:
        #print(m.groupdict())
        states = states.copy()
        timestamp = m.group('timestamp')
        level = skill_levels.index(m.group('level'))
        states[m.group('skill')] = level
        return (timestamp, states)
    
    m = re.match(r'DXRStats: (?P<timestamp>[\d:]+) (skills|augs): (?P<skills>.+)', line)
    if not m:
        return None
    #print(m.groupdict())
    levels = m.group('skills').split(', ')
    if not levels:
        return None
    states = states.copy()
    for namelvl in levels:
        (name, lvl) = namelvl.split(':')
        states[name] = lvl
        skills.add(name)
    timestamp = m.group('timestamp')
    return (timestamp, states)



def MakeLayout():
    global augs, skills
    img = Image.open('baselayout.png')
    gc = ImageDraw.Draw(img)
    text = '\n'.join(augs)
    if augs:
        text += '\n'
    text += '\n'.join(skills)
    DrawColumn(gc, 0, '', text)
    outname = Path('out') / 'layout.png'
    img.save(outname)


def MakePlayerImage(col, player, timestamp, state):
    #img = Image.open('layout.png')
    img = Image.new("RGBA", (IMAGE_WIDTH, IMAGE_HEIGHT))#, 'black')
    gc = ImageDraw.Draw(img)
    DrawPlayer(gc, col, player, state)
    outname = player + ' ' + timestamp.replace(':', '-') + '.png'
    outpath = Path('out') / outname
    img.save(outpath)

def DrawPlayer(gc, col, name, state):
    global augs, skills
    text = ''
    for aug in augs:
        lvl = state.get(aug, '')
        text += str(lvl) + '\n'
    for skill in skills:
        lvl = state.get(skill, 0)
        text += skill_levels[int(lvl)] + '\n'
    DrawColumn(gc, col, name, text)


def DrawColumn(gc, col, header, text):
    coords = (col * 100, 10)
    text = header + '\n' + text
    gc.text(coords, text, font=font)




idx = 1
for (k,v) in players.items():
    handlePlayer(idx, k, v)
    idx += 1
MakeLayout()

