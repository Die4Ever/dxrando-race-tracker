from pathlib import Path
import re
from drawing.skillsaugs import MakeLayout, MakePlayerImage
from drawing.bingo import timestampToInt, timeToString, DrawBingoBoard

skill_levels =   ['UNTRAINED', 'TRAINED', 'ADVANCED', 'MASTER']

players = {
    'Nitram': 'testlog.txt',
    'Ramisme': 'testlog.txt',
    'Voukras': 'testlog.txt',
}

def main():
    Path('out').mkdir(exist_ok=True)
    MakeLayout()
    idx = 0
    states = {}
    for (player, v) in players.items():
        states[player] = handlePlayer(idx, player, v)
        idx += 1
    DrawBingo(states)



def handlePlayer(idx:int, player:str, logpath:str):
    state_changes = {}
    logtext = Path(logpath).read_text()
    last_timestamp = None
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
        if state_changes.get(timestamp): # multiple lines for the same timestamp
            if states == state_changes[last_timestamp]:
                state_changes.pop(timestamp)
                continue
        else:
            last_timestamp = timestamp
        state_changes[timestamp] = states
    #print(state_changes)

    for (timestamp, state) in state_changes.items():
        MakePlayerImage(idx, player, timestamp, state)
    return state_changes


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


globalFlags = {} # HACK: easier than using lookback in parseAnyEntry, DXRFlags AnyEntry doesn't show timestamp
def parseFlags(line:str, states:dict):
    global globalFlags
    m = re.match(r'DXRFlags: INFO: AnyEntry .+, newgameplus_loops: (?P<newgameplus_loops>\d+)', line)
    if m:
        m.groupdict
        globalFlags = m.groupdict() #{'newgameplus_loops': int(m.group(1))}
    return None

def parseAnyEntry(line:str, states:dict):
    global globalFlags
    m = re.match(r'DXRStats:( INFO:)? PlayerAnyEntry (?P<timestamp>[\d:\.]+) skills/augs: (?P<skills>.+)', line)
    if not m:
        return None
    #print(line)
    #print(m.groupdict())
    timestamp = m.group('timestamp')
    skillslist = m.group('skills').split(', ')
    if not skillslist:
        return None
    states = globalFlags.copy() # start fresh, to delete no-longer existing augs
    for namelvl in skillslist:
        m = re.match(r'(.+):(\d)', namelvl)
        name = m.group(1)
        lvl = m.group(2)
        states[name] = int(lvl)
    return (timestamp, states)


bingoPos = r'(?P<pos>\d, \d)(?P<oopsMissingCast>\.0+)?'
def parseBingoState(line:str, states:dict):
    m = re.match(r'DXREvents:( INFO:)? Bingo state (?P<timestamp>[\d:\.]+): '+bingoPos+r', (?P<event>[^:,]+), (?P<progress>\d+), (?P<max>\d+), (?P<mask>[-\d]+), (?P<desc>.+)', line)
    if not m:
        return None
    #print(m.groupdict())
    states = states.copy()
    timestamp = m.group('timestamp')
    states['bingo-'+m.group('pos')] = dict(
        event=m.group('event'),
        progress=int(m.group('progress')),
        max=int(m.group('max')),
        mask=int(m.group('mask')),
        desc=m.group('desc'),
    )
    return (timestamp, states)


def parseBingoProgress(line:str, states:dict):
    m = re.match(r'PlayerDataItem: IncrementBingoProgress (?P<timestamp>[\d:\.]+) '+bingoPos+r' (?P<event>[^:,]+): (?P<progress>\d+) / (?P<max>\d+) (?P<mask>[-\d]+)', line)
    if not m:
        return None
    #print(m.groupdict())
    states = states.copy()
    timestamp = m.group('timestamp')
    slot = states['bingo-'+m.group('pos')].copy()
    slot['event'] = m.group('event')
    slot['progress'] = int(m.group('progress'))
    slot['max'] = int(m.group('max'))
    slot['mask'] = int(m.group('mask'))
    states['bingo-'+m.group('pos')] = slot
    return (timestamp, states)


def parseBingoFailure(line:str, states:dict):
    m = re.match(r'PlayerDataItem: MarkBingoAsFailed (?P<timestamp>[\d:\.]+) '+bingoPos+r' (?P<event>[^:,]+) (?P<mask>[-\d]+)', line)
    if not m:
        return None
    #print(m.groupdict())
    states = states.copy()
    timestamp = m.group('timestamp')
    key = 'bingo-'+m.group('pos')
    if key not in states:
        return None # bingo failures log right before bingo state updates
    slot = states[key].copy()
    slot['event'] = m.group('event')
    slot['mask'] = int(m.group('mask'))
    states[key] = slot
    return (timestamp, states)


def checkLogLine(line:str, states:dict):
    ret = parseFlags(line, states)
    if ret:
        return ret
    
    ret = parseUpgrade(line, states)
    if ret:
        return ret

    ret = parseAugInstall(line, states)
    if ret:
        return ret
    
    ret = parseAnyEntry(line, states)
    if ret:
        return ret
    
    ret = parseBingoState(line, states)
    if ret:
        return ret
    
    ret = parseBingoProgress(line, states)
    if ret:
        return ret
    
    ret = parseBingoFailure(line, states)
    if ret:
        return ret
    return None


def GetNextBoard(lastDrawnTime: float, states: dict, prev: dict):
    new = {}
    nextTime = 86400
    for (player, v) in states.items(): # check each player
        for (timestamp, state) in v.items(): # find the next state from any player
            time = timestampToInt(timestamp)
            if not state.get('bingo-0, 0'):
                continue
            if time > nextTime: # newer than something we just found in this function
                break
            if time > lastDrawnTime: # newer than previous draw
                if time < nextTime:
                    nextTime = time
                    new = {} # not a tie, so new dict
                new[player] = state
                break
    if not new:
        return (False, False)
    new = {**prev, **new} # new player states overwrite old ones, keep the previous states for players we didn't iterate on
    return (nextTime, new)


def DrawBingo(states: dict):
    print('DrawBingo')
    lastDrawnTime = -1
    board = {}
    while True:
        (lastDrawnTime, board) = GetNextBoard(lastDrawnTime, states, board)
        if not board:
            break
        DrawBingoBoard(lastDrawnTime, board)


if __name__ == "__main__":
    main()
