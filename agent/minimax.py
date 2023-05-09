import copy
import itertools
import math

from referee.game import \
    PlayerColor, Action, SpawnAction, SpreadAction, HexPos, HexDir


ALPHA = 0.1
BOARD_SIZE = 7
DIRECTIONS = [HexDir.Up, HexDir.UpRight, HexDir.UpLeft, HexDir.Down, HexDir.DownLeft, HexDir.DownRight]

# Weights for tdLeaf heuristic
weights = {'power_diff': 0.5298628211093089,
           # 'eaten_diff': 1.8436272690352981e-13,
           # 'ally_diff': 9.218136345176491e-14,
           'token_diff': 0.40045007157768786,
           'min_dist': 0.06968610731292038}
def getDistance(game):
    """
    Get min distance from any player token to any opponent token
    """
    dist = 0
    min_dist = 0
    player_pieces, opp_pieces = getCells(game)
    for pos in player_pieces.keys():
        for opp_pos in opp_pieces.keys():
            dist = abs(pos.r - opp_pos.r) + abs(pos.q - opp_pos.q)

            if dist < min_dist:
                dist = min_dist
    return dist

def normalize_weights(weights):
    """
    Normalize weights so that they sum to 1, while preserving the signs of the original weights.
    """
    total = sum([abs(weight) for weight in weights.values()]) + 1e-6
    scaling_factor = 1.0 / total
    normalized_weights = {factor: weight * scaling_factor for factor, weight in weights.items()}
    return normalized_weights


def minimaxDecision(depth, game):
    """
    Find best move
    """
    global weights
    best_operator = None
    best_value = float('-inf')

    # Start minimax
    for op in getOperators(game):
        # Get child board with move applied
        state = copy.deepcopy(game)
        state.apply_action(op)

        # Opponent turn, depth = 2
        value, _ = minimaxValue(state, game, depth, float('-inf'), float('inf'))
        state.undo_action()

        # Get max value
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
    # Check Terminal state
    if state.game_over or depth == 0:
        return utility(state, game), weights
    else:
        # Maximising player
        if game.turn_color == state.turn_color:
            for op in getOperators(state):
                # Get child board
                new_state = copy.deepcopy(state)
                new_state.apply_action(op)

                # Get maximum between alpha and value
                alpha = max(alpha, minimaxValue(new_state, game, depth - 1, alpha, beta)[0])
                new_state.undo_action()

                # Stop minimax iteration if alpha is less than beta
                if alpha <= beta:
                    break
            return alpha, weights
        else:
            for op in getOperators(state):
                # Get child board
                new_state = copy.deepcopy(state)
                new_state.apply_action(op)

                # Player turn, depth = 1
                beta = min(beta, minimaxValue(new_state, game, depth - 1, alpha, beta)[0])
                new_state.undo_action()

                # Stop minimax iteration if beta more than alpha
                if beta >= alpha:
                    break
            return beta, weights

def utility(state, game):
    """
    Calculate the utility value of the given state for the given player and
    return a numeric value representing the utility
    """

    # Switch color to agent's color
    if state.turn_color != game.turn_color:
        switchColour(state)

    player_cells, opponent_cells = getCells(state)

    # Check if terminal state
    if state.game_over:
        if len(opponent_cells) == 0:
            return 1000
        elif len(player_cells) == 0:
            return -1000

    # Get player and opponent tokens on the board
    player_tokens = len(player_cells)
    opponent_tokens = len(opponent_cells)

    # Get token difference
    token_diff = player_tokens - opponent_tokens

    player_power, opponent_power = getPower(state)
    power_diff = player_power - opponent_power

    # player_ate, player_ally = checkEaten(state)
    # switchColour(state)
    # opponent_ate, opponent_ally = checkEaten(state)
    # switchColour(state)

    # eaten_diff = player_ate - opponent_ate
    #
    # ally_diff = player_ally - opponent_ally

    if player_tokens > 1:
        min_dist = getDistance(state)
    else:
        min_dist = 0

    val = weights["power_diff"] * power_diff + \
          weights["token_diff"] * token_diff + \
          weights["min_dist"] * min_dist
    # weights["eaten_diff"] * eaten_diff + \
    # weights["ally_diff"] * ally_diff + \

    return val

def getCells(game):
    """
    Get player and opponent cells and return as a dictionary
    """
    player_cells = {}
    opponent_cells = {}
    for pos, state in game._state.items():
        if state.player == game.turn_color:
            player_cells[pos] = state.power
        elif state.player != game.turn_color and state.player is not None:
            opponent_cells[pos] = state.power
    return player_cells, opponent_cells


def getOperators(game):
    """
    Get valid moves on the board
    """
    player_cells, opponent_cells = getCells(game)

    # Spawn if total power is less than or equal to 48
    if game._total_power <= 48:
        empty_cells = getEmptyCells(game)
        spawn_actions = [SpawnAction(pos) for pos in empty_cells]
    # Spread from every cell
    spread_actions = [SpreadAction(pos, direction) for pos in player_cells for direction in DIRECTIONS]

    return spawn_actions + spread_actions


def checkEaten(game):
    """
    Check how many opponent cells can be eaten
    """
    player_cells, opponent_cells = getCells(game)
    eaten_tokens = 0
    ally_tokens = 0

    # If player spreads, check how many opponent tokens can be eaten
    for pos, power in player_cells:
        for direction in DIRECTIONS:
            i = 0
            while i <= power:
                neighbour = pos.__add__(direction)
                if neighbour in opponent_cells:
                    eaten_tokens += 1
                elif neighbour in player_cells:
                    ally_tokens += 1
                i += 1

    return eaten_tokens, ally_tokens


def getEmptyCells(game):
    """
    Get certain empty cells of the board
    """
    player_cells, opp_cells = getCells(game)
    empty_cells = []
    reachable_cells, unreachable_cells = getUnReachableCells(opp_cells, game)

    # Token can spawn in surrounding player cells if not occupied
    for cell in player_cells:
        for direction in DIRECTIONS:
            new_pos = cell.__add__(direction)

            if not game._cell_occupied(new_pos) and new_pos not in reachable_cells:
                empty_cells.append(new_pos)

    # Add cells that are around the opponent tokens out of their reach
    empty_cells.extend(unreachable_cells)
    return empty_cells



def switchColour(game):
    """
    Switch game color turn
    """
    if game.turn_color == PlayerColor.RED:
        game._turn_color = PlayerColor.BLUE
    elif game.turn_color == PlayerColor.BLUE:
        game._turn_color = PlayerColor.RED


def getUnReachableCells(cells, game):
    """
    Get cells both out of opponent's tokens reach and within its reach
    """
    reachable_cells, unreachable_cells = [], []
    # Get cells if opponent Spreads
    for cell, power in cells.items():
        for i in range(1, power + 2):
            for direction in DIRECTIONS:
                new_pos = HexPos((cell.r + i * direction.r) % BOARD_SIZE, (cell.q + i * direction.q) % BOARD_SIZE)

                if not game._cell_occupied(new_pos):
                    # Cells that are 1 cell out of opponent's reach
                    if i == power + 1 and new_pos not in reachable_cells:
                        unreachable_cells.append(new_pos)
                    else:
                        reachable_cells.append(new_pos)
                        # Remove newly discovered reachable cells
                        if new_pos in unreachable_cells:
                            unreachable_cells.remove(new_pos)

    return reachable_cells, unreachable_cells


def getPower(game):
    """
    Get total power of the player colour turn tokens on the board
    """
    player_power = 0
    opp_power = 0
    for cell, state in game._state.items():
        if state.player == game.turn_color:
            player_power += state.power
        elif state.player != game.turn_color and state.player is not None:
            opp_power += state.power
    return player_power, opp_power

def tdleafUpdate(state):
    """
    Update weights using tdleaf
    """
    global weights
    depth = 2

    # Expected value of state
    result, _ = minimaxValue(state, state, depth, float('-inf'), float('inf'))
    # Actual value of state
    val = utility(state, state)
    # Actual number of features
    f_i = features(state)
    new_weights = {}

    # Get difference of expected and actual
    for factor in weights.keys():
        new_weights[factor] = weights[factor] + ALPHA * (result - val) * f_i[factor]
    weights = normalize_weights(new_weights)
    return weights


def features(state):
    """
    Numbers for a list of features
    """
    player_cells, opponent_cells = getCells(state)

    player_tokens = len(player_cells)
    opponent_tokens = len(opponent_cells)

    token_diff = player_tokens - opponent_tokens

    player_power, opponent_power = getPower(state)
    power_diff = player_power - opponent_power

    # player_ate, player_ally = checkEaten(state)
    # switchColour(state)
    # opponent_ate, opponent_ally = checkEaten(state)
    # switchColour(state)

    # eaten_diff = player_ate - opponent_ate
    #
    # ally_diff = player_ally - opponent_ally

    if player_tokens > 1:
        min_dist = getDistance(state)
    else:
        min_dist = 0

    return {"power_diff": power_diff,
            # "eaten_diff": eaten_diff,
            # "ally_diff": ally_diff,
            "token_diff": token_diff,
            "min_dist": min_dist}