import re
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path

FONT_NAME = "CourierPrimeCode.ttf"

MAGIC_GREEN="#1e641e"
DEFAULT_DIMENSION = 1080
DEFAULT_FONT_SIZE = 28
DEFAULT_BORDER_SIZE = 16 # just used for padding, not line thickness

prevBoards = dict()
def DrawBingoBoard(time: float, board: dict):
    global prevBoards
    timestamp = timeToString(time)
    #print('\n\nDrawBingoBoard', timestamp)
    bingoDrawer = BingoBoardDrawer(board, DEFAULT_DIMENSION, DEFAULT_FONT_SIZE)
    bingoDrawer.generateBoards()
    for player, img in bingoDrawer.imgs.items():
        if img == prevBoards.get(player):
            continue
        prevBoards[player] = img
        outname = 'bingo ' + player + ' ' + timestamp.replace(':', '-') + '.png'
        outpath = Path('out') / outname
        bingoDrawer.saveBoard(player, outpath)


def timestampToInt(timestamp):
    m = re.match(r'(?P<hours>\d+):(?P<minutes>\d+):(?P<seconds>[\d.]+)', timestamp)
    seconds = int(m.group('hours'))*3600
    seconds += int(m.group('minutes'))*60
    seconds += float(m.group('seconds'))
    return seconds

def timeToString(time):
    hours = int(time // 3600)
    time -= hours * 3600
    minutes = int(time // 60)
    time -= minutes * 60
    seconds = time
    timestamp = f"{hours:02}:{minutes:02}:{seconds:04.1f}"
    return timestamp



class BingoBoardDrawer:
    def __init__(self,eventJson,dimension,fontsize):
        self.board = [[None]*5 for i in range(5)]
        self.dimension = dimension
        self.winners = []
        self.players = []
        self.font = ImageFont.truetype(FONT_NAME,fontsize)
        self.imgs = dict()
        self.loadBingoEvents(eventJson)


    def loadBingoEvents(self,eventJson):
        highest_ngplus_loops = 0
        for x in range(0,5):
            for y in range(0,5):
                self.board[x][y]={}
        
        for (player, board) in eventJson.items():
            self.players.append(player)
            ngplus_loops = int(board['newgameplus_loops'])
            #print('loadBingoEvents', player, ngplus_loops)
            if ngplus_loops > highest_ngplus_loops:
                highest_ngplus_loops = ngplus_loops
                self.winners = []
            if ngplus_loops == highest_ngplus_loops:
                self.winners.append(player)
            for x in range(0,5):
                for y in range(0,5):
                    bingoTag = "bingo-"+str(x)+", "+str(y)
                    if bingoTag in board:
                        self.board[x][y][player]=board[bingoTag]


    def getSquareCoords(self,x,y):
        squareSize = self.dimension/5

        lowerCorner = (x*squareSize,y*squareSize)
        upperCorner = ((x+1)*squareSize-1,(y+1)*squareSize-1)

        return [lowerCorner,upperCorner]


    def getSquareColour(self, player, x, y):
        square = self.board[x][y][player]
        if square["progress"]>=square["max"]:
            return MAGIC_GREEN
        else:
            return "black"
        

    def getLineSize(self,line):
        bbox=self.font.getbbox(line)
        #width = bbox[2]-bbox[0]
        #height = bbox[3]-bbox[1]
        width=bbox[2]
        height=bbox[3]
        #info("Line '"+line+"' is "+str(width)+" by "+str(height))
        return (width,height)

    def drawBingoText(self,boardX,boardY,border,image_draw,player, **kwargs):
        square = self.board[boardX][boardY]
        #square = list(square.values())[0]
        square = square.get(player)
        if not square:
            print('drawBingoText missing', player, 'in', boardX, boardY, repr(self.board))
            return
        coords = self.getSquareCoords(boardX,boardY)
        text = square["desc"]
        #if square["max"]>1: # TODO
        #    text = text + "\n("+str(square["progress"])+"/"+str(square["max"])+")"
        x = coords[0][0]+border
        y = coords[0][1]+border
        squareSize = self.dimension/5 - (2*border) 

        lines = text.split('\n')
        true_lines = []
        for line in lines:
            if self.getLineSize(line)[0] <= squareSize:
                true_lines.append(line)
            else:
                current_line = ''
                for word in line.split(' '):
                    if self.getLineSize(current_line + word)[0] <= squareSize:
                        if current_line!='':
                            current_line+=' '
                        current_line += word
                    else:
                        true_lines.append(current_line)
                        current_line = word
                true_lines.append(current_line)

        x_offset = y_offset = 0
        lineheight = self.getLineSize(true_lines[0])[1] * 1.3 # Give a margin of 0.3x the font height
        y = int(y + squareSize / 2)
        y_offset = - (len(true_lines) * lineheight) / 2

        for line in true_lines:
            linewidth = self.getLineSize(line)[0]
            x_offset = (squareSize - linewidth) / 2
            image_draw.text(
                (int(x + x_offset), int(y + y_offset)),
                line,
                font=self.font,
                fill="white",
                stroke_width=2,
                stroke_fill="black",
                **kwargs
                )
            y_offset += lineheight



    def drawSquare(self, x, y, draw):
        idx = -1
        for player in self.players:
            idx += 1
            if player not in self.winners:
                continue
            self.drawSquarePlayer(x, y, draw, player, idx)


    def drawSquarePlayer(self, x, y, draw, player, idx):
        colors = ["#1e642e", "#6e440e", "#1e546e"]
        color = colors[idx]
        square = self.board[x][y].get(player)
        if not square:
            print('drawSquare missing', player, 'in', x, y, repr(self.board[x][y]))
            print(repr(self.board))
            return
        (nw, se) = self.getSquareCoords(x,y) # NW and SE corners
        width = se[0] - nw[0]
        width /= len(self.players)
        height = se[1] - nw[1]
        progress = square['progress'] / square['max']
        height *= min(progress, 1)
        nw = (nw[0] + width * idx, se[1] - height)
        se = (nw[0] + width, se[1])
        coords = (nw, se)
        draw.rectangle(coords,fill=color)
        coords = self.getSquareCoords(x,y) # NW and SE corners
        draw.rectangle(coords,outline="grey")


    def generateBoards(self):
        #print("Generating board")
        idx = -1
        for player in self.players:
            idx += 1
            img = Image.new("RGBA",(self.dimension,self.dimension))
            draw = ImageDraw.Draw(img)
            for x in range(0,5):
                for y in range(0,5):
                    self.drawSquarePlayer(x, y, draw, player, idx)
                    self.drawBingoText(x,y,DEFAULT_BORDER_SIZE,draw, player)
            self.imgs[player] = img

    #For testing purposes
    def saveBoard(self, player, outpath):
        #self.img=self.img.convert('RGB')
        self.imgs[player].save(outpath)

    #For testing purposes
    #def showBoard(self):
    #    self.img.show()
