# server.py
import argparse
import socket
import threading
import time
from datetime import datetime
import secrets # For generating secure pairing codes
import uuid # For generating unique IDs if needed


import chess
import chess.pgn


from shared import send_message, recv_message
from ui import render_board, prompt_move
from ai_player import RandomMoveAI # Import the AI player
from powerups import get_random_powerup, PowerUp # Import power-up logic
from random_events import get_random_event, RandomEvent # Import random event logic

class GameHost:
    def __init__(self, host='127.0.0.1', port=5000, ai_opponent=False, game_mode='standard'):
        self.addr = (host, port)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            self.sock.bind(self.addr)
        except socket.error as e:
            print(f"Error binding socket to {self.addr}: {e}")
            raise
        self.sock.listen(1)
        self.conn = None
        self.addr_connected = None
        self.board = chess.Board()
        self.game = chess.pgn.Game()
        self.node = self.game
        self.ai_opponent = ai_opponent
        self.ai = None
        if self.ai_opponent:
            self.ai = RandomMoveAI(self.board)
        self.pairing_code = None # Initialize pairing code
        self.game_mode = game_mode # Store the selected game mode

        # Game mode specific initializations
        self.powerups = {chess.WHITE: [], chess.BLACK: []} # For Power-Up Chess
        self.random_event_active = None # For Random Event Chess


    def wait_for_client(self, use_pairing_code=False):
        print(f"Waiting for client on {self.addr[0]}:{self.addr[1]} ...")
        if use_pairing_code:
            self.pairing_code = secrets.token_urlsafe(8) # Generate a random 8-character code
            print(f"Share this pairing code with your opponent: {self.pairing_code}")
        
        try:
            self.conn, self.addr_connected = self.sock.accept()
            print(f"Client connected from {self.addr_connected}")
        except socket.error as e:
            print(f"Error accepting client connection: {e}")
            return False

        if use_pairing_code:
            # Receive pairing code from client
            msg = recv_message(self.conn)
            if msg is None or msg.get('type') != 'pairing_code' or msg.get('code') != self.pairing_code:
                print("Invalid or missing pairing code. Disconnecting client.")
                send_message(self.conn, {'type': 'pairing_code_status', 'status': 'rejected', 'reason': 'Invalid or missing code'})
                self.conn.close()
                self.conn = None
                return False
            print("Pairing code accepted.")
            send_message(self.conn, {'type': 'pairing_code_status', 'status': 'accepted'})
        return True


    def run(self):
        try:
            if not self.ai_opponent:
                if not self.wait_for_client(use_pairing_code=self.use_pairing_code):
                    return # Exit if pairing code failed
            # Host is White by default
            self.play_loop(is_host_white=True)
        finally:
            if self.conn:
                self.conn.close()
            self.sock.close()


    def _handle_host_move(self):
        mv = prompt_move('White')
        if self.handle_local_special(mv):
            return True # Special command handled, or game over
        move = self.parse_move_input(mv)
        if move and move in self.board.legal_moves:
            # Check for capture before making the move
            captured_piece = self.board.piece_at(move.to_square)
            self.board.push(move)
            if self.game_mode == 'powerup' and captured_piece:
                powerup = get_random_powerup()
                self.powerups[self.board.turn].append(powerup) # Add to the player who just moved (whose turn it now is)
                print(f"You earned a power-up: {powerup.name}!")
            
            if not self.ai_opponent: # Only send message if not AI
                send_message(self.conn, {'type':'opponent_move','move': move.uci()})
            self.node = self.node.add_variation(move)
            return True
        else:
            if self.parse_move_input(mv) is None:
                print('Invalid move format. Please use UCI (e.g., e2e4) or SAN (e.g., Nf3).')
            else:
                print('Illegal move. Please try again.')
            return False

    def _handle_opponent_move(self):
        if self.ai_opponent:
            print('AI is thinking...')
            move = self.ai.choose_move()
            if move:
                self.board.push(move)
                self.node = self.node.add_variation(move)
                return True
            else:
                print("AI could not find a legal move. This shouldn't happen unless the game is over.")
                return False
        else:
            print('Waiting for opponent move...')
            msg = recv_message(self.conn)
            if msg is None:
                print('Connection closed by opponent')
                return False
            if msg.get('type') == 'opponent_move':
                mv = msg['move']
                move = chess.Move.from_uci(mv)
                # Check for capture before making the move
                captured_piece = self.board.piece_at(move.to_square)
                self.board.push(move)
                if self.game_mode == 'powerup' and captured_piece:
                    powerup = get_random_powerup()
                    self.powerups[self.board.turn].append(powerup) # Add to the player who just moved (whose turn it now is)
                    print(f"Opponent earned a power-up: {powerup.name}!")
                self.node = self.node.add_variation(move)
                return True
            elif msg.get('type') == 'resign':
                print('Opponent resigned. You win!')
                return False # Game ends
            elif msg.get('type') == 'offer_draw':
                print('Opponent offers a draw. Type "accept" to accept, anything else to decline.')
                resp = input('> ').strip().lower()
                if resp == 'accept':
                    send_message(self.conn, {'type':'draw_accepted'})
                    print('Draw agreed')
                    return False # Game ends
                else:
                    send_message(self.conn, {'type':'draw_declined'})
                    return True # Continue game
        return True # Default to continue if no specific end condition met

    def play_loop(self, is_host_white=True):
        turn_count = 0
        while True:
            current_player_powerups = [p.name for p in self.powerups[self.board.turn]]
            render_board(self.board, orientation=chess.WHITE, powerups=current_player_powerups, event_message=self.random_event_active)
            self.random_event_active = None # Clear event message after rendering
            if self.board.is_game_over():
                print("Game over:", self.board.result())
                break

            if self.game_mode == 'random_event' and turn_count > 0 and turn_count % 5 == 0: # Trigger every 5 turns
                event = get_random_event()
                event_message = f"{event.name}: {event.description}"
                if event.trigger(self.board):
                    self.random_event_active = f"SUCCESS - {event_message}"
                    if not self.ai_opponent:
                        send_message(self.conn, {'type': 'random_event_triggered', 'event_name': event.name, 'event_description': event.description, 'board_fen': self.board.fen()})
                else:
                    self.random_event_active = f"FAILED - {event_message}"
                    if not self.ai_opponent:
                        send_message(self.conn, {'type': 'random_event_failed', 'event_name': event.name, 'event_description': event.description})
                # Re-render board after event
                render_board(self.board, orientation=chess.WHITE, powerups=current_player_powerups, event_message=self.random_event_active)
            
            turn_count += 1

            if self.board.turn == chess.WHITE:
                if not self._handle_host_move():
                    if self.board.is_game_over(): # Check again after host move
                        break
                    continue # Invalid move, prompt again
            else: # Black's turn
                if not self._handle_opponent_move():
                    break # Game ended by opponent action or AI issue
        # end loop
        self.finish()

    def _activate_powerup(self, player_color: chess.Color, powerup_index: int, *args):
        if not (0 <= powerup_index < len(self.powerups[player_color])):
            print("Invalid power-up index.")
            return False

        powerup = self.powerups[player_color][powerup_index]
        
        # Special handling for power-ups that require additional input
        if isinstance(powerup, PowerUp): # Ensure it's a PowerUp object
            try:
                if powerup.activate(self.board, player_color, *args):
                    self.powerups[player_color].pop(powerup_index)
                    if not self.ai_opponent:
                        send_message(self.conn, {'type': 'powerup_activated', 'player': 'host', 'powerup_name': powerup.name, 'args': args})
                    return True
                else:
                    print(f"Failed to activate {powerup.name}. Check arguments.")
                    return False
            except Exception as e:
                print(f"Error activating power-up {powerup.name}: {e}")
                return False
        return False

    def handle_local_special(self, mv):
        low = mv.lower()
        if low == 'resign':
            send_message(self.conn, {'type':'resign'})
            print('You resigned.')
            return True
        if low == 'offer draw' or low == 'offer_draw':
            send_message(self.conn, {'type':'offer_draw'})
            print('Draw offered to opponent')
            return True
        if low == 'save':
            self.save_pgn()
            return True
        if low == 'export_image':
            try:
                from export_image import export_board_image
                export_board_image(self.board, filename=f'final_{int(time.time())}.png')
                print('Exported image')
            except Exception as e:
                print('Could not export image:', e)
            return True
        
        if self.game_mode == 'powerup' and low.startswith('activate'):
            parts = low.split()
            if len(parts) >= 2 and parts[1].isdigit():
                powerup_index = int(parts[1])
                # Pass remaining parts as arguments to the power-up
                powerup_args = parts[2:]
                # Convert square names to chess.Square objects if applicable
                processed_args = []
                for arg in powerup_args:
                    try:
                        processed_args.append(chess.parse_square(arg))
                    except ValueError:
                        processed_args.append(arg) # Keep as string if not a square
                
                if self._activate_powerup(chess.WHITE, powerup_index, *processed_args):
                    return True
                else:
                    print("Power-up activation failed.")
                    return False
            else:
                print("Invalid 'activate' command. Usage: activate <index> [args]")
                return False
        return False


    def parse_move_input(self, mv_text):
        # Accept UCI (e2e4) or SAN (Nf3). Try UCI first, then SAN.
        try:
            if len(mv_text) in (4,5) and mv_text[0].isalpha():
                return chess.Move.from_uci(mv_text)
        except Exception:
            pass
        try:
            return self.board.parse_san(mv_text)
        except Exception:
            return None


    def save_pgn(self):
        self.game.headers['Event'] = 'CLI Networked Game'
        self.game.headers['Date'] = datetime.utcnow().strftime('%Y.%m.%d')
        exporter = chess.pgn.FileExporter(open(f'game_{int(time.time())}.pgn', 'w'))
        self.game.accept(exporter)
        print('Saved PGN')


    def finish(self):
        # Write PGN when done
        self.save_pgn()

def main():
    parser = argparse.ArgumentParser(description="CLI Chess Host")
    parser.add_argument("--host", default="127.0.0.1", help="Host address to bind to")
    parser.add_argument("--port", type=int, default=5000, help="Port to listen on")
    parser.add_argument("--ai", action="store_true", help="Play against AI opponent (offline)")
    parser.add_argument("--pairing-code", action="store_true", help="Enable pairing code for secure connection")
    parser.add_argument("--mode", default="standard", choices=["standard", "powerup", "random_event"],
                        help="Select game mode: standard, powerup, or random_event")
    args = parser.parse_args()

    host = GameHost(host=args.host, port=args.port, ai_opponent=args.ai, game_mode=args.mode)
    host.use_pairing_code = args.pairing_code # Set pairing code flag
    host.run()

if __name__ == '__main__':
    main()