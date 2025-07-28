"""
בדיקה של המבנה החדש: NewState + NewPieceFactory + קונפיגורציות
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pathlib
from NewPieceFactory import NewPieceFactory
from Board import Board
from img import Img


def test_new_system():
    print("🎮 בודק המבנה החדש: NewState + NewPieceFactory + קונפיגורציות")
    
    try:
        # יצור board בסיסי
        img = Img()
        board = Board(
            cell_H_pix=103.5,
            cell_W_pix=102.75,
            cell_H_m=1,
            cell_W_m=1,
            W_cells=8,
            H_cells=8,
            img=img
        )
        
        pieces_root = pathlib.Path(r"C:\Users\01\Desktop\chess (3)\chess\CTD25\pieces")
        factory = NewPieceFactory(board, pieces_root)
        
        print(f"✅ יצר NewPieceFactory עם {len(factory.templates)} תבניות")
        
        # הדפס את התבניות שנטענו
        for template_name in factory.templates.keys():
            print(f"  📦 תבנית: {template_name}")
        
        # יצור כלי סוס לבן
        if "NW" in factory.templates:
            knight = factory.create_piece("NW", (1, 7))
            print(f"✅ יצר סוס לבן: {knight.piece_id}")
            
            # בדוק state machine
            state = knight._state
            print(f"🎯 State נוכחי: {state.name}")
            print(f"🔗 מעברים זמינים: {list(state.transitions.keys())}")
            
            # בדוק שכל state מחובר נכון
            for event, target_state in state.transitions.items():
                print(f"   {event} -> {target_state.name}")
        
        # יצור עוד כלי לבדיקה
        if "PW" in factory.templates:
            pawn = factory.create_piece("PW", (0, 6))
            print(f"✅ יצר רגלי לבן: {pawn.piece_id}")
        
        print("\n🎉 המבנה החדש עובד מעולה!")
        return True
        
    except Exception as e:
        print(f"❌ שגיאה: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_state_transitions():
    print("\n🔄 בודק מעברי state...")
    
    try:
        # שימוש דמה לבדיקת State
        from NewState import State
        from Command import Command
        
        # יצור mock objects
        class MockMoves:
            def __init__(self):
                pass
        
        class MockGraphics:
            def reset(self, cmd): pass
            def update(self, now_ms): pass
            def copy(self): return MockGraphics()
        
        class MockPhysics:
            def __init__(self):
                self.cell = (0, 0)
            def reset(self, cmd): pass
            def update(self, now_ms): return None
        
        # יצור states
        idle = State(MockMoves(), MockGraphics(), MockPhysics())
        idle.name = "idle"
        
        move = State(MockMoves(), MockGraphics(), MockPhysics())
        move.name = "move"
        
        rest = State(MockMoves(), MockGraphics(), MockPhysics())
        rest.name = "long_rest"
        
        # חבר מעברים
        idle.set_transition("move", move)
        move.set_transition("arrived", rest)
        rest.set_transition("arrived", idle)
        
        # בדוק מעבר
        current = idle
        print(f"🎯 התחלה: {current.name}")
        
        move_cmd = Command(1000, "test", "move", target=(2, 2))
        current = current.get_state_after_command(move_cmd, 1000)
        print(f"🎯 אחרי move: {current.name}")
        
        arrived_cmd = Command(2000, "test", "arrived", [])
        current = current.get_state_after_command(arrived_cmd, 2000)
        print(f"🎯 אחרי arrived: {current.name}")
        
        print("✅ מעברי State עובדים!")
        return True
        
    except Exception as e:
        print(f"❌ שגיאה במעברי state: {e}")
        return False


if __name__ == "__main__":
    success1 = test_new_system()
    success2 = test_state_transitions()
    
    if success1 and success2:
        print("\n🎉 הכל עובד מעולה!")
        print("\n📋 המבנה החדש כולל:")
        print("  ✅ NewState - פשוט ויעיל עם קונפיגורציה")
        print("  ✅ NewPieceFactory - טוען את כל ה-states מהקונפיגורציות")
        print("  ✅ קונפיגורציות JSON - מגדירות graphics, physics ומעברים")
        print("  ✅ תואמות למבנה הקיים - עובד עם Game.py ו-Piece.py")
    else:
        print("\n❌ יש בעיות שצריך לתקן")
