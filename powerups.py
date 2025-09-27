# powerups.py
import chess
import random

class PowerUp:
    def __init__(self, name, description):
        self.name = name
        self.description = description

    def activate(self, board: chess.Board, player_color: chess.Color, *args, **kwargs):
        """
        Applies the effect of the power-up to the board or game state.
        Returns True if activation was successful, False otherwise.
        """
        raise NotImplementedError

    def deactivate(self, board: chess.Board, player_color: chess.Color):
        """
        Reverts any temporary effects of the power-up.
        """
        pass

class ExtraMovePowerUp(PowerUp):
    def __init__(self):
        super().__init__("Extra Move", "Allows you to make two moves in a single turn.")

    def activate(self, board: chess.Board, player_color: chess.Color, *args, **kwargs):
        # This power-up's effect is handled in the game loop by allowing an extra move input.
        # No direct board modification here.
        print(f"{'White' if player_color == chess.WHITE else 'Black'} activated Extra Move! Make another move.")
        return True

class PieceSwapPowerUp(PowerUp):
    def __init__(self):
        super().__init__("Piece Swap", "Swap the positions of two of your non-pawn pieces.")

    def activate(self, board: chess.Board, player_color: chess.Color, square1: chess.Square, square2: chess.Square):
        piece1 = board.piece_at(square1)
        piece2 = board.piece_at(square2)

        if not (piece1 and piece2 and piece1.color == player_color and piece2.color == player_color and
                piece1.piece_type != chess.PAWN and piece2.piece_type != chess.PAWN):
            print("Invalid pieces for swap. Must be your non-pawn pieces.")
            return False

        # Temporarily remove pieces
        board.remove_piece_at(square1)
        board.remove_piece_at(square2)

        # Place them at new positions
        board.set_piece_at(square1, piece2)
        board.set_piece_at(square2, piece1)
        print(f"{'White' if player_color == chess.WHITE else 'Black'} swapped {piece1.unicode_symbol()} at {chess.square_name(square1)} with {piece2.unicode_symbol()} at {chess.square_name(square2)}.")
        return True

class TeleportPowerUp(PowerUp):
    def __init__(self):
        super().__init__("Teleport", "Move a non-pawn piece to any empty square on the board.")

    def activate(self, board: chess.Board, player_color: chess.Color, from_square: chess.Square, to_square: chess.Square):
        piece = board.piece_at(from_square)

        if not (piece and piece.color == player_color and piece.piece_type != chess.PAWN and
                board.piece_at(to_square) is None):
            print("Invalid teleport. Must be your non-pawn piece to an empty square.")
            return False

        board.remove_piece_at(from_square)
        board.set_piece_at(to_square, piece)
        print(f"{'White' if player_color == chess.WHITE else 'Black'} teleported {piece.unicode_symbol()} from {chess.square_name(from_square)} to {chess.square_name(to_square)}.")
        return True

class ShieldPowerUp(PowerUp):
    def __init__(self):
        super().__init__("Shield", "Protects a chosen piece from capture for one opponent's turn.")
        self.shielded_piece_square = None
        self.shielded_piece_color = None

    def activate(self, board: chess.Board, player_color: chess.Color, square: chess.Square):
        piece = board.piece_at(square)
        if not (piece and piece.color == player_color):
            print("Invalid piece for shield. Must be your piece.")
            return False
        self.shielded_piece_square = square
        self.shielded_piece_color = player_color
        print(f"{'White' if player_color == chess.WHITE else 'Black'} shielded {piece.unicode_symbol()} at {chess.square_name(square)}.")
        # Actual protection logic will be in game loop's move validation
        return True

    def deactivate(self, board: chess.Board, player_color: chess.Color):
        self.shielded_piece_square = None
        self.shielded_piece_color = None
        print(f"Shield for {'White' if player_color == chess.WHITE else 'Black'} has expired.")

class PawnPromotionPowerUp(PowerUp):
    def __init__(self):
        super().__init__("Pawn Promotion", "Instantly promote one of your pawns to a Queen.")

    def activate(self, board: chess.Board, player_color: chess.Color, square: chess.Square):
        piece = board.piece_at(square)
        if not (piece and piece.color == player_color and piece.piece_type == chess.PAWN):
            print("Invalid piece for promotion. Must be your pawn.")
            return False

        board.remove_piece_at(square)
        board.set_piece_at(square, chess.Piece(chess.QUEEN, player_color))
        print(f"{'White' if player_color == chess.WHITE else 'Black'} promoted pawn at {chess.square_name(square)} to Queen.")
        return True

# List of all available power-ups
ALL_POWERUPS = [
    ExtraMovePowerUp,
    PieceSwapPowerUp,
    TeleportPowerUp,
    ShieldPowerUp,
    PawnPromotionPowerUp,
]

def get_random_powerup():
    return random.choice(ALL_POWERUPS)()