#We have removed the parameters piece_square_table_weight, piece_mobility_bonus and pawn_advancement_endgame (low impact: all <±0.02).
import chess
import chess.engine
import chess.pgn
from collections import defaultdict
import pygame   
import os
from functools import lru_cache
import json

#List of specific PGN file names to process : 29041 games
PGN_FILE_NAMES = [
    "VachierLagrave.pgn",
    "Ding.pgn",
    "Karpov.pgn",
    "Kasparov.pgn",
    "Carlsen.pgn",
    "Caruana.pgn",
    "Firouzja.pgn"
]

#Path to the PGN folder within the current working directory
PGN_FOLDER_PATH = os.path.join(os.getcwd(), 'PGN')

# -- Function to build the opening book --
def build_opening_book(PGN_FILE_NAMES, max_depth=10):
    opening_book = defaultdict(lambda: defaultdict(int))
    total_games = 0

    for pgn_file_name in PGN_FILE_NAMES:
        pgn_path = os.path.join(PGN_FOLDER_PATH, pgn_file_name)
        with open(pgn_path, 'r', encoding='latin-1', errors='ignore') as pgn_file:
            while True:
                game = chess.pgn.read_game(pgn_file)
                if game is None:
                    break

                total_games += 1
                board = game.board()

                for move in game.mainline_moves():
                    if board.fullmove_number > max_depth:
                        break
                    san_move = board.san(move)
                    fen = board.board_fen()
                    opening_book[fen][san_move] += 1
                    board.push(move)

    print(f"Total games in opening book: {total_games}")
    return opening_book

#Build the opening book
opening_book = build_opening_book(PGN_FILE_NAMES)

#Save the opening book
with open('learned_opening_book.json', 'w') as json_file:
    json.dump(opening_book, json_file, indent=4)

print("Opening book saved to learned_opening_book.json")

# -- Function to get an opening move --
def get_opening_move(board):
    fen = board.board_fen()
    if fen in opening_book:
        print("Opening move detected. Using book move.")
        possible_moves = opening_book[fen]
        best_move = max(possible_moves, key=possible_moves.get)
        
        try:
            #Directly play using SAN
            move = board.parse_san(best_move)  #Use SAN directly
            if move in board.legal_moves:
                return move
            else:
                print(f"Move {best_move} from book is illegal in this position.")
        except Exception as e:
            print(f"Error parsing SAN move from book: {e}")
    
    return None

CHECKMATE = 1000
DRAW = 0
DEPTH = 4 #Number of half-moves

params = {
    'pawn_value': 0.6913448662622311,  #Pawn value
    'knight_value': 3.055774166457658,  #Knight value
    'bishop_value': 3.2965190268606355,  #Bishop value
    'rook_value': 5.457780352666133,  #Rook value
    'queen_value': 9.4440769607258,  #Queen value
    'center_control_bonus': 0.11047965351400284,  #Bonus for controlling central squares
    'king_safety_bonus': 0.28035874850192655,  #Bonus for king safety
    'double_pawn_penalty': -0.09914131881567168,  #Penalty for doubled pawns
    'isolated_pawn_penalty': 0.3312020723326411,  #Penalty for isolated pawns
    'passed_pawn_bonus': 0.40790331911220457,  #Bonus for passed pawns
    'attacked_piece_penalty': 0.17110843043534357,  #Penalty for attacked pieces
    'king_activity_endgame': 0.20763853234778232,  #Bonus for active king in the endgame
    'rook_open_file_bonus': 0.11087110678845488,  #Bonus for rooks on open files
    'rook_semi_open_file_bonus': 0.14925437852143525,  #Bonus for rooks on semi-open files
    'bishop_pair_bonus': 0.39295183191258515,  #Bonus for having the bishop pair
    'knight_outpost_bonus': 0.08500893762671113,  #Bonus for well-placed knights
    'king_proximity_to_center_endgame': 0.3275250912748785  #Bonus for a king near the center in the endgame
}

class AI():
    def AI_move(board):
        global nextMove
        nextMove = None
        #Check for mate in one
        for move in board.legal_moves:
            board.push(move)
            if board.is_checkmate():
                board.pop()
                print(f"AI plays (mate in one): {board.san(move)}")
                return move
            board.pop()
        nextMove = get_opening_move(board)  #Attempt to play a move from the opening book
        
        if nextMove is None:
            print("Not an opening position. Using NegaMax.")
            nextMove = findMoveNegaMaxAlphaBeta(board, DEPTH, -1000, 1000, 1 if board.turn == chess.WHITE else -1)
        
        #Convert the move to SAN notation for display
        if nextMove and nextMove in board.legal_moves:
            print(f"AI plays: {board.san(nextMove)}")
            return nextMove
        else:
            print("AI could not make a valid move.")
            return None

#Alpha-Beta Pruning is an enhancement of the Minimax/NegaMax algorithm that avoids exploring certain unnecessary branches of the search tree.
#Alpha: the best value that the maximizing player (White) can guarantee.
#Beta: the best value that the minimizing player (Black) can guarantee.
#Thanks to move ordering, the best moves (strong captures) are tested first. This maximizes the chances of triggering Alpha-Beta pruning, as good moves quickly increase alpha or reduce beta.

# -- Optimized NegaMax function with Move Ordering (MVV-LVA) --
def findMoveNegaMaxAlphaBeta(board, depth, alpha, beta, turnColor):
    global nextMove
    if depth == 0:
        return turnColor * evaluate_board_cached(board.fen())

    maxScore = -1000
    best_move = None

    #Correction: pass the parameters into move_ordering
    moves = sorted(board.legal_moves, key=lambda move: move_ordering(board, move, params), reverse=True)

    for move in moves:
        board.push(move)
        score = -findMoveNegaMaxAlphaBeta(board, depth - 1, -beta, -alpha, -turnColor)
        board.pop()

        if score > maxScore:
            maxScore = score
            best_move = move

        alpha = max(alpha, maxScore)
        if alpha >= beta:
            break
        
    if depth == DEPTH:
        if best_move is not None:
            return best_move
        else:
            # Fallback: return first legal move if something went wrong
            legal_moves = list(board.legal_moves)
            if legal_moves:
                print("Fallback: returning first legal move")
                return legal_moves[0]
            else:
                print("No legal moves available at top level.")
                return None
    return maxScore

# -- Move Ordering function using MVV-LVA (Most Valuable Victim - Least Valuable Attacker) --
def move_ordering(board, move, params):
    target = board.piece_at(move.to_square)
    if target:
        symbol = target.symbol().upper()
        #Map the piece symbols to the parameter names
        piece_name_map = {
            'P': 'pawn_value',
            'N': 'knight_value',
            'B': 'bishop_value',
            'R': 'rook_value',
            'Q': 'queen_value'
        }
        victim_value = params.get(piece_name_map.get(symbol, ''), 0)
        
        attacker = board.piece_at(move.from_square)
        if attacker:
            symbol_attacker = attacker.symbol().upper()
            attacker_value = params.get(piece_name_map.get(symbol_attacker, ''), 0)
        else:
            attacker_value = 0
        
        return victim_value - attacker_value

    #Non-capturing moves have lower priority
    return 0

@lru_cache(maxsize=100000)
def evaluate_board_cached(fen):
    board = chess.Board(fen)
    return evaluate_board(board, params)

# -- Parametric evaluation function that calculates the score of the position --
#The parameters are used to adjust the importance of each criterion
def evaluate_board(board, params):
    score = 0
    if board.is_checkmate():
        if board.turn == chess.WHITE:  #If it's White's turn, Black has won
            return -CHECKMATE  #Black wins
        else:
            return CHECKMATE  #White wins
    elif board.is_stalemate() or board.can_claim_threefold_repetition() or board.can_claim_fifty_moves():
        return DRAW #Draw by stalemate or repetition or the 50-move rule

    #Piece value calculation
    for square in chess.SQUARES: #The loop iterates over all squares of the chessboard
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

            #Add the piece's value to the score (positive for White, negative for Black)
            score += value if piece.color == chess.WHITE else -value

    #Add specific evaluations
    score += evaluate_pawn_structure(board, params)
    score += evaluate_center_control(board, params)
    score += evaluate_king_safety(board, params)
    score += evaluate_attacks(board, params)
    score += evaluate_advanced_endgame(board, params)
    score += evaluate_piece_specifics(board, params)
    score += evaluate_rook_open_file(board, params)
    score += evaluate_king_proximity_endgame(board, params)

    return score

# -- Pawn structure evaluation function --
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

    return score

# -- Function for evaluation of isolated pawns, passed pawns, and piece-square table bonuses --
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

    #Bonus for bishop pairs
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

# -- Function that evaluates king proximity to the center in the endgames --
def evaluate_king_proximity_endgame(board, params):
    score = 0
    for square in chess.SQUARES:
        piece = board.piece_at(square)
        if piece and piece.symbol().upper() == 'K':
            center_squares = [chess.D4, chess.E4, chess.D5, chess.E5]
            if square in center_squares:
                score += params['king_proximity_to_center_endgame'] if piece.color == chess.WHITE else -params['king_proximity_to_center_endgame']

    return score

#To play, you must choose your color and enter your moves in Algebraic Notation, as shown here: https://en.wikipedia.org/wiki/Algebraic_notation_(chess)
#You can also start a game from a specific position by importing a FEN using the startfen command.
#You can exit the game with exit command, and you can access the current game's FEN with the fen command.

# -- Function to manage chess games --
def play_game():
    board = chess.Board()
    move_history = []
    starting_fen = chess.STARTING_FEN  #Default: standard starting FEN

    #Choose your color
    player_color = input("Do you want to play as White or Black? (w/b): ").strip().lower()
    while player_color not in ['w', 'b']:
        player_color = input("Invalid choice. Choose 'w' for White or 'b': ").strip().lower()

    print("Enter your move (e.g., e4), 'fen' for the current position, 'startfen' to start from a custom FEN, or 'exit' to quit.")
    
    while not board.is_game_over():
        print(board)

        #Check for move repetition (threefold repetition)
        if board.can_claim_threefold_repetition():
            print("Draw due to threefold repetition.")
            break

        if (player_color == 'w' and board.turn == chess.WHITE) or (player_color == 'b' and board.turn == chess.BLACK):
            player_move = input("Your move: ")

            if player_move.lower() == 'exit':
                break

            if player_move.lower() == 'fen':
                print("FEN position:", board.fen())
                print("Move History:", ' '.join(board.san(move) for move in move_history))
                continue

            if player_move.lower() == 'startfen':
                custom_fen = input("Enter your custom FEN: ")
                try:
                    board.set_fen(custom_fen)
                    starting_fen = custom_fen
                    move_history = []
                    print("Game started from custom FEN.")
                    continue
                except ValueError:
                    print("Invalid FEN format. Try again.")
                    continue

            try:
                move = board.parse_san(player_move)
                if move in board.legal_moves:
                    board.push(move)
                    move_history.append(move)
                else:
                    print("Illegal move. Try again.")
            except ValueError as ve:
                print(f"Invalid SAN move format: {ve}. Use format like 'e4', 'Nf3', 'exd5', etc.")

        else:  #AI plays
            print("AI is thinking...")
            ai_move = AI.AI_move(board)
            if ai_move:
                try:
                    san_move = board.san(ai_move)
                    board.push(ai_move)
                    move_history.append(ai_move)
                except Exception as e:
                    print(f"Unexpected error with AI move: {e}")
                    break
            else:
                print("AI could not make a valid move.")
                break

    #Session finished
    print("\nGame Over!")
    if board.is_checkmate():
        winner = "White" if board.turn == chess.BLACK else "Black"
        print(f"Checkmate! {winner} wins!")
    elif board.is_stalemate():
        print("Stalemate! It's a draw.")
    elif board.is_insufficient_material():
        print("Draw due to insufficient material.")
    elif board.can_claim_threefold_repetition():
        print("Draw due to threefold repetition.")
    elif board.can_claim_fifty_moves():
        print("Draw by fifty-move rule.")
    else:
        print("Game ended by an unknown condition.")

    #Display the FEN of the final position
    print("\nFinal FEN of the game:")
    print(board.fen())  #Affiche directement le FEN final

    #Offer to restart with a FEN or from a custom position
    while True:
        restart_choice = input("\nDo you want to start a new game? (y/n/startfen): ").strip().lower()
        if restart_choice == 'y':
            play_game()  #Play a new game
            break
        elif restart_choice == 'n':
            print("Goodbye!")
            break
        elif restart_choice == 'startfen':
            custom_fen = input("Enter your custom FEN: ")
            try:
                board.set_fen(custom_fen)
                move_history = []
                print("Game started from custom FEN.")
                play_game()
                break
            except ValueError:
                print("Invalid FEN format. Returning to main menu.")
        else:
            print("Invalid choice. Please enter 'y', 'n', or 'startfen'.")

#Start the game
play_game()