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
        neighbour_opponent = getFarNeighbours(pos, power)

    for pos in neighbour_opponent:
        if not cellOccupied(pos, game):
            empty_cells.append(pos)
    spawn_actions = [SpawnAction(pos) for pos in empty_cells]

    # List possible SPREAD actions
    player_cells = getPlayerCells(game)
    spread_actions = []

    for pos in player_cells:
        for direction in DIRECTIONS:
            spread_actions.append(SpreadAction(pos, direction))


    return spawn_actions + spread_actions

def cellOccupied(cell, game):
    """
    Check whether the cell is occupied
    """
    if game._state[cell].player == None:
        return False
    return True


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
    # Check if game is over
    if state.game_over:
        if state.winner_color == state._turn_color:
            return float('inf')
        elif state.winner_color != state._turn_color:
            return float('-inf')
        else:
            return 0

    player_pieces = getPlayerCells(state)
    opponent_pieces = getOpponentCells(state)

    # Check if power stays the same
    player_power = sum(player_pieces.values())
    opponent_power = sum(opponent_pieces.values())
    distance = getDistance(player_pieces, opponent_pieces)

    # if the player's power is lower than the opponent's power, prioritize increasing power
    if player_power < opponent_power:
        return 1 / player_power

    # if the player's power is higher than the opponent's power, prioritize reducing distance
    elif player_power > opponent_power:
        if distance <= 2:
            return 100 - distance
        else:
            return 1 / distance

    else:
        # Check if piece is close to opponent piece
        for pos in player_pieces.keys():
            neighbours = getNeighbours(pos)
            for neighbour in neighbours:
                if neighbour in opponent_pieces:
                    return -1

    return 1

def utilityChatGPT(state):
    """
    Calculate the utility value of the given state for the given player and
    return a numeric value representing the utility
    """
    # Check if game is over
    if state.game_over:
        if state.winner_color == state._turn_color:
            return float('inf')
        elif state.winner_color != state._turn_color:
            return float('-inf')
        else:
            return 0

    player_pieces = getPlayerCells(state)
    opponent_pieces = getOpponentCells(state)

    player_power = sum(player_pieces.values())
    opponent_power = sum(opponent_pieces.values())

    distance = getDistance(player_pieces, opponent_pieces)

    # if the player's power is lower than the opponent's power, prioritize increasing power
    if player_power < opponent_power:
        return 1 / player_power

    # if the player's power is higher than the opponent's power, prioritize reducing distance
    elif player_power > opponent_power:
        if distance <= 2:
            return 100 - distance
        else:
            return 1 / distance

    # if the player's power is equal to the opponent's power, break the tie by reducing distance
    else:
        if distance <= 2:
            return 100 - distance
        else:
            return 1 / distance


def getDistance(player_pieces, opponent_pieces):
    """
    Get manhattan distance to closest opponent piece
    """
    min_distance = float('inf')
    for player_pos in player_pieces:
        for opp_pos in opponent_pieces:
            distance = abs(player_pos.r - opp_pos.r) + abs(player_pos.q - opp_pos.q)
            if distance < min_distance:
                min_distance = distance
    return min_distance

def getNeighbours(cell):
    """
    Get surrounding cells
    """
    neighbours = []
    for dir in DIRECTIONS:
        newq = cell.q + dir.q
        newr = cell.r + dir.r

        if 0 > newq or newq > 6:
            newq = newq % BOARD_SIZE
        if 0 > newr or newr > 6:
            newr = newr % BOARD_SIZE

        neighbours.append(HexPos(newr, newq))

    return neighbours

def getFarNeighbours(cell, power):
    """
    Get cells out of opponent's reach
    """
    power = power + 2
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
