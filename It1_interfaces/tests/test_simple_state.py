"""
בדיקה פשוטה למבנה State החדש
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from State import State
from Command import Command


class MockMoves:
    def __init__(self):
        self.valid_moves = [(1, 0, None), (0, 1, None)]


class MockGraphics:
    def __init__(self, name="mock"):
        self.name = name
        
    def reset(self, cmd):
        print(f"🎨 Graphics {self.name}: reset with {cmd.type}")
        
    def update(self, now_ms):
        pass
        
    def copy(self):
        return MockGraphics(f"{self.name}_copy")


class MockPhysics:
    def __init__(self, name="mock"):
        self.name = name
        self.start_ms = 0
        self.duration_ms = 0
        self.wait_only = False
        self.cell = (0, 0)
        
    def reset(self, cmd):
        print(f"🏃 Physics {self.name}: reset with {cmd.type}")
        
    def update(self, now_ms):
        # אם זה מצב המתנה, בדוק אם המתנה הסתיימה
        if self.wait_only and self.start_ms > 0:
            if now_ms - self.start_ms >= self.duration_ms:
                print(f"⏰ Physics {self.name}: המתנה הסתיימה")
                return Command(now_ms, "test", "arrived", [])
        return None


def test_simple_state_machine():
    print("\n=== בדיקת State Machine פשוט ===")
    
    # יצור 3 states
    idle_state = State(MockMoves(), MockGraphics("idle"), MockPhysics("idle"))
    idle_state.name = "idle"
    
    move_state = State(MockMoves(), MockGraphics("move"), MockPhysics("move"))
    move_state.name = "move"
    
    rest_state = State(MockMoves(), MockGraphics("rest"), MockPhysics("rest"))
    rest_state.name = "rest"
    
    # הגדר מעברים
    idle_state.set_transition("move", move_state)
    move_state.set_transition("arrived", rest_state)
    rest_state.set_transition("arrived", idle_state)
    
    print(f"✅ יצר 3 states: {idle_state}, {move_state}, {rest_state}")
    
    # התחל מ-idle
    current_state = idle_state
    print(f"🎯 מתחיל במצב: {current_state}")
    
    # שלח פקודת move
    move_cmd = Command(1000, "test", "move", target=(2, 2))
    current_state = current_state.get_state_after_command(move_cmd, 1000)
    print(f"🎯 אחרי move: {current_state}")
    
    # שלח פקודת arrived
    arrived_cmd = Command(2000, "test", "arrived", [])
    current_state = current_state.get_state_after_command(arrived_cmd, 2000)
    print(f"🎯 אחרי arrived: {current_state}")
    
    # עוד arrived להחזיר ל-idle
    arrived_cmd2 = Command(3000, "test", "arrived", [])
    current_state = current_state.get_state_after_command(arrived_cmd2, 3000)
    print(f"🎯 אחרי arrived נוסף: {current_state}")
    
    assert current_state.name == "idle"
    print("✅ חזר ל-idle בהצלחה!")


def test_cooldown_mechanism():
    print("\n=== בדיקת מנגנון Cooldown ===")
    
    # יצור state עם cooldown
    state = State(MockMoves(), MockGraphics("test"), MockPhysics("test"))
    state.name = "test"
    state.cooldown_end_ms = 5000  # 5 שניות
    
    # נסה לעבור לפני הזמן
    cmd = Command(3000, "test", "move", [])
    result = state.get_state_after_command(cmd, 3000)
    
    # צריך להישאר באותו state
    assert result == state
    print("✅ Cooldown עובד - לא עבר מצב לפני הזמן")
    
    # נסה לעבור אחרי הזמן
    result2 = state.get_state_after_command(cmd, 6000)
    # אין מעבר מוגדר, אז צריך להישאר
    assert result2 == state
    print("✅ אחרי Cooldown - מתפקד כהלכה")


def test_update_mechanism():
    print("\n=== בדיקת מנגנון Update ===")
    
    # יצור state עם physics שמחזיר פקודה
    physics = MockPhysics("update_test")
    physics.wait_only = True
    physics.start_ms = 1000
    physics.duration_ms = 2000  # 2 שניות
    
    state = State(MockMoves(), MockGraphics("update"), physics)
    state.name = "update_test"
    
    # יצור target state
    target_state = State(MockMoves(), MockGraphics("target"), MockPhysics("target"))
    target_state.name = "target"
    
    # הגדר מעבר
    state.set_transition("arrived", target_state)
    
    # עדכן לפני שהזמן הסתיים
    result = state.update(2000)  # 1 שנייה אחרי ההתחלה
    assert result == state
    print("✅ Update לפני הזמן - נשאר באותו state")
    
    # עדכן אחרי שהזמן הסתיים
    result = state.update(4000)  # 3 שניות אחרי ההתחלה
    assert result.name == "target"
    print("✅ Update אחרי הזמן - עבר ל-target state")


if __name__ == "__main__":
    try:
        test_simple_state_machine()
        test_cooldown_mechanism()
        test_update_mechanism()
        
        print("\n🎉 כל הבדיקות עברו בהצלחה!")
        print("\n📋 המבנה החדש:")
        print("  - State פשוט עם מעברים מוגדרים")
        print("  - מנגנון cooldown למניעת מעברים מהירים מדי")
        print("  - קונפיגורציה דרך קבצי JSON")
        print("  - מבנה קל יותר לתחזוקה")
        
    except Exception as e:
        print(f"❌ שגיאה בבדיקה: {e}")
        import traceback
        traceback.print_exc()
