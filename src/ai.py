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


class EvaluationEnemy:
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
        for move in allMoves:
            start, end = move
            score = self.evaluateBoard(board.simulateMove(start, end), color=self.color)
            if score > bestScore:
                bestMove, bestScore = move, score
        return bestMove

class MiniMaxEnemy(EvaluationEnemy):
    def __init__(self, color, depth):
        super().__init__(color)
        self.depth = depth

    def chooseMove(self, board: Board):
        allMoves = board.getAllLegalMoves(self.color)
        if not allMoves:
            return None
        bestMove, bestScore = None, float('-inf')
        for move in allMoves:
            start, end = move
            score = self.minimax(board.simulateMove(start, end), self.depth - 1, isMaximizing=False)
            if score > bestScore:
                bestMove, bestScore = move, score
        return bestMove

    def minimax(self, board: Board, depth, isMaximizing):
        if depth == 0 or board.isCheckmate('w') or board.isCheckmate('b') or board.isStalemate('w') or board.isStalemate('b'):
            return self.evaluateBoard(board, self.color)
        colorToPlay = self.color if isMaximizing else ('b' if self.color == 'w' else 'w')
        moves = board.getAllLegalMoves(colorToPlay)
        if not moves:
            return self.evaluateBoard(board, self.color)
        bestScore = float('-inf') if isMaximizing else float('inf')
        for move in moves:
            start, end = move
            score = self.minimax(board.simulateMove(start, end), depth - 1, False)
            bestScore = max(bestScore, score) if isMaximizing else min(bestScore, score)
        return bestScore