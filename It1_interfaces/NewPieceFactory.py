import pathlib
from typing import Dict, Tuple
import json
from Board import Board
from GraphicsFactory import GraphicsFactory
from Moves import Moves
from PhysicsFactory import PhysicsFactory
from Piece import Piece
from NewState import State


class NewPieceFactory:
    def __init__(self, board: Board, pieces_root: pathlib.Path):
        self.board = board
        self.pieces_root = pieces_root
        self.physics_factory = PhysicsFactory(board)
        self.graphics_factory = GraphicsFactory()
        self.templates: Dict[str, State] = {}
        
        # טען את כל התבניות מראש
        self.generate_library()

    # Scan folders once, cache ready-made state machines -----------
    def generate_library(self):
        """סרוק את כל התיקיות ויצור תבניות state machine לכל כלי"""
        for sub in self.pieces_root.iterdir():
            if sub.is_dir():
                # "…/PW" etc.
                print(f"🔧 יוצר תבנית עבור {sub.name}")
                self.templates[sub.name] = self._build_state_machine(sub)

    def _build_state_machine(self, piece_dir: pathlib.Path) -> State:
        """בנה state machine לכלי ספציפי מהקונפיגורציה"""
        board_size = (self.board.W_cells, self.board.H_cells)
        cell_px = (self.board.cell_W_pix, self.board.cell_H_pix)

        states: Dict[str, State] = {}

        # ── scan every sub-folder inside "states" ────────────────────────────
        states_dir = piece_dir / "states"
        if not states_dir.exists():
            print(f"⚠️ תיקיית states לא נמצאה: {states_dir}")
            # יצור state בסיסי אם אין תיקיית states
            return self._create_default_state(piece_dir)

        for state_dir in states_dir.iterdir():
            if not state_dir.is_dir():  # skip stray files
                continue

            name = state_dir.name  # idle / move / jump / …
            print(f"  📁 עובד על state: {name}")

            # 1. config --------------------------------------------------------
            cfg_path = state_dir / "config.json"
            if cfg_path.exists() and cfg_path.read_text().strip():
                try:
                    cfg = json.loads(cfg_path.read_text())
                except json.JSONDecodeError as e:
                    print(f"⚠️ שגיאה בקריאת config עבור {name}: {e}")
                    cfg = {}
            else:
                cfg = {}

            # 2. moves ---------------------------------------------------------
            moves_path = state_dir / "moves.txt"
            if not moves_path.exists():
                # נסה את moves.txt מהתיקייה הראשית של הכלי
                moves_path = piece_dir / "moves.txt"
            
            if moves_path.exists():
                moves = Moves.from_file(moves_path)
            else:
                print(f"⚠️ moves.txt לא נמצא עבור {name}")
                moves = Moves(valid_moves=[])  # יצור moves ריק

            # 3. graphics & physics -------------------------------------------
            sprites_dir = state_dir / "sprites"
            graphics_cfg = cfg.get("graphics", {})
            physics_cfg = cfg.get("physics", {})

            graphics = self.graphics_factory.load(
                sprites_dir=sprites_dir,
                cfg=graphics_cfg,
                board=self.board
            )
            
            physics = self.physics_factory.create(
                start_cell=(0, 0),  # יוגדר מאוחר יותר
                cfg=physics_cfg,
                piece_id="template"
            )

            state = State(moves, graphics, physics)
            state.name = name
            states[name] = state

        if not states:
            print(f"⚠️ לא נמצאו states עבור {piece_dir.name}")
            return self._create_default_state(piece_dir)

        # ── wire transitions מקונפיגורציה ───────────────────────────────────
        for name, st in states.items():
            # Read per-state config again
            cfg_path = piece_dir / "states" / name / "config.json"
            if cfg_path.exists():
                try:
                    cfg = json.loads(cfg_path.read_text())
                    physics_cfg = cfg.get("physics", {})
                    
                    # קרא את המצב הבא מהקונפיגורציה
                    next_state_name = physics_cfg.get("next_state_when_finished")
                    if next_state_name and next_state_name in states:
                        st.set_transition("arrived", states[next_state_name])
                        print(f"  🔗 {name} --arrived--> {next_state_name}")
                        
                except json.JSONDecodeError:
                    pass

        # ── default external transitions -------------------------------------
        for st in states.values():
            if "move" in states:
                st.set_transition("move", states["move"])
            if "jump" in states:
                st.set_transition("jump", states["jump"])

        # החזר את state ההתחלתי (idle או הראשון שיש)
        return states.get("idle") or next(iter(states.values()))

    def _create_default_state(self, piece_dir: pathlib.Path) -> State:
        """יצור state בסיסי אם אין קונפיגורציה"""
        moves_path = piece_dir / "moves.txt"
        if moves_path.exists():
            moves = Moves.from_file(moves_path)
        else:
            moves = Moves(valid_moves=[])

        # graphics ו-physics בסיסיים
        graphics = self.graphics_factory.load(
            sprites_dir=piece_dir,
            cfg={},
            board=self.board
        )
        
        physics = self.physics_factory.create(
            start_cell=(0, 0),
            cfg={},
            piece_id="default"
        )

        state = State(moves, graphics, physics)
        state.name = "idle"
        return state

    def create_piece(self, p_type: str, cell: Tuple[int, int], game_queue=None) -> Piece:
        """יצור כלי חדש מהתבנית"""
        if p_type not in self.templates:
            print(f"⚠️ תבנית לא נמצאה עבור {p_type}")
            # נסה ליצור תבנית חדשה
            piece_dir = self.pieces_root / p_type
            if piece_dir.exists():
                self.templates[p_type] = self._build_state_machine(piece_dir)
            else:
                raise ValueError(f"לא נמצא כלי מסוג {p_type}")

        template_idle = self.templates[p_type]

        # יצור physics object במיקום האמיתי
        shared_phys = self.physics_factory.create(cell, {}, piece_id=p_type)

        # שכפל את כל ה-states עם physics משותף
        clone_map: Dict[State, State] = {}
        stack = [template_idle]
        
        while stack:
            orig = stack.pop()
            if orig in clone_map:
                continue

            # יצור עותק של הstate
            clone_map[orig] = State(
                moves=orig.moves,  # safe to share
                graphics=orig.graphics.copy() if hasattr(orig.graphics, 'copy') else orig.graphics,
                physics=shared_phys,  # ← SAME physics for all states
                game_queue=game_queue  # הוסף את game_queue
            )
            clone_map[orig].name = orig.name
            
            # הוסף למחסנית את כל המצבים המחוברים
            stack.extend(orig.transitions.values())

        # חבר מחדש את הtransitions
        for orig, clone in clone_map.items():
            for event, target in orig.transitions.items():
                if target in clone_map:
                    clone.set_transition(event, clone_map[target])

        piece_id = f"{p_type}_{cell[0]}_{cell[1]}"
        return Piece(piece_id=piece_id, init_state=clone_map[template_idle])
