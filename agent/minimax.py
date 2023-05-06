import copy
import math

from referee.game import \
    PlayerColor, Action, SpawnAction, SpreadAction, HexPos, HexDir
from typing import List

BOARD_SIZE = 7
DIRECTIONS = [HexDir.Up, HexDir.UpRight, HexDir.UpLeft, HexDir.Down, HexDir.DownLeft, HexDir.DownRight]

ALPHA = 0.1

# Weights for tdLeaf heuristic
weights = {
    "player_power": 1,
    "opponent_power": -1,
    "highest_power": 0.7,
    "player_tokens": 0.5,
    "opponent_tokens": -0.5,
    "min_dist": -0.3,
}


def minimaxDecision(depth, game):
    """
    Find best move
    """
    global weights
    best_operator = None
    best_value = float('-inf')

    for op in getOperators(game):
        state = copy.deepcopy(game)
        state.apply_action(op)

        # Opponent turn, depth = 2
        value, _ = minimaxValue(state, game, depth, float('-inf'), float('inf'))
        state.undo_action()
        if value > best_value:
            best_value = value
            best_operator = op

    # if game.turn_count > 2:
    #     weights = tdleafUpdate(game)
    #
    # print(weights)

    return best_operator

def minimaxValue(state, game, depth, alpha, beta):
    """
    Calculate minimax value
    """
    global weights
    # Check Terminal nodes
    if state.game_over or depth == 0:
        # print(f"GAME OVER? {game_over(state)} VALUE {utility(state, game)} GAME TURN IS {game.turn_color}")
        return utility(state, game), weights
    else:
        if game.turn_color == state.turn_color:
            for op in getOperators(state):
                new_state = copy.deepcopy(state)
                new_state.apply_action(op)
                alpha = max(alpha, minimaxValue(new_state, game, depth - 1, alpha, beta)[0])
                new_state.undo_action()

                if alpha >= beta:
                    break
            return alpha, weights
        else:
            for op in getOperators(state):
                new_state = copy.deepcopy(state)
                new_state.apply_action(op)
                # Player turn, depth = 1
                beta = min(beta, minimaxValue(new_state, game, depth - 1, alpha, beta)[0])
                new_state.undo_action()

                if beta <= alpha:
                    break
            # print(f"MINIMUM {beta}")
            return beta, weights

def game_over(state):
    red_pow = 0
    blue_pow = 0
    for state in state._state.values():
        if state.player == PlayerColor.RED:
            red_pow += state.power
        elif state.player == PlayerColor.BLUE:
            blue_pow += state.power

    if red_pow == 0 or blue_pow == 0:
        return True
    return False


def utility(state, game):
    """
    Calculate the utility value of the given state for the given player and
    return a numeric value representing the utility
    """
    # Switch color to agent's color
    if state.turn_color != game.turn_color:
        switchColour(state)

    # Check if won
    if state.game_over:
        if len(getOpponentCells(state)) == 0:
            return float('1000')
        elif len(getPlayerCells(state)) == 0:
            return float('-1000')

    player_cells = getPlayerCells(state)
    opponent_cells = getOpponentCells(state)

    player_tokens = len(player_cells)
    opponent_tokens = len(opponent_cells)

    player_power = getPlayerPower(state)
    opponent_power = getOpponentPower(state)

    highest_power = getHighestPower(state)

    if player_tokens > 1:
        min_dist = getDistance(player_cells)
    else:
        min_dist = 0

    val = weights["player_power"] * player_power + \
          weights["opponent_power"] * opponent_power + \
          weights["highest_power"] * highest_power + \
          weights["player_tokens"] * player_tokens + \
          weights["opponent_tokens"] * opponent_tokens + \
          weights["min_dist"] * min_dist

    # print(f"{state.turn_color} POW {player_power} + OPP POW {opponent_power} +"
    #   f" HIGHEST POW {highest_power} + PLAY TOK {player_tokens} + OPP TOK {opponent_tokens} + MIN DIST {min_dist} "
    #   f"= {val}")

    # Switch back
    if state.turn_color != game.turn_color:
        switchColour(game)
    return val


def switchColour(game):
    match game.turn_color:
        case PlayerColor.RED:
            game._turn_color = PlayerColor.BLUE
        case PlayerColor.BLUE:
            game._turn_color = PlayerColor.RED


def getClosestDistance(game):
    player_cells = getPlayerCells(game)
    opponent_cells = getOpponentCells(game)
    min_dist = float('inf')
    for player_pos in player_cells.keys():
        for opp_pos in opponent_cells.keys():
            dist = math.sqrt(abs(player_pos.r - opp_pos.r) ** 2 + abs(player_pos.q - opp_pos.q) ** 2)
            if dist < min_dist:
                min_dist = dist
    return min_dist


def getPlayerCells(game):
    player_cells = {}
    for pos, state in game._state.items():
        if state.player == game.turn_color:
            player_cells[pos] = state.power
    return player_cells


def getOpponentCells(game):
    opponent_cells = {}
    for pos, state in game._state.items():
        if state.player != game.turn_color and state.player is not None:
            opponent_cells[pos] = state.power
    return opponent_cells


def getOperators(game) -> List[Action]:
    """
    Find all valid moves
    """
    empty_cells = getEmptyCells(game)
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


def getDistance(player_pieces):
    """
    Get minimum Manhattan distance to any other player piece
    """
    min_distance = float('inf')
    for i, piece1 in enumerate(player_pieces):
        for j, piece2 in enumerate(player_pieces):
            if i < j:
                distance = abs(piece1.r - piece2.r) + abs(piece1.q - piece2.q)
                if distance < min_distance:
                    min_distance = distance
    return min_distance


def getEmptyCells(game):
    """
    Get neighbor player cells and cells out of opponent's reach
    """
    reachable_cells, unreachable_cells = getUnReachableCells(getOpponentCells(game), game)

    player_cells = getPlayerCells(game)
    empty_cells = []
    for cell in player_cells.keys():
        for dir in DIRECTIONS:
            newq = cell.q + dir.q
            newr = cell.r + dir.r

            if 0 > newq or newq > 6:
                newq = newq % BOARD_SIZE
            if 0 > newr or newr > 6:
                newr = newr % BOARD_SIZE

            new_pos = HexPos(newr, newq)
            if not cellOccupied(new_pos, game):
                if new_pos not in unreachable_cells:
                    empty_cells.append(new_pos)

    empty_cells.extend(reachable_cells)
    return empty_cells


def getUnReachableCells(cells, game):
    """
    Get cells that opponent can and cannot reach
    """
    unreachable_cells = []
    reachable_cells = []
    for cell, power in cells.items():
        i = 1
        while i <= power + 1:
            for dir in DIRECTIONS:
                newq = cell.q + i * dir.q
                newr = cell.r + i * dir.r

                if 0 > newq or newq > 6:
                    newq = newq % BOARD_SIZE
                if 0 > newr or newr > 6:
                    newr = newr % BOARD_SIZE

                new_pos = HexPos(newr, newq)
                if not cellOccupied(new_pos, game):
                    if i == power + 1:
                        unreachable_cells.append(new_pos)
                    else:
                        reachable_cells.append(new_pos)

            i += 1

    return reachable_cells, unreachable_cells


def getPlayerPower(game):
    """
    Get total power of the player colour turn tokens on the board
    """
    total_power = 0
    for cell, state in game._state.items():
        if state.player == game.turn_color:
            total_power += state.power
    return total_power


def getOpponentPower(game):
    """
    Get total power of the player colour turn tokens on the board
    """
    total_power = 0
    for cell, state in game._state.items():
        if state.player != game.turn_color and state.player is not None:
            total_power += state.power
    return total_power


def getHighestPower(game):
    highest_power = float('-inf')
    for cell, state in game._state.items():
        if state.player == game.turn_color:
            if state.power > highest_power:
                highest_power = state.power
    return highest_power

def tdleafUpdate(state):
    global weights
    depth = 2
    result, _ = minimaxValue(state, state, depth, float('-inf'), float('inf'))
    val = utility(state, state)
    f_i = features(state)
    new_weights = {}
    for factor in weights.keys():
        new_weights[factor] = weights[factor] + ALPHA * (result - val) * f_i[factor]
    weights = new_weights
    return weights


def features(state):
    """
    Number for a list of features
    """
    player_power = getPlayerPower(state)
    opponent_power = getOpponentPower(state)

    player_cells = getPlayerCells(state)
    opponent_cells = getOpponentCells(state)

    player_tokens = len(player_cells)
    opponent_tokens = len(opponent_cells)

    highest_power = getHighestPower(state)

    if player_tokens > 1:
        min_dist = getDistance(player_cells)
    else:
        min_dist = 0

    return {
        "player_power": player_power,
        "opponent_power": opponent_power,
        "highest_power": highest_power,
        "player_tokens": player_tokens,
        "opponent_tokens": opponent_tokens,
        "min_dist": min_dist,
    }
