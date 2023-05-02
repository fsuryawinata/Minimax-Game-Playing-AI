from referee.game import \
    PlayerColor, Action, SpawnAction, SpreadAction, HexPos, HexDir, Board
from typing import List

BOARD_SIZE = 7
DIRECTIONS = [HexDir.Up, HexDir.UpRight, HexDir.UpLeft, HexDir.Down, HexDir.DownLeft, HexDir.DownRight]
UNDOMIN = 0
UNDOMAX = 0


def minimaxDecision(depth, game, colour):
    """
    Find best move
    """
    operators = getOperators(game)
    best_operator = None
    best_value = float('-inf')
    for op in operators:
        game.apply_action(op)
        state = game
        value = minimaxValue(state, game, depth, colour)
        game.undo_action()
        if value > best_value:
            best_value = value
            best_operator = op

    return best_operator


def getOperators(game) -> List[Action]:
    """
    Find all valid moves
    """
    opponent_cells = getOpponentCells(game)

    # List possible SPAWN actions within 2 moves of opponent cells
    empty_cells = []
    for pos, power in opponent_cells.items():
        neighbour_opponent = getNeighbours(pos, power)

    for pos in neighbour_opponent:
        if not game._cell_occupied(pos):
            empty_cells.append(pos)
    spawn_actions = [SpawnAction(pos) for pos in empty_cells]

    # List possible SPREAD actions
    player_cells = getPlayerCells(game)
    spread_actions = []

    for pos in player_cells:
        for direction in DIRECTIONS:
            spread_actions.append(SpreadAction(pos, direction))

    return spawn_actions + spread_actions


def minimaxValue(state, game, depth, player_colour):
    """
    Calculate minimax value
    """
    # Check Terminal nodes
    if state.game_over | depth == 0:
        return utility(state)

    elif player_colour == game.turn_color:
        return maxValue(state, game, depth, float('-inf'), float('inf'))
    else:
        return minValue(state, game, depth, float('-inf'), float('inf'))


def maxValue(state, game, depth, alpha, beta):
    if state.game_over or depth == 0:
        return utility(state)

    best_score = float('-inf')
    operators = getOperators(game)

    for op in operators:
        game.apply_action(op)
        new_state = game
        score = minValue(new_state, game, depth - 1, alpha, beta)
        game.undo_action()

        best_score = max(best_score, score)

        if best_score >= beta:
            return best_score

        alpha = max(alpha, best_score)
    return best_score


def minValue(state, game, depth, alpha, beta):
    if state.game_over or depth == 0:
        return utility(state)

    best_score = float('inf')
    operators = getOperators(game)

    for op in operators:
        game.apply_action(op)
        new_state = game
        score = maxValue(new_state, game, depth - 1, alpha, beta)
        game.undo_action()
        best_score = min(best_score, score)

        if best_score <= alpha:
            return best_score

        beta = min(beta, best_score)

    return best_score


def getPlayerCells(game):
    player_cells = {}
    for pos, state in game._state.items():
        if state.player == game._turn_color:
            player_cells[pos] = state.power
    return player_cells


def getOpponentCells(game):
    opponent_cells = {}
    for pos, state in game._state.items():
        if state.player != game._turn_color and state.player != None:
            opponent_cells[pos] = state.power
    return opponent_cells


def checkCapture(pos, direction, pow, opponent_pieces):
    """
    Check if SPREAD action captures any opponent pieces
    """
    i = 1
    while i <= pow:

        newq = pos.q + i * direction.q
        newr = pos.r + i * direction.r

        if 0 > newq or newq > 6:
            newq = newq % BOARD_SIZE
        if 0 > newr or newr > 6:
            newr = newr % BOARD_SIZE

        pos = HexPos(newq, newr)
        if pos in opponent_pieces:
            return 1
        i += 1
    return 0


def utility(state):
    """
    Calculate the utility value of the given state for the given player and
    return a numeric value representing the utility
    """
    player_pieces = getPlayerCells(state)
    opponent_pieces = getOpponentCells(state)

    for pos in player_pieces:
        if isWithin2Moves(pos, opponent_pieces):
            return 1

    # # Possible SPREAD action can capture opponent's token
    # for pos in player_pieces:
    #     for direction in DIRECTIONS:
    #         pow = state._state[pos].power
    #         if checkCapture(pos, direction, pow, opponent_pieces):
    #             return 1

    return -1


def isWithin2Moves(pos, opponent_pieces):
    for opponent_pos in opponent_pieces:
        if getDistance(pos, opponent_pos) <= 2:
            return True
    return False


def getDistance(pos1, pos2):
    """
    Get the distance between two hexagonal positions
    """
    q1, r1 = pos1.q, pos1.r
    q2, r2 = pos2.q, pos2.r
    return (abs(q1 - q2) + abs(q1 + r1 - q2 - r2) + abs(r1 - r2)) // 2


def getNeighbours(cell, power):
    """
    Get surrounding cells
    """
    power = power + 1
    neighbours = []
    for dir in DIRECTIONS:
        newq = cell.q + power * dir.q
        newr = cell.r + power * dir.r

        if 0 > newq or newq > 6:
            newq = newq % BOARD_SIZE
        if 0 > newr or newr > 6:
            newr = newr % BOARD_SIZE

        neighbours.append(HexPos(newr, newq))

    return neighbours


def utilitypower(state):
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
