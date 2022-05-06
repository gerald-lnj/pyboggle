from functools import cache, lru_cache
from typing import Optional, Sequence

from networkx.generators.trees import prefix_tree


def _file_lines_iterator(wordlist_filepath: str):
    with open(wordlist_filepath) as fobj:
        for line in fobj:
            if line != "\n":
                yield line.strip()


@cache
def prefix_tree_from_filepath(wordlist_filepath: str):
    return prefix_tree(_file_lines_iterator(wordlist_filepath))


class WordTree:
    def __init__(self, wordlist_filepath: str) -> None:
        self.tree = prefix_tree_from_filepath(wordlist_filepath)
        self.exists = lru_cache()(self._exists)
        self.search_path = lru_cache()(self._search_path)

    def _exists(self, word: str):
        if len(word) < 3:
            # Boggle rules: word must be at least 3 letters
            return False
        node_label = self._search_path(word)
        if node_label is None:
            return False
        return -1 in self.tree.successors(node_label)

    def _search_path(self, word: Sequence[str], node: int = 0) -> Optional[int]:
        """
        A recursive method that checks if supplied sequence of letters
        is a valid path (valid word) in self.tree.

        Args:
            word (Sequence[str]): A sequence of str. Likely a str, or a list of str.
            node (int, optional): The node to start searching from. Defaults to 0.

        Returns:
            Optional[int]: None if path does not exist,
            otherwise the node label of the last element.
        """
        if len(word) == 0:
            # base case reached, word sequence is a valid path.
            return node

        # get node where node["source"] == word[0]
        next_node = next(
            (
                node
                for node in self.tree[node]
                if self.tree.nodes[node]["source"] == word[0]
            ),
            None,
        )

        if not next_node:
            return None
        else:
            return self.search_path(word[1:], node=next_node)
