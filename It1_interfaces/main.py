from CTD25.It1_interfaces.img import Img
from CTD25.It1_interfaces.Board import Board
from CTD25.It1_interfaces.Game import Game
from CTD25.It1_interfaces.PieceFactory import PieceFactory
import pathlib
import cv2

# טען את התמונה
img = Img()
img.read("E:/chess/CTD25/board.png")
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

pieces_root = pathlib.Path("E:/chess/CTD25/pieces")
factory = PieceFactory(board, pieces_root)

start_positions = [
    ("RB", (0, 0)), ("NB", (0, 1)), ("BB", (0, 2)), ("QB",  (0, 3)), ("KB",  (0, 4)), ("BB", (0, 5)), ("NB", (0, 6)), ("RB", (0, 7)),
    ("PB", (1, 0)), ("PB", (1, 1)), ("PB", (1, 2)), ("PB", (1, 3)), ("PB", (1, 4)), ("PB", (1, 5)), ("PB", (1, 6)), ("PB", (1, 7)),
    ("RW", (7, 0)), ("NW", (7, 1)), ("BW", (7, 2)), ("QW",  (7, 3)), ("KW",  (7, 4)), ("BW", (7, 5)), ("NW", (7, 6)), ("RW", (7, 7)),
    ("PW", (6, 0)), ("PW", (6, 1)), ("PW", (6, 2)), ("PW", (6, 3)), ("PW", (6, 4)), ("PW", (6, 5)), ("PW", (6, 6)), ("PW", (6, 7)),
]

pieces = []
for p_type, cell in start_positions:
    try:
        piece = factory.create_piece(p_type, cell)
        pieces.append(piece)
    except Exception as e:
        print(f"בעיה עם {p_type}: {e}")


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
game = Game(pieces, board)











# from CTD25.It1_interfaces.Board import Board
# from CTD25.It1_interfaces.img import Img
# from CTD25.It1_interfaces.PieceFactory import PieceFactory
# from CTD25.It1_interfaces.Game import Game
# import pathlib

# # 1. טען את תמונת הלוח
# img = Img()
# img.read("E:/chess/CTD25/board.png")
# if img.img is None:
#     raise RuntimeError("Board image failed to load!")

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