#!/usr/bin/env python3
"""
בדיקה מהירה להכתרת חייל במשחק האמיתי.
נדמה תנועה של חייל לבן לשורה 0.
"""

import time
import pathlib
from Board import Board
from Game import Game
from PieceFactory import PieceFactory
from Command import Command
from img import Img

def test_real_game_promotion():
    print("👑 בדיקת הכתרה במשחק אמיתי...")
    
    # יצירת לוח ומפעל כלים כמו במשחק האמיתי
    img = Img()
    img.read(r"c:\Users\01\Desktop\chess\CTD25\board.png")
    
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
    
    # צור משחק
    game = Game([], board)
    
    # צור חייל לבן ב-(1,1) (קרוב לשורה 0)
    pawn = factory.create_piece("PW", (1, 1), game.user_input_queue)
    pawn.piece_id = "PW0"  # ID כמו במשחק האמיתי
    pawn._state._physics.piece_id = "PW0"
    
    # הוסף את הכלי למשחק
    game.pieces = [pawn]
    
    print(f"🔵 חייל נוצר במיקום: {pawn._state._physics.cell} עם ID: {pawn.piece_id}")
    print(f"📋 כלים לפני הכתרה: {[p.piece_id for p in game.pieces]}")
    
    # נדמה תנועת חייל דרך ה-Game._move_piece (כמו במשחק האמיתי)
    print("🎯 מזיז חייל צעד אחד קדימה...")
    game._move_piece(pawn, 1, 0, 1)  # מ-(1,1) ל-(1,0) - אותה עמודה, שורה למעלה
    
    # המתן לתנועה ולהכתרה
    print("⏱️ מחכה לתנועה ולהכתרה...")
    start_time = time.time()
    while time.time() - start_time < 7:  # 7 שניות
        # עדכן את הכלי
        current_time = int(time.time() * 1000)
        for piece in game.pieces[:]:  # copy the list since it might change
            piece.update(current_time)
        
        # עבד את התור
        while not game.user_input_queue.empty():
            cmd = game.user_input_queue.get()
            print(f"🔄 מעבד פקודה: {cmd.type} עבור {cmd.piece_id}")
            game._process_input(cmd)
        time.sleep(0.1)
    
    print(f"📋 כלים אחרי תנועה: {[p.piece_id for p in game.pieces]}")
    
    # בדוק תוצאה
    piece_ids = [p.piece_id for p in game.pieces]
    has_queen = any("QW" in piece_id for piece_id in piece_ids)
    has_original_pawn = "PW0" in piece_ids
    
    if has_queen and not has_original_pawn:
        print("✅ הכתרה הצליחה! חייל הפך למלכה.")
    elif has_original_pawn and not has_queen:
        print("❌ הכתרה נכשלה! החייל לא הפך למלכה.")
    else:
        print(f"🤔 מצב מוזר: יש מלכה={has_queen}, יש חייל מקורי={has_original_pawn}")
    
    return has_queen and not has_original_pawn

if __name__ == "__main__":
    success = test_real_game_promotion()
    print("🏁 סיום בדיקת הכתרה")
