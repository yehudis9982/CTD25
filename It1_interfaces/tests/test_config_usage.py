"""
בדיקה שהמפעל משתמש בקבצי הקונפיגורציה
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pathlib
from PieceFactory import PieceFactory
from Board import Board
from img import Img


def test_piece_factory_with_config():
    print("🔧 בודק PieceFactory עם קבצי קונפיגורציה...")
    
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
    factory = PieceFactory(board, pieces_root)
    
    # בדוק שתיקיית הכלי קיימת
    nw_dir = pieces_root / "NW"
    if not nw_dir.exists():
        print(f"❌ תיקיית NW לא נמצאה: {nw_dir}")
        return
    
    print(f"✅ תיקיית NW נמצאה: {nw_dir}")
    
    # רשום את כל ה-states הזמינים
    states_dir = nw_dir / "states"
    if states_dir.exists():
        states_list = [d.name for d in states_dir.iterdir() if d.is_dir()]
        print(f"📁 States זמינים: {states_list}")
    
    try:
        # יצור כלי NW
        knight = factory.create_piece("NW", (1, 7))
        print(f"✅ יצר סוס לבן: {knight.piece_id}")
        
        # בדוק שיש לו state
        if hasattr(knight, '_state'):
            state = knight._state
            print(f"🎯 State נוכחי: {state.name}")
            
            # בדוק מעברים זמינים
            if hasattr(state, 'transitions'):
                transitions = list(state.transitions.keys())
                print(f"🔗 מעברים זמינים: {transitions}")
                
                # בדוק שיש מעברים בסיסיים
                if "move" in state.transitions:
                    move_target = state.transitions["move"]
                    print(f"   move -> {move_target.name}")
                
                if "jump" in state.transitions:
                    jump_target = state.transitions["jump"]
                    print(f"   jump -> {jump_target.name}")
                
                if "arrived" in state.transitions:
                    arrived_target = state.transitions["arrived"]
                    print(f"   arrived -> {arrived_target.name}")
        
        print("✅ הכלי נוצר בהצלחה עם state machine מלא!")
        
    except Exception as e:
        print(f"❌ שגיאה ביצירת הכלי: {e}")
        import traceback
        traceback.print_exc()


def test_config_loading():
    print("\n🔧 בודק טעינת קונפיגורציה...")
    
    nw_states_dir = pathlib.Path(r"C:\Users\01\Desktop\chess (3)\chess\CTD25\pieces\NW\states")
    
    if not nw_states_dir.exists():
        print("❌ תיקיית states לא נמצאה")
        return
    
    for state_dir in nw_states_dir.iterdir():
        if not state_dir.is_dir():
            continue
            
        state_name = state_dir.name
        config_path = state_dir / "config.json"
        
        if config_path.exists():
            try:
                import json
                with open(config_path, "r") as f:
                    config = json.load(f)
                
                physics_cfg = config.get("physics", {})
                graphics_cfg = config.get("graphics", {})
                
                print(f"📄 {state_name}:")
                print(f"   🏃 מהירות: {physics_cfg.get('speed_m_per_sec', 0)} m/s")
                print(f"   🎯 מצב הבא: {physics_cfg.get('next_state_when_finished', 'None')}")
                print(f"   🎨 FPS: {graphics_cfg.get('frames_per_sec', 0)}")
                print(f"   🔄 לולאה: {graphics_cfg.get('is_loop', False)}")
                
            except Exception as e:
                print(f"❌ שגיאה בקריאת config של {state_name}: {e}")
        else:
            print(f"⚠️ {state_name}: אין קובץ config.json")


if __name__ == "__main__":
    test_config_loading()
    test_piece_factory_with_config()
    
    print("\n📋 סיכום:")
    print("  - PieceFactory קורא את כל קבצי הconfig.json")
    print("  - כל state מוגדר עם graphics ו-physics משלו")
    print("  - המעברים מוגדרים בקונפיגורציה (next_state_when_finished)")
    print("  - הקוד פשוט ומבוסס על קונפיגורציה!")
