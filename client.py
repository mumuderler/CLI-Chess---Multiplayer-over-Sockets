# client.py
import argparse
import socket
import time
import chess
from datetime import datetime

from shared import send_message, recv_message
from ui import render_board, prompt_move
from powerups import PowerUp # Import PowerUp base class for type checking

import chess.pgn

class GameClient:
    def __init__(self, host='127.0.0.1', port=5000, use_pairing_code=False, game_mode='standard'):
        self.addr = (host, port)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.board = chess.Board()
        self.game = chess.pgn.Game()
        self.node = self.game
        self.use_pairing_code = use_pairing_code
        self.game_mode = game_mode # Store the selected game mode

        # Game mode specific initializations
        self.powerups = {chess.WHITE: [], chess.BLACK: []} # For Power-Up Chess
        self.random_event_active = None # For Random Event Chess


    def connect(self):
        try:
            self.sock.connect(self.addr)
            print(f'Connected to host {self.addr}')
        except socket.error as e:
            print(f"Error connecting to host {self.addr}: {e}")
            raise

        if self.use_pairing_code:
            code = input("Enter pairing code provided by host: ").strip()
            send_message(self.sock, {'type': 'pairing_code', 'code': code})
            # Wait for pairing code status from server
            msg = recv_message(self.sock)
            if msg and msg.get('type') == 'pairing_code_status':
                if msg.get('status') == 'accepted':
                    print("Pairing code accepted by host.")
                else:
                    print(f"Pairing code rejected by host: {msg.get('reason', 'Unknown reason')}")
                    self.sock.close()
                    raise ConnectionRefusedError("Pairing code rejected.")
            else:
                print("Did not receive pairing code status from host. Disconnecting.")
                self.sock.close()
                raise ConnectionRefusedError("No pairing code status.")


    def run(self):
        try:
            self.connect()
            self.play_loop()
        except (socket.error, ConnectionRefusedError) as e:
            print(f"Game client encountered an error: {e}")
        finally:
            self.sock.close()

    def _handle_local_move(self):
        mv = prompt_move('Black')
        if self.handle_local_special(mv):
            return True # Special command handled, or game over
        move = self.parse_move_input(mv)
        if move and move in self.board.legal_moves:
            self.board.push(move)
            send_message(self.sock, {'type':'opponent_move','move': move.uci()})
            self.node = self.node.add_variation(move)
            return True
        else:
            if self.parse_move_input(mv) is None:
                print('Invalid move format. Please use UCI (e.g., e2e4) or SAN (e.g., Nf3).')
            else:
                print('Illegal move. Please try again.')
            return False

    def _activate_powerup(self, player_color: chess.Color, powerup_index: int, *args):
        # Client sends activation request to server
        send_message(self.sock, {'type': 'activate_powerup', 'index': powerup_index, 'args': args})
        
        # Wait for server's response on activation status
        msg = recv_message(self.sock)
        if msg and msg.get('type') == 'powerup_activation_status':
            if msg.get('status') == 'success':
                print(f"Power-up '{msg.get('powerup_name')}' activated successfully!")
                # Remove power-up from local list (server already did this)
                if 0 <= powerup_index < len(self.powerups[player_color]):
                    self.powerups[player_color].pop(powerup_index)
                return True
            else:
                print(f"Power-up activation failed: {msg.get('reason', 'Unknown reason')}")
                return False
        print("Did not receive power-up activation status from host.")
        return False

    def _handle_opponent_move(self):
        print('Waiting for opponent move...')
        msg = recv_message(self.sock)
        if msg is None:
            print('Connection closed by host')
            return False
        if msg.get('type') == 'opponent_move':
            mv = msg['move']
            move = chess.Move.from_uci(mv)
            self.board.push(move)
            self.node = self.node.add_variation(move)
            return True
        elif msg.get('type') == 'resign':
            print('Opponent resigned. You win!')
            return False # Game ends
        elif msg.get('type') == 'offer_draw':
            print('Opponent offers a draw. Type "accept" to accept, anything else to decline.')
            resp = input('> ').strip().lower()
            if resp == 'accept':
                send_message(self.sock, {'type':'draw_accepted'})
                print('Draw agreed')
                return False # Game ends
            else:
                send_message(self.sock, {'type':'draw_declined'})
                return True # Continue game
        elif msg.get('type') == 'draw_accepted':
            print('Host accepted draw. Game over.')
            return False
        elif msg.get('type') == 'draw_declined':
            print('Host declined draw.')
            return True
        elif msg.get('type') == 'powerup_earned':
            powerup_name = msg.get('powerup_name')
            player_color = chess.WHITE if msg.get('player') == 'host' else chess.BLACK
            # For now, just store the name. Actual PowerUp object will be on server.
            self.powerups[player_color].append(powerup_name)
            print(f"Opponent earned a power-up: {powerup_name}!")
            return True
        elif msg.get('type') == 'powerup_activated':
            powerup_name = msg.get('powerup_name')
            player_color = chess.WHITE if msg.get('player') == 'host' else chess.BLACK
            # Remove power-up from local list (server already did this)
            if powerup_name in self.powerups[player_color]:
                self.powerups[player_color].remove(powerup_name)
            print(f"Opponent activated power-up: {powerup_name}!")
            return True
        elif msg.get('type') == 'random_event_triggered':
            event_name = msg.get('event_name')
            event_description = msg.get('event_description')
            board_fen = msg.get('board_fen')
            self.board.set_fen(board_fen) # Update board state
            self.random_event_active = f"SUCCESS - {event_name}: {event_description}"
            return True
        elif msg.get('type') == 'random_event_failed':
            event_name = msg.get('event_name')
            event_description = msg.get('event_description')
            self.random_event_active = f"FAILED - {event_name}: {event_description}"
            return True
        return True # Default to continue if no specific end condition met

    def play_loop(self):
        while True:
            current_player_powerups = [p for p in self.powerups[self.board.turn]] # Power-ups are already names (strings) on client
            render_board(self.board, orientation=chess.BLACK, powerups=current_player_powerups, event_message=self.random_event_active)
            self.random_event_active = None # Clear event message after rendering
            if self.board.is_game_over():
                print("Game over:", self.board.result())
                break

            if self.board.turn == chess.BLACK:
                if not self._handle_local_move():
                    if self.board.is_game_over(): # Check again after local move
                        break
                    continue # Invalid move, prompt again
            else: # White's turn (opponent)
                if not self._handle_opponent_move():
                    break # Game ended by opponent action or network issue
        # end loop
        self.finish()

    def handle_local_special(self, mv):
        low = mv.lower()
        if low == 'resign':
            send_message(self.sock, {'type':'resign'})
            print('You resigned.')
            return True
        if low == 'offer draw' or low == 'offer_draw':
            send_message(self.sock, {'type':'offer_draw'})
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
                powerup_args = parts[2:]
                processed_args = []
                for arg in powerup_args:
                    try:
                        processed_args.append(chess.parse_square(arg))
                    except ValueError:
                        processed_args.append(arg)
                
                if self._activate_powerup(chess.BLACK, powerup_index, *processed_args):
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
    parser = argparse.ArgumentParser(description="CLI Chess Client")
    parser.add_argument("--host", default="127.0.0.1", help="Host address to connect to")
    parser.add_argument("--port", type=int, default=5000, help="Port to connect to")
    parser.add_argument("--pairing-code", action="store_true", help="Enable pairing code for secure connection")
    parser.add_argument("--mode", default="standard", choices=["standard", "powerup", "random_event"],
                        help="Select game mode: standard, powerup, or random_event")
    args = parser.parse_args()

    client = GameClient(host=args.host, port=args.port, use_pairing_code=args.pairing_code, game_mode=args.mode)
    client.run()

if __name__ == '__main__':
    main()