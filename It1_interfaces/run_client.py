#!/usr/bin/env python3
"""
הפעלת לקוח השחמט
"""

import logging
from Client import ChessClient

# הגדרת לוגגר
logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    logger.info("מפעיל לקוח שחמט...")
    
    client = ChessClient(host='localhost', port=8888)
    
    try:
        client.run()
    except KeyboardInterrupt:
        logger.info("הלקוח נסגר על ידי המשתמש")
    except Exception as e:
        logger.error(f"שגיאה בהפעלת הלקוח: {e}")
    finally:
        client.disconnect()

if __name__ == "__main__":
    main()