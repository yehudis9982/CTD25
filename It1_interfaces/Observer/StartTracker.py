import pathlib
import cv2
import time
import logging
from Observer.Subscriber import Subscriber
from Observer.GameStartEvent import GameStartEvent
from Observer.EventType import EventType

logger = logging.getLogger(__name__)

class StartTracker(Subscriber):
    """מטפל בהצגת הלוגו ובטעינת המשחק"""
    
    def __init__(self):
        self.logo_displayed = False
    
    def show_logo_with_loading(self):
        """הצג לוגו במהלך טעינת המשחק"""
        try:
            # טען את הלוגו
            logo_path = pathlib.Path(__file__).parent.parent.parent / "Photos" / "logo.png"
            if logo_path.exists():
                logo_img = cv2.imread(str(logo_path))
                if logo_img is not None:
                    # הצג את הלוגו
                    cv2.imshow("Chess Game - Loading...", logo_img)
                    cv2.waitKey(1)  # עדכן את החלון
                    logger.info("Logo displayed during game loading")
                    self.logo_displayed = True
                    return True
                else:
                    logger.warning("Failed to load logo image")
                    return False
            else:
                logger.warning("Logo file not found at: %s", logo_path)
                return False
        except Exception as e:
            logger.error("Error displaying logo: %s", e)
            return False
    
    def close_logo_screen(self):
        """סגור את מסך הלוגו"""
        if self.logo_displayed:
            try:
                cv2.destroyWindow("Chess Game - Loading...")
                cv2.waitKey(1)  # וודא שהחלון נסגר
                time.sleep(0.5)  # תן עוד רגע לראות את הלוגו
                self.logo_displayed = False
                logger.info("Logo screen closed")
            except:
                pass
    
    def update(self, event):
        """מטפל ב-events"""
        if event.type == EventType.GAME_START:
            logger.info("Game start event received - showing logo")
            self.show_logo_with_loading()
    
    def finish_loading(self):
        """סיים את הטעינה וסגור את הלוגו"""
        self.close_logo_screen()
