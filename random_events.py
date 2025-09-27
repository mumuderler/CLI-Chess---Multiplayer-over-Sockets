# random_events.py
import chess
import random

class RandomEvent:
    def __init__(self, name, description):
        self.name = name
        self.description = description

    def trigger(self, board: chess.Board):
        """
        Applies the effect of the random event to the board or game state.
        Returns True if the event was successfully triggered, False otherwise.
        """
        raise NotImplementedError

class PieceTransformationEvent(RandomEvent):
    def __init__(self):
        super().__init__("Piece Transformation", "A random pawn transforms into a random non-pawn piece.")

    def trigger(self, board: chess.Board):
        pawns = [sq for sq, piece in board.piece_map().items() if piece.piece_type == chess.PAWN]
        if not pawns:
            print("No pawns on the board for Piece Transformation event.")
            return False

        target_square = random.choice(pawns)
        original_piece = board.piece_at(target_square)
        
        new_piece_type = random.choice([chess.KNIGHT, chess.BISHOP, chess.ROOK, chess.QUEEN])
        board.set_piece_at(target_square, chess.Piece(new_piece_type, original_piece.color))
        print(f"Event: A {original_piece.color_name()} pawn at {chess.square_name(target_square)} transformed into a {chess.piece_name(new_piece_type)}!")
        return True

class BoardRotationEvent(RandomEvent):
    def __init__(self):
        super().__init__("Board Rotation", "The entire board rotates 180 degrees.")

    def trigger(self, board: chess.Board):
        # Create a new board and manually place pieces after rotation
        new_board = chess.Board()
        new_board.clear()

        for sq in chess.SQUARES:
            piece = board.piece_at(sq)
            if piece:
                rotated_rank = 7 - chess.square_rank(sq)
                rotated_file = 7 - chess.square_file(sq)
                rotated_square = chess.square(rotated_file, rotated_rank)
                new_board.set_piece_at(rotated_square, piece)
        
        board.set_board_fen(new_board.fen())
        # Also need to rotate turn
        board.turn = not board.turn
        print("Event: The board has rotated 180 degrees!")
        return True

class GravityEvent(RandomEvent):
    def __init__(self):
        super().__init__("Gravity", "All pieces 'fall' to the lowest possible rank in their file.")

    def trigger(self, board: chess.Board):
        for file_idx in range(8):
            pieces_in_file = []
            for rank_idx in range(8):
                sq = chess.square(file_idx, rank_idx)
                piece = board.piece_at(sq)
                if piece:
                    pieces_in_file.append(piece)
                    board.remove_piece_at(sq) # Clear original position
            
            # Place pieces from bottom up
            for i, piece in enumerate(pieces_in_file):
                target_sq = chess.square(file_idx, i)
                board.set_piece_at(target_sq, piece)
        print("Event: Gravity has pulled all pieces to the bottom of their files!")
        return True

class KingSwapEvent(RandomEvent):
    def __init__(self):
        super().__init__("King Swap", "The positions of the two kings are swapped.")

    def trigger(self, board: chess.Board):
        white_king_sq = board.king(chess.WHITE)
        black_king_sq = board.king(chess.BLACK)

        if white_king_sq is None or black_king_sq is None:
            print("Error: Kings not found for King Swap event.")
            return False

        # Temporarily remove kings
        board.remove_piece_at(white_king_sq)
        board.remove_piece_at(black_king_sq)

        # Swap positions
        board.set_piece_at(white_king_sq, chess.Piece(chess.KING, chess.BLACK))
        board.set_piece_at(black_king_sq, chess.Piece(chess.KING, chess.WHITE))

        # Check if either king is in check after swap
        if board.is_check():
            print("King Swap would result in immediate check. Reverting swap.")
            # Revert the swap
            board.remove_piece_at(white_king_sq)
            board.remove_piece_at(black_king_sq)
            board.set_piece_at(white_king_sq, chess.Piece(chess.KING, chess.WHITE))
            board.set_piece_at(black_king_sq, chess.Piece(chess.KING, chess.BLACK))
            return False # Event failed
        
        print(f"Event: Kings have swapped positions! White King at {chess.square_name(white_king_sq)}, Black King at {chess.square_name(black_king_sq)}.")
        return True

# List of all available random events
ALL_RANDOM_EVENTS = [
    PieceTransformationEvent,
    BoardRotationEvent,
    GravityEvent,
    KingSwapEvent,
]

def get_random_event():
    return random.choice(ALL_RANDOM_EVENTS)()