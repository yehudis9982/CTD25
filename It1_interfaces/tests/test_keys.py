import cv2
import numpy as np

def test_keyboard():
    """Test keyboard input detection"""
    print("🔍 Testing keyboard input detection...")
    print("Press keys to test - ESC to exit")
    print()
    print("Expected keys:")
    print("- WASD for movement")
    print("- Enter for selection")
    print("- Numbers 8,2,4,6 for movement")
    print("- Space for selection")
    print()
    
    # Create a simple test window
    img = np.zeros((400, 600, 3), dtype=np.uint8)
    cv2.putText(img, "Key Test - Press Keys", (50, 200), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
    cv2.imshow("Keyboard Test", img)
    
    while True:
        key = cv2.waitKey(30)
        
        if key != -1:  # Key pressed
            print(f"\n🔥 KEY DETECTED: {key}")
            
            # Character keys
            if 32 <= key <= 126:
                char = chr(key)
                print(f"   Character: '{char}'")
                
                # Test specific keys
                if char.lower() in 'wasd':
                    print(f"   ✅ WASD detected: {char.upper()}")
                elif char in '8246':
                    print(f"   ✅ Number detected: {char}")
                elif char == ' ':
                    print(f"   ✅ SPACE detected")
                else:
                    print(f"   ❓ Other character: {char}")
            else:
                print(f"   Special key code: {key}")
                
                # Test Enter variants
                if key in [10, 13, 39, 226, 249]:
                    print(f"   ✅ ENTER variant detected: {key}")
                elif key == 27:
                    print(f"   ✅ ESC detected - exiting...")
                    break
                else:
                    print(f"   ❓ Unknown special key: {key}")
        
        # Update display
        cv2.imshow("Keyboard Test", img)
    
    cv2.destroyAllWindows()
    print("\n✅ Keyboard test completed!")

if __name__ == "__main__":
    test_keyboard()
