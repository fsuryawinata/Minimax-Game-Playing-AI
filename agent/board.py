# COMP30024 Artificial Intelligence, Semester 1 2023
# Project Part B: Game Playing Agent

from collections import defaultdict
from dataclasses import dataclass

from referee.game.hex import HexPos, HexDir
from referee.game.player import PlayerColor
from referee.game.actions import Action, SpawnAction, SpreadAction
from referee.game.exceptions import IllegalActionException
from referee.game.constants import *


# Taken from referee/game/board.py
@dataclass(frozen=True, slots=True)
class CellState:
    player: PlayerColor | None = None
    power: int = 0

    def __post_init__(self):
        if self.player is None or self.power > MAX_CELL_POWER:
            object.__setattr__(self, "power", 0)
            object.__setattr__(self, "player", None)
    def __iter__(self):
        yield self.player
        yield self.power


@dataclass(frozen=True, slots=True)
class CellMutation:
    cell: HexPos
    prev: CellState
    next: CellState

    def __str__(self):
        return f"CellMutation({self.cell}, {self.prev}, {self.next})"


# The BoardMutation class is used to represent the *minimal* set of changes in
# the state of the board as a result of an action.

@dataclass(frozen=True, slots=True)
class BoardMutation:
    action: Action
    cell_mutations: set[CellMutation]

    def __str__(self):
        return f"BoardMutation({self.cell_mutations})"

class Board:
    def __init__(self, initial_state: dict[HexPos, CellState]={}):
        self._state: dict[HexPos, CellState] = \
            defaultdict(lambda: CellState(None, 0))
        self._state.update(initial_state)
        self._turn_color: PlayerColor = PlayerColor.RED
        self._history: list[BoardMutation] = []

