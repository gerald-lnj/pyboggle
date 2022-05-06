# pyboggle

pyboggle is a implementation of the Boggle board game by Hasbro.

### It features:
- Checking and scoring for valid words in a board
- Solving a board for all possible words
- Doing the above in a (self-proclaimed) efficient manner

## Quick Start

```python
from pyboggle import BoggleBoard
board = BoggleBoard()
board.start_game()
```

## Approach

There are 2 main aspects to this implementation of Boggle: the `WordTree` wordlist, and the `BoggleBoard` board itself.

### BoggleBoard

The `BoggleBoard` class represents each postion on the board with a `Dice` instance. It also stores the relative positions of the dice in an undirected adjacency graph, where each node in the graph is a `Dice` instance. 

This graph is used to check if a guess attempt is possible on this board, by asserting that the chain of letters exists as a path on the  adjacency graph.

It is also used to execute a depth first search (DFS) of all paths between every combination of dice, to get all posiible words on the board.

This exahustive search is optimised by checking the current traversed path aginst the word list, and early exiting the current branch if the partial word is invalid.

### WordTree

The `WordTree` word list is constucted from the CSW15 set of words in a .txt format. A prefix tree is constructed from this word list, which allows for quick searching, and early exiting of the DFS search. 

Creation of the prefix tree is further optimised by excluding all words which contain letters not present in the current `BoggleBoard` layout.