#!/usr/bin/env python3

from PieceFactory import PieceFactory
from Board import Board
from img import Img
import pathlib
import json

def test_state_transitions():
    print("Testing state transitions...")
    
    # צור board פשוט
    img = Img()
    board = Board(103.5, 102.75, 1, 1, 8, 8, img)
    pieces_root = pathlib.Path(__file__).parent.parent / "pieces"
    factory = PieceFactory(board, pieces_root)
    
    # בדוק קונפיגורציה של jump במיוחד
    jump_config_path = pieces_root / "PW" / "states" / "jump" / "config.json"
    print(f"\nChecking jump config at: {jump_config_path}")
    if jump_config_path.exists():
        try:
            content = jump_config_path.read_text(encoding='utf-8-sig').strip()
            print(f"Content: {repr(content[:100])}...")
            config = json.loads(content)
            print(f"Parsed config: {config}")
            next_state = config.get("physics", {}).get("next_state_when_finished")
            print(f"Next state should be: {next_state}")
        except Exception as e:
            print(f"Error reading config: {e}")
    
    # בדוק מצב של כלי ספציפי
    pawn_template = factory.templates.get('PW')
    if pawn_template:
        print('\n✅ PW template found')
        print(f'Name: {pawn_template.name}')
        print(f'Transitions: {pawn_template.transitions}')
        
        # בדוק אם יש מעבר מ-jump
        if 'jump' in pawn_template.transitions:
            jump_state = pawn_template.transitions['jump']
            print(f'Jump state name: {jump_state.name}')
            print(f'Jump state transitions: {jump_state.transitions}')
            
            # בדוק short_rest
            if 'arrived' in jump_state.transitions:
                short_rest_state = jump_state.transitions['arrived']
                print(f'Short rest state name: {short_rest_state.name}')
                print(f'Short rest transitions: {short_rest_state.transitions}')
        else:
            print('❌ No "jump" transition found!')
    else:
        print('❌ No PW template found')

if __name__ == "__main__":
    test_state_transitions()
