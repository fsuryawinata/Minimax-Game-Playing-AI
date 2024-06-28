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

        best_action = self.minimax_decision(board)
        return best_action

    def minimax_decision(self, board):
        maxdepth = 0
        alpha = float('-inf')
        beta = float('inf')
        highest_value = alpha
        equal_actions = []

        for action in self.possible_moves(board):
            board.apply_action(action)
            new_state = board

            # Check if action has resulted in a win, if so, return action before minimaxing.
            if new_state.winner_color:
                return action

            value = self.minimax_value(new_state, maxdepth, alpha, beta)
            board.undo_action()

            if value > highest_value:
                highest_value_action = action
                highest_value = value
                equal_actions.clear()
                equal_actions.append(action)
            elif value == highest_value:
                equal_actions.append(action)

        if(len(equal_actions) > 1):
            highest_value_action = random.choice(equal_actions)

        equal_actions.clear()

        return highest_value_action



    def minimax_value(self, board, depth, alpha, beta):
        # print(f"depth = {depth}")   
        # print(board._state.values())

        # return score of the current board
        if depth == 0 or board.game_over:
            return self.evaluate(board)

        # for maximising 
        else:
            if board.turn_color == self._color:
                best_value = float('-inf')

                for action in self.possible_moves(board):
                    board.apply_action(action)
                    new_state = board
                    value = self.minimax_value(new_state, depth - 1, alpha, beta)
                    board.undo_action()

                    if value > best_value:
                        best_value = value

                    if best_value > alpha:
                        alpha = best_value

                    if alpha <= beta:
                        break

                return best_value

            # for min
            else:
                best_value = float('inf')

                for action in self.possible_moves(board):
                    board.apply_action(action)
                    new_state = board
                    value = self.minimax_value(new_state, depth - 1, alpha, beta)
                    board.undo_action()

                    if value < best_value:
                        best_value = value

                    if best_value < beta:
                        beta = best_value

                    if beta >= alpha:
                        break

                return best_value

    def possible_moves(self, board) -> list[Action]:
        actions = []
        # print(board._state.items())

        for pos, cell in board._state.copy().items():
            if cell.player == board.turn_color:
                for direction in HexDir:
                    neighbourpos = pos.__add__(direction)
                    
                    #if it is not occupied (free cell) , spawn next to allies
                    if not self.board._cell_occupied(neighbourpos) and self.board._total_power < 49:
                        actions.append(SpawnAction(neighbourpos))

                    actions.append(SpreadAction(pos, direction))

        # print("start spawning")
        # # goes through empty cell on board for a possible spawn action
        #for r in range(0, BOARD_N):
            #for q in range(0, BOARD_N):
                #pos = HexPos(r, q)
                #if not self.board._cell_occupied(pos) and self.board._total_power < 49:
                    #actions.append(SpawnAction(pos))

        # print("done spawning")

        return actions


    def evaluate(self, board):
        red_power = board._color_power(PlayerColor.RED)
        blue_power = board._color_power(PlayerColor.BLUE)

        power_diff = red_power - blue_power

        num_red_cells = 0
        num_blue_cells = 0

        red_capture_count = 0
        blue_capture_count = 0

        red_spread_allies = 0
        blue_spread_allies = 0

        for pos, cell in board._state.copy().items():
            if cell.player == PlayerColor.RED:
                num_red_cells += 1

                # checks spread
                for direction in HexDir:
                    targetpos = pos
                    for dist in range(1, cell.power + 1):
                        targetpos = pos.__add__(direction)
                        # spread to capture enemies
                        if board._state[targetpos].player == PlayerColor.BLUE:
                            red_capture_count += 1
                        # spread to allies
                        elif board._state[targetpos].player == PlayerColor.RED:
                            red_spread_allies += 1

            
            elif cell.player == PlayerColor.BLUE:
                num_blue_cells += 1

                for direction in HexDir:
                    targetpos = pos
                    for dist in range(1, cell.power + 1):
                        targetpos = pos.__add__(direction)
                        # spread to capture enemies
                        if board._state[targetpos].player == PlayerColor.RED:
                            blue_capture_count += 1
                        # spread to allies
                        elif board._state[targetpos].player == PlayerColor.BLUE:
                            blue_spread_allies += 1

        occupied_cell_difference = num_red_cells - num_blue_cells
        capture_difference = red_capture_count - blue_capture_count
        spread_allies_difference = red_spread_allies - blue_spread_allies
        
        # priority - capture > power > cell diff
        evaluation = (0.2 * power_diff
                    + 0.1 * (occupied_cell_difference)
                    + 0.6 * (capture_difference)
                    + 0.4 * (spread_allies_difference) )

        if board.turn_color == PlayerColor.RED:
            return evaluation
        else:
            return -evaluation

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