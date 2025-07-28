"""
בדיקת המבנה החדש של State Pattern
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from StatePattern import IdleState, MoveState, JumpState, RestShortState, RestLongState
from StateContext import StateContext
from Command import Command


class MockGraphics:
    def __init__(self):
        self.current_state = "idle"
    
    def reset(self, cmd):
        if hasattr(cmd, 'params') and cmd.params and 'target_state' in cmd.params:
            self.current_state = cmd.params['target_state']
            print(f"🎨 MockGraphics: עבר למצב {self.current_state}")
    
    def update(self, now_ms):
        pass


class MockPhysics:
    def __init__(self, cell=(0, 0)):
        self.cell = cell
        self.moving = False
        self.move_start_time = None
        self.move_duration = 1000  # 1 שנייה
        self.target_cell = None
    
    def reset(self, cmd):
        if cmd.type == "move":
            self.moving = True
            self.move_start_time = getattr(cmd, 'timestamp', 0)
            self.target_cell = getattr(cmd, 'target', self.cell)
            print(f"🏃 MockPhysics: התחלת תנועה ל-{self.target_cell}")
        elif cmd.type == "jump":
            self.cell = getattr(cmd, 'target', self.cell)
            print(f"🦘 MockPhysics: קפיצה ל-{self.cell}")
    
    def update(self, now_ms):
        if self.moving and self.move_start_time:
            elapsed = now_ms - self.move_start_time
            if elapsed >= self.move_duration:
                # סיים תנועה
                self.cell = self.target_cell
                self.moving = False
                print(f"✅ MockPhysics: הגיע ל-{self.cell}")
                return Command(timestamp=now_ms, piece_id=None, type="arrived", params=None)
        return None


class MockMoves:
    def __init__(self):
        self.valid_moves = [(1, 0, None), (0, 1, None), (-1, 0, None), (0, -1, None)]


def test_idle_to_move():
    print("\n=== בדיקת מעבר מ-Idle ל-Move ===")
    
    moves = MockMoves()
    graphics = MockGraphics()
    physics = MockPhysics()
    
    context = StateContext(moves, graphics, physics)
    
    # בדוק שהתחלנו ב-idle
    assert context.state == "idle"
    print(f"✅ התחלנו במצב: {context.state}")
    
    # שלח פקודת move
    move_cmd = Command(timestamp=1000, piece_id="test", type="move", target=(2, 2))
    context.process_command(move_cmd)
    
    # בדוק שעברנו למצב move
    assert context.state == "move"
    print(f"✅ עברנו למצב: {context.state}")
    
    # עדכן כמה פעמים עד שהתנועה תסתיים
    for i in range(5):
        time_ms = 1000 + (i * 300)  # כל 300ms
        context.update(time_ms)
        print(f"⏰ עדכון {i+1}: מצב = {context.state}, זמן = {time_ms}")
        
        if context.state == "rest_long":
            break
    
    # בדוק שעברנו למצב rest_long
    assert context.state == "rest_long"
    print(f"✅ עברנו למצב מנוחה: {context.state}")


def test_idle_to_jump():
    print("\n=== בדיקת מעבר מ-Idle ל-Jump ===")
    
    moves = MockMoves()
    graphics = MockGraphics()
    physics = MockPhysics()
    
    context = StateContext(moves, graphics, physics)
    
    # שלח פקודת jump
    jump_cmd = Command(timestamp=2000, piece_id="test", type="jump", target=(3, 3))
    context.process_command(jump_cmd)
    
    # בדוק שעברנו למצב jump
    assert context.state == "jump"
    print(f"✅ עברנו למצב: {context.state}")
    
    # עדכן פעם אחת - קפיצה מיידית
    context.update(2100)
    
    # בדוק שעברנו למצב rest_short
    assert context.state == "rest_short"
    print(f"✅ עברנו למצב מנוחה: {context.state}")


def test_rest_timeout():
    print("\n=== בדיקת סיום מנוחה ===")
    
    moves = MockMoves()
    graphics = MockGraphics()
    physics = MockPhysics()
    
    context = StateContext(moves, graphics, physics)
    
    # עבור למצב rest_short
    jump_cmd = Command(timestamp=3000, piece_id="test", type="jump", target=(1, 1))
    context.process_command(jump_cmd)
    context.update(3100)  # עבור ל-rest_short
    
    assert context.state == "rest_short"
    print(f"✅ במצב מנוחה: {context.state}")
    
    # חכה שהמנוחה תסתיים (2 שניות = 2000ms)
    context.update(3000 + 2500)  # 2.5 שניות אחרי התחלת המנוחה
    
    # בדוק שחזרנו ל-idle
    assert context.state == "idle"
    print(f"✅ חזרנו למצב: {context.state}")


def test_reject_command_during_rest():
    print("\n=== בדיקת דחיית פקודות במהלך מנוחה ===")
    
    moves = MockMoves()
    graphics = MockGraphics()
    physics = MockPhysics()
    
    context = StateContext(moves, graphics, physics)
    
    # עבור למצב rest_short
    jump_cmd = Command(timestamp=4000, piece_id="test", type="jump", target=(1, 1))
    context.process_command(jump_cmd)
    context.update(4100)
    
    assert context.state == "rest_short"
    
    # נסה לשלוח פקודת move במהלך המנוחה
    rejected_cmd = Command(timestamp=4500, piece_id="test", type="move", target=(2, 2))
    context.process_command(rejected_cmd)
    
    # בדוק שנשארנו במצב rest_short
    assert context.state == "rest_short"
    print(f"✅ פקודה נדחתה, נשארנו במצב: {context.state}")


if __name__ == "__main__":
    try:
        test_idle_to_move()
        test_idle_to_jump()
        test_rest_timeout()
        test_reject_command_during_rest()
        
        print("\n🎉 כל הבדיקות עברו בהצלחה!")
        print("\n📋 סיכום המבנה החדש:")
        print("  - IdleState: מצב בסיסי שמקבל פקודות")
        print("  - MoveState: מצב תנועה עם אנימציה")
        print("  - JumpState: מצב קפיצה מיידית")
        print("  - RestShortState: מנוחה קצרה (2 שניות)")
        print("  - RestLongState: מנוחה ארוכה (5 שניות)")
        print("  - StateContext: מנהל את המעברים בין המצבים")
        
    except Exception as e:
        print(f"❌ שגיאה בבדיקה: {e}")
        import traceback
        traceback.print_exc()
