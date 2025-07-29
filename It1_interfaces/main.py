import logging
from img import Img
from Board import Board
from Game import Game
from PieceFactory import PieceFactory  # השתמש במפעל החדש
import pathlib
import cv2
import time
from Observer.Publisher import Publisher
from Observer.StartTracker import StartTracker
from Observer.GameStartEvent import GameStartEvent
from Observer.EventType import EventType

# הגדרת לוגגר
logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

logger.info("Starting chess game with New State Pattern")
logger.info("מתחיל משחק שחמט עם State + קונפיגורציות")

# צור publisher ו-start tracker
publisher = Publisher()
start_tracker = StartTracker()
publisher.subscribe(start_tracker)

# שלח event שהמשחק מתחיל
logger.info("Publishing game start event")
publisher.notify(GameStartEvent())

# טען את התמונה
logger.info("Loading board image")
img = Img()
img.read(pathlib.Path(__file__).parent.parent / "board.png")
logger.info("Image loaded successfully: %s", img.img is not None)
if img.img is None:
    logger.error("Board image failed to load!")
    start_tracker.close_logo_screen()
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

pieces_root = pathlib.Path(__file__).parent.parent / "pieces"
factory = PieceFactory(board, pieces_root)  # השתמש במפעל החדש

# עדכן את הלוגו במהלך הטעינה
if start_tracker.logo_displayed:
    cv2.waitKey(100)  # תן זמן להציג את הלוגו

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
        # Update physics with the correct piece_id - תיקון ל-State
        if hasattr(piece._state, 'physics'):
            piece._state.physics.piece_id = unique_id
        elif hasattr(piece._state, '_physics'):
            piece._state._physics.piece_id = unique_id
        pieces.append(piece)
        logger.info("Created piece %s at position %s", unique_id, cell)
    except Exception as e:
        logger.error("Problem creating piece %s: %s", p_type, e)

# עדכן את המשחק עם הכלים
game.pieces = pieces

# סגור את מסך הלוגו לפני תחילת המשחק
start_tracker.finish_loading()

logger.info("Starting game loop")
game.run()



