import copy


class Board:
    def __init__(self):
        self.grid = [[None for _ in range(8)] for _ in range(8)]
        self.lastDoublePawn = None
        self.setupDefaultBoard()

    def setupDefaultBoard(self):
        order = [Rook, Knight, Bishop, Queen, King, Bishop, Knight, Rook]
        for c, cls in enumerate(order):
            self.grid[0][c] = cls("b", 0, c)
            self.grid[7][c] = cls("w", 7, c)
        for c in range(8):
            self.grid[1][c] = Pawn("b", 1, c)
            self.grid[6][c] = Pawn("w", 6, c)

    def movePiece(self, from_pos, to_pos):
        r1, c1 = from_pos
        r2, c2 = to_pos
        piece = self.grid[r1][c1]
        if piece:
            # EN PASSANT CAPTURE
            if isinstance(piece, Pawn):
                if c2 != c1 and self.grid[r2][c2] is None:
                    capturedRow, capturedCol = r1, c2
                    capturedPawn = self.grid[capturedRow][capturedCol]
                    if capturedPawn == self.lastDoublePawn:
                        self.grid[capturedRow][capturedCol] = None

            # DOUBLE PAWN MOVE
            if isinstance(piece, Pawn) and abs(r2 - r1) == 2:
                self.lastDoublePawn = piece
            else:
                self.lastDoublePawn = None

            # CASTLING
            if isinstance(piece, King) and abs(c2 - c1) == 2:
                if c2 > c1:
                    rook_start = (r1, 7)
                    rook_end = (r1, c2 - 1)
                else:
                    rook_start = (r1, 0)
                    rook_end = (r1, c2 + 1)
                rook = self.grid[rook_start[0]][rook_start[1]]
                if rook and isinstance(rook, Rook):
                    self.grid[rook_end[0]][rook_end[1]] = rook
                    self.grid[rook_start[0]][rook_start[1]] = None
                    rook.row, rook.col = rook_end
                    rook.hasMoved = True

            # NORMAL MOVE
            self.grid[r2][c2] = piece
            self.grid[r1][c1] = None
            piece.row, piece.col = r2, c2
            piece.hasMoved = True
            # PROMOTION
            if isinstance(piece, Pawn):
                if (piece.color == "w" and r2 == 0) or (piece.color == "b" and r2 == 7):
                    self.grid[r2][c2] = Queen(piece.color, r2, c2)

    def findKing(self, color):
        for r in range(8):
            for c in range(8):
                piece = self.grid[r][c]
                if piece and piece.color == color and piece.__class__.__name__ == "King":
                    return r, c
        return None

    def isInCheck(self, color):
        kingPosition = self.findKing(color)
        if not kingPosition:
            return False
        kingRow, kingColumn = kingPosition
        for r in range(8):
            for c in range(8):
                piece = self.grid[r][c]
                if piece is not None and piece.color != color:
                    if (kingRow, kingColumn) in piece.getMoves(self, ignoreCastling=True):
                        return True
        return False

    def simulateMove(self, start, end):
        newBoard = copy.deepcopy(self)
        piece = newBoard.grid[start[0]][start[1]]
        newBoard.grid[start[0]][start[1]] = None
        newBoard.grid[end[0]][end[1]] = piece
        piece.row, piece.col = end
        return newBoard

    def getLegalMoves(self, piece):
        legalMoves = []
        for move in piece.getMoves(self):
            simulatedBoard = self.simulateMove((piece.row, piece.col), move)
            if not simulatedBoard.isInCheck(piece.color):
                legalMoves.append(move)
        return legalMoves

    def hasAnyLegalMove(self, color):
        for r in range(8):
            for c in range(8):
                piece = self.grid[r][c]
                if piece is not None and piece.color == color:
                    if self.getLegalMoves(piece):
                        return True
        return False

    def isCheckmate(self, color):
        if not self.isInCheck(color):
            return False
        return not self.hasAnyLegalMove(color)

    def isStalemate(self, color):
        if self.isInCheck(color):
            return False
        return not self.hasAnyLegalMove(color)

    def getAllLegalMoves(self, color):
        allMoves = []
        for r in range(8):
            for c in range(8):
                piece = self.grid[r][c]
                if piece and piece.color == color:
                    possible_moves = self.getLegalMoves(piece)
                    for move in possible_moves:
                        allMoves.append(((r, c), move))
        return allMoves

    def isSquareAttacked(self, row, col, color):
        for r in range(8):
            for c in range(8):
                piece = self.grid[r][c]
                if piece and piece.color != color:
                    if (row, col) in piece.getMoves(self, ignoreCastling=True):
                        return True
        return False

class Piece:
    def __init__(self, color, row, col):
        self.color = color
        self.row, self.col = row, col
        self.hasMoved = False

    def getMoves(self, board, ignoreCastling=False):
        raise NotImplementedError

    @staticmethod
    def inBoardBounds(r, c):
        return 0 <= r < 8 and 0 <= c < 8

    def enemyOnTargetTile(self, board, r, c):
        if not self.inBoardBounds(r, c):
            return False
        target = board.grid[r][c]
        return target is not None and target.color != self.color

    def notFriendOnTargetTile(self, board, r, c):
        if not self.inBoardBounds(r, c):
            return False
        target = board.grid[r][c]
        return target is None or target.color != self.color


class Pawn(Piece):
    def getMoves(self, board, ignoreCastling=False):
        moves = []
        direction = -1 if self.color == "w" else 1
        startRow = 6 if self.color == "w" else 1
        if self.inBoardBounds(self.row + direction, self.col) and not board.grid[self.row + direction][self.col]:
            moves.append((self.row + direction, self.col))
            if self.row == startRow and self.inBoardBounds(self.row + 2 * direction, self.col) and not board.grid[self.row + 2 * direction][self.col]:
                moves.append((self.row + 2 * direction, self.col))
        for dc in (-1, 1):
            r, c = self.row + direction, self.col + dc
            if self.inBoardBounds(r, c) and self.enemyOnTargetTile(board, r, c):
                moves.append((r, c))
        for dc in (-1, 1):
            sideColumn = self.col + dc
            if 0 <= sideColumn < 8:
                sidePawn = board.grid[self.row][sideColumn]
                if isinstance(sidePawn, Pawn) and sidePawn.color != self.color:
                    if sidePawn == board.lastDoublePawn:
                        moves.append((self.row + direction, sideColumn))
        return moves

class Rook(Piece):
    def getMoves(self, board, ignoreCastling=False):
        moves = []
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        for dr, dc in directions:
            r, c = self.row + dr, self.col + dc
            while self.inBoardBounds(r, c):
                target = board.grid[r][c]
                if target is None:
                    moves.append((r, c))
                elif target.color != self.color:
                    moves.append((r, c))
                    break
                else:
                    break
                r += dr
                c += dc
        return moves

class Knight(Piece):
    def getMoves(self, board, ignoreCastling=False):
        moves = []
        knightMoves = [(-2, -1), (-2, 1), (2, -1), (2, 1), (-1, -2), (-1, 2), (1, -2), (1, 2)]
        for dr, dc in knightMoves:
            r, c = self.row + dr, self.col + dc
            if self.inBoardBounds(r, c):
                if self.notFriendOnTargetTile(board, r, c):
                    moves.append((r, c))
        return moves

class Bishop(Piece):
    def getMoves(self, board, ignoreCastling=False):
        moves = []
        directions = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
        for dr, dc in directions:
            r, c = self.row + dr, self.col + dc
            while self.inBoardBounds(r, c):
                target = board.grid[r][c]
                if target is None:
                    moves.append((r, c))
                elif target.color != self.color:
                    moves.append((r, c))
                    break
                else:
                    break
                r += dr
                c += dc
        return moves


class Queen(Piece):
    def getMoves(self, board, ignoreCastling=False):
        moves = []
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1)]
        for dr, dc in directions:
            r, c = self.row + dr, self.col + dc
            while self.inBoardBounds(r, c):
                target = board.grid[r][c]
                if target is None:
                    moves.append((r, c))
                elif target.color != self.color:
                    moves.append((r, c))
                    break
                else:
                    break
                r += dr
                c += dc
        return moves

class King(Piece):
    def getMoves(self, board, ignoreCastling=False):
        moves = []
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                if dr == dc == 0:
                    continue
                r, c = self.row + dr, self.col + dc
                if self.inBoardBounds(r, c) and self.notFriendOnTargetTile(board, r, c):
                    moves.append((r, c))

        if not ignoreCastling and not self.hasMoved:
            if not board.isInCheck(self.color):
                # KINGSIDE CASTLING
                rook = board.grid[self.row][7]
                if isinstance(rook, Rook) and not rook.hasMoved:
                    if all(board.grid[self.row][c] is None for c in range(self.col+1, 7)):
                        if not board.isSquareAttacked(self.row, self.col, self.color) and \
                           not board.isSquareAttacked(self.row, self.col+1, self.color) and \
                           not board.isSquareAttacked(self.row, self.col+2, self.color):
                            moves.append((self.row, self.col+2))
                # QUEENSIDE CASTLING
                rook = board.grid[self.row][0]
                if isinstance(rook, Rook) and not rook.hasMoved:
                    if all(board.grid[self.row][c] is None for c in range(1, self.col)):
                        if not board.isSquareAttacked(self.row, self.col, self.color) and \
                           not board.isSquareAttacked(self.row, self.col-1, self.color) and \
                           not board.isSquareAttacked(self.row, self.col-2, self.color):
                            moves.append((self.row, self.col-2))

        return moves