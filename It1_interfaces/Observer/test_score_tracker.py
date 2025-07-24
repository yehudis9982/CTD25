import pytest
import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from ScoreTracker import ScoreTracker
from PieceCaptureEvent import PieceCaptureEvent


class TestScoreTracker:
    """Test suite for ScoreTracker class"""
    
    def setup_method(self):
        """Setup a fresh ScoreTracker instance for each test"""
        self.tracker = ScoreTracker()
    
    def test_initial_score(self):
        """Test that initial scores are zero for both players"""
        assert self.tracker.score["white"] == 0
        assert self.tracker.score["black"] == 0
    
    def test_piece_values_initialization(self):
        """Test that piece values are correctly initialized"""
        expected_values = {
            'P': 1,  # Pawn
            'N': 3,  # Knight
            'B': 3,  # Bishop
            'R': 5,  # Rook
            'Q': 9,  # Queen
            'K': 0   # King
        }
        assert self.tracker.piece_values == expected_values
    
    def test_pawn_capture_by_white(self):
        """Test capturing a pawn by white player"""
        # Create a mock event with piece attribute
        event = type('MockEvent', (), {
            'piece': 'P',
            'captured_by': 'white'
        })()
        
        self.tracker.update(event)
        
        assert self.tracker.score["white"] == 1
        assert self.tracker.score["black"] == 0
    
    def test_pawn_capture_by_black(self):
        """Test capturing a pawn by black player"""
        event = type('MockEvent', (), {
            'piece': 'P',
            'captured_by': 'black'
        })()
        
        self.tracker.update(event)
        
        assert self.tracker.score["white"] == 0
        assert self.tracker.score["black"] == 1
    
    def test_queen_capture_by_white(self):
        """Test capturing a queen by white player"""
        event = type('MockEvent', (), {
            'piece': 'Q',
            'captured_by': 'white'
        })()
        
        self.tracker.update(event)
        
        assert self.tracker.score["white"] == 9
        assert self.tracker.score["black"] == 0
    
    def test_multiple_captures(self):
        """Test multiple captures by different players"""
        # White captures a pawn
        event1 = type('MockEvent', (), {
            'piece': 'P',
            'captured_by': 'white'
        })()
        
        # Black captures a knight
        event2 = type('MockEvent', (), {
            'piece': 'N',
            'captured_by': 'black'
        })()
        
        # White captures a rook
        event3 = type('MockEvent', (), {
            'piece': 'R',
            'captured_by': 'white'
        })()
        
        self.tracker.update(event1)
        self.tracker.update(event2)
        self.tracker.update(event3)
        
        assert self.tracker.score["white"] == 6  # 1 + 5
        assert self.tracker.score["black"] == 3  # 3
    
    def test_king_capture_no_points(self):
        """Test that capturing a king gives 0 points"""
        event = type('MockEvent', (), {
            'piece': 'K',
            'captured_by': 'white'
        })()
        
        self.tracker.update(event)
        
        assert self.tracker.score["white"] == 0
        assert self.tracker.score["black"] == 0
    
    def test_unknown_piece_type(self):
        """Test handling of unknown piece type"""
        event = type('MockEvent', (), {
            'piece': 'X',  # Unknown piece
            'captured_by': 'white'
        })()
        
        self.tracker.update(event)
        
        # Should default to 0 points for unknown piece
        assert self.tracker.score["white"] == 0
        assert self.tracker.score["black"] == 0
    
    def test_all_piece_types(self):
        """Test all standard chess piece types"""
        pieces_and_values = [
            ('P', 1), ('N', 3), ('B', 3), 
            ('R', 5), ('Q', 9), ('K', 0)
        ]
        
        total_expected = 0
        for piece, value in pieces_and_values:
            event = type('MockEvent', (), {
                'piece': piece,
                'captured_by': 'white'
            })()
            
            self.tracker.update(event)
            total_expected += value
        
        assert self.tracker.score["white"] == total_expected
        assert self.tracker.score["black"] == 0
    
    def test_with_real_piece_capture_event(self):
        """Test with actual PieceCaptureEvent"""
        # Create a real PieceCaptureEvent
        event = PieceCaptureEvent("P", "white")
        
        # Add the required attributes that ScoreTracker expects
        event.piece = "P"
        event.captured_by = "white"
        
        self.tracker.update(event)
        assert self.tracker.score["white"] == 1
        assert self.tracker.score["black"] == 0
    
    def test_get_score_white(self):
        """Test get_score method for white player"""
        # Initially should be 0
        assert self.tracker.get_score("white") == 0
        
        # Add some points for white
        event = type('MockEvent', (), {
            'piece': 'Q',
            'captured_by': 'white'
        })()
        
        self.tracker.update(event)
        assert self.tracker.get_score("white") == 9
    
    def test_get_score_black(self):
        """Test get_score method for black player"""
        # Initially should be 0
        assert self.tracker.get_score("black") == 0
        
        # Add some points for black
        event = type('MockEvent', (), {
            'piece': 'R',
            'captured_by': 'black'
        })()
        
        self.tracker.update(event)
        assert self.tracker.get_score("black") == 5
    
    def test_get_score_invalid_player(self):
        """Test get_score method with invalid player color"""
        # Should return 0 for unknown player
        assert self.tracker.get_score("red") == 0
        assert self.tracker.get_score("blue") == 0
        assert self.tracker.get_score("") == 0
        assert self.tracker.get_score(None) == 0
    
    def test_get_score_after_multiple_captures(self):
        """Test get_score method after multiple captures"""
        # White captures pawn and knight
        event1 = type('MockEvent', (), {
            'piece': 'P',
            'captured_by': 'white'
        })()
        
        event2 = type('MockEvent', (), {
            'piece': 'N',
            'captured_by': 'white'
        })()
        
        # Black captures rook
        event3 = type('MockEvent', (), {
            'piece': 'R',
            'captured_by': 'black'
        })()
        
        self.tracker.update(event1)
        self.tracker.update(event2)
        self.tracker.update(event3)
        
        assert self.tracker.get_score("white") == 4  # 1 + 3
        assert self.tracker.get_score("black") == 5  # 5


# Test helper function
def test_score_tracker_is_subscriber():
    """Test that ScoreTracker is a proper Subscriber"""
    from Subscriber import Subscriber
    
    tracker = ScoreTracker()
    assert isinstance(tracker, Subscriber)
    assert hasattr(tracker, 'update')


if __name__ == "__main__":
    # Run tests if script is executed directly
    pytest.main([__file__, "-v"])
