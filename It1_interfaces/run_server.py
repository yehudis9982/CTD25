#!/usr/bin/env python3
"""
הפעלת שרת השחמט
"""

import logging
from Server import ChessServer

# הגדרת לוגגר
logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    logger.info("מפעיל שרת שחמט...")
    
    server = ChessServer(host='localhost', port=8888)
    
    try:
        server.start_server()
    except KeyboardInterrupt:
        logger.info("השרת נסגר על ידי המשתמש")
    except Exception as e:
        logger.error(f"שגיאה בהפעלת השרת: {e}")

if __name__ == "__main__":
    main()