import random

from src.pieces import *


class RandomEnemy:
    def __init__(self, color):
        self.color = color

    def chooseMove(self, board):
        allMoves = board.getAllLegalMoves(self.color)
        if not allMoves:
            return None
        return random.choice(allMoves)


class ScoreEnemy:
    def __init__(self, color):
        self.color = color

    @staticmethod
    def evaluateBoard(board, color):
        pieces = {'pawn': 10, 'knight': 30, 'bishop': 30, 'rook': 50, 'queen': 90, 'king': 900}
        score = 0
        for row in board.grid:
            for piece in row:
                if piece is not None:
                    value = pieces[f"{piece.__class__.__name__.lower()}"]
                    if piece.color == color:
                        score += value
                    else:
                        score -= value
        return score

    def chooseMove(self, board: Board):
        allMoves = board.getAllLegalMoves(self.color)
        if not allMoves:
            return None
        bestMove, bestScore = None, float('-inf')
        return random.choice(allMoves)