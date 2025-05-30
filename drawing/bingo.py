import re
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path

FONT_NAME = "CourierPrimeCode.ttf"

MAGIC_GREEN="#1e641e"
DEFAULT_DIMENSION = 1080
DEFAULT_FONT_SIZE = 28
DEFAULT_BORDER_SIZE = 16 # just used for padding, not line thickness

def DrawBingoBoard(time: float, board: dict):
    timestamp = timeToString(time)
    print('\n\nDrawBingoBoard', timestamp)
    bingoDrawer = BingoBoardDrawer(board, DEFAULT_DIMENSION, DEFAULT_FONT_SIZE)
    bingoDrawer.generateBoard()
    outname = 'bingo ' + timestamp.replace(':', '-') + '.png'
    outpath = Path('out') / outname
    bingoDrawer.saveBoard(outpath)

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
        self.font = ImageFont.truetype(FONT_NAME,fontsize)
        self.img = Image.new("RGB",(dimension,dimension))
        self.loadBingoEvents(eventJson)


    def loadBingoEvents(self,eventJson):
        for x in range(0,5):
            for y in range(0,5):
                self.board[x][y]={}
        
        for (player, board) in eventJson.items():
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

    def getTextBoxValue(self,x,y):
        coords = self.getSquareCoords(x,y)
        squareSize = self.dimension/5

        boxVal = (coords[0][0],coords[0][1],squareSize,squareSize)

        return boxVal

    def getSquareColour(self,x,y):
        return "black" # TODO: check each player
        square = self.board[x][y]
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

    def drawBingoText(self,boardX,boardY,border,image_draw, **kwargs):
        square = self.board[boardX][boardY]
        print('before', boardX, boardY, square)
        square = square[list(square.keys())[0]]
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
                **kwargs
                )
            y_offset += lineheight



    def generateBoard(self):
        #print("Generating board")
        draw = ImageDraw.Draw(self.img)
        for x in range(0,5):
            for y in range(0,5):
                draw.rectangle(self.getSquareCoords(x,y),fill=self.getSquareColour(x,y),outline="grey")
                self.drawBingoText(x,y,DEFAULT_BORDER_SIZE,draw)

    #For testing purposes
    def saveBoard(self, outpath):
        self.img=self.img.convert('RGB')
        self.img.save(outpath)

    #For testing purposes
    def showBoard(self):
        self.img.show()
