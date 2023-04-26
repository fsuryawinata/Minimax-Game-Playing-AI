RED = 1
BLUE = 2
BOARD_SIZE = 6

from referee.game import Board

def isFinished(state):
    """
    Check whether the game is won by either players
    """
    # If the opponent's token is all eaten
    if Board.game_over:
        return True
    else:
        return False


def utility(state, player):
    # Calculate the utility value of the given state for the given player
    # Return a numeric value representing the utility
    pass  # TODO: Implement this method
