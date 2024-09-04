from PIL import Image, ImageDraw, ImageFont
#from io import BytesIO
from pathlib import Path
import json
import re

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

players = {
    'Nitram': 'testlog.txt',
    'Ramisme': 'testlog.txt',
    'Voukras': 'testlog.txt',
}

font = ImageFont.truetype(FONT_NAME, FONT_SIZE)

def main():
    Path('out').mkdir(exist_ok=True)
    MakeLayout()
    idx = 0
    for (k,v) in players.items():
        handlePlayer(idx, k, v)
        idx += 1



def handlePlayer(idx:int, player:str, logpath:str):
    state_changes = {}
    logtext = Path(logpath).read_text()
    states = {}
    for line in logtext.splitlines():
        ret = checkLogLine(line, states)
        if not ret:
            continue
        (timestamp, newstates) = ret
        if not newstates or newstates == states:
            continue
        #print('')
        #print('')
        #print(line)
        #print(timestamp, 'newstates == ', newstates)
        states = newstates
        state_changes[timestamp] = states
    print(state_changes)

    for (timestamp, state) in state_changes.items():
        MakePlayerImage(idx, player, timestamp, state)


def parseUpgrade(line:str, states:dict):
    global skill_levels
    # skills/augs are interchangeable here
    m = re.match(r'.*: ClientMessage: (?P<name>.+) upgraded to ((?P<levelname>\w+)|(level (?P<levelnum>\d))) \(from .* to .*\) (?P<timestamp>[\d:\.]+)', line)
    if not m:
        return None
    #print(m.groupdict())
    states = states.copy()
    timestamp = m.group('timestamp')
    levelname = m.group('levelname')
    levelnum = m.group('levelnum')
    if levelname:
        level = skill_levels.index(levelname)
    else:
        level = int(levelnum) - 1
    states[m.group('name')] = level
    return (timestamp, states)


def parseAugInstall(line:str, states:dict):
    # based on vanilla AugNowHaveAtLevel, we should improve that so we can get the aug strength
    m = re.match(r'.*: ClientMessage: Augmentation (?P<aug>.+) at level 1 (?P<timestamp>[\d:\.]+)', line)
    if not m:
        return None
    #print(m.groupdict())
    states = states.copy()
    timestamp = m.group('timestamp')
    states[m.group('aug')] = 0
    return (timestamp, states)


def parseAnyEntry(line:str, states:dict):
    m = re.match(r'DXRStats: PlayerAnyEntry (?P<timestamp>[\d:\.]+) skills/augs: (?P<skills>.+)', line)
    if not m:
        return None
    #print(line)
    #print(m.groupdict())
    timestamp = m.group('timestamp')
    skillslist = m.group('skills').split(', ')
    if not skillslist:
        return None
    states = dict() # states.copy() # start fresh, to delete no-longer existing augs
    for namelvl in skillslist:
        m = re.match(r'(.+):(\d)', namelvl)
        name = m.group(1)
        lvl = m.group(2)
        states[name] = int(lvl)
    return (timestamp, states)


def checkLogLine(line:str, states:dict):
    ret = parseUpgrade(line, states)
    if ret:
        return ret

    ret = parseAugInstall(line, states)
    if ret:
        return ret
    
    return parseAnyEntry(line, states)



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
    print(text)
    DrawColumn(gc, col, name, text, align='center')


def DrawColumn(gc:ImageDraw.ImageDraw, col, header, text, align='left'):
    coords = (START_X + col * COL_WIDTH, START_Y)
    print('DrawColumn', header)
    print(text)
    text = header + '\n' + text
    gc.text(coords, text, font=font, align=align, spacing=30)


if __name__ == "__main__":
    main()
