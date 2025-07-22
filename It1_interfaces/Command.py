from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional

@dataclass
class Command:
    timestamp: int          # ms since game start
    piece_id: str
    type: str               # "move" | "jump" | "reset" | ...
    params: Optional[List] = None  # payload (e.g. ["e2", "e4"]) 
    target: Optional[Tuple[int, int]] = None  # target position for moves 
