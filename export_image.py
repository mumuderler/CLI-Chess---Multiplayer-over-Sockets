# export_image.py
import chess
from PIL import Image, ImageDraw, ImageFont

def export_board_image(board: chess.Board, filename="board.png", square_size=60):
    # Colors approximating chess.com
    LIGHT_SQUARE_COLOR = (240, 217, 181)
    DARK_SQUARE_COLOR = (181, 136, 99)

    # Unicode pieces (matching ui.py)
    UNICODE_PIECES = {
        chess.PAWN: ('♙', '♟'),
        chess.KNIGHT: ('♘', '♞'),
        chess.BISHOP: ('♗', '♝'),
        chess.ROOK: ('♖', '♜'),
        chess.QUEEN: ('♕', '♛'),
        chess.KING: ('♔', '♚'),
    }

    # Image dimensions
    board_size = 8 * square_size
    img = Image.new('RGB', (board_size, board_size), 'white')
    draw = ImageDraw.Draw(img)

    # Try to load a font that supports Unicode chess pieces
    try:
        # This font is often available on various systems
        font = ImageFont.truetype("arial.ttf", int(square_size * 0.7))
    except IOError:
        try:
            # Fallback for Linux/macOS
            font = ImageFont.truetype("DejaVuSans.ttf", int(square_size * 0.7))
        except IOError:
            print("Warning: Could not find a suitable font for chess pieces. Using default.")
            font = ImageFont.load_default()

    for r in range(8):
        for f in range(8):
            x = f * square_size
            y = (7 - r) * square_size # Invert y-axis for chess board (rank 8 at top)

            is_light = ((f + r) % 2 == 0)
            color = LIGHT_SQUARE_COLOR if is_light else DARK_SQUARE_COLOR
            draw.rectangle([x, y, x + square_size, y + square_size], fill=color)

            sq = chess.square(f, r)
            piece = board.piece_at(sq)
            if piece:
                sym = UNICODE_PIECES[piece.piece_type][0 if piece.color == chess.WHITE else 1]
                
                # Center the piece text
                text_width, text_height = draw.textsize(sym, font=font)
                text_x = x + (square_size - text_width) / 2
                text_y = y + (square_size - text_height) / 2
                
                draw.text((text_x, text_y), sym, font=font, fill=(0, 0, 0)) # Black color for pieces

    img.save(filename)