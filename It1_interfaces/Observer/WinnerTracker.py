from Subscriber import Subscriber


class WinnerTracker(Subscriber):
    def __init__(self):
        """Initialize WinnerTracker"""
        self.game_over = False
        self.winner = None
    
    def update(self, event):
        """Update when game over event occurs"""
        if event.type == "game_over":
            self.game_over = True
            self.winner = event.data.get("winner", "Unknown")
            print(f"🏆 Game Over! Winner: {self.winner}")
    
    def is_game_over(self):
        """Check if game is over"""
        return self.game_over
    
    def get_winner(self):
        """Get the winner of the game"""
        return self.winner
    
    def reset(self):
        """Reset the tracker for a new game"""
        self.game_over = False
        self.winner = None

    