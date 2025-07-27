from .Subscriber import Subscriber


class WinnerTracker(Subscriber):
    def __init__(self):
        """Initialize WinnerTracker"""
        self.game_over = False
        self.winner = None
        self.winner_text = None  # טקסט הניצחון להצגה על הלוח
    
    def update(self, event):
        """Update when game over event occurs"""
        if event.type == "game_over":
            self.game_over = True
            self.winner = event.data.get("winner", "Unknown")
            self.winner_text = event.data.get("winner_text", "🎮 המשחק נגמר! 🎮")
            print(f"🏆 Game Over! Winner: {self.winner}")
    
    def is_game_over(self):
        """Check if game is over"""
        return self.game_over
    
    def get_winner(self):
        """Get the winner of the game"""
        return self.winner
        
    def get_winner_text(self):
        """Get the winner text for display"""
        return self.winner_text
        
    def set_winner_text(self, text):
        """Set the winner text for display"""
        self.winner_text = text
    
    def reset(self):
        """Reset the tracker for a new game"""
        self.game_over = False
        self.winner = None
        self.winner_text = None

    

    