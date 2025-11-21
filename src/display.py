import pygame_gui
import random
import sys

from src.tools import *
from src.pieces import *
from src.ai import *

WINDOW_SIZE = (400, 400)
FPS = 60


class GameScreen:
    def __init__(self, windowSurface, playerSide="w", enemy=None):
        self.aiMoveDelay, self.aiTimer = None, 0
        self.windowSurface, self.turn = windowSurface, "w"
        self.playerSide = playerSide
        self.draggingPiece, self.dragStart, self.dragOffset = None, None, (0, 0)
        self.gameOver, self.gameOverMessage = False, None
        self.mouseOverBoard, self.hoveredTile = False, None
        self.board = Board()
        self.enemy = enemy
        print(self.enemy)
        self.boardImage = loadSvgSprite("images/boards/rect-8x8.svg")
        self.piecesSprites = {}
        self.availableMoves, self.dragAvailableMoves = [], []
        for piece in ["pawn-w", "rook-w", "knight-w", "bishop-w", "queen-w", "king-w", "pawn-b", "rook-b", "knight-b", "bishop-b", "queen-b", "king-b"]:
            self.piecesSprites[piece] = loadSvgSprite(f"images/pieces/{piece}.svg")
        boardWidth, boardHeight = self.boardImage.get_size()
        windowWidth, windowHeight = WINDOW_SIZE
        scale = min(windowWidth / boardWidth, windowHeight / boardHeight)
        newWidth, newHeight = int(boardWidth * scale), int(boardHeight * scale)
        self.boardImage = pygame.transform.smoothscale(self.boardImage, (newWidth, newHeight))
        self.boardRectangle = self.boardImage.get_rect(topleft=(0, 0))
        self.boardWidth, self.boardHeight = self.boardRectangle.width / 8, self.boardRectangle.height / 8

    def update(self, events, timeDelta):
        if self.gameOver:
            for event in events:
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    self.gameOver = False
                    return
            self.windowSurface.fill((0, 0, 0))
            self.windowSurface.blit(self.boardImage, self.boardRectangle)
            self.drawPieces()
            overlay = pygame.Surface(self.windowSurface.get_size(), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180))
            font = pygame.font.SysFont("Arial", 28, bold=True)
            textSurface = font.render(self.gameOverMessage, True, (255, 255, 255))
            textRectangle = textSurface.get_rect(center=(self.windowSurface.get_width() // 2, self.windowSurface.get_height() // 2))
            self.windowSurface.blit(overlay, (0, 0))
            self.windowSurface.blit(textSurface, textRectangle)
            pygame.display.update()
            return

        if self.enemy and self.turn == self.enemy.color:
            if self.aiMoveDelay is None:
                self.aiMoveDelay = random.uniform(0.5, 1.5)
                self.aiTimer = 0
            self.aiTimer += timeDelta
            if self.aiTimer >= self.aiMoveDelay:
                aiMove = self.enemy.chooseMove(self.board)
                self.aiMoveDelay = None  # reset for next turn
                self.aiTimer = 0
                if aiMove:
                    (startRow, startCol), (endRow, endCol) = aiMove
                    self.board.movePiece((startRow, startCol), (endRow, endCol))
                    self.turn = "b" if self.turn == "w" else "w"
                    if self.board.isCheckmate(self.turn):
                        self.showEndScreen(f"Checkmate! {'White' if self.turn == 'b' else 'Black'} wins!")
                    elif self.board.isStalemate(self.turn):
                        self.showEndScreen("Stalemate! It's a draw.")
            return

        for event in events:
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            # HOVERING LOGIC
            if event.type == pygame.MOUSEMOTION:
                mousePosition = event.pos
                if self.boardRectangle.collidepoint(mousePosition):
                    row, col = self.getTileFromPos(mousePosition)
                    if (row, col) != self.hoveredTile:
                        self.hoveredTile = (row, col)
                        if not self.draggingPiece:
                            self.onHoverTile(row, col)
                else:
                    if self.hoveredTile is not None:
                        self.hoveredTile = None
                        if not self.draggingPiece:
                            self.onLeaveBoard()

            # DRAGGING PIECE
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mousePosition = event.pos
                if self.boardRectangle.collidepoint(mousePosition):
                    row, col = self.getTileFromPos(mousePosition)
                    piece = self.board.grid[row][col]
                    if piece and piece.color == self.turn:
                        self.draggingPiece = piece
                        self.dragStart = (row, col)
                        self.dragAvailableMoves = self.board.getLegalMoves(piece)
                        self.availableMoves = list(self.dragAvailableMoves)
                        xMouse, yMouse = mousePosition
                        if self.playerSide == "b":
                            drawRow, drawCol = 7 - row, 7 - col
                        else:
                            drawRow, drawCol = row, col
                        xPiece = self.boardRectangle.left + drawCol * self.boardWidth + self.boardWidth / 2
                        yPiece = self.boardRectangle.top + drawRow * self.boardHeight + self.boardHeight / 2
                        self.dragOffset = (xPiece - xMouse, yPiece - yMouse)

            # DROPPING PIECE
            if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                if self.draggingPiece:
                    mousePosition = event.pos
                    if self.boardRectangle.collidepoint(mousePosition):
                        row, col = self.getTileFromPos(mousePosition)
                        if (row, col) in self.dragAvailableMoves:
                            self.board.movePiece(self.dragStart, (row, col))
                            self.turn = "b" if self.turn == "w" else "w"
                            if self.board.isCheckmate(self.turn):
                                self.showEndScreen(f"Checkmate! {'White' if self.turn == 'b' else 'Black'} wins!")
                            elif self.board.isStalemate(self.turn):
                                self.showEndScreen("Stalemate! It's a draw.")
                    self.draggingPiece = None
                    self.dragStart = None
                    self.dragOffset = (0, 0)
                    self.dragAvailableMoves = []
                    self.availableMoves = []

        # HOVER CLEANUP
        if not pygame.mouse.get_focused() and self.hoveredTile is not None:
            self.hoveredTile = None
            self.onLeaveBoard()

        # DRAWING BOARD AND PIECES
        self.windowSurface.fill((0, 0, 0))
        self.windowSurface.blit(self.boardImage, self.boardRectangle)
        if self.draggingPiece:
            self.highlightMoves(self.dragAvailableMoves)
        elif self.hoveredTile:
            self.highlightTile(self.hoveredTile)
        if self.availableMoves and not self.draggingPiece:
            self.highlightMoves(self.availableMoves)
        if self.board.isInCheck(self.turn):
            kingPosition = self.board.findKing(self.turn)
            if kingPosition:
                checkColor = (255, 0, 0, 100)
                surf = pygame.Surface((self.boardWidth, self.boardHeight), pygame.SRCALPHA)
                surf.fill(checkColor)
                r, c = kingPosition
                if self.playerSide == "b":
                    r, c = 7 - r, 7 - c
                x = self.boardRectangle.left + c * self.boardWidth
                y = self.boardRectangle.top + r * self.boardHeight
                self.windowSurface.blit(surf, (x, y))
        self.drawPieces(excludeDragging=True)
        if self.draggingPiece:
            self.drawDraggingPiece()
        if self.gameOver:
            overlay = pygame.Surface(self.windowSurface.get_size(), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180))
            font = pygame.font.SysFont("Arial", 28, bold=True)
            textSurface = font.render(self.gameOverMessage, True, (255, 255, 255))
            textRectangle = textSurface.get_rect(center=(self.windowSurface.get_width() // 2, self.windowSurface.get_height() // 2))
            self.windowSurface.blit(overlay, (0, 0))
            self.windowSurface.blit(textSurface, textRectangle)
        pygame.display.update()

    def drawPieces(self, excludeDragging=False):
        for r in range(8):
            for c in range(8):
                piece = self.board.grid[r][c]
                if not piece:
                    continue
                if excludeDragging and piece == self.draggingPiece:
                    continue
                key = f"{piece.__class__.__name__.lower()}-{piece.color}"
                sprite = self.piecesSprites.get(key)
                if not sprite:
                    continue
                sw, sh = sprite.get_size()
                scale = min(self.boardWidth / sw, self.boardHeight / sh)
                scaledSprite = pygame.transform.smoothscale(sprite, (int(sw * scale), int(sh * scale)))
                drawRow, drawColumn = (7 - r, 7 - c) if self.playerSide == "b" else (r, c)
                x = int(self.boardRectangle.left + drawColumn * self.boardWidth + (self.boardWidth - scaledSprite.get_width()) / 2)
                y = int(self.boardRectangle.top + drawRow * self.boardHeight + (self.boardHeight - scaledSprite.get_height()) / 2)
                self.windowSurface.blit(scaledSprite, (x, y))

    def drawDraggingPiece(self):
        xMouse, yMouse = pygame.mouse.get_pos()
        piece = self.draggingPiece
        if not piece:
            return
        key = f"{piece.__class__.__name__.lower()}-{piece.color}"
        sprite = self.piecesSprites.get(key)
        if not sprite:
            return
        sw, sh = sprite.get_size()
        scale = min(self.boardWidth / sw, self.boardHeight / sh)
        scaledSprite = pygame.transform.smoothscale(sprite, (int(sw * scale), int(sh * scale)))
        x = xMouse + self.dragOffset[0] - scaledSprite.get_width() / 2
        y = yMouse + self.dragOffset[1] - scaledSprite.get_height() / 2
        self.windowSurface.blit(scaledSprite, (x, y))

    def getTileFromPos(self, pos):
        x, y = pos
        xRelative = x - self.boardRectangle.left
        yRelative = y - self.boardRectangle.top
        col = int(xRelative // self.boardWidth)
        row = int(yRelative // self.boardHeight)
        if self.playerSide == "b":
            row, col = 7 - row, 7 - col
        return row, col

    def onHoverTile(self, row, col):
        piece = self.board.grid[row][col]
        if piece and piece.color == self.turn:
            self.availableMoves = self.board.getLegalMoves(piece)
        else:
            self.availableMoves = []

    def onLeaveBoard(self):
        self.availableMoves = []

    def highlightTile(self, tile):
        row, col = tile
        if self.playerSide == "b":
            row, col = 7 - row, 7 - col
        highlightColor = (255, 255, 0, 80)
        highlightSurface = pygame.Surface((self.boardWidth, self.boardHeight), pygame.SRCALPHA)
        highlightSurface.fill(highlightColor)
        x, y = self.boardRectangle.left + col * self.boardWidth, self.boardRectangle.top + row * self.boardHeight
        self.windowSurface.blit(highlightSurface, (x, y))

    def highlightMoves(self, moves):
        moveColor = (0, 100, 255, 80)
        for (row, col) in moves:
            if self.playerSide == "b":
                row, col = 7 - row, 7 - col
            highlightSurface = pygame.Surface((self.boardWidth, self.boardHeight), pygame.SRCALPHA)
            highlightSurface.fill(moveColor)
            x, y = self.boardRectangle.left + col * self.boardWidth, self.boardRectangle.top + row * self.boardHeight
            self.windowSurface.blit(highlightSurface, (x, y))

    def showEndScreen(self, message):
        self.gameOver = True
        self.gameOverMessage = message
        font = pygame.font.SysFont("Arial", 32, bold=True)
        textSurface = font.render(message, True, (255, 255, 255))
        textRectangle = textSurface.get_rect(center=(self.windowSurface.get_width() // 2, self.windowSurface.get_height() // 2))
        overlay = pygame.Surface(self.windowSurface.get_size(), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.windowSurface.blit(overlay, (0, 0))
        self.windowSurface.blit(textSurface, textRectangle)
        pygame.display.update()
        pygame.time.wait(4000)


class Game:
    COLOR_BG_MENU = (30, 30, 30)
    COLOR_BG_GAME = (0, 100, 200)
    COLOR_BG_OPTIONS = (30, 30, 30)

    MAIN_MENU = "menu"
    GAME = "game"
    OPTIONS = "options"

    AVAILABLE_AIS = {"None": None, "Random": RandomEnemy, "Evaluation": EvaluationEnemy, "MiniMax (Depth 2)": lambda color: MiniMaxEnemy(color, depth=2),
    "MiniMax (Depth 3)": lambda color: MiniMaxEnemy(color, depth=3),}

    def __init__(self):
        pygame.init()
        pygame.display.set_caption("ChessBoard")
        self.windowSurface = pygame.display.set_mode(WINDOW_SIZE)
        self.clock = pygame.time.Clock()
        self.mainMenuManager = pygame_gui.UIManager(WINDOW_SIZE)
        self.optionsMenuManager = pygame_gui.UIManager(WINDOW_SIZE)
        self.state = self.MAIN_MENU
        self.ongoingGame, self.playAsWhite = False, True
        self.gameScreen = None
        self.selectedAIName, self.selectedAIClass = "Random", RandomEnemy
        self.optionsMenuCreated = False
        self._createMainMenu()

    def _createMainMenu(self):
        buttonWidth, buttonHeight = 150, 50
        xCenter, yStart, spacing = (WINDOW_SIZE[0] - buttonWidth) // 2, 50, 70

        self.newGameButton = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((xCenter, yStart), (buttonWidth, buttonHeight)),
            text="New Game",
            manager=self.mainMenuManager,
        )
        self.continueButton = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((xCenter, yStart + spacing), (buttonWidth, buttonHeight)),
            text="Continue",
            manager=self.mainMenuManager,
        )
        self.sideToggleButton = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((xCenter, yStart + 2 * spacing), (buttonWidth, buttonHeight)),
            text="Play as: White",
            manager=self.mainMenuManager,
        )
        self.optionsButton = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((xCenter, yStart + 3 * spacing), (buttonWidth, buttonHeight)),
            text="Options",
            manager=self.mainMenuManager,
        )
        self.exitButton = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((xCenter, yStart + 4 * spacing), (buttonWidth, buttonHeight)),
            text="Exit",
            manager=self.mainMenuManager,
        )

    def mainMenuLoop(self, events, timeDelta):
        for event in events:
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame_gui.UI_BUTTON_PRESSED:
                if event.ui_element == self.newGameButton:
                    self.state, self.ongoingGame = self.GAME, True
                    self.gameScreen = GameScreen(self.windowSurface, "w" if self.playAsWhite else "b", enemy=self.selectedAIClass("b" if self.playAsWhite else "w") if self.selectedAIClass else None)
                    self.gameScreen.playerSide = "w" if self.playAsWhite else "b"
                    self.gameScreen.turn = "w"
                elif event.ui_element == self.sideToggleButton:
                    self.playAsWhite = not self.playAsWhite
                    new_text = "Play as: White" if self.playAsWhite else "Play as: Black"
                    self.sideToggleButton.set_text(new_text)
                elif event.ui_element == self.continueButton and self.ongoingGame:
                    self.state = self.GAME
                elif event.ui_element == self.optionsButton:
                    if not self.optionsMenuCreated:
                        self._createOptionsMenu()
                        self.optionsMenuCreated = True
                    self.state = self.OPTIONS
                elif event.ui_element == self.exitButton:
                    pygame.quit()
                    sys.exit()
            self.mainMenuManager.process_events(event)
        if not self.ongoingGame:
            self.continueButton.disable()
        else:
            self.continueButton.enable()
        self.mainMenuManager.update(timeDelta)
        self.windowSurface.fill(self.COLOR_BG_MENU)
        self.mainMenuManager.draw_ui(self.windowSurface)
        pygame.display.update()

    def optionLoop(self, events, timeDelta):
        for event in events:
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame_gui.UI_DROP_DOWN_MENU_CHANGED:
                if event.ui_element == self.aiDropdown:
                    self.selectedAIName = event.text
                    self.selectedAIClass = self.AVAILABLE_AIS[event.text]

            if event.type == pygame_gui.UI_BUTTON_PRESSED:
                if event.ui_element == self.backButton:
                    self.state = self.MAIN_MENU

            self.optionsMenuManager.process_events(event)

        self.optionsMenuManager.update(timeDelta)
        self.windowSurface.fill(self.COLOR_BG_OPTIONS)
        self.optionsMenuManager.draw_ui(self.windowSurface)
        pygame.display.update()

    def _createOptionsMenu(self):
        buttonWidth, buttonHeight = 200, 40
        xCenter = (WINDOW_SIZE[0] - buttonWidth) // 2
        yStart = 100
        self.aiLabel = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect((xCenter, yStart - 40), (buttonWidth, 30)),
            text="AI Type:",
            manager=self.optionsMenuManager ,
        )
        self.aiDropdown = pygame_gui.elements.UIDropDownMenu(
            options_list=list(self.AVAILABLE_AIS.keys()),
            starting_option=self.selectedAIName,
            relative_rect=pygame.Rect((xCenter, yStart), (buttonWidth, buttonHeight)),
            manager=self.optionsMenuManager ,
        )
        self.backButton = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((xCenter, yStart + 100), (buttonWidth, buttonHeight)),
            text="Back",
            manager=self.optionsMenuManager ,
        )

    def run(self):
        while True:
            timeDelta = self.clock.tick(FPS) / 1000.0
            events = pygame.event.get()
            if self.state == self.MAIN_MENU:
                self.mainMenuLoop(events, timeDelta)
            elif self.state == self.GAME:
                keys = pygame.key.get_pressed()
                if keys[pygame.K_ESCAPE]:
                    self.state = self.MAIN_MENU
                elif self.gameScreen:
                    self.gameScreen.update(events, timeDelta)
            elif self.state == self.OPTIONS:
                self.optionLoop(events, timeDelta)
