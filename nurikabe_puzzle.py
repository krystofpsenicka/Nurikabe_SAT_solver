#!/usr/bin/env python3

import subprocess
from argparse import ArgumentParser
from itertools import product

def load_instance(input_file_name):
    global GRID_SIZE, NR_CELLS, NR_AT_VARS
    instance = []
    with open(input_file_name, "r") as file:
        GRID_SIZE = int(next(file))  # first line is the grid size
        for line in file:
            line = line.split()
            if line:
                line = [int(i) for i in line]
                instance.append(line)
    
    NR_CELLS = GRID_SIZE * GRID_SIZE
    NR_AT_VARS = NR_CELLS  # Each cell can be either black (true) or white (false)

    return instance

def cell_to_var(i, j):
    return (i * GRID_SIZE + j) + 1

def var_to_cell(var):
    return ((var - 1) // GRID_SIZE, (var - 1) % GRID_SIZE)


# Returns a dictionary with all possible paths between all pairs of cells
def get_all_paths(grid_size):

    def is_valid(x, y):
        return 0 <= x < grid_size and 0 <= y < grid_size

    def find_paths(start, end):
        paths = []
        queue = [(start, [start])]
        while queue:
            (x, y), path = queue.pop(0)
            if (x, y) == end:
                paths.append(path)
                continue
            for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nx, ny = x + dx, y + dy
                if is_valid(nx, ny) and (nx, ny) not in path:
                    queue.append(((nx, ny), path + [(nx, ny)]))
        return paths

    all_paths = {}
    for (i, j), (k, l) in product(product(range(grid_size), repeat=2), repeat=2):
        if (i, j) != (k, l):
            all_paths[((i, j), (k, l))] = find_paths((i, j), (k, l))
    return all_paths

# Returns the path variables for all paths between two cells
def get_path_variables(cell1, cell2, path_vars):
    return [path_var for (c1, c2, _), path_var in path_vars.items() if (c1, c2) == (cell1, cell2) or (c1, c2) == (cell2, cell1)]


def encode(instance):
    cnf = []
    nr_reachable_vars = (NR_CELLS * NR_CELLS)
    nr_vars = NR_AT_VARS + nr_reachable_vars

    # variables for the connectivity of the islands
    def island_reachable_to_var(i, j, k, l):
        return NR_AT_VARS + (i * GRID_SIZE + j) * NR_CELLS + (k * GRID_SIZE + l) + 1

    # gets the adjacent cells in their variable form
    def get_adjacent(i, j):
        adjacent = []
        if i > 0:
            adjacent.append(cell_to_var(i-1, j))
        if i < GRID_SIZE-1:
            adjacent.append(cell_to_var(i+1, j))
        if j > 0:
            adjacent.append(cell_to_var(i, j-1))
        if j < GRID_SIZE-1:
            adjacent.append(cell_to_var(i, j+1))
        return adjacent
    
    def get_non_adjacent(i, j):
        non_adjacent = []
        adjacent = get_adjacent(i, j)
        for k in range(GRID_SIZE):
            for l in range(GRID_SIZE):
                if cell_to_var(k, l) not in adjacent and (k != i or l != j):
                    non_adjacent.append(cell_to_var(k, l))
        return non_adjacent

   

    cells_with_2 = []
    numbered_cells = []
    # Hints
    for i in range(GRID_SIZE):
        for j in range(GRID_SIZE):
            if instance[i][j] == 1:
                numbered_cells.append((i, j))
                cnf.append([-cell_to_var(i, j), 0])  # Must be white
                # It is island-reachable from itself
                cnf.append([island_reachable_to_var(i, j, i, j), 0])
                # All adjacent cells must be black
                adjacent = get_adjacent(i, j)
                for a in adjacent:
                    cnf.append([a, 0])
            elif instance[i][j] == 2:
                numbered_cells.append((i, j))
                cells_with_2.append((i, j))
                cnf.append([-cell_to_var(i, j), 0])  # Must be white
                # It is island-reachable from itself
                cnf.append([island_reachable_to_var(i, j, i, j), 0])
                # Exactly one adjacent cell is white
                adjacent = get_adjacent(i, j)
                for k in range(len(adjacent)):
                    for l in range(k+1, len(adjacent)):
                        cnf.append([adjacent[k], adjacent[l], 0]) # at least one must be black in each pair of adjacent cells
                # All non-adjacent cells must be island-unreachable
                nonadjacent = get_non_adjacent(i, j)
                for a in nonadjacent:
                    k, l = var_to_cell(a)
                    cnf.append([-(island_reachable_to_var(i,j, k, l)), 0])

    # If a non-numbered cell is white, it has to be island-reachable from a cell numbered 2
    for i in range(GRID_SIZE):
        for j in range(GRID_SIZE):
            if (i, j) not in numbered_cells:
                clause = []
                clause.append(cell_to_var(i, j))
                for k, l in cells_with_2:
                    clause.append(island_reachable_to_var(k, l, i, j))
                cnf.append(clause + [0])

    # No 2x2 block of black cells
    for i in range(GRID_SIZE - 1):
        for j in range(GRID_SIZE - 1):
            cnf.append([-cell_to_var(i, j), -cell_to_var(i+1, j), -cell_to_var(i, j+1), -cell_to_var(i+1, j+1), 0])


    # Connectivity of the sea using auxiliary variables
    path_vars = {}
    path_counter = nr_vars + 1

    all_paths = get_all_paths(GRID_SIZE)

    for (cell1, cell2), paths in all_paths.items():
        for path in paths:
            path_var = path_counter
            path_vars[(cell1, cell2, tuple(path))] = path_var
            path_counter += 1

            # Clause to ensure path_var is true if all cells on the path are black
            cnf.append([-cell_to_var(x, y) for x, y in path] + [path_var, 0])

            # Clauses to ensure path_var is false if any cell on the path is white
            for x, y in path:
                cnf.append([cell_to_var(x, y), -path_var, 0])


    # Encode actual connectivity of the sea
    # For each pair of cells, if they are both black then there must be a path between them
    for (i, j), (k, l) in product(product(range(GRID_SIZE), repeat=2), repeat=2):
        if (i, j) != (k, l):
            current_path_variables = get_path_variables((i, j), (k, l), path_vars)

            # Clause to ensure that if both cells are black, at least one path variable is true
            cnf.append([-cell_to_var(i, j), -cell_to_var(k, l), path_var] + current_path_variables + [0])









    nr_vars += path_counter

    # # all variables in the formula
    # for i in range(1, nr_vars+1):
    #     cnf.append([i, -i, 0])


    return (cnf, nr_vars)

def call_solver(cnf, nr_vars, output_name, solver_name, verbosity):
    with open(output_name, "w") as file:
        file.write("p cnf " + str(nr_vars) + " " + str(len(cnf)) + '\n')
        for clause in cnf:
            file.write(' '.join(str(lit) for lit in clause) + '\n')

    return subprocess.run(['./' + solver_name, '-model', '-verb=' + str(verbosity), output_name], stdout=subprocess.PIPE)

def print_result(result, instance):
    for line in result.stdout.decode('utf-8').split('\n'):
        print(line)

    if result.returncode == 20:
        return

    model = []
    for line in result.stdout.decode('utf-8').split('\n'):
        if line.startswith("v"):
            vars = line.split(" ")
            vars.remove("v")
            model.extend(int(v) for v in vars)
    model.remove(0)

    print()
    print("##################################################################")
    print("###########[ Human readable result of the Nurikabe puzzle ]###########")
    print("##################################################################")
    print()

    print("W: white cell (island) ")
    print("B: black cell (sea) ")
    print()

    for i in range(GRID_SIZE):
        for j in range(GRID_SIZE):
            if model[cell_to_var(i, j) - 1] > 0:
                print("B", end=" ")
            else:
                print("W", end=" ")
        print()

if __name__ == "__main__":
    parser = ArgumentParser()

    parser.add_argument(
        "-i",
        "--input",
        default="input.in",
        type=str,
        help="The instance file."
    )
    parser.add_argument(
        "-o",
        "--output",
        default="formula.cnf",
        type=str,
        help="Output file for the DIMACS format (i.e. the CNF formula)."
    )
    parser.add_argument(
        "-s",
        "--solver",
        default="glucose-syrup",
        type=str,
        help="The SAT solver to be used."
    )
    parser.add_argument(
        "-v",
        "--verb",
        default=1,
        type=int,
        choices=range(0, 2),
        help="Verbosity of the SAT solver used."
    )
    args = parser.parse_args()

    instance = load_instance(args.input)
    cnf, nr_vars = encode(instance)
    result = call_solver(cnf, nr_vars, args.output, args.solver, args.verb)
    if result:
        print_result(result, instance)
    else:
        print("Solver was not called due to an error in clause generation.")