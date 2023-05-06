# COMP30024 Artificial Intelligence, Semester 1 2023
# Project Part B: Game Playing Agent

from referee.game import \
    PlayerColor, Action, SpawnAction, SpreadAction, HexPos, HexDir, Board
#from .board import Board
from .minimax import minimaxDecision


class Agent:
    def __init__(self, color: PlayerColor, **referee: dict):
        """
        Initialise the agent.
        """
        self._color = color
        # Initialise game
        self.game = Board()

    def action(self, **referee: dict) -> Action:
        """
        Return the next action to take.
        """
        # Spawn in middle if first turn
        if self.game.turn_count == 0:
            return SpawnAction(HexPos(3, 3))
        depth = 4
        move = minimaxDecision(depth, self.game)
        return move

    def turn(self, color: PlayerColor, action: Action, **referee: dict):
        """
        Update the agent with the last player's action.
        """
        print(referee["time_remaining"])
        self.game.apply_action(action)
