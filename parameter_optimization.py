import json  #Loading the library to handle JSON files
import numpy as np  #Loading the library for numerical computations
from scipy.optimize import minimize  #Loading the gradient descent algorithm (BFGS)
import chess  #Loading the python-chess library to manipulate chess positions
from tqdm import tqdm #Progress bar to track progresst
import random
from multiprocessing import Pool, cpu_count
import time

#Load grandmaster move data
with open('master_moves_data.json', 'r') as json_file:
    master_moves_data = json.load(json_file)  #Loading move and position data
print(f"Number of master_moves_data: {len(master_moves_data)}")

#Randomly select 0.1% of the moves (we have trained with other proportions of the dataset too)
sampled_moves_data = random.sample(master_moves_data, len(master_moves_data) // 1000)
print(f"Number of sampled_moves_data: {len(sampled_moves_data)}")

#Initialize evaluation function parameters (this parameters are trained parameters from last optimization)
params = {
    'pawn_value': 0.6913448662622311,  #Pawn value
    'knight_value': 3.055774166457658,  #Knight value
    'bishop_value': 3.2965190268606355,  #Bishop value
    'rook_value': 5.457780352666133,  #Rook value
    'queen_value': 9.4440769607258,  #Queen value
    'center_control_bonus': 0.11047965351400284,  #Bonus for controlling central squares
    'king_safety_bonus': 0.28035874850192655,  #Bonus for king safety
    'piece_mobility_bonus': -0.015016171091712107,  #Bonus for piece mobility
    'double_pawn_penalty': -0.09914131881567168,  #Penalty for doubled pawns
    'isolated_pawn_penalty': 0.3312020723326411,  #Penalty for isolated pawns
    'passed_pawn_bonus': 0.40790331911220457,  #Bonus for passed pawns
    'attacked_piece_penalty': 0.17110843043534357,  #Penalty for attacked pieces
    'piece_square_table_weight': 0.000017110843043534357,  #Weight of positional score tables
    'king_activity_endgame': 0.20763853234778232,  #Bonus for active king in the endgame
    'pawn_advancement_endgame': 0.016567360294815363,  #Bonus for pawn advancement in the endgame
    'rook_open_file_bonus': 0.11087110678845488,  #Bonus for rooks on open files
    'rook_semi_open_file_bonus': 0.14925437852143525,  #Bonus for rooks on semi-open files
    'bishop_pair_bonus': 0.39295183191258515,  #Bonus for having the bishop pair
    'knight_outpost_bonus': 0.08500893762671113,  #Bonus for well-placed knights
    'king_proximity_to_center_endgame': 0.3275250912748785  #Bonus for a king near the center in the endgame
}

#Piece positional score tables
knightScores = [[1, 1, 1, 1, 1, 1, 1, 1],
                [1, 2, 2, 2, 2, 2, 2, 1],
                [1, 2, 3, 3, 3, 3, 2, 1],
                [1, 2, 3, 4, 4, 3, 2, 1],
                [1, 2, 3, 4, 4, 3, 2, 1],
                [1, 2, 3, 3, 3, 3, 2, 1],
                [1, 2, 2, 2, 2, 2, 2, 1],
                [1, 1, 1, 1, 1, 1, 1, 1]]

bishopScores = [[4, 3, 2, 1, 1, 2, 3, 4],
                [3, 4, 3, 2, 2, 3, 4, 3],
                [2, 3, 4, 3, 3, 4, 3, 2],
                [1, 2, 3, 4, 4, 3, 2, 1],
                [1, 2, 3, 4, 4, 3, 2, 1],
                [2, 3, 4, 3, 3, 4, 3, 2],
                [3, 4, 3, 2, 2, 3, 4, 3],
                [4, 3, 2, 1, 1, 2, 3, 4]]

queenScores =  [[1, 1, 1, 3, 1, 1, 1, 1],
                [1, 2, 3, 3, 3, 1, 1, 1],
                [1, 4, 3, 3, 3, 4, 2, 1],
                [1, 2, 3, 3, 3, 2, 2, 1],
                [1, 2, 3, 3, 3, 2, 2, 1],
                [1, 4, 3, 3, 3, 4, 2, 1],
                [1, 1, 2, 3, 3, 1, 1, 1],
                [1, 1, 1, 3, 1, 1, 1, 1]]

rookScores =  [ [4, 3, 4, 4, 4, 4, 3, 4],
                [4, 4, 4, 4, 4, 4, 4, 4],
                [1, 1, 2, 3, 3, 2, 1, 1],
                [1, 2, 3, 4, 4, 3, 2, 1],
                [1, 2, 3, 4, 4, 3, 2, 1],
                [1, 1, 2, 2, 2, 2, 1, 1],
                [4, 4, 4, 4, 4, 4, 4, 4],
                [4, 3, 4, 4, 4, 4, 3, 4]]

whitePawnScores =  [[8, 8, 8, 8, 8, 8, 8, 8],
                    [8, 8, 8, 8, 8, 8, 8, 8],
                    [5, 6, 6, 7, 7, 6, 6, 5],
                    [2, 3, 3, 5, 5, 3, 3, 2],
                    [1, 2, 3, 4, 4, 3, 2, 1],
                    [1, 1, 2, 3, 3, 2, 1, 1],
                    [1, 1, 1, 0, 0, 1, 1, 1],
                    [0, 0, 0, 0, 0, 0, 0, 0]]

blackPawnScores =  [[0, 0, 0, 0, 0, 0, 0, 0],
                    [1, 1, 1, 0, 0, 1, 1, 1],
                    [1, 1, 2, 3, 3, 2, 1, 1],
                    [1, 2, 3, 4, 4, 3, 2, 1],
                    [2, 3, 3, 5, 5, 3, 3, 2],
                    [5, 6, 6, 7, 7, 6, 6, 5],
                    [8, 8, 8, 8, 8, 8, 8, 8],
                    [8, 8, 8, 8, 8, 8, 8, 8]]

#Parametric evaluation function that calculates the position score
#Parameters are used to adjust the importance of each criterion
def evaluate_board(board, params):
    score = 0

    if board.is_checkmate():  #If it's checkmate, the game is over
        return 10000 if board.turn == chess.BLACK else -10000

    #Calculation of piece values
    for square in chess.SQUARES: #The loop iterates over all squares on the boarder
        piece = board.piece_at(square)
        if piece:
            symbol = piece.symbol().upper()
            if symbol == 'P':
                value = params['pawn_value']
            elif symbol == 'N':
                value = params['knight_value']
            elif symbol == 'B':
                value = params['bishop_value']
            elif symbol == 'R':
                value = params['rook_value']
            elif symbol == 'Q':
                value = params['queen_value']
            else:
                continue

            #Add the piece value to the score (positive for White, negative for Black)
            score += value if piece.color == chess.WHITE else -value

    #Add specific evaluations
    score += evaluate_pawn_structure(board, params)
    score += evaluate_piece_square_table(board, params)
    score += evaluate_center_control(board, params)
    score += evaluate_king_safety(board, params)
    score += evaluate_piece_mobility(board, params)
    score += evaluate_attacks(board, params)
    score += evaluate_advanced_endgame(board, params)
    score += evaluate_piece_specifics(board, params)
    score += evaluate_rook_open_file(board, params)
    score += evaluate_king_proximity_endgame(board, params)

    return score

# -- Evaluation function for piece-square tables --
def evaluate_piece_square_table(board, params):
    score = 0

    #Piece-square tables
    piece_square_tables = {
        'N': knightScores,
        'B': bishopScores,
        'Q': queenScores,
        'R': rookScores,
        'wp': whitePawnScores,
        'bp': blackPawnScores
    }

    for square in chess.SQUARES:
        piece = board.piece_at(square)
        if piece:
            symbol = piece.symbol().upper()
            table_key = symbol if symbol in piece_square_tables else symbol.lower()
            
            #Special handling for white and black pawns
            if piece.symbol().lower() == 'p':
                table_key = 'wp' if piece.color == chess.WHITE else 'bp'

            table = piece_square_tables.get(table_key)
            if table:
                row = chess.square_rank(square)
                col = chess.square_file(square)
                
                #Tables are oriented for White. Flip them for Black.
                if piece.color == chess.WHITE:
                    score += params['piece_square_table_weight'] * table[row][col]
                else:
                    score -= params['piece_square_table_weight'] * table[7 - row][col]

    return score

# -- Pawn structure evaluation --
def evaluate_pawn_structure(board, params):
    score = 0
    for file in range(8):
        for color in [chess.WHITE, chess.BLACK]:
            pawns = [sq for sq in chess.SQUARES if board.piece_at(sq) and board.piece_at(sq).symbol().lower() == 'p' and board.piece_at(sq).color == color]
            penalty = params['double_pawn_penalty'] * (len(pawns) - len(set([chess.square_file(sq) for sq in pawns])))
            score += penalty if color == chess.WHITE else -penalty

    return score

# -- Other evaluation functions (Center control, King safety, Mobility, Attacks) --
def evaluate_center_control(board, params):
    center_squares = [chess.D4, chess.E4, chess.D5, chess.E5]
    score = sum([params['center_control_bonus'] for sq in center_squares if board.piece_at(sq)])
    return score

def evaluate_king_safety(board, params):
    king_squares = [chess.G1, chess.G8, chess.C1, chess.C8]
    score = sum([params['king_safety_bonus'] for sq in king_squares if board.piece_at(sq) and board.piece_at(sq).symbol().upper() == 'K'])
    return score

def evaluate_piece_mobility(board, params):
    score = len(list(board.legal_moves)) * params['piece_mobility_bonus']
    return score

def evaluate_attacks(board, params):
    score = 0
    for move in board.legal_moves:
        target = board.piece_at(move.to_square)
        if target:
            score += params['attacked_piece_penalty'] * (1 if target.color == chess.BLACK else -1)
    return score

# -- Function for endgame evaluations --
def evaluate_advanced_endgame(board, params):
    score = 0

    #King activity in the endgame
    for square in chess.SQUARES:
        piece = board.piece_at(square)
        if piece and piece.symbol().upper() == 'K':
            if board.is_checkmate() or board.fullmove_number > 40:
                if piece.color == chess.WHITE:
                    score += params['king_activity_endgame'] * (7 - chess.square_rank(square))
                else:
                    score -= params['king_activity_endgame'] * (chess.square_rank(square))

    #Pawn advancement
    for square in chess.SQUARES:
        piece = board.piece_at(square)
        if piece and piece.symbol().lower() == 'p':
            rank = chess.square_rank(square)
            score += params['pawn_advancement_endgame'] * (rank if piece.color == chess.WHITE else 7 - rank)

    return score

# -- Function for evaluation of isolated and passed pawns, and piece-square table bonuses --
def evaluate_piece_specifics(board, params):
    score = 0

    #Bonus for isolated pawns
    for square in chess.SQUARES:
        piece = board.piece_at(square)
        if piece and piece.symbol().lower() == 'p':
            if is_isolated_pawn(board, square):
                score -= params['isolated_pawn_penalty'] if piece.color == chess.WHITE else -params['isolated_pawn_penalty']

    #Bonus for passed pawns
        if piece and piece.symbol().lower() == 'p' and is_passed_pawn(board, square):
            score += params['passed_pawn_bonus'] if piece.color == chess.WHITE else -params['passed_pawn_bonus']

    #Bonus for bishop pair
    bishops = [p for p in board.piece_map().values() if p.symbol().lower() == 'b']
    if len(bishops) >= 2:
        score += params['bishop_pair_bonus'] if bishops[0].color == chess.WHITE else -params['bishop_pair_bonus']

    #Bonus for knights on outposts
    for square in chess.SQUARES:
        piece = board.piece_at(square)
        if piece and piece.symbol().lower() == 'n':
            if is_knight_outpost(board, square):
                score += params['knight_outpost_bonus'] if piece.color == chess.WHITE else -params['knight_outpost_bonus']

    return score

# -- Function that checks for isolated pawns --
def is_isolated_pawn(board, square):
    file = chess.square_file(square)
    for adj_file in [file - 1, file + 1]:
        if 0 <= adj_file <= 7:  #Check file boundaries
            for rank in range(8):
                adj_square = chess.square(adj_file, rank)
                piece = board.piece_at(adj_square)
                if piece and piece.symbol().lower() == 'p':
                    return False
    return True

# -- Function that checks for passed pawns --
def is_passed_pawn(board, square):
    file = chess.square_file(square)
    rank = chess.square_rank(square)
    direction = 1 if board.piece_at(square).color == chess.WHITE else -1

    for adj_file in [file - 1, file, file + 1]:
        if adj_file < 0 or adj_file > 7:
            continue
        for r in range(rank + direction, 8 if direction == 1 else -1, direction):
            if r < 0 or r > 7:
                continue
            
            adj_square = chess.square(adj_file, r)
            if board.piece_at(adj_square) and board.piece_at(adj_square).symbol().lower() == 'p':
                return False

    return True

# -- Function that checks for knights on outposts --
def is_knight_outpost(board, square):
    file = chess.square_file(square)
    rank = chess.square_rank(square)
    return (file in [2, 3, 4, 5]) and (rank in [3, 4, 5])

# -- Function that evaluates rooks on open and semi-open files --
def evaluate_rook_open_file(board, params):
    score = 0
    for file in range(8):
        white_rooks = [square for square in chess.SQUARES if board.piece_at(square) and board.piece_at(square).symbol() == 'R' and board.piece_at(square).color == chess.WHITE]
        black_rooks = [square for square in chess.SQUARES if board.piece_at(square) and board.piece_at(square).symbol() == 'r' and board.piece_at(square).color == chess.BLACK]

        for rook in white_rooks:
            if is_open_file(board, file):
                score += params['rook_open_file_bonus']
            elif is_semi_open_file(board, file):
                score += params['rook_semi_open_file_bonus']

        for rook in black_rooks:
            if is_open_file(board, file):
                score -= params['rook_open_file_bonus']
            elif is_semi_open_file(board, file):
                score -= params['rook_semi_open_file_bonus']

    return score

# -- Function that checks for open and semi-open files --
def is_open_file(board, file):
    return all(not board.piece_at(chess.square(file, rank)) for rank in range(8))

def is_semi_open_file(board, file):
    return sum(1 for rank in range(8) if board.piece_at(chess.square(file, rank))) == 1

# -- Function that evaluates king proximity to the center in the endgame --
def evaluate_king_proximity_endgame(board, params):
    score = 0
    for square in chess.SQUARES:
        piece = board.piece_at(square)
        if piece and piece.symbol().upper() == 'K':
            center_squares = [chess.D4, chess.E4, chess.D5, chess.E5]
            if square in center_squares:
                score += params['king_proximity_to_center_endgame'] if piece.color == chess.WHITE else -params['king_proximity_to_center_endgame']

    return score

# -- Cost function --
def evaluate_position_worker(data_and_params):
    data, temp_params = data_and_params
    board = chess.Board(data['fen'])
    best_move = data['move']

    legal_moves = list(board.legal_moves)
    move_scores = {move: evaluate_board(board, temp_params) for move in legal_moves}

    best_move_score = move_scores.get(best_move, 0)
    max_score = max(move_scores.values())

    return (max_score - best_move_score) ** 2

def cost_function(x):
    temp_params = {key: x[i] for i, key in enumerate(params.keys())}
    task_data = [(data, temp_params) for data in sampled_moves_data]

    with Pool(cpu_count()) as pool:
        errors = list(pool.imap(evaluate_position_worker, task_data))

    total_error = sum(errors)
    print(f"Total error: {total_error} with parameters: {temp_params}")
    return total_error

if __name__ == '__main__':
    initial_values = list(params.values())

    print("Optimization in progress...")
    result = minimize(cost_function, initial_values, method='BFGS', options={'maxiter': 5})

    optimized_params = {key: result.x[i] for i, key in enumerate(params.keys())}
    with open('trained_parameters.json', 'w') as json_file:
        json.dump(optimized_params, json_file, indent=4)

    print("Optimized parameters saved in trained_parameters.json")