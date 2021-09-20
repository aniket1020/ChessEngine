import chess


class ChessBoard(object):
    def __init__(self):
        self.board = chess.Board()

    def key(self):
        return self.board.board_fen(), self.board.turn, self.board.castling_rights, self.board.ep_square

    def edges(self):
        return list(self.board.legal_moves)


if __name__ == "__main__":
    s = ChessBoard()
