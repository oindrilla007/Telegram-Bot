#!/usr/bin/env python3
"""
Main script to run the Workout Bot
"""

import sys
import os

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.bot.main import main

if __name__ == "__main__":
    main()