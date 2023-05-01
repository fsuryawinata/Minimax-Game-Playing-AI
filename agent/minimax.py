from referee.game import \
    PlayerColor, Action, SpawnAction, SpreadAction, HexPos, HexDir, Board
from typing import List

BOARD_SIZE = 7
DIRECTIONS = [HexDir.Up, HexDir.UpRight, HexDir.UpLeft, HexDir.Down, HexDir.DownLeft, HexDir.DownRight]


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
        game.undo_action()
        value = minimaxValue(state, game, depth, colour)
        if value > best_value:
            best_value = value
            best_operator = op

    return best_operator


def getOperators(game) -> List[Action]:
    """
    Find all valid moves
    """
    # List possible SPAWN actions
    empty_cells = [pos for pos in game._state.keys() if not game._cell_occupied(pos)]
    for r in range(BOARD_SIZE):
        for q in range(BOARD_SIZE):
            if not game._cell_occupied(HexPos(r, q)):
                empty_cells.append(HexPos(r, q))
    spawn_actions = [SpawnAction(pos) for pos in empty_cells]

    # List possible SPREAD actions
    player_cells = []
    spread_actions = []
    power = []

    for pos, state in game._state.items():
        if state.player == game._turn_color:
            player_cells.append(pos)
            power.append(state.power)

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
    if state.game_over | depth == 0:
        return utility(state)

    best_score = float('-inf')
    operators = getOperators(game)
    # print(f"GAME STATE {game._state.values()}")
    for op in operators:
        # print(f"TOTAL POWER {game._total_power}")
        game.apply_action(op)
        new_state = game
        game.undo_action()
        score = minValue(new_state, game, depth - 1, alpha, beta)
        best_score = max(best_score, score)
        # print(f"TOTAL POWER {game._total_power}")

        if best_score >= beta:
            return best_score

        alpha = max(alpha, best_score)

    return best_score


def minValue(state, game, depth, alpha, beta):
    if state.game_over | depth == 0:
        return utility(state)

    best_score = float('inf')
    operators = getOperators(game)

    for op in operators:
        game.apply_action(op)
        new_state = game
        game.undo_action()
        score = maxValue(new_state, game, depth - 1, alpha, beta)
        best_score = min(best_score, score)

        if best_score >= beta:
            return best_score

        beta = min(beta, best_score)

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
