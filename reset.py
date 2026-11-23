import os
import sys
from setup_db import initialize

def reset(db_path='shop.db'):
    """Delete the database and recreate it with fresh seed data."""
    if os.path.exists(db_path):
        os.remove(db_path)
    initialize(db_path)

if __name__ == '__main__':
    reset(sys.argv[1] if len(sys.argv) > 1 else 'shop.db')