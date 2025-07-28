#!/usr/bin/env python3
"""
בדיקה מיוחדת למקשי WASD עם שיטות זיהוי מרובות
"""
import cv2
import time

def test_wasd_keys():
    print("=== בדיקת מקשי WASD עם שיטות זיהוי מרובות ===")
    print("לחץ על W, A, S, D, רווח, או ESC ליציאה")
    
    # יצירת חלון ריק
    img = cv2.imread("board.png") if cv2.haveImageReader("board.png") else None
    if img is None:
        import numpy as np
        img = np.zeros((400, 400, 3), dtype=np.uint8)
        cv2.putText(img, "WASD Test", (150, 200), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
    
    cv2.imshow("WASD Test", img)
    cv2.setWindowProperty("WASD Test", cv2.WND_PROP_TOPMOST, 1)
    
    print("\nמתחיל בדיקת מקשים...")
    
    detected_keys = set()
    
    while True:
        # שיטה 1: waitKey רגיל
        key1 = cv2.waitKey(10) & 0xFF
        
        # שיטה 2: waitKey עם זמן קצר יותר
        key2 = cv2.waitKey(1) & 0xFF
        
        # שיטה 3: קריאה ללא מסכה
        key3_raw = cv2.waitKey(5)
        key3 = key3_raw & 0xFF if key3_raw != -1 else 255
        
        keys_to_check = [key1, key2, key3]
        
        for key in keys_to_check:
            if key != 255 and key not in detected_keys:  # מקש חדש נלחץ
                detected_keys.add(key)
                
                print(f"\n🔍 מקש זוהה: {key}")
                
                # בדיקה ישירה של קודי WASD
                if key == 119:  # w
                    print("✅ W זוהה! (קוד 119)")
                elif key == 97:  # a
                    print("✅ A זוהה! (קוד 97)")
                elif key == 115:  # s
                    print("✅ S זוהה! (קוד 115)")
                elif key == 100:  # d
                    print("✅ D זוהה! (קוד 100)")
                elif key == 32:  # space
                    print("✅ רווח זוהה! (קוד 32)")
                elif key == 27:  # escape
                    print("✅ ESC זוהה! (קוד 27) - יוצא...")
                    cv2.destroyAllWindows()
                    return
                else:
                    # המרה לתו אם אפשר
                    if 32 <= key <= 126:
                        char = chr(key)
                        print(f"   תו: '{char}'")
                        
                        # בדיקה נוספת של WASD
                        if char.lower() in ['w', 'a', 's', 'd']:
                            print(f"🎯 WASD זוהה דרך המרת תו: '{char.lower()}'")
                    else:
                        print(f"   מקש מיוחד: {key}")
                
                # הצגת כל המקשים שזוהו עד כה
                print(f"מקשים שזוהו עד כה: {sorted(detected_keys)}")
        
        time.sleep(0.01)  # מניעת עומס CPU

if __name__ == "__main__":
    test_wasd_keys()
