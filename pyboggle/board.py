import itertools
import random
from pprint import pprint
from typing import Iterable, List, Set

import matplotlib.pyplot as plt
from networkx import Graph, all_simple_paths, draw_networkx, shortest_path
from networkx.algorithms.traversal import dfs_edges
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
        for y, cell_row in enumerate(self.cells):
            for x, cell in enumerate(cell_row):
                self.solve_cell(cell)

    def solve_cell(self, cell: Cell, source: int = 0, visited_cells: Set[Cell] = set()):
        print(f"\ntesting {[str(i) for i in visited_cells] + [str(cell)]}")
        # print(f"visited: {visited_cells}")
        if self.word_tree.tree.out_degree(source) == 0:
            # leaf encountered, valid word
            print(shortest_path(self.word_tree.tree, 0, source))

        successor_nodes: Iterable[int] = self.word_tree.tree.successors(source)
        cell_node = next(
            (
                node
                for node in successor_nodes
                if a.word_tree.tree.nodes[node]["source"] == cell.face
            ),
            None,
        )
        if cell_node is not None:
            visited_cells.add(cell)
            adj_cells: Set[Cell] = set(self.adjacency.neighbors(cell))
            next_cells = adj_cells.difference(visited_cells)
            for adj_cell in next_cells:
                self.solve_cell(adj_cell, cell_node, visited_cells)
        else:
            print("end encountered")

    def _all_simple_paths_graph(self, source: Cell, target: Cell):
        targets = set([target])
        cutoff = len(self.adjacency) - 1
        visited = dict.fromkeys([source])
        stack = [iter(self.adjacency[source])]
        while stack:

            children = stack[-1]
            child = next(children, None)
            if child is None:
                stack.pop()
                visited.popitem()
            elif len(visited) < cutoff:
                if child in visited:
                    continue
                if child in targets:
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
    a.test()
    pprint(list(dfs_edges(a.adjacency)))
    draw_networkx(G=a.adjacency)
    all_simple_paths(a.adjacency, a.cells[0][0], a.cells[3][3])
    plt.show()
    list(a._all_simple_paths_graph(a.cells[0][0], a.cells[3][3]))
