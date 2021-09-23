import chess


class ChessBoard(object):
    def __init__(self):
        self.board = chess.Board()


if __name__ == "__main__":
    s = ChessBoard()
