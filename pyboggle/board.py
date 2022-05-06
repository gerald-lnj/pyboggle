import curses
import itertools
import random
from dataclasses import dataclass
from functools import cached_property
from typing import List, Optional, Set, Tuple, Union

from networkx import Graph, is_simple_path

from .words import WordTree

CLASSIC_TILES = [
    ("A", "A", "C", "I", "O", "T"),
    ("A", "B", "I", "L", "T", "Y"),
    ("A", "B", "J", "M", "O", "Qu"),
    ("A", "C", "D", "E", "M", "P"),
    ("A", "C", "E", "L", "R", "S"),
    ("A", "D", "E", "N", "V", "Z"),
    ("A", "H", "M", "O", "R", "S"),
    ("B", "I", "F", "O", "R", "X"),
    ("D", "E", "N", "O", "S", "W"),
    ("D", "K", "N", "O", "T", "U"),
    ("E", "E", "F", "H", "I", "Y"),
    ("E", "G", "K", "L", "U", "Y"),
    ("E", "G", "I", "N", "T", "V"),
    ("E", "H", "I", "N", "P", "S"),
    ("E", "L", "P", "S", "T", "U"),
    ("G", "I", "L", "R", "U", "W"),
]
NEW_TILES = [
    ("A", "A", "E", "E", "G", "N"),
    ("A", "B", "B", "J", "O", "O"),
    ("A", "C", "H", "O", "P", "S"),
    ("A", "F", "F", "K", "P", "S"),
    ("A", "O", "O", "T", "T", "W"),
    ("C", "I", "M", "O", "T", "U"),
    ("D", "E", "I", "L", "R", "X"),
    ("D", "E", "L", "R", "V", "Y"),
    ("D", "I", "S", "T", "T", "Y"),
    ("E", "E", "G", "H", "N", "W"),
    ("E", "E", "I", "N", "S", "U"),
    ("E", "H", "R", "T", "V", "W"),
    ("E", "I", "O", "S", "S", "T"),
    ("E", "L", "R", "T", "T", "Y"),
    ("H", "I", "M", "N", "U", "Qu"),
    ("H", "L", "N", "N", "R", "Z"),
]


@dataclass(frozen=True)
class Dice:
    """
    An object that represents a single physical dice
    on a physical Boggle board.
    """

    faces: Tuple[str]

    @cached_property
    def face(self):
        """Exploit cached property to always reuse the first randomly chosen face."""
        return random.choice(self.faces)


class BoggleBoard:
    """
    An object that represents a physical Boggle board, of size 4 x 4.
    Each dice/tile/dice (the chosen term is dice) is represented by a Dice object.
    """

    def __init__(self, tiles: str = "classic") -> None:
        if tiles == "classic":
            self.tiles = CLASSIC_TILES
        elif tiles == "new":
            self.tiles = NEW_TILES
        else:
            raise ValueError(f"Invalid tile set {tiles}.")
        self.dice: List[List[Dice]] = self._create_dice()
        self.adjacency = self._create_adjacency_graph()
        filter = "".join(d.face for d in itertools.chain(*self.dice))
        self.word_tree = WordTree("pyboggle/word_lists/csw15.txt", filter=filter)

    def _create_dice(self) -> List[List[Dice]]:
        """
        Randomly creates 4x4 Dice based on a chosen tileset.

        Returns:
            List[List[Dice]]: 2D list of Dice
        """
        random.shuffle(self.tiles)
        dice = []
        for i in range(4):
            dice_row = []
            for j in range(4):
                tile = self.tiles[(i * 4) + j]
                dice_row.append(Dice(tile))
            dice.append(dice_row)
        return dice

    def _create_adjacency_graph(self) -> Graph:
        """
        Generates an internal adjacency graph to record positions of Dice.

        Returns:
            Graph: Undirected graph which contains information of Dice positions.
                Each node label is a Dice object, with no node attributes.
        """
        graph = Graph()
        for y, dice_row in enumerate(self.dice):
            for x, dice in enumerate(dice_row):
                idx_adjustments = (-1, 0, 1)
                adjustments = list(itertools.product(idx_adjustments, idx_adjustments))
                adjusted_idxs = set((x + i, y + j) for i, j in adjustments)
                for adjusted_x, adjusted_y in adjusted_idxs:
                    if adjusted_y < 0 or adjusted_x < 0:
                        continue
                    try:
                        adj_dice = self.dice[adjusted_y][adjusted_x]
                    except IndexError:
                        continue
                    if dice != adj_dice:
                        graph.add_edge(dice, adj_dice)
        return graph

    def _all_simple_paths_graph(self, source: Dice, target: Dice):
        """
        A modified version of networkx.algorithms._all_simple_paths_graph.
        Carries out all path traversals similar to the original, but early
        exits when an invalid path according to word.WordTree.tree is encountered.

        Args:
            source (Dice): A Dice object in self.adjacency
            target (Dice): A Dice object in self.adjacency

        Yields:
            List[Dice]: A list of Dice objects forming a path.
                This will be a valid path, but may not be a valid word.
        """
        # modification 1: accept a single target directly
        targets = set([target])
        cutoff = len(self.adjacency) - 1
        visited = dict.fromkeys([source])
        stack = [iter(self.adjacency[source])]
        while stack:
            # modification 2: add early exit check for path traversal
            if visited_word := "".join(dice.face for dice in visited.keys()):
                if self.word_tree.search_path(visited_word) is None:
                    # early exit this path if not valid in self.word_tree.tree
                    stack.pop()
                    visited.popitem()
                    continue
            children = stack[-1]
            child: Optional[Dice] = next(children, None)
            if child is None:
                stack.pop()
                visited.popitem()
            elif len(visited) < cutoff:
                if child in visited:
                    continue
                if child in targets:
                    if self.word_tree.search_path(visited_word + child.face):
                        yield list(visited) + [child]
                visited[child] = None
                if targets - set(visited.keys()):  # expand stack until find all targets
                    stack.append(iter(self.adjacency[child]))
                else:
                    visited.popitem()  # maybe other ways to child
            else:  # len(visited) == cutoff:
                for target in (targets & (set(children) | {child})) - set(
                    visited.keys()
                ):
                    yield list(visited) + [target]
                stack.pop()
                visited.popitem()

    def _is_valid_path(self, word: str) -> bool:
        """
        Given a word, make a generator of all possible dice paths that can make that word,
        and check if any of those paths are valid in self.adjacency.

        Args:
            word (str): Word to check.

        Returns:
            bool: Whether word is a valid path or not
        """
        all_dice = list(itertools.chain(*self.dice))
        # for each char, a generator of dice which has the correct face
        matching_dice = [
            [dice for dice in all_dice if dice.face == char] for char in word
        ]
        path_permutations = list(itertools.product(*matching_dice))
        return any(is_simple_path(self.adjacency, path) for path in path_permutations)

    def solver(self) -> Set[str]:
        """
        Get list of all words that exist in board.

        Returns:
            Set[str]: Set of all valid words in board.
        """
        words: Set[str] = set()
        dice = itertools.chain(*self.dice)
        combinations = itertools.combinations(dice, 2)
        for dice1, dice2 in combinations:
            paths = self._all_simple_paths_graph(dice1, dice2)
            reversed_paths = self._all_simple_paths_graph(dice2, dice1)
            all_paths = itertools.chain(paths, reversed_paths)
            for path in all_paths:
                if path:
                    if self.word_tree.exists(
                        word := "".join(dice.face for dice in path)
                    ):
                        words.add(word)
        print(f"All possible words: {sorted(words)}")
        print(f"Board score: {self.scorer(words)}")
        return words

    def scorer(self, words: Union[Set[str], str]):
        """
        Get score of word(s) as int. Assumes valid word.
        """
        if type(words) is str:
            words = set([words])
        scoring = {
            3: 1,
            4: 1,
            5: 2,
            6: 3,
            7: 5,
            8: 11,
        }
        total_points = 0
        for word in words:
            assert (length := len(word)) >= 3, "Words must be at least 3 letters."
            length = min(8, length)
            total_points += scoring[length]
        return total_points

    def attempt_word(self, word: str) -> Optional[int]:
        """Check if word is possible in board, and exists in word list"""
        if self._is_valid_path(word) and self.word_tree.exists(word):
            return self.scorer(word)

    def _start_game(self, stdscr: curses.window):
        def update_display(
            stdscr: curses.window, words: List[str], points: int, msg: str
        ):
            stdscr.clear()
            stdscr.addstr(str(self))
            stdscr.addstr(f"\n\nCurrent words: {', '.join(words)}")
            stdscr.addstr(f"\nCurrent points: {points}")
            stdscr.addstr(f"\n{msg}")
            stdscr.refresh()

        current_points = 0
        current_words: List[str] = []
        input: List[str] = []
        msg = ""

        while True:
            update_display(stdscr, current_words, current_points, msg)
            msg = ""
            c = stdscr.getkey()
            if c == "\x1b":  # escape key
                curses.endwin()
                stdscr.erase()
                return current_words, current_points
            elif c == "\n":  # enter
                word = "".join(input)
                score = self.attempt_word(word)
                if score:
                    if word not in current_words:
                        current_words.append(word)
                        current_points += score
                        msg = f"{word} was worth {score} points"
                    else:
                        msg = f"You have already guessed {word}"
                else:
                    msg = f"{word} is not a valid word"
                input = []

            else:
                if c.isalpha():
                    input.append(c.upper())

    def start_game(self):
        words, points = curses.wrapper(self._start_game)
        print(f"Guessed words: {', '.join(words)}")
        print(f"Total points: {points}")

    def __str__(self) -> str:
        return "\n".join(
            " ".join(dice.face.ljust(2) for dice in dice_row) for dice_row in self.dice
        )


if __name__ == "main":
    a = BoggleBoard()
    a.solver()
