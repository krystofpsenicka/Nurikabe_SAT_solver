# Documentation

## Problem description

Nurikabe is a japanese determination puzzle. In an $n \times n$ grid some of the cells are numbered (in our case the numbers are constrained to 1 and 2 only). The challenge is to paint each cell either black or white, according to the following rules:
1. Each numbered cell is apart of an island, the number in it is the number of cells in that island
2. Each island must contain exactly one numbered cell
3. There must be only one sea (it has to be contiguous), and it can not contain any $2 \times 2$ areas of black cells

More information about the puzzle can be found on [wikipedia](https://en.wikipedia.org/wiki/Nurikabe_(puzzle)).

An example of a valid input is:

```
3
0 0 2
1 0 0
0 0 2
```

where the first line is the size of the grid. Then follows the grid itself. A 0 means an empty cell and 1 and 2 mean a numbered cell.

## Encoding

The problem is encoded using three sets of variables. Variables $p_{i,j}$ represent the color of the cell at position $(i,j)$. If $p_{i,j}$ is true then the cell at position $(i,j)$ is black, otherwise the cell is white. Variables $island\_reachable(i, j, k, l)$ represent that the cell $(i, j)$ is in the same island as the cell $(k, l)$. And the $path\_variables(i, j, k, l)$ represent if there is a specific path between nodes $(i, j)$ and $(k, l)$.

To represent the decision problem if there is a solution to the Nurikabe puzzle, we use the following constraints:

- **Hints**: All numbered cells have to be white.
    - If a cell is numbered, it must be white.
        $$ \neg p_{i,j} \quad \text{for each numbered cell } (i,j) $$
    - It is island-reachable from itself.
        $$ island\_reachable(i, j, i, j) \quad \text{for each numbered cell } (i,j) $$
    - All adjacent cells must be black.
        $$ p_{i',j'} \quad \text{for each cell } (i',j') \text{ adjacent to a numbered cell } (i,j) $$
    - Exactly one adjacent cell is white for cells numbered 2. (In each pair of adjacent cells at least one cell is black)
        $$\bigwedge_{(i',j') \neq (i'', j'') \text{ adjacent to } (i,j)} (p_{i',j'} \lor p_{i', j'}) \quad \text{for each cell } (i,j) \text{ numbered 2} $$
    - All non-adjacent cells must be island-unreachable.
        $$ \neg island\_reachable(i, j, k, l) \quad \text{for each cell } (k,l) \text{ not adjacent to } (i,j) $$

- **Island Reachability**: If a non-numbered cell is white, it has to be island-reachable from a cell numbered 2.
    - For each non-numbered cell, if it is white, there must be a path to a cell numbered 2.
        $$ \neg p_{i,j} \implies \bigvee_{(k,l) \text{ numbered 2}} island\_reachable(i, j, k, l) $$

- **No 2x2 Block of Black Cells**: There must not be any 2x2 block of black cells.
    - For each 2x2 block of cells, at least one cell must be white.
        $$ \neg (p_{i,j} \wedge p_{i+1,j} \wedge p_{i,j+1} \wedge p_{i+1,j+1}) \quad \text{for each } (i,j) $$

- **Sea Connectivity**: The sea (black cells) must be contiguous.
    - For each pair of black cells, there must be a path between them.
        $$ \bigwedge_{(i,j),(k,l)} (p_{i,j} \wedge p_{k,l}) \implies \bigvee_{\text{path\_variables(i, j, k, l)}} path\_var $$
    - Path variables ensure that if all cells on the path are black, the path variable is true.
        $$ path\_variables(i, j, k, l) \implies \bigwedge_{(m,n) \text{ on path}} p_{m,n} $$
    - Path variables ensure that if any cell on the path is white, the path variable is false.
        $$ \neg path\_variables(i, j, k, l) \implies \bigvee_{(m,n) \text{ on path}} \neg p_{m,n} $$

## User documentation


Basic usage: 
```
nurikabe_puzzle.py [-h] [-i INPUT] [-o OUTPUT] [-s SOLVER] [-v {0,1}]
```

Used libraries:
- itertools
- argparse


Command-line options:

* `-h`, `--help` : Show a help message and exit.
* `-i INPUT`, `--input INPUT` : The instance file. Default: "input.in".
* `-o OUTPUT`, `--output OUTPUT` : Output file for the DIMACS format (i.e. the CNF formula).
* `-s SOLVER`, `--solver SOLVER` : The SAT solver to be used.
*  `-v {0,1}`, `--verb {0,1}` :  Verbosity of the SAT solver used.

Output:

```
B B B W 
W W B B 
B B W B 
W B B B
```

- W means that the cell at the given position is white (island cell)
- B means that the cell at the given position is black (sea cell)


## Example instances

* `input-3by3.in`: A solvable 3x3 instance
* `input-3by3-unsat.in`: An unsolvable 3x3 instance
* `input-4by4.in`: A solvable 4x4 instance
* `input-4by4-unsat.in`: An unsolvable 4x4 instance
* `input-5by5-hard.in`: A solvable 5x5 instance that takes too long to encode, so the python script execution gets killed

## Experiments

Encoding a 4x4 puzzle already takes nontrivial time and encoding a 5x5 puzzle takes way too long (the script stops and doesn't solve the instance). The time for encoding scales very fast since there is a variable for each path between each pair of cells on the grid. 