from img import Img
from Board import Board
from Game import Game
from PieceFactory import PieceFactory
import pathlib
import cv2

print("🎮 Starting chess game...")
print("🎮 מתחיל משחק שחמט...")

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
factory = PieceFactory(board, pieces_root)

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
        piece._state._physics.piece_id = unique_id
        pieces.append(piece)
    except Exception as e:
        print(f"בעיה עם {p_type}: {e}")

# עדכן את המשחק עם הכלים
game.pieces = pieces


display_board = board.clone()
now = 0
for piece in pieces:
    piece.draw_on_board(display_board, now)



cv2.imshow("Chess - מצב התחלתי", display_board.img.img)
cv2.waitKey(0)
cv2.destroyAllWindows()        
# הצג את הלוח בלבד

# cv2.imshow("Chess Board", board.img.img)
# cv2.waitKey(0)
# cv2.destroyAllWindows()


# # ואז תעביר את board ל-Game
game.run()

# # 2. צור את הלוח
# board = Board(
#     cell_H_pix=80,
#     cell_W_pix=80,
#     cell_H_m=1,
#     cell_W_m=1,
#     W_cells=8,
#     H_cells=8,
#     img=img
# )





# # 3. צור את PieceFactory
# pieces_root = pathlib.Path("E:/chess/CTD25/pieces")
# factory = PieceFactory(board, pieces_root)

# # 4. בנה את הכלים עם מיקומים התחלתיים (דוגמה)
# start_positions = {
#     "BB": (0, 0),
#     "PW": (7, 7),
#     # הוסיפי עוד כלים ומיקומים לפי הצורך
# }
# pieces = []
# for p_type, cell in start_positions.items():
#     piece = factory.create_piece(p_type, cell)
#     pieces.append(piece)



# display_board = board.clone()

# # ציור כל החיילים על הלוח
# now = 0
# for piece in pieces:
#     piece.draw_on_board(display_board, now)

# # הצג את התמונה
# import cv2
# cv2.imshow("Chess - מצב התחלתי", display_board.img.img)
# cv2.waitKey(0)
# cv2.destroyAllWindows()
# # 5. צור והרץ את המשחק

# # game = Game(pieces, board)
game.run()

# print("display_board.img:", display_board.img)
# print("display_board.img.img:", display_board.img.img)
