# CLI Chess — Multiplayer over Sockets
 
A polished, cross-platform, command-line multiplayer chess project written in Python. This repo contains a networked host/client pair, full chess rules (via python-chess), a tidy CLI board renderer with ANSI coloring, PGN export at game end, and an optional PNG exporter of the final position.

Files

README.md — usage and quick start (this file also serves as the top-level docs)
server.py — host program (waits for a connection, runs the game as White by default)
client.py — client program (connects to the host and plays Black by default)
shared.py — shared utilities: network protocol, message helpers
ui.py — CLI board renderer, move prompt, ANSI colors
export_image.py — optional: generate a PNG of the final board position (uses Pillow)
requirements.txt — python-chess and Pillow

Quick features

Two-player networked chess over TCP sockets.

Legal move checking and full rules (via python-chess).

SAN (algebraic) and UCI move input supported; input convenience for the CLI.

PGN generation & writing when the game ends (file name includes timestamp).

Optional final-board PNG export (approximate chess.com color palette, Unicode pieces matching typical Staunton shapes).

Cross-platform: runs on Linux, Windows, and iOS (in Python environments like Pythonista/StaSh or a terminal app that supports Python). Use the same commands on all platforms.

How to run (quick)

Create a virtualenv (optional) and install dependencies:

python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt

On the host machine (player hosting the game):

python server.py --port 5000 [--ai] [--pairing-code] [--mode {standard|powerup|random_event}]

*   `--ai`: Play against a minimal AI opponent (offline).
*   `--pairing-code`: Enable a pairing code for a more secure connection. The host will display a code that the client must enter.
*   `--mode`: Select game mode. Options: `standard` (default), `powerup`, `random_event`.

Host waits for a connection (unless `--ai` is used) and will be White by default.

On the connecting machine (client):

python client.py --host HOST_IP --port 5000 [--pairing-code] [--mode {standard|powerup|random_event}]

*   `--pairing-code`: If the host is using a pairing code, you must also use this flag and enter the code when prompted.
*   `--mode`: Select game mode. Must match the host's selected mode.

Play in the terminal. Commands are shown in the CLI (move input, resign, offer draw, save, export_image).

### Game Modes

**Standard Chess:** The classic game of chess.

**Power-Up Chess:**
Players can earn and activate special abilities to influence the game.
*   **Earning Power-Ups:** Power-ups are earned randomly upon capturing an opponent's piece.
*   **Activating Power-Ups:** Use the command `activate <index> [args]` where `<index>` is the number next to the power-up in your inventory, and `[args]` are any additional parameters required by the power-up (e.g., square names for Piece Swap or Teleport).
*   **Available Power-Ups:**
    *   **Extra Move:** Make two moves in a single turn.
    *   **Piece Swap:** Swap the positions of two of your non-pawn pieces.
    *   **Teleport:** Move a non-pawn piece to any empty square.
    *   **Shield:** Protects a chosen piece from capture for one opponent's turn.
    *   **Pawn Promotion:** Instantly promote one of your pawns to a Queen.

**Random Event Chess:**
The game is spiced up with unpredictable events that can change the board state. Events trigger randomly every few turns.
*   **Possible Events:**
    *   **Piece Transformation:** A random pawn transforms into a random non-pawn piece.
    *   **Board Rotation:** The entire board rotates 180 degrees.
    *   **Gravity:** All pieces "fall" to the lowest possible rank in their file.
    *   **King Swap:** The positions of the two kings are swapped (reverted if it causes immediate check).


How to build executables

You can bundle the server and client into single executables for easier distribution. This requires PyInstaller.

1.  Install PyInstaller:
    ```bash
    pip install pyinstaller
    ```
2.  Run the build script:
    ```bash
    python build_scripts/build.py
    ```
    This will create `server` and `client` executables (or `server.exe` and `client.exe` on Windows) in a new `dist/` directory.
3.  Run the executables:
    ```bash
    ./dist/server --port 5000
    ./dist/client --host HOST_IP --port 5000
    ```
    (Adjust commands for Windows, e.g., `.\dist\server.exe`)



Notes about pieces & board coloring

CLI uses Unicode chess piece glyphs (standard blocks: ♔ ♕ ♖ ♗ ♘ ♙ for White and ♚ ♛ ♜ ♝ ♞ ♟ for Black). These visually resemble the default pieces used by many web chess clients, including chess.com.

Board coloring for the CLI and PNG exporter approximates the common light/dark chessboard palette (light #f0d9b5, dark #b58863), which matches many site defaults and gives a familiar look.


Quick next steps for you (summary):

Install dependencies from the generated requirements.txt (python-chess, Pillow).

Run python server.py --port 5000 on the host machine.

Run python client.py --host <HOST_IP> --port 5000 on the opponent machine.

Play in the terminal; supported commands include resign, offer draw, save (writes PGN), and export_image (writes a PNG of the final position). Moves may be entered as UCI (e2e4) or SAN (Nf3).

Notes:

The CLI uses Unicode pieces (♔♕♖♗♘♙ / ♚♛♜♝♞♟) that visually match default Staunton-style pieces similar to chess.com. The CLI + PNG exporter use an approximate chess.com-like board palette (light #f0d9b5, dark #b58863).

Cross-platform: works on Linux, Windows, and iOS terminal environments that support Python. On older Windows consoles you may need to enable ANSI colors or use Windows Terminal / PowerShell.