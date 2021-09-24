import traceback

import chess
import chess.svg
import base64
import os
import time
import sys

from chessboard import ChessBoard
from flask import Flask, Response, request
from subprocess import Popen, PIPE, STDOUT

app = Flask(__name__)
s = ChessBoard()

if len(sys.argv) == 2:
    isAlphaBeta = sys.argv[1]
    if isAlphaBeta == '--minmaxab':
        print("Running Minimax with Alpha-beta")
        isAlphaBeta = True
    else:
        isAlphaBeta = False
        print("Running Minimax")
else:
    isAlphaBeta = False
    print("Running Minimax")

INF = 1000000000
whitePieces = \
    {
        'P': 10
        , 'B': 30
        , 'N': 30
        , 'R': 50
        , 'Q': 90
        , 'K': 900
    }
blackPieces = \
    {
        'p': -10
        , 'b': -30
        , 'n': -30
        , 'r': -50
        , 'q': -90
        , 'k': -900
    }

fTime = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'time.txt'), "w")


def to_svg(state_to_svg):
    return base64.b64encode(chess.svg.board(board=state_to_svg.board).encode('utf-8')).decode('utf-8')


def is_promotion(source, target):
    piece = s.board.piece_at(source)
    if target <= 7:
        if piece.symbol() == 'P' or piece.symbol() == 'p':
            return True
    return False


@app.route("/")
def chess_start():
    ret = open("index.html").read()
    return ret.replace('start', s.board.fen())


@app.route("/player_move")
def player_move():
    if not s.board.is_game_over():
        source = int(request.args.get('from', default=''))
        target = int(request.args.get('to', default=''))
        promotion = True if request.args.get('promotion', default='') == 'true' else False
        print(source, target)
        playerMove = s.board.san(chess.Move(source, target, promotion=chess.QUEEN if promotion else None))

        if playerMove is not None and playerMove != "":
            print("player moves", playerMove)
            try:
                s.board.push_san(playerMove)
                computer_move()
            except Exception as err:
                # traceback.print_exc()
                print(f"{err}")
        response = app.response_class(
            response=s.board.fen(),
            status=200
        )
        return response

    print("GAME IS OVER")
    response = app.response_class(
        response="game over",
        status=200
    )
    return response


@app.route('/sunfish/<int:num>')
def sunfish(num):

    print(s.board.fen())
    s.board = s.board.mirror()
    print(s.board.fen())
    player_minmax = 0
    player_sunfish = 0

    for _ in range(num):
        sunfish_process = Popen(['python3', 'sunfish.py'], stdout=PIPE, stdin=PIPE, stderr=STDOUT)
        while not s.board.is_game_over():
            sunfish_move = sunfish_process.stdout.readline().decode().strip()

            source = chess.parse_square(sunfish_move[:2])
            target = chess.parse_square(sunfish_move[2:])
            promotion = True if is_promotion(source, target) is True else False

            print("sunfish", sunfish_move, promotion)

            try:
                playerMove = s.board.san(chess.Move(source, target, promotion=chess.QUEEN if promotion else None))
            except:
                playerMove = None

            if playerMove is not None and playerMove != "":
                try:
                    s.board.push_san(playerMove)
                    print(s.board.fen())
                    if s.board.is_checkmate() or s.board.is_insufficient_material() or s.board.is_stalemate():
                        break
                    if isAlphaBeta:
                        st = time.time()
                        try:
                            score, move = minimax_ab(3, -INF, INF, False)
                            print(f"minmax {move}")
                            s.board.push(move)
                            print(s.board.fen())
                            # sunfish_process.communicate(input=move.uci().encode('utf-8'))

                            sunfish_process.stdin.write(f"{move.uci()}\n".encode('utf-8'))
                            if sunfish_process.poll() is not None:
                                break
                            sunfish_process.stdin.flush()

                        except:
                            traceback.print_exc()
                        en = time.time()
                        diff = round((en - st) * 1000)  # Milliseconds
                    else:
                        st = time.time()
                        try:
                            score, move = minimax(3, False)
                            print(f"minmax {move}")
                            s.board.push(move)
                            print(s.board.fen())
                            # sunfish_process.communicate(input=move.uci().encode('utf-8'))

                            sunfish_process.stdin.write(f"{move.uci()}\n".encode('utf-8'))
                            if sunfish_process.poll() is not None:
                                break
                            sunfish_process.stdin.flush()

                        except:
                            traceback.print_exc()
                        en = time.time()
                        diff = round((en - st) * 1000)  # Milliseconds
                    fTime.write(f"Diff : {diff} ms\n")
                except Exception as err:
                    # traceback.print_exc()
                    print(f"{err}")
            else:
                break
        print("GAME OVER")
        try:
            # sunfish_process.stdin.close()
            sunfish_process.terminate()
        except Exception as err:
            print(f"{err}")

        res = s.board.result()
        print(res)
        print(s.board.fen())

        if res == '1-0':
            player_sunfish = player_sunfish+1
        elif res == '0-1':
            player_minmax = player_minmax+1
        elif res == '1/2-1/2':
            player_sunfish = player_sunfish + 1
            player_minmax = player_minmax + 1

        s.board.reset()
        s.board = s.board.mirror()
        print(s.board.fen())

    response = app.response_class(
        response=f"Wins\nSunfish - {player_sunfish} \nMinmax - {player_minmax}",
        status=200
    )
    return response


@app.route("/new_game")
def new_game():
    s.board.reset()
    response = app.response_class(
        response=s.board.fen(),
        status=200
    )
    return response


def minimax_eval():
    eval_sum = 0
    for pos in chess.SQUARES:
        piece = s.board.piece_at(pos)

        if piece is not None:
            if piece.symbol() in whitePieces:
                eval_sum = eval_sum + whitePieces.get(piece.symbol())
            elif piece.symbol() in blackPieces:
                eval_sum = eval_sum + blackPieces.get(piece.symbol())
    return eval_sum


def minimax(depth, isMaximizingPlayer):
    if depth == 0 or s.board.is_game_over():
        return minimax_eval(), chess.Move.null()

    nextMove = chess.Move.null()
    if isMaximizingPlayer:
        maxEval = -INF
        for move in s.board.legal_moves:
            s.board.push(move)
            eval_sum, retMove = minimax(depth - 1, False)
            retMove = s.board.pop()
            maxEval = max(maxEval, eval_sum)
            if maxEval == eval_sum:
                nextMove = retMove
        return maxEval, nextMove
    else:
        minEval = INF
        for move in s.board.legal_moves:
            s.board.push(move)
            eval_sum, retMove = minimax(depth - 1, True)
            retMove = s.board.pop()
            minEval = min(minEval, eval_sum)
            if minEval == eval_sum:
                nextMove = retMove
        return minEval, nextMove


def minimax_ab(depth, alpha, beta, isMaximizingPlayer):
    if depth == 0 or s.board.is_game_over():
        return minimax_eval(), s.board.peek()

    nextMove = chess.Move.null()
    if isMaximizingPlayer:
        maxEval = -INF
        for move in s.board.legal_moves:
            s.board.push(move)
            eval_sum, retMove = minimax_ab(depth - 1, alpha, beta, False)
            retMove = s.board.pop()
            maxEval = max(maxEval, eval_sum)
            if maxEval == eval_sum:
                nextMove = retMove
            alpha = max(alpha, eval_sum)
            if beta <= alpha:
                break
        return maxEval, nextMove
    else:
        minEval = INF
        for move in s.board.legal_moves:
            s.board.push(move)
            eval_sum, retMove = minimax_ab(depth - 1, alpha, beta, True)
            retMove = s.board.pop()
            minEval = min(minEval, eval_sum)
            if minEval == eval_sum:
                nextMove = retMove
            beta = min(beta, eval_sum)
            if beta <= alpha:
                break
        return minEval, nextMove


# Write for Minimax algorithm
def computer_move():
    diff = 0
    if isAlphaBeta:
        st = time.time()
        try:
            score, move = minimax_ab(3, -INF, INF, False)
            print(f"-->{move}")
            s.board.push(move)
        except:
            traceback.print_exc()
        en = time.time()
        diff = round((en - st) * 1000)  # Milliseconds
    else:
        st = time.time()
        try:
            score, move = minimax(3, False)
            print(f"-->{move}")
            s.board.push(move)
        except:
            traceback.print_exc()
        en = time.time()
        diff = round((en - st) * 1000)  # Milliseconds
    fTime.write(f"Diff : {diff} ms\n")


if __name__ == '__main__':
    app.run(debug=True)
