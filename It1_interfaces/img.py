from __future__ import annotations

import pathlib
import logging

import cv2
import numpy as np

logger = logging.getLogger(__name__)

class Img:
    def __init__(self):
        self.img = None

    def read(self, path: str | pathlib.Path,
             size: tuple[int, int] | None = None,
             keep_aspect: bool = False,
             interpolation: int = cv2.INTER_AREA) -> "Img":
        """
        Load `path` into self.img and **optionally resize**.

        Parameters
        ----------
        path : str | Path
            Image file to load.
        size : (width, height) | None
            Target size in pixels.  If None, keep original.
        keep_aspect : bool
            • False  → resize exactly to `size`
            • True   → shrink so the *longer* side fits `size` while
                       preserving aspect ratio (no cropping).
        interpolation : OpenCV flag
            E.g.  `cv2.INTER_AREA` for shrink, `cv2.INTER_LINEAR` for enlarge.

        Returns
        -------
        Img
            `self`, so you can chain:  `sprite = Img().read("foo.png", (64,64))`
        """
        path = str(path)
        self.img = cv2.imread(path, cv2.IMREAD_UNCHANGED)
        if self.img is None:
            logger.warning(f"Failed to load image {path}")
            return self

        # הוסף קטע זה: אם זו תמונת חייל, הקטן לגודל תא הלוח (למשל 80x80)
        if "sprites" in path and size is None:
            size = (80, 80)  # או קח מהגדרת הלוח

        if size is not None:
            target_w, target_h = size
            h, w = self.img.shape[:2]

            if keep_aspect:
                scale = min(target_w / w, target_h / h)
                new_w, new_h = int(w * scale), int(h * scale)
            else:
                new_w, new_h = target_w, target_h

            self.img = cv2.resize(self.img, (new_w, new_h), interpolation=interpolation)

        if self.img.shape[2] == 3:
            self.img = cv2.cvtColor(self.img, cv2.COLOR_BGR2BGRA)

        return self

    def draw_on(self, other_img, x, y):
        if self.img is None:
            logger.warning("self.img is None")
            return
        if other_img.img is None:
            logger.warning("other_img.img is None")
            return
        if not hasattr(self.img, "shape"):
            logger.warning("self.img has no shape")
            return
        if not hasattr(other_img.img, "shape"):
            logger.warning("other_img.img has no shape")
            return
        if self.img.shape[2] != other_img.img.shape[2]:
            logger.warning(f"Shape mismatch: {self.img.shape} vs {other_img.img.shape}")
            return

        h, w = self.img.shape[:2]
        H, W = other_img.img.shape[:2]

        if y + h > H or x + w > W:
            raise ValueError("Logo does not fit at the specified position.")

        roi = other_img.img[y:y + h, x:x + w]

        if self.img.shape[2] == 4:
            b, g, r, a = cv2.split(self.img)
            mask = a / 255.0
            for c in range(3):
                roi[..., c] = (1 - mask) * roi[..., c] + mask * self.img[..., c]
        else:
            other_img.img[y:y + h, x:x + w] = self.img

    def put_text(self, txt, x, y, font_size, color=(255, 255, 255, 255), thickness=1):
        if self.img is None:
            raise ValueError("Image not loaded.")
        cv2.putText(self.img, txt, (x, y),
                    cv2.FONT_HERSHEY_SIMPLEX, font_size,
                    color, thickness, cv2.LINE_AA)

    def show(self):
        if self.img is None:
            raise ValueError("Image not loaded.")
        cv2.imshow("Image", self.img)
        cv2.waitKey(0)
        cv2.destroyAllWindows()

    def display(self, window_name="Game Window"):
        """Display the image in a window without blocking the game loop."""
        if self.img is None:
            raise ValueError("Image not loaded.")
        cv2.imshow(window_name, self.img)

    def display_with_background(self, window_name="Game Window", background_scale=1.3, gradient_colors=None, auto_resize_window=True, max_window_size=None, cursors_info=None, score_info=None, moves_info=None, player_names=None):
        """Display the image with a background gradient."""
        if self.img is None:
            raise ValueError("Image not loaded.")
        
        # קבל גודל התמונה הנוכחית
        img_height, img_width = self.img.shape[:2]
        
        # חשב גודל הרקע - הרחב יותר כדי לתת מקום לטבלת המהלכים
        bg_width = int(img_width * background_scale) + 400  # הוסף 400 פיקסלים רוחב נוסף
        bg_height = int(img_height * background_scale)
        
        # בדוק אם צריך להקטין בגלל גודל המסך
        if max_window_size is None:
            max_window_size = (1200, 900)  # גודל מקסימלי סביר
        
        max_width, max_height = max_window_size
        if bg_width > max_width or bg_height > max_height:
            # חשב יחס קנה מידה כדי להתאים לחלון
            scale_w = max_width / bg_width
            scale_h = max_height / bg_height
            scale = min(scale_w, scale_h)
            
            bg_width = int(bg_width * scale)
            bg_height = int(bg_height * scale)
            img_width = int(img_width * scale)
            img_height = int(img_height * scale)
            
            # שנה גודל התמונה המקורית
            resized_img = cv2.resize(self.img, (img_width, img_height))
        else:
            resized_img = self.img
        
        # צבעי גרדיאנט ברירת מחדל (אפור כהה לאפור בהיר)
        if gradient_colors is None:
            gradient_colors = {
                'top': [50, 50, 50],      # אפור כהה למעלה (BGR)
                'bottom': [120, 120, 120] # אפור בהיר למטה (BGR)
            }
        
        # יצירת רקע עם גרדיאנט
        background = np.zeros((bg_height, bg_width, 3), dtype=np.uint8)
        
        for y in range(bg_height):
            # חישוב אינטנסיביות לפי מיקום Y
            ratio = y / bg_height
            
            # מיזוג צבעים
            color = [
                int(gradient_colors['top'][i] * (1 - ratio) + gradient_colors['bottom'][i] * ratio)
                for i in range(3)
            ]
            
            background[y, :] = color
        
        # חישוב מיקום למרכז התמונה על הרקע
        center_x = (bg_width - img_width) // 2
        center_y = (bg_height - img_height) // 2
        
        # הצבת התמונה על הרקע
        if resized_img.shape[2] == 4:  # תמונה עם שקיפות
            # טיפול בשקיפות
            alpha = resized_img[:, :, 3] / 255.0
            for c in range(3):
                background[center_y:center_y + img_height, center_x:center_x + img_width, c] = \
                    (1 - alpha) * background[center_y:center_y + img_height, center_x:center_x + img_width, c] + \
                    alpha * resized_img[:, :, c]
        else:
            # ללא שקיפות - פשוט העתק
            background[center_y:center_y + img_height, center_x:center_x + img_width] = resized_img
        
        # התאם את גודל החלון לתמונה
        if auto_resize_window:
            cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
            cv2.resizeWindow(window_name, bg_width, bg_height)
        
        # ציור הסמנים על הרקע הסופי
        if cursors_info:
            self._draw_cursors_on_background(background, cursors_info, center_x, center_y, img_width, img_height)
        
        # ציור הניקוד על הרקע
        if score_info:
            self._draw_score_on_background(background, score_info, bg_width, bg_height, player_names)
        
        # ציור המהלכים על הרקע
        if moves_info:
            self._draw_moves_history(background, moves_info, bg_width, bg_height, img_width)
        
        # הצגת הרקע עם התמונה
        cv2.imshow(window_name, background)

    def _draw_cursors_on_background(self, background, cursors_info, board_x, board_y, board_width, board_height):
        """Draw cursors on the final background image."""
        # חישוב גודל משבצת
        cell_width = board_width // 8
        cell_height = board_height // 8
        
        # ציור סמן שחקן 1 (אדום זוהר) - מקשי מספרים
        if cursors_info.get('player1_cursor'):
            x1, y1 = cursors_info['player1_cursor']
            top_left_1 = (board_x + x1 * cell_width, board_y + y1 * cell_height)
            bottom_right_1 = (board_x + (x1 + 1) * cell_width - 1, board_y + (y1 + 1) * cell_height - 1)
            cv2.rectangle(background, top_left_1, bottom_right_1, (0, 0, 255), 8)  # אדום זוהר BGR עבה מאוד
        
        # ציור סמן שחקן 2 (ירוק זוהר) - WASD
        if cursors_info.get('player2_cursor'):
            x2, y2 = cursors_info['player2_cursor']
            top_left_2 = (board_x + x2 * cell_width, board_y + y2 * cell_height)
            bottom_right_2 = (board_x + (x2 + 1) * cell_width - 1, board_y + (y2 + 1) * cell_height - 1)
            cv2.rectangle(background, top_left_2, bottom_right_2, (0, 255, 0), 8)  # ירוק זוהר BGR עבה מאוד
        
        # סימון כלי נבחר של שחקן 1 (צהוב זוהר)
        if cursors_info.get('player1_selected'):
            px, py = cursors_info['player1_selected']
            piece_top_left = (board_x + px * cell_width, board_y + py * cell_height)
            piece_bottom_right = (board_x + (px + 1) * cell_width - 1, board_y + (py + 1) * cell_height - 1)
            cv2.rectangle(background, piece_top_left, piece_bottom_right, (0, 255, 255), 4)  # צהוב זוהר עבה
        
        # סימון כלי נבחר של שחקן 2 (ורוד/מגנטה זוהר)
        if cursors_info.get('player2_selected'):
            px, py = cursors_info['player2_selected']
            piece_top_left = (board_x + px * cell_width, board_y + py * cell_height)
            piece_bottom_right = (board_x + (px + 1) * cell_width - 1, board_y + (py + 1) * cell_height - 1)
            cv2.rectangle(background, piece_top_left, piece_bottom_right, (255, 0, 255), 4)  # ורוד/מגנטה זוהר עבה

    def _draw_score_on_background(self, background, score_info, bg_width, bg_height, player_names=None):
        """Draw score information on the background."""
        white_score = score_info.get('white_score', 0)
        black_score = score_info.get('black_score', 0)
        
        # שמות המשתמשים או ברירת מחדל
        if player_names:
            player1_name = player_names.get('player1', 'PLAYER 1')
            player2_name = player_names.get('player2', 'PLAYER 2')
        else:
            player1_name = 'PLAYER 1'
            player2_name = 'PLAYER 2'
        
        # פונט וגודל
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.8
        thickness = 2
        
        # ניקוד שחקן 1 (לבן) - למטה
        white_text = f"{player1_name} (WHITE): {white_score}"
        text_size = cv2.getTextSize(white_text, font, font_scale, thickness)[0]
        white_x = (bg_width - text_size[0]) // 2
        white_y = bg_height - 20
        cv2.putText(background, white_text, (white_x, white_y), font, font_scale, (255, 255, 255), thickness)
        
        # ניקוד שחקן 2 (שחור) - למעלה  
        black_text = f"{player2_name} (BLACK): {black_score}"
        text_size = cv2.getTextSize(black_text, font, font_scale, thickness)[0]
        black_x = (bg_width - text_size[0]) // 2
        black_y = 30
        cv2.putText(background, black_text, (black_x, black_y), font, font_scale, (255, 255, 255), thickness)

    def _draw_moves_history(self, background, moves_info, bg_width, bg_height, img_width):
        """Draw moves history on the background."""
        white_moves = moves_info.get('white_moves', [])
        black_moves = moves_info.get('black_moves', [])
        
        # הגדרות פונט
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.4
        thickness = 1
        line_height = 18
        
        # כמה מהלכים להציג (המהלכים האחרונים)
        max_moves_to_show = 6
        
        # חישוב מיקום הלוח כדי להימנע מחפיפה
        board_center_x = bg_width // 2
        board_width_estimated = img_width  # גודל הלוח הנוכחי (אחרי resize)
        board_left = board_center_x - board_width_estimated // 2
        board_right = board_center_x + board_width_estimated // 2
        
        # תצוגת מהלכים של שחקן לבן (צד שמאל רחוק)
        start_x_white = 20  # שמאל קיצוני
        start_y_white = 120
        
        white_title = "WHITE MOVES:"
        cv2.putText(background, white_title, (start_x_white, start_y_white), 
                   font, font_scale, (255, 255, 255), thickness)
        
        recent_white = white_moves[-max_moves_to_show:] if len(white_moves) > max_moves_to_show else white_moves
        for i, move in enumerate(recent_white):
            move_text = f"{len(white_moves) - len(recent_white) + i + 1}. {move['move']} ({move['time']})"
            y_pos = start_y_white + (i + 1) * line_height
            cv2.putText(background, move_text, (start_x_white, y_pos), 
                       font, font_scale, (200, 200, 200), thickness)
        
        # תצוגת מהלכים של שחקן שחור (קרוב יותר ללוח)
        start_x_black = bg_width - 250  # קרוב עוד יותר ללוח
        start_y_black = 120
        
        black_title = "BLACK MOVES:"
        cv2.putText(background, black_title, (start_x_black, start_y_black), 
                   font, font_scale, (255, 255, 255), thickness)
        
        recent_black = black_moves[-max_moves_to_show:] if len(black_moves) > max_moves_to_show else black_moves
        for i, move in enumerate(recent_black):
            move_text = f"{len(black_moves) - len(recent_black) + i + 1}. {move['move']} ({move['time']})"
            y_pos = start_y_black + (i + 1) * line_height
            cv2.putText(background, move_text, (start_x_black, y_pos), 
                       font, font_scale, (200, 200, 200), thickness)
