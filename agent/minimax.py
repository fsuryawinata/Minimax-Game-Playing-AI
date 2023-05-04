import copy
import math

from referee.game import \
    PlayerColor, Action, SpawnAction, SpreadAction, HexPos, HexDir
from typing import List

BOARD_SIZE = 7
DIRECTIONS = [HexDir.Up, HexDir.UpRight, HexDir.UpLeft, HexDir.Down, HexDir.DownLeft, HexDir.DownRight]

prev_red_token = 0
prev_blue_token = 0

EAT_WEIGHT = 4
POWER_WEIGHT = 3
TOKEN_WEIGHT = 2
DISTANCE_WEIGHT = 1


def minimaxDecision(depth, game, colour):
    """
    Find best move
    """
    operators = getOperators(game)
    best_operator = None
    best_value = float('-inf')

    for op in operators:
        setRedTokens(game)
        setBlueTokens(game)

        state = copy.deepcopy(game)
        state.apply_action(op)

        value = minimaxValue1(state, game, depth - 1, float('-inf'), float('inf'), colour)
        #print(f"VALUE {value}")
        state.undo_action()
        if value > best_value:
            best_value = value
            best_operator = op
            #print(f"BEST VALUE {best_value} BEST OP {best_operator}")

    return best_operator

def minimaxValue(state, game, depth, alpha, beta, player_colour):
    """
    Calculate minimax value
    """
    # Check Terminal nodes
    if state.game_over or depth == 0:
        return utility(state)
    else:
        # Switch color since game's color turn is the opponent now
        player_colour = switchColour(player_colour)
        #print(f"COLOR {player_colour}, GAME TURN {game.turn_color}")

        if player_colour == game.turn_color:
            for op in getOperators(state):
                setRedTokens(game)
                setBlueTokens(game)

                new_state = copy.deepcopy(game)
                new_state.apply_action(op)
                alpha = max(alpha, minimaxValue(new_state, game, depth - 1, alpha, beta, player_colour))
                new_state.undo_action()

                if alpha >= beta:
                    break

            return alpha
        else:
            for op in getOperators(state):
                setRedTokens(game)
                setBlueTokens(game)

                new_state = copy.deepcopy(game)
                new_state.apply_action(op)
                beta = min(beta, minimaxValue(new_state, game, depth - 1, alpha, beta, player_colour))
                new_state.undo_action()

                if beta <= alpha:
                    break

            return beta

def minimaxValue1(state, game, depth, alpha, beta, player_colour):
    """
    Calculate minimax value
    """
    # Check Terminal nodes
    if state.game_over or depth == 0:
        return utility(state)
    else:
        #print(f"COLOR {player_colour}, GAME TURN {game.turn_color}")

        if player_colour == game.turn_color:
            return maxValue(state, game, depth - 1, float('-inf'), float('inf'))
        else:
            return minValue(state, game, depth - 1, float('-inf'), float('inf'))
def switchColour(colour):
    match colour:
        case PlayerColor.RED:
            return PlayerColor.BLUE
        case PlayerColor.BLUE:
            return PlayerColor.RED

def maxValue(state, game, depth, alpha, beta):
    if state.game_over or depth == 0:
        return utility(state)

    for op in getOperators(state):
        setRedTokens(game)
        setBlueTokens(game)

        new_state = copy.deepcopy(state)
        new_state.apply_action(op)
        alpha = max(alpha, minValue(new_state, game, depth - 1, alpha, beta))
        new_state.undo_action()

        if alpha >= beta:
            return alpha

    return alpha


def minValue(state, game, depth, alpha, beta):
    if state.game_over or depth == 0:
        return utility(state)

    for op in getOperators(state):
        setRedTokens(game)
        setBlueTokens(game)

        new_state = copy.deepcopy(state)
        new_state.apply_action(op)
        beta = min(beta, maxValue(new_state, game, depth - 1, alpha, beta))
        new_state.undo_action()

        if beta <= alpha:
            return beta

    return beta

def utility(state):
    """
    Calculate the utility value of the given state for the given player and
    return a numeric value representing the utility
    """
    tokens_eaten = 0

    # Check how many pieces an opponent node is eaten
    # by comparing the previous power
    player_cells = len(getPlayerCells(state))
    match state.turn_color:
        case PlayerColor.RED:
            opponent_tokens = getBlueTokens(state)
            # Token eaten
            if opponent_tokens < prev_blue_token:
                tokens_eaten = prev_blue_token - opponent_tokens
                #print(f"RED TOKENS {opponent_tokens} TOKENS EATEN {tokens_eaten}, PREV BLUE TOKEN {prev_blue_token}")

            # Player token eaten
            if player_cells < prev_red_token:
                tokens_eaten = player_cells - prev_red_token

        case PlayerColor.BLUE:
            opponent_tokens = getRedTokens(state)
            # Token eaten
            if opponent_tokens < prev_red_token:
                tokens_eaten = prev_red_token - opponent_tokens
                #print(f"BLUE TOKENS {opponent_tokens} EATEN {tokens_eaten}, PREV RED TOKEN {prev_red_token}")

            # Player token eaten
            if player_cells < prev_blue_token:
                tokens_eaten = player_cells - prev_blue_token

    # Get number of tokens on the board
    player_tokens = len(getPlayerCells(state))

    # Get total power of the player color tokens on the board
    total_power = getTotalPower(state)


    # Get the closest distance to opponent piece
    distance = getClosestDistance(state)
    utility_val = EAT_WEIGHT * tokens_eaten + POWER_WEIGHT * total_power\
                  + DISTANCE_WEIGHT * distance + TOKEN_WEIGHT * player_tokens
    return utility_val

def getClosestDistance(game):
    player_cells = getPlayerCells(game)
    opponent_cells = getOpponentCells(game)
    min_dist = float('inf')
    for player_pos in player_cells.keys():
        for opp_pos in opponent_cells.keys():
            dist = math.sqrt(abs(player_pos.r - opp_pos.r)**2 + abs(player_pos.q - opp_pos.q)**2)
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

def getOperators(game) -> List[Action]:
    """
    Find all valid moves
    """

    # List possible SPAWN actions within 2 moves of opponent cells
    empty_cells = []
    for r in range(BOARD_SIZE):
        for q in range(BOARD_SIZE):
            if not cellOccupied(HexPos(r, q), game):
                empty_cells.append(HexPos(r, q))
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


def setRedTokens(game):
    """
    Set total number of red tokens on the board before action made
    """
    global prev_red_token
    prev_red_token = 0
    for cell, state in game._state.items():
        if state.player == PlayerColor.BLUE:
            prev_red_token += 1


def getRedTokens(game):
    """
    Get total number of red tokens on the board
    """
    total_red_token = 0
    for cell, state in game._state.items():
        if state.player == PlayerColor.BLUE:
            total_red_token += 1
    return total_red_token


def setBlueTokens(game):
    """
    Set total number of blue tokens on the board before action made
    """
    global prev_blue_token
    prev_blue_token = 0
    for cell, state in game._state.items():
        if state.player == PlayerColor.BLUE:
            prev_blue_token += 1


def getBlueTokens(game):
    """
    Get total number of blue tokens on the board
    """
    total_blue_token = 0
    for cell, state in game._state.items():
        if state.player == PlayerColor.BLUE:
            total_blue_token += 1
    return total_blue_token


def getTotalPower(game):
    """
    Get total power of the player colour turn tokens on the board
    """
    total_power = 0
    for cell, state in game._state.items():
        if state.player == game.turn_color:
            total_power += state.power
    return total_power

def getHighestPower(game):
    highest_power = float('-inf')
    for cell, state in game._state.items():
        if state.player == game.turn_color:
            if state.power > highest_power:
                highest_power = state.power
    return highest_power