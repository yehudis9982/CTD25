from It1_interfaces.Command import Command

def test_command_creation():
    cmd = Command(
        timestamp=1234,
        piece_id="pawn1",
        type="Move",
        params=["e2", "e4"]
    )
    assert cmd.timestamp == 1234
    assert cmd.piece_id == "pawn1"
    assert cmd.type == "Move"
    assert cmd.params == ["e2", "e4"]