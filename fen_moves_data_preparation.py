#Prepare the FEN and move data from grandmaster games and save the data to master_moves_data.json.
import chess
import chess.pgn
import json
import os

#List of specific PGN file names to process
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

fen_moves_data = [] #Initialize a list to store (FEN, SAN move) pairs from each position in the games.
total_games = 0 #Counter to track the total number of games processed.

for pgn_file_name in PGN_FILE_NAMES: #Loop to process each PGN file of grandmasters.
    pgn_path = os.path.join(PGN_FOLDER_PATH, pgn_file_name)
    with open(pgn_path, 'r', encoding='latin-1', errors='ignore') as pgn_file: #Open each PGN file for reading with encoding error handling.
        while True: #Loop to read each game in the PGN file.
            game = chess.pgn.read_game(pgn_file) #Read the next game from the PGN file.
            if game is None: #Check for end of PGN file (no more games left).
                break

            total_games += 1 #Increment the counter of processed games.
            board = game.board() #Initialize the board to the starting position for each game.

            for move in game.mainline_moves(): #Loop through each move in the game.
                fen = board.fen() #Get the FEN position before each move.
                san_move = board.san(move) #Convert the move to SAN (Standard Algebraic Notation).
                fen_moves_data.append({"fen": fen, "move": san_move}) #Store the (FEN, move) pair in the fen_moves_data list.
                board.push(move) #Update the board with the move played to advance the game.

print(f"Total games processed: {total_games}") #Display the total number of games processed once all files are parsed. 29041 games are processed.

with open('master_moves_data.json', 'w') as json_file: #Save the extracted data (FEN and moves) to a JSON file with indentation for readability.
    json.dump(fen_moves_data, json_file, indent=4)
print("FEN and moves data saved to master_moves_data.json") #Confirmation message that the data has been successfully saved.