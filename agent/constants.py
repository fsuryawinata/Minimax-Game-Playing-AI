from referee.game import HexDir

BOARD_SIZE = 7
DIRECTIONS = [HexDir.Up, HexDir.UpRight, HexDir.UpLeft, HexDir.Down, HexDir.DownLeft, HexDir.DownRight]
EAT_WEIGHT = 10
POWER_WEIGHT = 8
TOKEN_WEIGHT = 5
DISTANCE_WEIGHT = 1
ALPHA = 0.1