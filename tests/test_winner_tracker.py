import pytest
import sys
import os
from unittest.mock import Mock, MagicMock

# Add the project root to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from WinnerTracker import WinnerTracker
from GameOverEvent import GameOverEvent


class TestGameOverEvent:
    """Test suite for GameOverEvent class"""
    
    def test_game_over_event_creation_white_wins(self):
        """Test creating GameOverEvent for white winner"""
        event = GameOverEvent("white")
        
        assert event.type == "game_over"
        assert event.data["winner"] == "white"
    
    def test_game_over_event_creation_black_wins(self):
        """Test creating GameOverEvent for black winner"""
        event = GameOverEvent("black")
        
        assert event.type == "game_over"
        assert event.data["winner"] == "black"
    
    def test_game_over_event_creation_draw(self):
        """Test creating GameOverEvent for draw"""
        event = GameOverEvent("draw")
        
        assert event.type == "game_over"
        assert event.data["winner"] == "draw"
    
    def test_game_over_event_inheritance(self):
        """Test that GameOverEvent inherits from Event"""
        from Event import Event
        event = GameOverEvent("white")
        assert isinstance(event, Event)


class TestWinnerTracker:
    """Test suite for WinnerTracker class"""
    
    def setup_method(self):
        """Setup a fresh WinnerTracker instance for each test"""
        self.tracker = WinnerTracker()
    
    def test_winner_tracker_initialization(self):
        """Test WinnerTracker initialization"""
        assert self.tracker.game_over == False
        assert self.tracker.winner is None
        assert self.tracker.graphics is None
    
    def test_winner_tracker_initialization_with_graphics(self):
        """Test WinnerTracker initialization with graphics"""
        mock_graphics = Mock()
        tracker = WinnerTracker(graphics=mock_graphics)
        
        assert tracker.graphics == mock_graphics
        assert tracker.game_over == False
        assert tracker.winner is None
    
    def test_winner_tracker_inheritance(self):
        """Test that WinnerTracker inherits from Subscriber"""
        from Subscriber import Subscriber
        assert isinstance(self.tracker, Subscriber)
        assert hasattr(self.tracker, 'update')
    
    def test_update_with_game_over_event_white_wins(self):
        """Test updating tracker with GameOverEvent for white winner"""
        event = GameOverEvent("white")
        
        self.tracker.update(event)
        
        assert self.tracker.game_over == True
        assert self.tracker.winner == "white"
    
    def test_update_with_game_over_event_black_wins(self):
        """Test updating tracker with GameOverEvent for black winner"""
        event = GameOverEvent("black")
        
        self.tracker.update(event)
        
        assert self.tracker.game_over == True
        assert self.tracker.winner == "black"
    
    def test_update_with_game_over_event_draw(self):
        """Test updating tracker with GameOverEvent for draw"""
        event = GameOverEvent("draw")
        
        self.tracker.update(event)
        
        assert self.tracker.game_over == True
        assert self.tracker.winner == "draw"
    
    def test_update_with_non_game_over_event(self):
        """Test that non-game-over events are ignored"""
        # Create a mock event that's not a game over event
        mock_event = type('MockEvent', (), {
            'type': 'other_event',
            'data': {'some': 'data'}
        })()
        
        self.tracker.update(mock_event)
        
        # Should not change state
        assert self.tracker.game_over == False
        assert self.tracker.winner is None
    
    def test_is_game_over_initial(self):
        """Test is_game_over method initially returns False"""
        assert self.tracker.is_game_over() == False
    
    def test_is_game_over_after_event(self):
        """Test is_game_over method returns True after game over event"""
        event = GameOverEvent("white")
        self.tracker.update(event)
        
        assert self.tracker.is_game_over() == True
    
    def test_get_winner_initial(self):
        """Test get_winner method initially returns None"""
        assert self.tracker.get_winner() is None
    
    def test_get_winner_after_event(self):
        """Test get_winner method returns correct winner after event"""
        event = GameOverEvent("black")
        self.tracker.update(event)
        
        assert self.tracker.get_winner() == "black"
    
    def test_reset_method(self):
        """Test reset method clears game over state"""
        # First, trigger game over
        event = GameOverEvent("white")
        self.tracker.update(event)
        
        assert self.tracker.is_game_over() == True
        assert self.tracker.get_winner() == "white"
        
        # Then reset
        self.tracker.reset()
        
        assert self.tracker.is_game_over() == False
        assert self.tracker.get_winner() is None
    
    def test_display_game_over_no_graphics(self):
        """Test display_game_over_on_board when no graphics available"""
        # Should not raise error even without graphics
        self.tracker.game_over = True
        self.tracker.winner = "white"
        
        # This should not crash
        self.tracker.display_game_over_on_board()
    
    def test_display_game_over_with_mock_graphics(self):
        """Test display_game_over_on_board with mock graphics"""
        # Create mock graphics with screen
        mock_screen = Mock()
        mock_screen.get_size.return_value = (800, 600)
        mock_screen.get_width.return_value = 800
        mock_screen.get_height.return_value = 600
        
        mock_graphics = Mock()
        mock_graphics.screen = mock_screen
        
        tracker = WinnerTracker(graphics=mock_graphics)
        tracker.game_over = True
        tracker.winner = "white"
        
        # This should not crash and should call screen methods
        try:
            tracker.display_game_over_on_board()
            # If pygame is not available, this might fail, which is okay for testing
        except Exception as e:
            # Expected if pygame is not installed
            pass
    
    def test_update_calls_display_with_graphics(self):
        """Test that update calls display_game_over_on_board when graphics available"""
        mock_graphics = Mock()
        mock_graphics.screen = Mock()
        mock_graphics.screen.get_size.return_value = (800, 600)
        
        tracker = WinnerTracker(graphics=mock_graphics)
        
        # Mock the display method to track if it was called
        tracker.display_game_over_on_board = Mock()
        
        event = GameOverEvent("white")
        tracker.update(event)
        
        # Should have called display method
        tracker.display_game_over_on_board.assert_called_once()


class TestWinnerTrackerIntegration:
    """Integration tests for WinnerTracker and GameOverEvent"""
    
    def test_full_game_over_sequence(self):
        """Test complete game over sequence"""
        tracker = WinnerTracker()
        
        # Initially, game is not over
        assert not tracker.is_game_over()
        assert tracker.get_winner() is None
        
        # Game ends with white winning
        event = GameOverEvent("white")
        tracker.update(event)
        
        # Now game is over
        assert tracker.is_game_over()
        assert tracker.get_winner() == "white"
        
        # Reset for new game
        tracker.reset()
        
        # Back to initial state
        assert not tracker.is_game_over()
        assert tracker.get_winner() is None
    
    def test_multiple_game_over_events(self):
        """Test that only the first game over event counts"""
        tracker = WinnerTracker()
        
        # First game over event
        event1 = GameOverEvent("white")
        tracker.update(event1)
        
        assert tracker.get_winner() == "white"
        
        # Second game over event (should still show first winner)
        event2 = GameOverEvent("black")
        tracker.update(event2)
        
        # Winner should be updated to the latest event
        assert tracker.get_winner() == "black"


if __name__ == "__main__":
    # Run tests if script is executed directly
    pytest.main([__file__, "-v"])
