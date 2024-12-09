# Star Pusher (a Sokoban clone)
# By Al Sweigart al@inventwithpython.com
# http://inventwithpython.com/pygame
# Released under a "Simplified BSD" license

import random, sys, copy, os, pygame
from pygame.locals import *
from pygame import mixer


FPS = 30 # frames per second to update the screen
WINWIDTH = 800 # width of the program's window, in pixels
WINHEIGHT = 600 # height in pixels
HALF_WINWIDTH = int(WINWIDTH / 2)
HALF_WINHEIGHT = int(WINHEIGHT / 2)

# The total width and height of each tile in pixels.
TILEWIDTH = 50
TILEHEIGHT = 85
TILEFLOORHEIGHT = 40

CAM_MOVE_SPEED = 5 # how many pixels per frame the camera moves

# The percentage of outdoor tiles that have additional
# decoration on them, such as a tree or rock.
OUTSIDE_DECORATION_PCT = 20

BRIGHTBLUE = (  0, 170, 255)
DARKBLUE = (27, 120, 133)
WHITE      = (255, 255, 255)
BGCOLOR = DARKBLUE
TEXTCOLOR = WHITE

UP = 'up'
DOWN = 'down'
LEFT = 'left'
RIGHT = 'right'


def main():
    global FPSCLOCK, DISPLAYSURF, IMAGESDICT, TILEMAPPING, OUTSIDEDECOMAPPING, BASICFONT, PLAYERIMAGES, currentImage
    # Starting the mixer
    mixer.init()
    # Loading the song
    mixer.music.load("Blue's song.mp3")
    # Setting the volume
    mixer.music.set_volume(0.6)
    # Start playing the song
    mixer.music.play(loops=-1)
    # Pygame initialization and basic set up of the global variables.
    pygame.init()
    FPSCLOCK = pygame.time.Clock()

    # Because the Surface object stored in DISPLAYSURF was returned
    # from the pygame.display.set_mode() function, this is the
    # Surface object that is drawn to the actual computer screen
    # when pygame.display.update() is called.
    DISPLAYSURF = pygame.display.set_mode((WINWIDTH, WINHEIGHT))

    pygame.display.set_caption('Star Pusher')
    BASICFONT = pygame.font.Font('freesansbold.ttf', 18)

    # A global dict value that will contain all the Pygame
    # Surface objects returned by pygame.image.load().
    IMAGESDICT = {'uncovered goal': pygame.image.load('RedSelector.png'),
                  'covered goal': pygame.image.load('Selector.png'),
                  'star': pygame.image.load('Box.png'),
                  'grabstar': pygame.image.load('Grabbox.png'),
                  'corner': pygame.image.load('Wall_Block_Tall.png'),
                  'wall': pygame.image.load('Wall_Block_Tall.png'),
                  'inside floor': pygame.image.load('Plain_Block.png'),
                  'outside floor': pygame.image.load('Grass_Block.png'),
                  'title': pygame.image.load('star_title.png'),
                  'solved': pygame.image.load('star_solved.png'),
                  'princess': pygame.image.load('princess.png'),
                  'boy': pygame.image.load('boy.png'),
                  'catgirl': pygame.image.load('catgirl.png'),
                  'horngirl': pygame.image.load('horngirl.png'),
                  'pinkgirl': pygame.image.load('pinkgirl.png'),
                  'rock': pygame.image.load('Empty.png'),
                  'short tree': pygame.image.load('Empty.png'),
                  'tall tree': pygame.image.load('Empty.png'),
                  'ugly tree': pygame.image.load('Empty.png'),
                  'up': pygame.image.load('Blueup.png'),
                  'right': pygame.image.load('Blueright.png'),
                  'down': pygame.image.load('Bluedown.png'),
                  'left': pygame.image.load('Blueleft.png'),
                  'empty': pygame.image.load('Empty.png'),
                  'opendoor': pygame.image.load('OpenDoor.png'),
                  'closeddoor': pygame.image.load('ClosedDoor.png'),
                  'button': pygame.image.load('Button.png'),
                  'buttoff': pygame.image.load('Buttoff.png')
                  }

    # These dict values are global, and map the character that appears
    # in the level file to the Surface object it represents.
    TILEMAPPING = {'x': IMAGESDICT['corner'],
                   '#': IMAGESDICT['wall'],
                   'o': IMAGESDICT['inside floor'],
                   ' ': IMAGESDICT['empty']}
    OUTSIDEDECOMAPPING = {'1': IMAGESDICT['rock'],
                          '2': IMAGESDICT['short tree'],
                          '3': IMAGESDICT['tall tree'],
                          '4': IMAGESDICT['ugly tree']}

    # PLAYERIMAGES is a list of all possible characters the player can be.
    # currentImage is the index of the player's current player image.
    currentImage = 0
    PLAYERIMAGES = [IMAGESDICT['up'],
                    IMAGESDICT['left'],
                    IMAGESDICT['down'],
                    IMAGESDICT['right']]

    startScreen() # show the title screen until the user presses a key

    # Read in the levels from the text file. See the readLevelsFile() for
    # details on the format of this file and how to make your own levels.
    levels = readLevelsFile('starPusherLevels.txt')
    currentLevelIndex = 0

    # The main game loop. This loop runs a single level, when the user
    # finishes that level, the next/previous level is loaded.
    while True: # main game loop
        # Run the level to actually start playing the game:
        result = runLevel(levels, currentLevelIndex)

        if result in ('solved', 'next'):
            # Go to the next level.
            currentLevelIndex += 1
            if currentLevelIndex >= len(levels):
                # If there are no more levels, go back to the first one.
                currentLevelIndex = 0
        elif result == 'back':
            # Go to the previous level.
            currentLevelIndex -= 1
            if currentLevelIndex < 0:
                # If there are no previous levels, go to the last one.
                currentLevelIndex = len(levels)-1
        elif result == 'reset':
            pass # Do nothing. Loop re-calls runLevel() to reset the level


def runLevel(levels, levelNum):
    global currentImage
    levelObj = levels[levelNum]
    mapObj = decorateMap(levelObj['mapObj'], levelObj['startState']['player'])
    gameStateObj = copy.deepcopy(levelObj['startState'])
    mapNeedsRedraw = True # set to True to call drawMap()
    levelSurf = BASICFONT.render('Level %s of %s' % (levelNum + 1, len(levels)), 1, TEXTCOLOR)
    levelRect = levelSurf.get_rect()
    levelRect.bottomleft = (20, WINHEIGHT - 35)
    mapWidth = len(mapObj) * TILEWIDTH
    mapHeight = (len(mapObj[0]) - 1) * TILEFLOORHEIGHT + TILEHEIGHT
    MAX_CAM_X_PAN = abs(HALF_WINHEIGHT - int(mapHeight / 2)) + TILEWIDTH
    MAX_CAM_Y_PAN = abs(HALF_WINWIDTH - int(mapWidth / 2)) + TILEHEIGHT

    levelIsComplete = False
    # Track how much the camera has moved:
    cameraOffsetX = 0
    cameraOffsetY = 0
    # Track if the keys to move the camera are being held down:
    cameraUp = False
    cameraDown = False
    cameraLeft = False
    cameraRight = False

    while True: # main game loop
        # Reset these variables:
        playerTurn = None
        playerMoveTo = -1
        keyPressed = False
        Grab = False

        for event in pygame.event.get(): # event handling loop
            if event.type == QUIT:
                # Player clicked the "X" at the corner of the window.
                terminate()

            elif event.type == KEYDOWN:
                # Handle key presses
                keyPressed = True
                if event.key == K_LEFT:
                    playerMoveTo = 1
                elif event.key == K_RIGHT:
                    playerMoveTo = 3
                elif event.key == K_UP:
                    playerMoveTo = 0
                elif event.key == K_DOWN:
                    playerMoveTo = 2

                # Set the camera move mode.
                elif event.key == K_q:
                    cameraLeft = True
                elif event.key == K_d:
                    cameraRight = True
                elif event.key == K_z:
                    cameraUp = True
                elif event.key == K_s:
                    cameraDown = True

                elif event.key == K_w:
                    playerTurn = LEFT    
                elif event.key == K_x:
                    playerTurn = RIGHT    

                elif event.key == K_n:
                    return 'next'
                elif event.key == K_b:
                    return 'back'

                elif event.key == K_SPACE:
                    Grab = True

                elif event.key == K_ESCAPE:
                    terminate() # Esc key quits.
                elif event.key == K_BACKSPACE:
                    return 'reset' # Reset the level.
                

            elif event.type == KEYUP:
                # Unset the camera move mode.
                if event.key == K_q:
                    cameraLeft = False
                elif event.key == K_d:
                    cameraRight = False
                elif event.key == K_z:
                    cameraUp = False
                elif event.key == K_s:
                    cameraDown = False

        if playerMoveTo != -1 and not levelIsComplete:
            # If the player pushed a key to move, make the move
            # (if possible) and push any stars that are pushable.
            moved = makeMove(mapObj, gameStateObj, playerMoveTo)

            if moved:
                # increment the step counter.
                gameStateObj['stepCounter'] += 1
                print(gameStateObj['stepCounter'] )
                mapNeedsRedraw = True

            if isLevelFinished(levelObj, gameStateObj):
                # level is solved, we should show the "Solved!" image.
                levelIsComplete = True
                keyPressed = False

        if playerTurn != None and not levelIsComplete:
            # If the player pushed a key to turn, make the turn
            # (if possible) and push any stars that are pushable.
            turned = makeTurn(mapObj, gameStateObj, playerTurn)

            if turned:
                mapNeedsRedraw = True

            if isLevelFinished(levelObj, gameStateObj):
                # level is solved, we should show the "Solved!" image.
                levelIsComplete = True
                keyPressed = False

        if Grab and not levelIsComplete:
            # If the player pushed a key to grab, grab
            # (if possible)
            grabbed = makeGrab(mapObj,gameStateObj)

            if grabbed:
                mapNeedsRedraw = True

            if isLevelFinished(levelObj, gameStateObj):
                # level is solved, we should show the "Solved!" image.
                levelIsComplete = True
                keyPressed = False

        DISPLAYSURF.fill(BGCOLOR)

        if mapNeedsRedraw:
            mapSurf = drawMap(mapObj, gameStateObj, levelObj['goals'])
            mapNeedsRedraw = False

        if cameraUp and cameraOffsetY < MAX_CAM_X_PAN:
            cameraOffsetY += CAM_MOVE_SPEED
        elif cameraDown and cameraOffsetY > -MAX_CAM_X_PAN:
            cameraOffsetY -= CAM_MOVE_SPEED
        if cameraLeft and cameraOffsetX < MAX_CAM_Y_PAN:
            cameraOffsetX += CAM_MOVE_SPEED
        elif cameraRight and cameraOffsetX > -MAX_CAM_Y_PAN:
            cameraOffsetX -= CAM_MOVE_SPEED

        # Adjust mapSurf's Rect object based on the camera offset.
        mapSurfRect = mapSurf.get_rect()
        mapSurfRect.center = (HALF_WINWIDTH + cameraOffsetX, HALF_WINHEIGHT + cameraOffsetY)

        # Draw mapSurf to the DISPLAYSURF Surface object.
        DISPLAYSURF.blit(mapSurf, mapSurfRect)

        DISPLAYSURF.blit(levelSurf, levelRect)
        stepSurf = BASICFONT.render('Steps: %s' % (gameStateObj['stepCounter']), 1, TEXTCOLOR)
        stepRect = stepSurf.get_rect()
        stepRect.bottomleft = (20, WINHEIGHT - 10)
        DISPLAYSURF.blit(stepSurf, stepRect)

        if levelIsComplete:
            # is solved, show the "Solved!" image until the player
            # has pressed a key.
            solvedRect = IMAGESDICT['solved'].get_rect()
            solvedRect.center = (HALF_WINWIDTH, HALF_WINHEIGHT)
            DISPLAYSURF.blit(IMAGESDICT['solved'], solvedRect)

            if keyPressed:
                return 'solved'

        pygame.display.update() # draw DISPLAYSURF to the screen.
        FPSCLOCK.tick()


def isWall(mapObj, x, y):
    """Returns True if the (x, y) position on
    the map is a wall, otherwise return False."""

    if x < 0 or x >= len(mapObj) or y < 0 or y >= len(mapObj[x]):
        return False # x and y aren't actually on the map.
    elif mapObj[x][y] in ('#', 'x'):
        return True # wall is blocking

    return False


def decorateMap(mapObj, startxy):
    """Makes a copy of the given map object and modifies it.
    Here is what is done to it:
        * Walls that are corners are turned into corner pieces.
        * The outside/inside floor tile distinction is made.
        * Tree/rock decorations are randomly added to the outside tiles.

    Returns the decorated map object."""

    startx, starty = startxy # Syntactic sugar

    # Copy the map object so we don't modify the original passed
    mapObjCopy = copy.deepcopy(mapObj)

    # Remove the non-wall characters from the map data
    for x in range(len(mapObjCopy)):
        for y in range(len(mapObjCopy[0])):
            if mapObjCopy[x][y] in ('$', '.', '@', '+', '*'):
                mapObjCopy[x][y] = ' '

    # Flood fill to determine inside/outside floor tiles.
    floodFill(mapObjCopy, startx, starty, ' ',  'o')

    # Convert the adjoined walls into corner tiles.
    for x in range(len(mapObjCopy)):
        for y in range(len(mapObjCopy[0])):

            if mapObjCopy[x][y] == '#':
                if (isWall(mapObjCopy, x, y-1) and isWall(mapObjCopy, x+1, y)) or \
                   (isWall(mapObjCopy, x+1, y) and isWall(mapObjCopy, x, y+1)) or \
                   (isWall(mapObjCopy, x, y+1) and isWall(mapObjCopy, x-1, y)) or \
                   (isWall(mapObjCopy, x-1, y) and isWall(mapObjCopy, x, y-1)):
                    mapObjCopy[x][y] = 'x'

            elif mapObjCopy[x][y] == ' ' and random.randint(0, 99) < OUTSIDE_DECORATION_PCT:
                mapObjCopy[x][y] = random.choice(list(OUTSIDEDECOMAPPING.keys()))

    return mapObjCopy


def isBlocked(mapObj, gameStateObj, x, y):
    """Returns True if the (x, y) position on the map is
    blocked by a wall or star or closed door, otherwise return False."""

    if (x, y) in gameStateObj['doors'] and not(isDoorOpen(gameStateObj,x, y)):
        return True

    elif isWall(mapObj, x, y):
        return True

    elif x < 0 or x >= len(mapObj) or y < 0 or y >= len(mapObj[x]):
        return True # x and y aren't actually on the map.

    elif (x, y) in gameStateObj['stars']:
        return True # a star is blocking

    return False

def makeGrab(mapObj, gameStateObj):
    """Checks if there is a box/star in the direction the player
    is facing. If so that box/star will be replaced by a grabbed box"""
    # Make sure the player can grab a box/star
    playerx, playery = gameStateObj['player']

    # This variable is "syntactic sugar". Typing "stars" is more
    # readable than typing "gameStateObj['stars']" in our code.
    stars = gameStateObj['stars']
    grabStar = gameStateObj['grabstar']
    direction = gameStateObj['playerdirection']
    # The code for handling each of the directions is so similar aside
    # from adding or subtracting 1 to the x/y coordinates. We can
    # simplify it by using the xOffset and yOffset variables.
    if  direction == 0:
        xOffset = 0
        yOffset = -1
    elif direction == 3:
        xOffset = 1
        yOffset = 0
    elif direction == 2:
        xOffset = 0
        yOffset = 1
    elif direction == 1:
        xOffset = -1
        yOffset = 0

    #check that there's a box/star
    if (playerx + xOffset, playery + yOffset) in stars:
        stars.remove((playerx + xOffset, playery + yOffset))
        grabStar.append((playerx + xOffset, playery + yOffset))
        return True
    elif (playerx + xOffset, playery + yOffset) in grabStar:
        grabStar.remove((playerx + xOffset, playery + yOffset))
        stars.append((playerx + xOffset, playery + yOffset))
        return True
    else:
        return False


def makeTurn(mapObj, gameStateObj, playerTurn):
    """"""
    plr_dir = gameStateObj['playerdirection']
    stars = gameStateObj['stars']

    if playerTurn == LEFT:
        turnamount = 1
    elif playerTurn == RIGHT:
        turnamount = -1
    if (plr_dir + turnamount == 4) or (plr_dir + turnamount == -1):
        turnamount = turnamount*(-3)

    if gameStateObj['grabstar'] != []:
        turnstar1 = moveStar(mapObj, gameStateObj, plr_dir + turnamount)
        if not turnstar1 :
            gameStateObj['grabstaroffset'] = [(0,0)]
            gameStateObj['otherstar'] = []
            return False
        if playerTurn == LEFT:
            turnamount2 = 1
        elif playerTurn == RIGHT:
            turnamount2 = -1
        if (plr_dir + turnamount2 +turnamount == 4) or (plr_dir + turnamount2+ turnamount== -1):
            turnamount2 = turnamount2 * (-3)
        turnstar2 = moveStar(mapObj, gameStateObj, plr_dir + turnamount2 + turnamount)
        if not turnstar2 :
            gameStateObj['grabstaroffset'] = [(0,0)]
            gameStateObj['otherstar'] = []
            return False
        gameStateObj['grabstar'] = [(gameStateObj['grabstar'][0][0]+gameStateObj['grabstaroffset'][0][0],gameStateObj['grabstar'][0][1]+gameStateObj['grabstaroffset'][0][1])]
        gameStateObj['grabstaroffset'] = [(0,0)]
        if gameStateObj['otherstar'] != []:
            for i in range(len(gameStateObj['otherstar'])) :
                stars[gameStateObj['otherstar'][i][0]] = gameStateObj['otherstar'][i][1]
        gameStateObj['otherstar'] = []

    gameStateObj['playerdirection'] = plr_dir + turnamount
    return True

def moveStar(mapObj, gameStateObj, playerMoveTo):
    """Given a map and game state object, see if it is possible for the
        player to make the given move. If it is, then change the player's
        position (and the position of any pushed star). If not, do nothing.

        Returns True if the player moved, otherwise False."""

    # Make sure the player can move in the direction they want.
    [(starx, stary)] = [(gameStateObj['grabstar'][0][0]+gameStateObj['grabstaroffset'][0][0],gameStateObj['grabstar'][0][1]+gameStateObj['grabstaroffset'][0][1])]

    # This variable is "syntactic sugar". Typing "stars" is more
    # readable than typing "gameStateObj['stars']" in our code.
    stars = gameStateObj['stars']
    pushstars= gameStateObj['otherstar']

    # The code for handling each of the directions is so similar aside
    # from adding or subtracting 1 to the x/y coordinates. We can
    # simplify it by using the xOffset and yOffset variables.
    if playerMoveTo == 0:
        xOffset = 0
        yOffset = -1
    elif playerMoveTo == 3:
        xOffset = 1
        yOffset = 0
    elif playerMoveTo == 2:
        xOffset = 0
        yOffset = 1
    elif playerMoveTo == 1:
        xOffset = -1
        yOffset = 0

    # See if the player can move in that direction.
    if isWall(mapObj, starx + xOffset, stary + yOffset):
        return False
    if (starx + xOffset, stary + yOffset) in gameStateObj['doors'] and not(isDoorOpen(gameStateObj,starx + xOffset, stary + yOffset)):
        return False
    else:
        if (starx + xOffset, stary + yOffset) in stars:
            # There is a star in the way, see if the star can push it.
            if not isBlocked(mapObj, gameStateObj, starx + (xOffset * 2), stary + (yOffset * 2)):
                # Move the star.
                pushstars.append( (stars.index((starx + xOffset, stary + yOffset)),(starx + xOffset*2, stary + yOffset*2)) )
            else:
                return False
        # Move the player upwards.
        gameStateObj['grabstaroffset'] = [(gameStateObj['grabstaroffset'][0][0]+xOffset, gameStateObj['grabstaroffset'][0][1]+yOffset)]
        return True

def makeMove(mapObj, gameStateObj, playerMoveTo):
    """Given a map and game state object, see if it is possible for the
    player to make the given move. If it is, then change the player's
    position (and the position of any pushed star). If not, do nothing.

    In addition, check if there is a grabstar, and move it in the same direction

    Returns True if the player moved, otherwise False."""

    # Make sure the player can move in the direction they want.
    playerx, playery = gameStateObj['player']


    # This variable is "syntactic sugar". Typing "stars" is more
    # readable than typing "gameStateObj['stars']" in our code.
    stars = gameStateObj['stars']

    if gameStateObj['grabstar'] != []:
        starwalk = moveStar(mapObj, gameStateObj, playerMoveTo)
        if not starwalk:
            return False


    # The code for handling each of the directions is so similar aside
    # from adding or subtracting 1 to the x/y coordinates. We can
    # simplify it by using the xOffset and yOffset variables.
    if playerMoveTo == 0:
        xOffset = 0
        yOffset = -1
    elif playerMoveTo == 3:
        xOffset = 1
        yOffset = 0
    elif playerMoveTo == 2:
        xOffset = 0
        yOffset = 1
    elif playerMoveTo == 1:
        xOffset = -1
        yOffset = 0

    # See if the player can move in that direction.
    if isWall(mapObj, playerx + xOffset, playery + yOffset):
        gameStateObj['grabstaroffset'] = [(0,0)]
        gameStateObj['otherstar'] = []
        return False
    elif (playerx + xOffset, playery + yOffset) in gameStateObj['doors'] and not(isDoorOpen(gameStateObj,playerx + xOffset, playery + yOffset)):
        gameStateObj['grabstaroffset'] = [(0, 0)]
        gameStateObj['otherstar'] = []
        return False
    else:
        if (playerx + xOffset, playery + yOffset) in stars:
            # There is a star in the way, see if the player can push it.
            if not isBlocked(mapObj, gameStateObj, playerx + (xOffset*2), playery + (yOffset*2)):
                # Move the star.
                ind = stars.index((playerx + xOffset, playery + yOffset))
                stars[ind] = (stars[ind][0] + xOffset, stars[ind][1] + yOffset)
            else:
                gameStateObj['grabstaroffset'] = [(0,0)]
                gameStateObj['otherstar'] = []
                return False
        # Move the player upwards.
        if gameStateObj['grabstar'] != []:
            gameStateObj['grabstar'] = [(gameStateObj['grabstar'][0][0]+gameStateObj['grabstaroffset'][0][0],gameStateObj['grabstar'][0][1]+gameStateObj['grabstaroffset'][0][1])]
        gameStateObj['grabstaroffset'] = [(0,0)]
        gameStateObj['player'] = (playerx + xOffset, playery + yOffset)
        if gameStateObj['otherstar'] != []:
            for i in range(len(gameStateObj['otherstar'])):
                stars[gameStateObj['otherstar'][i][0]]= gameStateObj['otherstar'][i][1]
        gameStateObj['otherstar'] = []
        return True


def startScreen():
    """Display the start screen (which has the title and instructions)
    until the player presses a key. Returns None."""

    # Position the title image.
    titleRect = IMAGESDICT['title'].get_rect()
    topCoord = 50 # topCoord tracks where to position the top of the text
    titleRect.top = topCoord
    titleRect.centerx = HALF_WINWIDTH
    topCoord += titleRect.height

    # Unfortunately, Pygame's font & text system only shows one line at
    # a time, so we can't use strings with \n newline characters in them.
    # So we will use a list with each line in it.
    instructionText = ['Poussez et tirez les boites sur les tuiles colorées!',
                       'Utilisez les flèches pour bouger, et ZQSD pour maneuvrer la caméra.',
                       'Appuyez sur ESPACE devant une boite pour la saisir, et W et X pour tourner.',
                       'Backspace pour réinitialiser le niveau et Esc pour le quitter.',
                       'N pour sauter le niveau et B pour retourner au niveau précedent.']

    # Start with drawing a blank color to the entire window:
    DISPLAYSURF.fill(BGCOLOR)

    # Draw the title image to the window:
    DISPLAYSURF.blit(IMAGESDICT['title'], titleRect)

    # Position and draw the text.
    for i in range(len(instructionText)):
        instSurf = BASICFONT.render(instructionText[i], 1, TEXTCOLOR)
        instRect = instSurf.get_rect()
        topCoord += 10 # 10 pixels will go in between each line of text.
        instRect.top = topCoord
        instRect.centerx = HALF_WINWIDTH
        topCoord += instRect.height # Adjust for the height of the line.
        DISPLAYSURF.blit(instSurf, instRect)

    while True: # Main loop for the start screen.
        for event in pygame.event.get():
            if event.type == QUIT:
                terminate()
            elif event.type == KEYDOWN:
                if event.key == K_ESCAPE:
                    terminate()
                return # user has pressed a key, so return.

        # Display the DISPLAYSURF contents to the actual screen.
        pygame.display.update()
        FPSCLOCK.tick()


def readLevelsFile(filename):
    assert os.path.exists(filename), 'Cannot find the level file: %s' % (filename)
    mapFile = open(filename, 'r')
    # Each level must end with a blank line
    content = mapFile.readlines() + ['\r\n']
    mapFile.close()

    levels = [] # Will contain a list of level objects.
    levelNum = 0
    mapTextLines = [] # contains the lines for a single level's map.
    mapObj = [] # the map object made from the data in mapTextLines
    for lineNum in range(len(content)):
        # Process each line that was in the level file.
        line = content[lineNum].rstrip('\r\n')

        if ';' in line:
            # Ignore the ; lines, they're comments in the level file.
            line = line[:line.find(';')]

        if line != '':
            # This line is part of the map.
            mapTextLines.append(line)
        elif line == '' and len(mapTextLines) > 0:
            # A blank line indicates the end of a level's map in the file.
            # Convert the text in mapTextLines into a level object.

            # Find the longest row in the map.
            maxWidth = -1
            for i in range(len(mapTextLines)):
                if len(mapTextLines[i]) > maxWidth:
                    maxWidth = len(mapTextLines[i])
            # Add spaces to the ends of the shorter rows. This
            # ensures the map will be rectangular.
            for i in range(len(mapTextLines)):
                mapTextLines[i] += ' ' * (maxWidth - len(mapTextLines[i]))

            # Convert mapTextLines to a map object.
            for x in range(len(mapTextLines[0])):
                mapObj.append([])
            for y in range(len(mapTextLines)):
                for x in range(maxWidth):
                    mapObj[x].append(mapTextLines[y][x])

            # Loop through the spaces in the map and find the @, ., and $
            # characters for the starting game state.
            startx = None # The x and y for the player's starting position
            starty = None
            goals = [] # list of (x, y) tuples for each goal.
            buttons = []
            doors = []
            stars = [] # list of (x, y) for each star's starting position.
            grabStar = []
            for x in range(maxWidth):
                for y in range(len(mapObj[x])):
                    if mapObj[x][y] in ('d'):
                        # 'd' is door
                        doors.append((x,y))
                    if mapObj[x][y] in ('b', 'p', 's'):
                        # 'b' is button, 'p' is player & button, 's' is star & button
                        buttons.append((x,y))
                    if mapObj[x][y] in ('@', '+','p'):
                        # '@' is player, '+' is player & goal
                        startx = x
                        starty = y
                    if mapObj[x][y] in ('.', '+', '*'):
                        # '.' is goal, '*' is star & goal
                        goals.append((x, y))
                    if mapObj[x][y] in ('$', '*', 's'):
                        # '$' is star
                        stars.append((x, y))

            # Basic level design sanity checks:
            assert startx != None and starty != None, 'Level %s (around line %s) in %s is missing a "@" or "+" to mark the start point.' % (levelNum+1, lineNum, filename)
            assert len(goals) > 0, 'Level %s (around line %s) in %s must have at least one goal.' % (levelNum+1, lineNum, filename)
            assert len(stars) >= len(goals), 'Level %s (around line %s) in %s is impossible to solve. It has %s goals but only %s stars.' % (levelNum+1, lineNum, filename, len(goals), len(stars))

            # Create level object and starting game state object.
            gameStateObj = {'player': (startx, starty),
                            'stepCounter': 0,
                            'stars': stars,
                            'playerdirection': 2,
                            'grabstar': grabStar,
                            'doors': doors,
                            'buttons': buttons,
                            'grabstaroffset': [(0,0)],
                            'buttonPressed?': False,
                            'otherstar': []}
            levelObj = {'width': maxWidth,
                        'height': len(mapObj),
                        'mapObj': mapObj,
                        'goals': goals,
                        'startState': gameStateObj}

            levels.append(levelObj)

            # Reset the variables for reading the next map.
            mapTextLines = []
            mapObj = []
            gameStateObj = {}
            levelNum += 1
    return levels


def floodFill(mapObj, x, y, oldCharacter, newCharacter):
    """Changes any values matching oldCharacter on the map object to
    newCharacter at the (x, y) position, and does the same for the
    positions to the left, right, down, and up of (x, y), recursively."""

    # In this game, the flood fill algorithm creates the inside/outside
    # floor distinction. This is a "recursive" function.
    # For more info on the Flood Fill algorithm, see:
    #   http://en.wikipedia.org/wiki/Flood_fill
    if mapObj[x][y] == oldCharacter:
        mapObj[x][y] = newCharacter

    if x < len(mapObj) - 1 and (mapObj[x+1][y] == oldCharacter or mapObj[x+1][y] == 'd'):
        floodFill(mapObj, x+1, y, oldCharacter, newCharacter) # call right
    if x > 0 and (mapObj[x-1][y] == oldCharacter or mapObj[x-1][y] == 'd'):
        floodFill(mapObj, x-1, y, oldCharacter, newCharacter) # call left
    if y < len(mapObj[x]) - 1 and (mapObj[x][y+1] == oldCharacter or mapObj[x][y+1] == 'd'):
        floodFill(mapObj, x, y+1, oldCharacter, newCharacter) # call down
    if y > 0 and (mapObj[x][y-1] == oldCharacter or mapObj[x][y-1] == 'd'):
        floodFill(mapObj, x, y-1, oldCharacter, newCharacter) # call up


def drawMap(mapObj, gameStateObj, goals):
    """Draws the map to a Surface object, including the player and
    stars. This function does not call pygame.display.update(), nor
    does it draw the "Level" and "Steps" text in the corner."""

    # mapSurf will be the single Surface object that the tiles are drawn
    # on, so that it is easy to position the entire map on the DISPLAYSURF
    # Surface object. First, the width and height must be calculated.
    mapSurfWidth = len(mapObj) * TILEWIDTH
    mapSurfHeight = (len(mapObj[0]) - 1) * TILEFLOORHEIGHT + TILEHEIGHT
    mapSurf = pygame.Surface((mapSurfWidth, mapSurfHeight))
    mapSurf.fill(BGCOLOR) # start with a blank color on the surface.

    # Draw the tile sprites onto this surface.
    for x in range(len(mapObj)):
        for y in range(len(mapObj[x])):
            spaceRect = pygame.Rect((x * TILEWIDTH, y * TILEFLOORHEIGHT, TILEWIDTH, TILEHEIGHT))
            if mapObj[x][y] in TILEMAPPING:
                baseTile = TILEMAPPING[mapObj[x][y]]
            elif mapObj[x][y] in OUTSIDEDECOMAPPING:
                baseTile = TILEMAPPING[' ']

            # First draw the base ground/wall tile.
            mapSurf.blit(baseTile, spaceRect)

            if mapObj[x][y] in OUTSIDEDECOMAPPING:
                # Draw any tree/rock decorations that are on this tile.
                mapSurf.blit(OUTSIDEDECOMAPPING[mapObj[x][y]], spaceRect)
            elif (x, y) in gameStateObj['stars']:
                if (x, y) in goals:
                    # A goal AND star are on this space, draw goal first.
                    mapSurf.blit(IMAGESDICT['covered goal'], spaceRect)
                elif (x,y) in gameStateObj['buttons']:
                    mapSurf.blit(IMAGESDICT['button'], spaceRect)
                elif (x,y) in gameStateObj['doors']:
                    mapSurf.blit(IMAGESDICT['opendoor'], spaceRect)
                # Then draw the star sprite.
                mapSurf.blit(IMAGESDICT['star'], spaceRect)
            elif (x, y) in gameStateObj['grabstar']:
                if (x, y) in goals:
                    # A goal AND star are on this space, draw goal first.
                    mapSurf.blit(IMAGESDICT['covered goal'], spaceRect)
                elif (x,y) in gameStateObj['buttons']:
                    mapSurf.blit(IMAGESDICT['button'], spaceRect)
                elif (x,y) in gameStateObj['doors']:
                    mapSurf.blit(IMAGESDICT['opendoor'], spaceRect)
                # Then draw the star sprite.
                mapSurf.blit(IMAGESDICT['grabstar'], spaceRect)
            elif (x,y) in gameStateObj['doors']:
                if isDoorOpen(gameStateObj,x,y):
                    mapSurf.blit(IMAGESDICT['opendoor'], spaceRect)
                else:
                    mapSurf.blit(IMAGESDICT['closeddoor'], spaceRect)
            elif (x,y) in gameStateObj['buttons']:
                mapSurf.blit(IMAGESDICT['buttoff'], spaceRect)
            elif (x, y) in goals:
                # Draw a goal without a star on it.
                mapSurf.blit(IMAGESDICT['uncovered goal'], spaceRect)


            # Last draw the player on the board.
            if (x, y) == gameStateObj['player']:
                if (x,y) in gameStateObj['buttons']:
                    mapSurf.blit(IMAGESDICT['button'], spaceRect)
                elif (x,y) in gameStateObj['doors']:
                    mapSurf.blit(IMAGESDICT['opendoor'], spaceRect)
                # Note: The value "currentImage" refers
                # to a key in "PLAYERIMAGES" which has the
                # specific player image we want to show.
                varAnything = gameStateObj['playerdirection']
                print(varAnything)
                mapSurf.blit(PLAYERIMAGES[gameStateObj['playerdirection']], spaceRect)

    return mapSurf


def isLevelFinished(levelObj, gameStateObj):
    """Returns True if all the goals have stars in them."""
    for goal in levelObj['goals']:
        if (goal not in gameStateObj['stars']) and (goal not in gameStateObj['grabstar']):
            # Found a space with a goal but no star on it.
            return False
    return True

def isDoorOpen (gameStateObj,x,y):
    """Returns True if all the goals have stars in them."""
    for button in gameStateObj['buttons']:
        if (button in gameStateObj['stars']) or (button in gameStateObj['grabstar']) or (button == gameStateObj['player']):
            # Found a space with a button but no star or player on it.
            return True
    if ((x,y) in gameStateObj['stars']) or ((x,y) in gameStateObj['grabstar']) or ((x,y) == gameStateObj['player']):
            return True
    return False


def terminate():
    pygame.quit()
    sys.exit()


if __name__ == '__main__':
    main()