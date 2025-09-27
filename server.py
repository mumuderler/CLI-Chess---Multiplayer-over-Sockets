# server.py
import argparse
import socket
import threading
import time
from datetime import datetime


import chess
import chess.pgn


from shared import send_message, recv_message
from ui import render_board, prompt_move

class GameHost:
    self.node = self.game


    def wait_for_client(self):
        print(f"Waiting for client on {self.addr[0]}:{self.addr[1]} ...")
        self.conn, self.addr_connected = self.sock.accept()
        print(f"Client connected from {self.addr_connected}")


    def run(self):
        try:
            self.wait_for_client()
            # Host is White by default
            self.play_loop(is_host_white=True)
        finally:
            if self.conn:
                self.conn.close()
                self.sock.close()


    def play_loop(self, is_host_white=True):
        while True:
            render_board(self.board, orientation=chess.WHITE)
            if self.board.is_game_over():
                print("Game over:", self.board.result())
                break


            if self.board.turn == chess.WHITE:
            # Host (white) move
                mv = prompt_move('White')
                if self.handle_local_special(mv):
                    if self.board.is_game_over():
                        break
                    continue
                move = self.parse_move_input(mv)
                if move and move in self.board.legal_moves:
                    self.board.push(move)
                    send_message(self.conn, {'type':'opponent_move','move': move.uci()})
                    self.node = self.node.add_variation(move)
                else:
                    print('Illegal move or bad input')
            else:
                # wait for opponent move
                print('Waiting for opponent move...')
                msg = recv_message(self.conn)
                if msg is None:
                    print('Connection closed by opponent')
                    break
                if msg.get('type') == 'opponent_move':
                    mv = msg['move']
                    move = chess.Move.from_uci(mv)
                    self.board.push(move)
                    self.node = self.node.add_variation(move)
                elif msg.get('type') == 'resign':
                    print('Opponent resigned. You win!')
                    break
                elif msg.get('type') == 'offer_draw':
                    print('Opponent offers a draw. Type "accept" to accept, anything else to decline.')
                    resp = input('> ').strip().lower()
                    if resp == 'accept':
                        send_message(self.conn, {'type':'draw_accepted'})
                        print('Draw agreed')
                        break
                    else:
                        send_message(self.conn, {'type':'draw_declined'})
        # end loop
        self.finish()

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