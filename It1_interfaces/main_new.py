from img import Img
from Board import Board
from Game import Game
from NewPieceFactory import NewPieceFactory  # השתמש במפעל החדש
import pathlib
import cv2


print("🎮 Starting chess game with new State Pattern...")
print("🎮 מתחיל משחק שחמט עם מבנה State חדש...")

# טען את התמונה
print("📸 Loading board image...")
img = Img()
img.read(r"c:\Users\01\Desktop\chess\CTD25\board.png")
print("📸 Image loaded:", img.img is not None)
if img.img is None:
    raise RuntimeError("Board image failed to load!")

# צור את הלוח עם התמונה
board = Board(
    cell_H_pix=103.5,
    cell_W_pix=102.75,
    cell_H_m=1,
    cell_W_m=1,
    W_cells=8,
    H_cells=8,
    img=img
)

pieces_root = pathlib.Path(r"c:\Users\01\Desktop\chess\CTD25\pieces")
factory = NewPieceFactory(board, pieces_root)  # השתמש במפעל החדש

start_positions = [
    # כלים שחורים בחלק העליון של הלוח (שורות 0-1)
    ("RB", (0, 0)), ("NB", (1, 0)), ("BB", (2, 0)), ("QB",  (3, 0)), ("KB",  (4, 0)), ("BB", (5, 0)), ("NB", (6, 0)), ("RB", (7, 0)),
    ("PB", (0, 1)), ("PB", (1, 1)), ("PB", (2, 1)), ("PB", (3, 1)), ("PB", (4, 1)), ("PB", (5, 1)), ("PB", (6, 1)), ("PB", (7, 1)),
    # כלים לבנים בחלק התחתון של הלוח (שורות 6-7)
    ("PW", (0, 6)), ("PW", (1, 6)), ("PW", (2, 6)), ("PW", (3, 6)), ("PW", (4, 6)), ("PW", (5, 6)), ("PW", (6, 6)), ("PW", (7, 6)),
    ("RW", (0, 7)), ("NW", (1, 7)), ("BW", (2, 7)), ("QW",  (3, 7)), ("KW",  (4, 7)), ("BW", (5, 7)), ("NW", (6, 7)), ("RW", (7, 7)),
]

pieces = []
piece_counters = {}  # Track count per piece type for unique IDs

# צור את המשחק עם התור
game = Game([], board)

print("🔧 Creating pieces with new State Pattern...")
for p_type, cell in start_positions:
    try:
        # Create unique piece ID by adding counter
        if p_type not in piece_counters:
            piece_counters[p_type] = 0
        unique_id = f"{p_type}{piece_counters[p_type]}"
        piece_counters[p_type] += 1
        
        piece = factory.create_piece(p_type, cell, game.user_input_queue)
        # Override the piece ID with unique ID
        piece.piece_id = unique_id
        # Update physics with the correct piece_id
        if hasattr(piece, '_state') and hasattr(piece._state, 'physics'):
            piece._state.physics.piece_id = unique_id
        pieces.append(piece)
        print(f"✅ יצר {unique_id} במיקום {cell}")
    except Exception as e:
        print(f"❌ בעיה עם {p_type}: {e}")

# עדכן את המשחק עם הכלים
game.pieces = pieces

print(f"🎮 Created {len(pieces)} pieces successfully!")
print("🎮 Starting game loop...")
game.run()
