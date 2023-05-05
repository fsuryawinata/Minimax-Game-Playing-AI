import copy
import math

from referee.game import \
    PlayerColor, Action, SpawnAction, SpreadAction, HexPos, HexDir
from typing import List

BOARD_SIZE = 7
DIRECTIONS = [HexDir.Up, HexDir.UpRight, HexDir.UpLeft, HexDir.Down, HexDir.DownLeft, HexDir.DownRight]
EAT_WEIGHT = 10
POWER_WEIGHT = 8
TOKEN_WEIGHT = 5
DISTANCE_WEIGHT = 1
ALPHA = 0.1

# Weights for tdLeaf heuristic
weights = {
    "player_power": 10,
    "opponent_power": -10,
    "highest_power": 8,
    "opponent_tokens": -5,
    "player_tokens": 5,
    "min_distance": -1,
}

def minimaxDecision(depth, game):
    """
    Find best move
    """
    global weights
    print(f"FIRST {weights}")
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
            #print(f"BEST OP {best_operator}, VAL {best_value}")

    if game.turn_count > 2:
        weights = tdleafUpdate(game)
    #print(weights)
    return best_operator


def tdleafUpdate(state):
    global weights
    depth = 2
    result, _ = minimaxValue(state, state, depth, float('-inf'), float('inf'))
    val = utility(state)
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

    min_dist = getDistance(player_cells, opponent_cells)

    return {
        "player_power": player_power,
        "opponent_power": opponent_power,
        "highest_power": highest_power,
        "player_tokens": player_tokens,
        "opponent_tokens": opponent_tokens,
        "min_distance": min_dist
    }

def minimaxValue(state, game, depth, alpha, beta):
    """
    Calculate minimax value
    """
    global weights
    # Check Terminal nodes
    if state.game_over or depth == 0:
        return utility(state), weights
    else:
        if game.turn_color == state.turn_color:
            for op in getOperators(state):
                new_state = copy.deepcopy(state)
                new_state.apply_action(op)
                #print(f"OP {op}")
                alpha = max(alpha, minimaxValue(new_state, game, depth - 1, alpha, beta)[0])
                new_state.undo_action()

                if alpha >= beta:
                    break
            return alpha, weights
        else:
            for op in getOperators(state):
                new_state = copy.deepcopy(state)
                new_state.apply_action(op)
                #print(f"OP {op}")
                # Player turn, depth = 1
                #print(f"Pos is {getPlayerCells(new_state)} Opp pos is {getOpponentCells(new_state)} op is {op}")
                beta = min(beta, minimaxValue(new_state, game, depth - 1, alpha, beta)[0])
                new_state.undo_action()

                if beta <= alpha:
                    break
            return beta, weights


def utility(state):
    """
    Calculate the utility value of the given state for the given player and
    return a numeric value representing the utility
    """

    switchColour(state)

    player_power = getPlayerPower(state)
    opponent_power = getOpponentPower(state)

    player_cells = getPlayerCells(state)
    opponent_cells = getOpponentCells(state)

    player_tokens = len(player_cells)
    opponent_tokens = len(opponent_cells)

    # Check if won
    if opponent_tokens == 0:
        return float('inf')
    elif player_tokens == 0:
        return float('-inf')
    #print(f"PLAYER {player_tokens}, OPP {opponent_tokens}")

    min_dist = getDistance(player_cells, opponent_cells)

    highest_power = getHighestPower(state)
    switchColour(state)

    val = weights["player_power"] * player_power + \
            weights["opponent_power"] * opponent_power + \
            weights["highest_power"] * highest_power + \
            weights["player_tokens"] * player_tokens + \
            weights["opponent_tokens"] * opponent_tokens + \
            weights["min_distance"] * min_dist

    #print(f"WEIGHTS {weights} UTIL {val}")
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
    opponent_cells = getOpponentCells(game)
    player_cells = getPlayerCells(game)

    # List possible SPAWN actions within 2 moves of opponent cells
    empty_cells = []
    neighbour_opponent = []
    neighbour_player = []
    for pos, power in opponent_cells.items():
        neighbour_opponent = getFarNeighbours(pos, power)

    for pos in neighbour_opponent:
        if not cellOccupied(pos, game):
            empty_cells.append(pos)

    # List possible SPAWN actions within 2 moves of pplayer cells
    for pos, power in player_cells.items():
        neighbour_player = getNeighbours(pos)

    for pos in neighbour_player:
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
