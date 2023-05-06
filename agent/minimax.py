import copy
import itertools
import math

from referee.game import \
    PlayerColor, Action, SpawnAction, SpreadAction, HexPos, HexDir

BOARD_SIZE = 7
DIRECTIONS = [HexDir.Up, HexDir.UpRight, HexDir.UpLeft, HexDir.Down, HexDir.DownLeft, HexDir.DownRight]

ALPHA = 0.1

# Weights for tdLeaf heuristic
weights = {'power_diff': 0.059322496534763715, 'eaten_diff': 0.45826712894256777, 'ally_diff': 0.22913356447128388, 'token_diff': -0.16017352690800643, 'min_dist': 0.09310228314337837}


def normalize_weights(weights):
    """
    Normalize a dictionary of weights so that they sum to 1, while preserving the signs of the original weights.
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

    for op in getOperators(game):
        state = copy.deepcopy(game)
        state.apply_action(op)

        # Opponent turn, depth = 2
        value, _ = minimaxValue(state, game, depth, float('-inf'), float('inf'))
        state.undo_action()
        if value > best_value:
            best_value = value
            best_operator = op

    if game.turn_count > 2:
        weights = tdleafUpdate(game)

    print(weights)

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

                if alpha <= beta:
                    break
            return alpha, weights
        else:
            for op in getOperators(state):
                new_state = copy.deepcopy(state)
                new_state.apply_action(op)
                # Player turn, depth = 1
                beta = min(beta, minimaxValue(new_state, game, depth - 1, alpha, beta)[0])
                new_state.undo_action()

                if beta >= alpha:
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
    player_cells, opponent_cells = getCells(state)
    # Switch color to agent's color
    if state.turn_color != game.turn_color:
        switchColour(state)

    # Check if won
    if state.game_over:
        if len(opponent_cells) == 0:
            return float('1000')
        elif len(player_cells) == 0:
            return float('-1000')

    player_tokens = len(player_cells)
    opponent_tokens = len(opponent_cells)

    token_diff = player_tokens - opponent_tokens

    player_power, opponent_power = getPower(state)
    power_diff = player_power - opponent_power

    player_ate, player_ally = checkEaten(state)
    switchColour(state)
    opponent_ate, opponent_ally = checkEaten(state)
    switchColour(state)

    eaten_diff = player_ate - opponent_ate

    ally_diff = player_ally - opponent_ally

    highest_power = getHighestPower(game)

    if player_tokens > 1:
        min_dist = getDistance(player_cells)
    else:
        min_dist = 0

    val = weights["power_diff"] * power_diff + \
          weights["eaten_diff"] * eaten_diff + \
          weights["ally_diff"] * ally_diff + \
          weights["token_diff"] * token_diff + \
          weights["min_dist"] * min_dist

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
    player_cells, opponent_cells = getCells(game)
    min_dist = float('inf')
    for player_pos in player_cells.keys():
        for opp_pos in opponent_cells.keys():
            dist = math.sqrt(abs(player_pos.r - opp_pos.r) ** 2 + abs(player_pos.q - opp_pos.q) ** 2)
            if dist < min_dist:
                min_dist = dist
    return min_dist


def getCells(game):
    player_cells = {}
    opponent_cells = {}
    for pos, state in game._state.items():
        if state.player == game.turn_color:
            player_cells[pos] = state.power
        elif state.player != game.turn_color and state.player is not None:
            opponent_cells[pos] = state.power
    return player_cells, opponent_cells


def getOperators(game):
    player_cells, opponent_cells = getCells(game)
    empty_cells = getEmptyCells(game)
    spawn_actions = [SpawnAction(pos) for pos in empty_cells]
    spread_actions = [SpreadAction(pos, dir) for pos in player_cells for dir in DIRECTIONS]

    return spawn_actions + spread_actions


def checkEaten(game):
    player_cells, opponent_cells = getCells(game)
    eaten_tokens = 0
    ally_tokens = 0
    for pos, power in player_cells:
        for dir in DIRECTIONS:
            i = 0
            while i <= power:
                neighbour = pos.__add__(dir)
                if neighbour in opponent_cells:
                    eaten_tokens += 1
                elif neighbour in player_cells:
                    ally_tokens += 1
                i += 1

    return eaten_tokens, ally_tokens


def cellOccupied(cell, game):
    return game._state[cell].player is not None


def getDistance(player_pieces):
    return min(abs(p1.r - p2.r) + abs(p1.q - p2.q) for p1, p2 in itertools.combinations(player_pieces, 2))


def getEmptyCells(game):
    player_cells, opp_cells = getCells(game)
    empty_cells = []
    reachable_cells, unreachable_cells = getUnReachableCells(opp_cells, game)

    for cell in player_cells:
        for dir in DIRECTIONS:
            new_pos = HexPos((cell.r + dir.r) % BOARD_SIZE, (cell.q + dir.q) % BOARD_SIZE)

            if not cellOccupied(new_pos, game) and new_pos not in reachable_cells:
                empty_cells.append(new_pos)

    empty_cells.extend(unreachable_cells)
    return empty_cells


def getUnReachableCells(cells, game):
    reachable_cells, unreachable_cells = [], []
    for cell, power in cells.items():
        for i in range(1, power + 2):
            for dir in DIRECTIONS:
                new_pos = HexPos((cell.r + i * dir.r) % BOARD_SIZE, (cell.q + i * dir.q) % BOARD_SIZE)

                if not cellOccupied(new_pos, game):
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
    weights = normalize_weights(new_weights)
    return weights


def features(state):
    """
    Number for a list of features
    """
    player_cells, opponent_cells = getCells(state)

    player_tokens = len(player_cells)
    opponent_tokens = len(opponent_cells)

    token_diff = player_tokens - opponent_tokens

    player_power, opponent_power = getPower(state)
    power_diff = player_power - opponent_power

    player_ate, player_ally = checkEaten(state)
    switchColour(state)
    opponent_ate, opponent_ally = checkEaten(state)
    switchColour(state)

    eaten_diff = player_ate - opponent_ate

    ally_diff = player_ally - opponent_ally

    if player_tokens > 1:
        min_dist = getDistance(player_cells)
    else:
        min_dist = 0

    return {"power_diff": power_diff,
            "eaten_diff": eaten_diff,
            "ally_diff": ally_diff,
            "token_diff": token_diff,
            "min_dist": min_dist}

