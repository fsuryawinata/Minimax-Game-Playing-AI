BOARD_SIZE = 7

from referee.game import \
    PlayerColor, Action, SpawnAction, SpreadAction, HexPos, HexDir, Board
from typing import List


def minimaxDecision(depth, game, colour):
    """
    Find best move
    """
    operators = getOperators(game)
    best_operator = None
    best_value = float('-inf')
    for op in operators:
        game.apply_action(op)
        print(f"MINIMAX TEST ACTION {op}")
        state = game
        value = minimaxValue(state, game, depth, colour)
        if value > best_value:
            best_value = value
            best_operator = op
        game.undo_action()
    return best_operator


def getNeighbours(cell, power, game):
    """
    Get possible spread actions
    """
    r = cell.r
    q = cell.q
    neighbours = {}
    directions = [HexDir.Up, HexDir.UpRight, HexDir.UpLeft, HexDir.Down, HexDir.DownLeft, HexDir.DownRight]
    grid_size = 7

    # Generate "power" amount of successors in each direction
    i = 1
    index = 0

    for hex_dir in directions:
        while i <= power:
            dx = hex_dir.r
            dy = hex_dir.q
            neighbour = [r + dx * i, q + dy * i]
            print(f"ORIGINAL {r}, {q}")
            print(f"DIRECTION {dx}, {dy} Power {i}")
            print(f"NEIGHBOUR POS ({neighbour[0]}, {neighbour[1]})")

            # Wrap around the hexagon graph if the successor state is outside the boundaries
            if neighbour[0] < 0 or neighbour[0] < 6:
                neighbour[0] = neighbour[0] % grid_size
            if neighbour[1] < 0 or neighbour[1] < 6:
                neighbour[1] = neighbour[1] % grid_size

            neighbour = HexPos(neighbour[0], neighbour[1])
            # invalid spread so invalidate direction
            if game._cell_occupied(neighbour):
                for direction in neighbours.keys():
                    if direction == hex_dir:
                        neighbours.pop(direction)
                break
            else:
                # add to dictionary with direction taken
                neighbours[neighbour] = hex_dir
            index += 1
            i += 1
    return neighbours


def getOperators(game) -> List[Action]:
    """
    Find all valid moves
    """
    # List possible SPAWN actions
    empty_cells = [pos for pos in game._state.keys() if not game._cell_occupied(pos)]
    for r in range(BOARD_SIZE):
        for q in range(BOARD_SIZE):
            if not game._cell_occupied(HexPos(r, q)):
                empty_cells.append(HexPos(r,q))
    spawn_actions = [SpawnAction(pos) for pos in empty_cells]
    # List possible SPREAD actions

    player_cells = []
    spread_actions = []
    power = []

    for pos, state in game._state.items():
        if state.player == game._turn_color:
            player_cells.append(pos)
            power.append(state.power)

    j = 0
    for pos in player_cells:
        power = power[j]
        neighbour_cells = getNeighbours(pos, power, game)
        for cells, direction in neighbour_cells.items():
            spread_actions.append(SpreadAction(cells, direction))
    return spawn_actions + spread_actions


def minimaxValue(state, game, depth, player_colour):
    """
    Calculate minimax value
    """
    # Check Terminal nodes
    if state.game_over | depth == 0:
        return utility(state)

    elif player_colour == game.turn_color:
        return maxValue(state, game, depth, float('-inf'), float('-inf'))
    else:
        return minValue(state, game, depth, float('-inf'), float('-inf'))


def maxValue(state, game, depth, alpha, beta):
    if state.game_over | depth == 0:
        return utility(state)

    best_score = float('-inf')
    operators = getOperators(game)

    for op in operators:
        game.apply_action(op)
        print(f"MAX APPLY ACTION {op}")

        new_state = game
        score = minValue(new_state, game, depth - 1, alpha, beta)
        best_score = max(best_score, score)

        if best_score >= beta:
            return best_score

        alpha = max(alpha, best_score)
        game.undo_action()

    return best_score


def minValue(state, game, depth, alpha, beta):
    if state.game_over | depth == 0:
        return utility(state)

    best_score = float('-inf')
    operators = getOperators(game)

    for op in operators:
        game.apply_action(op)
        print(f"MIN APPLY ACTION {op}")
        new_state = game
        score = maxValue(new_state, game, depth - 1, alpha, beta)
        best_score = min(best_score, score)

        if best_score >= beta:
            return best_score

        beta = min(beta, best_score)
        game.undo_action()

    return best_score


def utility(state):
    # Calculate the utility value of the given state for the given player
    # Return a numeric value representing the utility
    red_pow = 0
    blue_pow = 1
    for pos, state in state._state.items():
        if state.player == PlayerColor.RED:
            red_pow += 1
        elif state.player == PlayerColor.BLUE:
            blue_pow += 1
    return red_pow - blue_pow
