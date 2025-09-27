# client.py
import argparse
import socket
import time
import chess
from datetime import datetime

from shared import send_message, recv_message
from ui import render_board, prompt_move

import chess.pgn

class GameClient:
    def __init__(self, host='127.0.0.1', port=5000):
        self.addr = (host, port)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.board = chess.Board()
        self.game = chess.pgn.Game()
        self.node = self.game


    def connect(self):
        self.sock.connect(self.addr)
        print(f'Connected to host {self.addr}')


    def run(self):
        try:
            self.connect()
            self.play_loop()
        finally:
            self.sock.close()

    def play_loop(self):
        while True:
            render_board(self.board, orientation=chess.BLACK) # show black at bottom for clien