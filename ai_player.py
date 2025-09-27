# ai_player.py
import chess
import random

class RandomMoveAI:
    def __init__(self, board: chess.Board):
        self.board = board

    def choose_move(self) -> chess.Move:
        """
        Chooses a random legal move from the current board state.
        """
        legal_moves = list(self.board.legal_moves)
        if legal_moves:
            return random.choice(legal_moves)
        return None