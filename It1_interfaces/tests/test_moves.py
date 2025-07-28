import pathlib
import tempfile
from CTD25.It1_interfaces.Moves import Moves

def make_moves_file(lines):
    tmp = tempfile.NamedTemporaryFile("w+", delete=False, encoding="utf-8")
    tmp.write("\n".join(lines))
    tmp.flush()
    return pathlib.Path(tmp.name)

def test_moves_basic():
    # כללי תנועה: ימינה, למטה, שמאלה, למעלה
    lines = ["0 1", "1 0", "0 -1", "-1 0"]
    path = make_moves_file(lines)
    moves = Moves(path, (3, 3))
    # מהמרכז אפשר לזוז לכל כיוון
    assert set(moves.get_moves(1, 1)) == {(1, 2), (2, 1), (1, 0), (0, 1)}
    # מהפינה (0,0) אפשר רק ימינה ולמטה
    assert set(moves.get_moves(0, 0)) == {(0, 1), (1, 0)}

def test_moves_with_comments_and_blanks():
    lines = [
        "# זה קובץ בדיקה",
        "",
        "1 0",
        "0 1",
        "   ",
        "# עוד הערה",
        "-1 0"
    ]
    path = make_moves_file(lines)
    moves = Moves(path, (2, 2))
    # מהתא (1,0) אפשר לעלות למעלה או ימינה
    assert set(moves.get_moves(1, 0)) == {(0, 0), (1, 1)}

def test_moves_out_of_bounds():
    lines = ["2 0", "0 2", "-2 0", "0 -2"]
    path = make_moves_file(lines)
    moves = Moves(path, (3, 3))
    # מהמרכז (1,1) אפשר לזוז לכל קצה
    assert set(moves.get_moves(1, 1)) == {(1, 3), (3, 1), (1, -1), (-1, 1)} & {(0, 1), (2, 1), (1, 0), (1, 2)}
    # בפועל, רק (1,3) ו-(3,1) מחוץ ללוח, אז לא יופיעו
    assert set(moves.get_moves(1, 1)) == {(1, -1), (-1, 1)} & set()  # לא חוקיים
    # לכן התוצאה צריכה להיות ריקה
    assert set(moves.get_moves(0, 0)) == {(2, 0), (0, 2)}
