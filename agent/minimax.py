RED = 1
BLUE = 2
BOARD_SIZE = 6

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
        value = minimaxValue(game.apply_action(op), game, depth, colour)
        if value > best_value:
            best_value = value
            best_operator = op
        game.undo_action(op)
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
    while i <= power:
        for hex_dir in directions:
            dx = hex_dir.r
            dy = hex_dir.q
            neighbour = HexPos(r + dx * i, q + dy * i)

            # invalid spread so invalidate direction
            if game._cell_occupied(neighbour):
                continue
            else:
                # Wrap around the hexagon graph if the successor state is outside the boundaries
                if neighbour.r < 0:
                    neighbour = HexPos(abs(neighbour.r) % grid_size, neighbour.q)
                elif neighbour.r > 6:
                    neighbour = HexPos(neighbour.r % grid_size, neighbour.q)
                if neighbour.q < 0:
                    neighbour = HexPos(neighbour.r, abs(neighbour.q) % grid_size)
                elif neighbour.q > 6:
                    neighbour = HexPos(neighbour.r, neighbour.q % grid_size)

                # add to dictionary with direction taken
                neighbours[hex_dir] = HexPos(dx, dy)
        index += 1
        i += 1
    return neighbours


def getOperators(game) -> List[Action]:
    """
    Find all valid moves
    """
    # List possible SPAWN actions
    empty_cells = [pos for pos in game._state.keys() if not game._cell_occupied(pos)]
    spawn_actions = [SpawnAction(pos) for pos in empty_cells]

    # List possible SPREAD actions

    player_cells = []
    spread_actions = []
    power = []
    i = 0
    for pos, state in game._state.items():
        if state.player == game._turn_color:
            player_cells[i] = pos
            power[i] = state.power
            i += 1

    j = 0
    for pos in player_cells:
        power = power[j]
        neighbour_cells = getNeighbours(pos, power, game)
        for direction, cells in neighbour_cells.items():
            spread_actions.append(SpreadAction(cells, direction))
    return spawn_actions + spread_actions


def minimaxValue(state, game, depth, player_colour):
    """
    Calculate minimax value
    """
    value = float('-inf')
    # Check Terminal nodes
    if state.game_over | depth == 0:
        return utility(state)
    elif player_colour == game.turn_color:
        maxValue(state, game, depth, float('-inf'), float('-inf'))
    else:
        minValue(state, game, depth, float('-inf'), float('-inf'))


def maxValue(state, game, depth, alpha, beta):
    if state.game_over | depth == 0:
        return utility(state)

    best_score = float('-inf')
    operators = getOperators(game)

    for op in operators:
        new_board = game.apply_action(op)
        score = minValue(new_board, game, depth - 1, alpha, beta)
        best_score = max(best_score, score)

        if best_score >= beta:
            return best_score

        alpha = max(alpha, best_score)
        game.undo_action

    return best_score


def minValue(state, game, depth, alpha, beta):
    if state.game_over | depth == 0:
        return utility(state)

    best_score = float('-inf')
    operators = getOperators(game)

    for op in operators:
        new_state = game.apply_action(op)
        score = maxValue(new_state, game, depth - 1, alpha, beta)
        best_score = min(best_score, score)

        if best_score >= beta:
            return best_score

        beta = min(beta, best_score)
        game.undo_action(op)

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
