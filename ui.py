# ui.py
import os
import sys
import chess


LIGHT_SQUARE = '\u001b[48;2;240;217;181m' # #f0d9b5
DARK_SQUARE = '\u001b[48;2;181;136;99m' # #b58863
RESET = '\u001b[0m'


UNICODE_PIECES = {
chess.PAWN: ('♙', '♟'),
chess.KNIGHT: ('♘', '♞'),
chess.BISHOP: ('♗', '♝'),
chess.ROOK: ('♖', '♜'),
chess.QUEEN: ('♕', '♛'),
chess.KING: ('♔', '♚'),
}

def clear():
    if os.name == 'nt':
        os.system('cls')
    else:
        os.system('clear')

def render_board(board: chess.Board, orientation: chess.Color=chess.WHITE, powerups: list=None, event_message: str=None):
    # orientation True=white on bottom
    ranks = range(8, 0, -1) if orientation == chess.WHITE else range(1, 9)
    files = range(0, 8) if orientation == chess.WHITE else range(7, -1, -1)


    out = []
    out.append(' a b c d e f g h')
    for r in ranks:
        row = [str(r) + ' ']
        for f in files:
            sq = chess.square(f, r-1)
            is_light = ((f + (r-1)) % 2 == 0)
            bg = LIGHT_SQUARE if is_light else DARK_SQUARE
            piece = board.piece_at(sq)
            if piece:
                sym = UNICODE_PIECES[piece.piece_type][0 if piece.color == chess.WHITE else 1]
                cell = f'{bg} {sym} {RESET}'
            else:
                cell = f'{bg} {RESET}'
            row.append(cell)
        out.append(''.join(row) + ' ' + str(r))
    out.append(' a b c d e f g h')
    print('\n'.join(out))

    if powerups and len(powerups) > 0:
        print("\n--- Available Power-Ups ---")
        for i, powerup_name in enumerate(powerups):
            print(f"{i}: {powerup_name}")
        print("---------------------------\n")
    
    if event_message:
        print(f"\n--- Event: {event_message} ---\n")


def prompt_move(turn_color_name: str):
    return input(f"{turn_color_name} to move > ").strip()