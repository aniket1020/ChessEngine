import traceback

import chess
import chess.svg
import base64
import os
import time

from state import State
from flask import Flask, Response, request

app = Flask(__name__)
s = State()


def to_svg(state_to_svg):
    return base64.b64encode(chess.svg.board(board=state_to_svg.board).encode('utf-8')).decode('utf-8')


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


@app.route("/new_game")
def new_game():
    s.board.reset()
    response = app.response_class(
        response=s.board.fen(),
        status=200
    )
    return response


# Write for Minimax algorithm
def computer_move():
    for mv in s.board.legal_moves:
        s.board.push(mv)
        break


if __name__ == '__main__':
    app.run(debug=True)
