import pytest
import sys
import os
from datetime import datetime

# Add the project root to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from MoveLogger import MoveLogger
from MoveMadeEvent import MoveMadeEvent


class TestMoveMadeEvent:
    """Test suite for MoveMadeEvent class"""
    
    def test_move_made_event_creation(self):
        """Test creating a MoveMadeEvent"""
        event = MoveMadeEvent("white", (0, 0), (1, 1))
        
        assert event.type == "move_made"
        assert event.data["piece_type"] == "white"
        assert event.data["start_position"] == (0, 0)
        assert event.data["end_position"] == (1, 1)
        assert event.data["timestamp"] is None
    
    def test_move_made_event_with_timestamp(self):
        """Test creating a MoveMadeEvent with timestamp"""
        timestamp = datetime.now()
        event = MoveMadeEvent("black", (2, 3), (4, 5), timestamp)
        
        assert event.type == "move_made"
        assert event.data["piece_type"] == "black"
        assert event.data["start_position"] == (2, 3)
        assert event.data["end_position"] == (4, 5)
        assert event.data["timestamp"] == timestamp
    
    def test_move_made_event_inheritance(self):
        """Test that MoveMadeEvent inherits from Event"""
        from Event import Event
        event = MoveMadeEvent("white", (0, 0), (1, 1))
        assert isinstance(event, Event)


class TestMoveLogger:
    """Test suite for MoveLogger class"""
    
    def setup_method(self):
        """Setup a fresh MoveLogger instance for each test"""
        self.logger = MoveLogger()
    
    def test_move_logger_initialization(self):
        """Test MoveLogger initialization"""
        assert self.logger.moves == {"white": [], "black": []}
    
    def test_move_logger_inheritance(self):
        """Test that MoveLogger inherits from Subscriber"""
        from Subscriber import Subscriber
        assert isinstance(self.logger, Subscriber)
        assert hasattr(self.logger, 'update')
    
    def test_update_with_move_made_event_no_timestamp(self):
        """Test updating logger with MoveMadeEvent without timestamp"""
        event = MoveMadeEvent("white", (0, 0), (1, 1))
        
        self.logger.update(event)
        
        moves = self.logger.get_moves("white")
        assert len(moves) == 1
        assert moves[0]["time"] == "unknown"
        assert moves[0]["move"] == "white from (0, 0) to (1, 1)"
    
    def test_update_with_move_made_event_with_timestamp(self):
        """Test updating logger with MoveMadeEvent with timestamp"""
        timestamp = datetime(2025, 1, 1, 12, 30, 45)
        event = MoveMadeEvent("black", (2, 3), (4, 5), timestamp)
        
        self.logger.update(event)
        
        moves = self.logger.get_moves("black")
        assert len(moves) == 1
        assert moves[0]["time"] == "12:30:45"
        assert moves[0]["move"] == "black from (2, 3) to (4, 5)"
    
    def test_update_with_non_move_event(self):
        """Test that non-MoveMadeEvent events are ignored"""
        # Create a mock event that's not a MoveMadeEvent
        mock_event = type('MockEvent', (), {
            'type': 'other_event',
            'data': {'some': 'data'}
        })()
        
        self.logger.update(mock_event)
        
        # Should not add anything to moves
        assert self.logger.get_moves("white") == []
        assert self.logger.get_moves("black") == []
    
    def test_multiple_moves_same_player(self):
        """Test logging multiple moves for the same player"""
        timestamp1 = datetime(2025, 1, 1, 12, 0, 0)
        timestamp2 = datetime(2025, 1, 1, 12, 5, 0)
        
        event1 = MoveMadeEvent("white", (0, 0), (1, 1), timestamp1)
        event2 = MoveMadeEvent("white", (1, 1), (2, 2), timestamp2)
        
        self.logger.update(event1)
        self.logger.update(event2)
        
        moves = self.logger.get_moves("white")
        assert len(moves) == 2
        assert moves[0]["time"] == "12:00:00"
        assert moves[0]["move"] == "white from (0, 0) to (1, 1)"
        assert moves[1]["time"] == "12:05:00"
        assert moves[1]["move"] == "white from (1, 1) to (2, 2)"
    
    def test_multiple_moves_different_players(self):
        """Test logging moves for different players"""
        event1 = MoveMadeEvent("white", (0, 0), (1, 1))
        event2 = MoveMadeEvent("black", (7, 7), (6, 6))
        
        self.logger.update(event1)
        self.logger.update(event2)
        
        white_moves = self.logger.get_moves("white")
        black_moves = self.logger.get_moves("black")
        
        assert len(white_moves) == 1
        assert len(black_moves) == 1
        assert white_moves[0]["move"] == "white from (0, 0) to (1, 1)"
        assert black_moves[0]["move"] == "black from (7, 7) to (6, 6)"
    
    def test_get_moves_empty_player(self):
        """Test getting moves for player with no moves"""
        moves = self.logger.get_moves("white")
        assert moves == []
        
        moves = self.logger.get_moves("black")
        assert moves == []
    
    def test_get_moves_nonexistent_player(self):
        """Test getting moves for non-existent player color"""
        # This will likely raise a KeyError due to the current implementation
        with pytest.raises(KeyError):
            self.logger.get_moves("red")


class TestMoveLoggerIntegration:
    """Integration tests for MoveLogger and MoveMadeEvent"""
    
    def setup_method(self):
        """Setup for integration tests"""
        self.logger = MoveLogger()
    
    def test_full_game_sequence(self):
        """Test a sequence of moves like in a real game"""
        # Simulate a few moves in a chess game
        moves_sequence = [
            ("white", (1, 4), (3, 4), datetime(2025, 1, 1, 10, 0, 0)),  # Pawn e2-e4
            ("black", (6, 4), (4, 4), datetime(2025, 1, 1, 10, 1, 0)),  # Pawn e7-e5
            ("white", (0, 6), (2, 5), datetime(2025, 1, 1, 10, 2, 0)),  # Knight g1-f3
            ("black", (7, 1), (5, 2), datetime(2025, 1, 1, 10, 3, 0)),  # Knight b8-c6
        ]
        
        # Log all moves
        for player, start, end, timestamp in moves_sequence:
            event = MoveMadeEvent(player, start, end, timestamp)
            self.logger.update(event)
        
        # Check white moves
        white_moves = self.logger.get_moves("white")
        assert len(white_moves) == 2
        assert white_moves[0]["time"] == "10:00:00"
        assert white_moves[0]["move"] == "white from (1, 4) to (3, 4)"
        assert white_moves[1]["time"] == "10:02:00"
        assert white_moves[1]["move"] == "white from (0, 6) to (2, 5)"
        
        # Check black moves
        black_moves = self.logger.get_moves("black")
        assert len(black_moves) == 2
        assert black_moves[0]["time"] == "10:01:00"
        assert black_moves[0]["move"] == "black from (6, 4) to (4, 4)"
        assert black_moves[1]["time"] == "10:03:00"
        assert black_moves[1]["move"] == "black from (7, 1) to (5, 2)"
    
    def test_mixed_events(self):
        """Test logger with mix of MoveMadeEvent and other events"""
        # Create MoveMadeEvent
        move_event = MoveMadeEvent("white", (0, 0), (1, 1))
        
        # Create mock non-move event
        other_event = type('OtherEvent', (), {
            'type': 'piece_capture',
            'data': {'piece': 'pawn'}
        })()
        
        self.logger.update(move_event)
        self.logger.update(other_event)  # Should be ignored
        
        white_moves = self.logger.get_moves("white")
        assert len(white_moves) == 1  # Only the move event should be logged


if __name__ == "__main__":
    # Run tests if script is executed directly
    pytest.main([__file__, "-v"])
