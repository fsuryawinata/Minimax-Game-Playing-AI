# COMP30024 Artificial Intelligence, Semester 1 2023
# Project Part B: Game Playing Agent

from referee.game import \
    PlayerColor, Action, SpawnAction, SpreadAction, HexPos, HexDir, Board

import random
BOARD_N = 7

# from .board import board


# This is the entry point for your game playing agent. Currently the agent
# simply spawns a token at the centre of the board if playing as RED, and
# spreads a token at the centre of the board if playing as BLUE. This is
# intended to serve as an example of how to use the referee API -- obviously
# this is not a valid strategy for actually playing the game!

class Agent:
    def __init__(self, color: PlayerColor, **referee: dict):
        """
        Initialise the agent.
        """
        self._color = color
        self.board = Board()

    def action(self, **referee: dict) -> Action:
        """
        Return the next action to take.
        """
        board = self.board
        if board.turn_count == 0:
            return SpawnAction(HexPos(3, 3))

        if board.turn_count == 1:
            return SpawnAction(HexPos(1, 1))    

        # print(current_state._state.keys())
        # print("_________________________")

        random_action = random.choice(self.possible_moves(board))
        return random_action

    def possible_moves(self, board) -> list[Action]:
        actions = []
        # print(board._state.items())

        for pos, cell in board._state.copy().items():
            if cell.player == board.turn_color:
                for direction in HexDir:
                    neighbourpos = pos.__add__(direction)
                    
                    #if it is not occupied (free cell) , spawn next to allies
                    #if not self.board._cell_occupied(neighbourpos) and self.board._total_power < 49:
                        #actions.append(SpawnAction(neighbourpos))

                    actions.append(SpreadAction(pos, direction))

        # print("start spawning")
        # # goes through empty cell on board for a possible spawn action
        for r in range(0, BOARD_N):
            for q in range(0, BOARD_N):
                pos = HexPos(r, q)
                if not self.board._cell_occupied(pos) and self.board._total_power < 49:
                    actions.append(SpawnAction(pos))

        # print("done spawning")

        return actions

    def turn(self, color: PlayerColor, action: Action, **referee: dict):
        """
        Update the agent with the last player's action.
        """

        self.board.apply_action(action)
        match action:
            case SpawnAction(cell):
                print(f"Testing: {color} SPAWN at {cell}")
                pass
            case SpreadAction(cell, direction):
                print(f"Testing: {color} SPREAD from {cell}, {direction}")
                pass