import itertools
import random
from typing import List, Optional

from networkx import Graph
from words import WordTree

CLASSIC_TILES = [
    ["A", "A", "C", "I", "O", "T"],
    ["A", "B", "I", "L", "T", "Y"],
    ["A", "B", "J", "M", "O", "Qu"],
    ["A", "C", "D", "E", "M", "P"],
    ["A", "C", "E", "L", "R", "S"],
    ["A", "D", "E", "N", "V", "Z"],
    ["A", "H", "M", "O", "R", "S"],
    ["B", "I", "F", "O", "R", "X"],
    ["D", "E", "N", "O", "S", "W"],
    ["D", "K", "N", "O", "T", "U"],
    ["E", "E", "F", "H", "I", "Y"],
    ["E", "G", "K", "L", "U", "Y"],
    ["E", "G", "I", "N", "T", "V"],
    ["E", "H", "I", "N", "P", "S"],
    ["E", "L", "P", "S", "T", "U"],
    ["G", "I", "L", "R", "U", "W"],
]
NEW_TILES = [
    ["A", "A", "E", "E", "G", "N"],
    ["A", "B", "B", "J", "O", "O"],
    ["A", "C", "H", "O", "P", "S"],
    ["A", "F", "F", "K", "P", "S"],
    ["A", "O", "O", "T", "T", "W"],
    ["C", "I", "M", "O", "T", "U"],
    ["D", "E", "I", "L", "R", "X"],
    ["D", "E", "L", "R", "V", "Y"],
    ["D", "I", "S", "T", "T", "Y"],
    ["E", "E", "G", "H", "N", "W"],
    ["E", "E", "I", "N", "S", "U"],
    ["E", "H", "R", "T", "V", "W"],
    ["E", "I", "O", "S", "S", "T"],
    ["E", "L", "R", "T", "T", "Y"],
    ["H", "I", "M", "N", "U", "Qu"],
    ["H", "L", "N", "N", "R", "Z"],
]


class Cell:
    def __init__(self, tile: List[str]) -> None:
        self.face: str = random.choice(tile)
        self.adjacent: List[Cell] = []
        self._hash = sum(sum(ord(char) for char in face) for face in tile)

    def __hash__(self) -> int:
        return self._hash

    def __str__(self) -> str:
        return self.face

    def __repr__(self) -> str:
        return f"Cell {self.face}"


class BoggleBoard:
    def __init__(self, tiles: str = "classic") -> None:
        if tiles == "classic":
            self.tiles = CLASSIC_TILES
        elif tiles == "new":
            self.tiles = NEW_TILES
        else:
            raise ValueError(f"Invalid tile set {tiles}.")
        self.cells: List[List[Cell]] = self.create_cells()
        self.adjacency = self.create_adjacency_graph()
        self.word_tree = WordTree("pyboggle/word_lists/csw15.txt")

    def create_cells(self):
        random.shuffle(self.tiles)
        cells = []
        for i in range(4):
            cell_row = []
            for j in range(4):
                tile = self.tiles[(i * 4) + j]
                cell_row.append(Cell(tile))
            cells.append(cell_row)
        # self._set_adjacent_cells(cells)
        return cells

    def print(self):
        for cell_row in self.cells:
            print(" ".join(str(cell).ljust(2) for cell in cell_row))

    def create_adjacency_graph(self):
        graph = Graph()
        for y, cell_row in enumerate(self.cells):
            for x, cell in enumerate(cell_row):
                idx_adjustments = (-1, 0, 1)
                adjustments = list(itertools.product(idx_adjustments, idx_adjustments))
                adjusted_idxs = set((x + i, y + j) for i, j in adjustments)
                for adjusted_x, adjusted_y in adjusted_idxs:
                    if adjusted_y < 0 or adjusted_x < 0:
                        continue
                    try:
                        adj_cell = self.cells[adjusted_y][adjusted_x]
                    except IndexError:
                        continue
                    if cell != adj_cell:
                        graph.add_edge(cell, adj_cell)
        return graph

    def solver(self):
        """
        Get list of all words that exist in board.
        """
        words = set()
        cells = itertools.chain(*self.cells)
        combinations = itertools.combinations(cells, 2)
        for cell1, cell2 in combinations:
            paths = self._all_simple_paths_graph(cell1, cell2)
            reversed_paths = self._all_simple_paths_graph(cell2, cell1)
            all_paths = itertools.chain(paths, reversed_paths)
            for path in all_paths:
                if path:
                    if self.word_tree.exists(
                        word := "".join(cell.face for cell in path)
                    ):
                        words.add(word)
        return words

    def _all_simple_paths_graph(self, source: Cell, target: Cell):
        """
        A modified version of

        Args:
            source (Cell): _description_
            target (Cell): _description_

        Yields:
            _type_: _description_
        """
        targets = set([target])
        cutoff = len(self.adjacency) - 1
        visited = dict.fromkeys([source])
        stack = [iter(self.adjacency[source])]
        while stack:
            if visited_word := "".join(cell.face for cell in visited.keys()):
                if self.word_tree.search_path(visited_word) is None:
                    # early exit this path if not valid in self.word_tree.tree
                    stack.pop()
                    visited.popitem()
                    continue
            children = stack[-1]
            child: Optional[Cell] = next(children, None)
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


if __name__ == "main":
    a = BoggleBoard()
    a.solver()
