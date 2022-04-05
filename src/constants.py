"""Class for storing all the constants"""
import os
from pathlib import Path

OUTSIDE_VIEW = 2
INSIDE_VIEW = 1

TOP_IMAGE = 0
BOTTOM_IMAGE = 1
LEFT_IMAGE = 2
RIGHT_IMAGE = 3

ZOMBIE_MENU = 6

# Farming type constants
FARM_FOOD = 1
FARM_OIL = 2
FARM_STEEL = 3
FARM_MINERAL = 4
FARM_GOLD = 5

# Config File path
CONFIG_PATH = Path(__file__).parent.parent / os.environ.\
    get("AOZ_CONFIG", "config.ini")
