import pygame
import chess
import chess.engine
import os
import random
import math
import time
import chess.pgn
from collections import defaultdict
from functools import lru_cache
import json

#Initialization of pygame
pygame.init()
BOARD_WIDTH, HEIGHT = 640, 640 #The chessboard occupies 480x640 (8 squares of 60x60)
SIDEBAR_WIDTH = 320
TOTAL_WIDTH = BOARD_WIDTH + SIDEBAR_WIDTH
SCREEN = pygame.display.set_mode((TOTAL_WIDTH, HEIGHT), pygame.RESIZABLE | pygame.SHOWN)
fullscreen_mode = False  #Fullscreen mode indicator

#Colors
WHITE = (225, 225, 225)
BLUE = (120, 160, 180)
SELECTED_COLOR = (150, 150, 150)
SIDEBAR_BG = (60, 60, 60)
TEXT_COLOR = (0, 0, 0)

#Load piece images
IMAGES = {}
PIECES = ['wp', 'bp', 'wr', 'br', 'wn', 'bn', 'wb', 'bb', 'wq', 'bq', 'wk', 'bk']
pygame.display.set_caption("Jeu d'échecs")

# -- Function to toggle fullscreen and resize --
def toggle_fullscreen():
    global SCREEN, fullscreen_mode, BOARD_WIDTH, HEIGHT, SIDEBAR_WIDTH, TOTAL_WIDTH
    screen_info = pygame.display.Info()  #Ensure screen_info is always defined
    if fullscreen_mode:
        BOARD_WIDTH = 640
        HEIGHT = 640
        SIDEBAR_WIDTH = 320
        TOTAL_WIDTH = BOARD_WIDTH + SIDEBAR_WIDTH
        SCREEN = pygame.display.set_mode((TOTAL_WIDTH, HEIGHT), pygame.RESIZABLE)
        fullscreen_mode = False
    else:
        screen_info = pygame.display.Info()
        HEIGHT = screen_info.current_h  #Screen height
        BOARD_WIDTH = HEIGHT  #The board is a square
        SIDEBAR_WIDTH = screen_info.current_w - BOARD_WIDTH  #The rest is for the sidebar
        TOTAL_WIDTH = screen_info.current_w
        SCREEN = pygame.display.set_mode((TOTAL_WIDTH, HEIGHT), pygame.RESIZABLE)
        fullscreen_mode = True
    #Resize the pieces
    for piece, image in IMAGES.items():
        IMAGES[piece] = pygame.transform.scale(image, (BOARD_WIDTH // 8, HEIGHT // 8))

# -- Function to load images --
def load_images():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    images_path = os.path.join(script_dir, "IMAGES")
    for piece in PIECES:
        full_path = os.path.join(images_path, f"{piece}.png")
        IMAGES[piece] = pygame.transform.scale(
            pygame.image.load(full_path), (BOARD_WIDTH // 8, HEIGHT // 8))

# -- Function to draw the chessboard --
def draw_board(selected_square=None, legal_moves=[], board=None):
    colors = [WHITE, BLUE]
    for r in range(8):
        for c in range(8):
            color = colors[(r + c) % 2]
            rect = pygame.Rect(c * BOARD_WIDTH // 8, r * HEIGHT // 8, BOARD_WIDTH // 8, HEIGHT // 8)
            pygame.draw.rect(SCREEN, color, rect)

            #Highlight the selected square
            if selected_square is not None:
                sel_col = chess.square_file(selected_square)
                sel_row = 7 - chess.square_rank(selected_square)
                if c == sel_col and r == sel_row:
                    transparent_surface = pygame.Surface((BOARD_WIDTH // 8, HEIGHT // 8), pygame.SRCALPHA)
                    transparent_surface.fill(SELECTED_COLOR)  #Apply color with transparency
                    SCREEN.blit(transparent_surface, rect.topleft)  #Display the surface at the correct position

            #Highlight accessible squares
            for move in legal_moves:
                target_col = chess.square_file(move.to_square)
                target_row = 7 - chess.square_rank(move.to_square)
                if c == target_col and r == target_row:
                    center_x = c * BOARD_WIDTH // 8 + (BOARD_WIDTH // 16)
                    center_y = r * HEIGHT // 8 + (HEIGHT // 16)
                    radius = BOARD_WIDTH // 48  #Circle size
                    #Create a surface with transparency (RGBA)
                    circle_surface = pygame.Surface((BOARD_WIDTH // 8, HEIGHT // 8), pygame.SRCALPHA)  #Transparent surface
                    pygame.draw.circle(circle_surface, (100, 100, 100, 150), (BOARD_WIDTH // 16, HEIGHT // 16), radius)
                    #Blit the surface onto the main screen
                    SCREEN.blit(circle_surface, (c * BOARD_WIDTH // 8, r * HEIGHT // 8))
        #Display letters and numbers
        font = pygame.font.Font(None, 20)
        for r in range(8):
            for c in range(8):
            #Color opposite to the square
                text_color = WHITE if (r + c) % 2 == 1 else BLUE
                rect = pygame.Rect(c * BOARD_WIDTH // 8, r * HEIGHT // 8, BOARD_WIDTH // 8, HEIGHT // 8)
                #Display numbers on the first column (on the left)
                if c == 0:
                    number_text = font.render(str(8 - r), True, text_color)
                    SCREEN.blit(number_text, (rect.x + 2, rect.y + 2))
                #Display letters on the last rank (at the bottom)
                if r == 7:
                    letter_text = font.render(chr(ord('a') + c), True, text_color)
                    text_rect = letter_text.get_rect(bottomright=(rect.right - 2, rect.bottom - 2))
                    SCREEN.blit(letter_text, text_rect)

    if board:
        if board.is_check():
            king_square = board.king(board.turn)
            king_col = chess.square_file(king_square)
            king_row = 7 - chess.square_rank(king_square)
            transparent_surface = pygame.Surface((BOARD_WIDTH // 8, HEIGHT // 8), pygame.SRCALPHA)
            transparent_surface.fill((255, 0, 0, 100)) #Transparent red
            SCREEN.blit(transparent_surface, (king_col * BOARD_WIDTH // 8, king_row * HEIGHT // 8))
        if board.is_checkmate():
            king_square = board.king(board.turn)
            king_col = chess.square_file(king_square)
            king_row = 7 - chess.square_rank(king_square)
            transparent_surface = pygame.Surface((BOARD_WIDTH // 8, HEIGHT // 8), pygame.SRCALPHA)
            transparent_surface.fill((0, 0, 0, 100)) #Transparent black
            SCREEN.blit(transparent_surface, (king_col * BOARD_WIDTH // 8, king_row * HEIGHT // 8))
                      
# -- Function to draw the pieces --
def draw_pieces(board):
    for square in chess.SQUARES:
        piece = board.piece_at(square)
        if piece:
            col = chess.square_file(square)
            row = 7 - chess.square_rank(square)
            piece_str = piece.symbol()
            img_key = ('w' if piece_str.isupper() else 'b') + piece_str.lower()
            SCREEN.blit(IMAGES[img_key], pygame.Rect(col * BOARD_WIDTH // 8, row * HEIGHT // 8, BOARD_WIDTH // 8, HEIGHT // 8))

# -- Function to draw sidebar --
def draw_sidebar(move_history, scroll_offset):
    sidebar_rect = pygame.Rect(BOARD_WIDTH, 0, SIDEBAR_WIDTH, HEIGHT)
    pygame.draw.rect(SCREEN, SIDEBAR_BG, sidebar_rect)

    #Calculate the target width for the title and the separator line
    target_width = int(SIDEBAR_WIDTH * (0.6 if fullscreen_mode else 0.85))

    #Adjust font size for the title
    title_font = pygame.font.Font(None, 100)  #Large initial size
    title_text = "History of moves played"
    
    #Reduce font size until the width matches the target
    while title_font.size(title_text)[0] > target_width:
        title_font = pygame.font.Font(None, title_font.get_height() - 1)

    #Center the text and display it
    title_surface = title_font.render(title_text, True, (225, 225, 225))
    title_x = BOARD_WIDTH + (SIDEBAR_WIDTH - title_surface.get_width()) // 2
    SCREEN.blit(title_surface, (title_x, 5))

    #Separator line below the title
    line_start_x = BOARD_WIDTH + (SIDEBAR_WIDTH - target_width) // 2
    line_end_x = line_start_x + target_width
    pygame.draw.line(SCREEN, (220, 220, 220), (line_start_x, 35), (line_end_x, 35), 2)

    #Calculate space reserved for buttons
    button_height = 40
    button_padding = 10
    reserved_for_buttons = button_height + button_padding + 10

    #Scroll area
    scroll_area_rect = pygame.Rect(BOARD_WIDTH + 5, 40, SIDEBAR_WIDTH - 10, HEIGHT - 45 - reserved_for_buttons)
    pygame.draw.rect(SCREEN, (45, 45, 45), scroll_area_rect)

    #Display the moves
    font = pygame.font.Font(None, 28)
    y_offset = 45
    line_height = 30
    num_area_width = 50

    for i in range(0, len(move_history), 2):
        draw_y = y_offset - scroll_offset

        if scroll_area_rect.top <= draw_y < scroll_area_rect.bottom:
            num_rect_full = pygame.Rect(BOARD_WIDTH + 5, draw_y, num_area_width, line_height)
            pygame.draw.rect(SCREEN, SIDEBAR_BG, num_rect_full)

            num_text = f"{i // 2 + 1}"
            font.set_italic(True)
            num_surface = font.render(num_text, True, (160, 160, 160))
            num_text_rect = num_surface.get_rect(center=num_rect_full.center)
            SCREEN.blit(num_surface, num_text_rect.topleft)

            #Space for white and black moves
            remaining_space = SIDEBAR_WIDTH - (num_area_width + 15)
            white_x = BOARD_WIDTH + 5 + num_area_width + 10
            black_x = white_x + (remaining_space // 2)

            #Show the moves
            white_move_text = move_history[i]
            white_surface = font.render(white_move_text, True, (225, 225, 225))
            SCREEN.blit(white_surface, (white_x, draw_y + 5))

            if i + 1 < len(move_history):
                black_move_text = move_history[i + 1]
                black_surface = font.render(black_move_text, True, (225, 225, 225))
                SCREEN.blit(black_surface, (black_x, draw_y + 5))

        y_offset += line_height

    total_lines = (len(move_history) + 1) // 2
    content_height = total_lines * line_height

    if content_height > scroll_area_rect.height:
        scrollbar_height = scroll_area_rect.height * scroll_area_rect.height // content_height
        scrollbar_pos = scroll_offset * scroll_area_rect.height // content_height
        scrollbar_rect = pygame.Rect(BOARD_WIDTH + SIDEBAR_WIDTH - 15, scroll_area_rect.top + scrollbar_pos, 10, scrollbar_height)
        pygame.draw.rect(SCREEN, (100, 100, 100), scrollbar_rect)
        return scrollbar_rect, scroll_area_rect
    else:
        return None, scroll_area_rect

# -- Function to animate piece movement --
def animate_move(board, move, reverse=False):
    start_square = move.to_square if reverse else move.from_square
    end_square = move.from_square if reverse else move.to_square
    start_col = chess.square_file(start_square)
    start_row = 7 - chess.square_rank(start_square)
    end_col = chess.square_file(end_square)
    end_row = 7 - chess.square_rank(end_square)
    piece = board.piece_at(end_square if reverse else start_square)  #Always animate the piece that made the initial move
    captured_piece = board.piece_at(start_square if reverse else end_square)  #Captured piece
    
    if piece is None:
        return  #If no piece is found, do not perform the animation

    img_key = ('w' if piece.symbol().isupper() else 'b') + piece.symbol().lower()
    captured_img_key = ('w' if captured_piece and captured_piece.symbol().isupper() else 'b') + captured_piece.symbol().lower() if captured_piece else None
    start_pos = (start_col * BOARD_WIDTH // 8, start_row * HEIGHT // 8)
    end_pos = (end_col * BOARD_WIDTH // 8, end_row * HEIGHT // 8)
    frames = 10  #Number of frames for the animation

    for i in range(frames + 1):
        draw_board()
        draw_pieces(board)
        #Hide the piece on the starting square
        rect = pygame.Rect(start_col * BOARD_WIDTH // 8, start_row * HEIGHT // 8, BOARD_WIDTH // 8, HEIGHT // 8)
        pygame.draw.rect(SCREEN, WHITE if (start_row + start_col) % 2 == 0 else BLUE, rect)
        #Hide the piece on the destination square if reverse=True
        if reverse:
            rect = pygame.Rect(end_col * BOARD_WIDTH // 8, end_row * HEIGHT // 8, BOARD_WIDTH // 8, HEIGHT // 8)
            pygame.draw.rect(SCREEN, WHITE if (end_row + end_col) % 2 == 0 else BLUE, rect)
        #Draw the captured piece on the capture square throughout the animation
        if captured_piece:
            captured_pos = (start_col * BOARD_WIDTH // 8, start_row * HEIGHT // 8) if reverse else (end_col * BOARD_WIDTH // 8, end_row * HEIGHT // 8)
            SCREEN.blit(IMAGES[captured_img_key], captured_pos)
        #Draw the moving piece
        x = start_pos[0] + (end_pos[0] - start_pos[0]) * i / frames
        y = start_pos[1] + (end_pos[1] - start_pos[1]) * i / frames
        SCREEN.blit(IMAGES[img_key], (x, y))
        pygame.display.flip()
        pygame.time.delay(2)

# -- Function to check special state --
def check_special_states(board, game_over_message):
    #If an end message is not already defined, initialize it based on the state
    if not game_over_message:  #Only if a message has not already been defined
        if board.is_checkmate():
            winner = "blancs" if board.turn == chess.BLACK else "noirs"
            game_over_message = f"Échec et mat! Les {winner} remportent la victoire."
        elif board.is_stalemate():
            game_over_message = "Pat! La partie est nulle."
        elif board.is_insufficient_material():
            game_over_message = "Matériel insuffisant! La partie est nulle."
        elif board.can_claim_threefold_repetition():
            game_over_message = "Trois répétitions! La partie est nulle."
        elif board.can_claim_fifty_moves():
            game_over_message = "Règle des 50 coups! La partie est nulle."
    return game_over_message

# -- Function to display message --
def display_message(message, color=(0, 0, 0)):
    font = pygame.font.Font(None, 30)
    font.set_italic(True) #Italicize the text
    text = font.render(message, True, color)
    text_rect = text.get_rect(center=(BOARD_WIDTH // 2, HEIGHT // 2)) #Center the text

    #Add a background to the text
    background_color = (200, 200, 200) #Background color (white)
    background_rect = text_rect.inflate(3, 3) #Background size
    pygame.draw.rect(SCREEN, background_color, background_rect)

    #Display the text over the background and shadow
    SCREEN.blit(text, text_rect)

# -- Function to choose a promote piece --
def choose_promotion_piece(board, square):
    running_promotion = True
    promotion_choice = None
    #Create a mini promotion menu
    options = ['q', 'r', 'b', 'n']
    pieces_display = ['wq', 'wr', 'wb', 'wn'] if board.turn == chess.WHITE else ['bn', 'bb', 'br', 'bq']
    option_rects = []

    menu_width = BOARD_WIDTH // 8
    menu_height = HEIGHT // 8
    col = chess.square_file(square)
    row = 7 - chess.square_rank(square)
    #Vertical menu position next to the promotion square
    menu_x = col * menu_width
    if board.turn == chess.WHITE:
        menu_y = row * menu_height - 3 * menu_height
    else:
        menu_y = row * menu_height
    #Ensure the menu stays within the window
    menu_y = max(0, min(HEIGHT - 4 * menu_height, menu_y))

    while running_promotion:
        #Dim the rest
        draw_board(board=board)
        draw_pieces(board)
        gray_surface = pygame.Surface((BOARD_WIDTH, HEIGHT), pygame.SRCALPHA)
        gray_surface.fill((50, 50, 50, 180))
        SCREEN.blit(gray_surface, (0, 0))

       #Prepare the option rectangles
        option_rects.clear()
        for i, piece_key in enumerate(pieces_display):
            rect = pygame.Rect(menu_x, menu_y + i * menu_height, menu_width, menu_height)
            option_rects.append((rect, options[i] if board.turn == chess.WHITE else options[3 - i]))

        #Handle highlighting
        mouse_pos = pygame.mouse.get_pos()
        for rect, _ in option_rects:
            if rect.collidepoint(mouse_pos):
                pygame.draw.rect(SCREEN, (255, 0, 0), rect) #Red highlight
            else:
                pygame.draw.rect(SCREEN, (200, 200, 200), rect)

        #Draw the pieces
        for i, (rect, _) in enumerate(option_rects):
            SCREEN.blit(IMAGES[pieces_display[i]], rect)

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                for rect, choice in option_rects:
                    if rect.collidepoint(event.pos):
                        promotion_choice = choice
                        running_promotion = False
                        break

    return promotion_choice

# -- Function to draw sidebar buttons --
def draw_sidebar_buttons():
    button_width = SIDEBAR_WIDTH // 6  #Width of each button = 1/6 of the sidebar
    padding = button_width // 6  #Spacing between buttons = 1/6 of the button width
    total_width = button_width * 5 + padding * 6  #5 buttons + 6 spacings (including edges)
    start_x = BOARD_WIDTH + padding  #Left alignment with padding
    start_y = HEIGHT - 50 - 5  #Position at the bottom of the sidebar, fixed height of 50

    button_texts = ["|<", "<", "AI", ">", ">|"]
    button_rects = []

    font = pygame.font.Font(None, 32)

    for i in range(5):
        rect = pygame.Rect(start_x + i * (button_width + padding), start_y, button_width, 50)
        pygame.draw.rect(SCREEN, (0, 0, 0), rect)
        pygame.draw.rect(SCREEN, (50, 50, 50), rect, 2)  #Border

        text_surf = font.render(button_texts[i], True, (255, 255, 255))
        text_rect = text_surf.get_rect(center=rect.center)
        SCREEN.blit(text_surf, text_rect)

        button_rects.append(rect)

    return button_rects

# -- Main function --
def main():
    board = chess.Board()
    load_images()
    selected_square = None
    move_made = False
    game_over_message = None
    running = True
    game_over = False
    move_history = []
    current_move_index = -1
    left_arrow_pressed = False
    right_arrow_pressed = False
    arrow_press_start_time = 0
    arrow_press_interval = 50  #Interval in milliseconds for fast forward/backward
    scroll_offset = 0
    scroll_speed = 20
    scrollbar_dragging = False
    scrollbar_rect = None

    while running:
        legal_moves = []
        if selected_square is not None:
            legal_moves = [move for move in board.legal_moves if move.from_square == selected_square]
        SCREEN.fill((200, 200, 200)) #Initial sidebar background
        draw_board(selected_square, legal_moves, board)
        draw_pieces(board)
        #Create a temporary board to properly calculate SAN
        temp_board = chess.Board()
        san_history = []
        for move in move_history:
            try:
                if move in temp_board.legal_moves:
                    san_history.append(temp_board.san(move))
                    temp_board.push(move)
            except:
                pass
        scrollbar_rect, scroll_area_rect = draw_sidebar(san_history, scroll_offset)
        button_rects = draw_sidebar_buttons()



        if game_over_message:
            display_message(game_over_message)

        pygame.display.flip()

        if not game_over and (board.is_checkmate() or board.is_stalemate() or board.is_insufficient_material() or board.can_claim_threefold_repetition() or board.can_claim_fifty_moves()):
            game_over_message = check_special_states(board, game_over_message)
            game_over = True

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.VIDEORESIZE:
                toggle_fullscreen()

            elif event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = pygame.mouse.get_pos()
                if scrollbar_rect and scrollbar_rect.collidepoint(mouse_pos):
                    scrollbar_dragging = True
                    #Calculate the relative offset between the click and the top of the scrollbar for natural dragging
                    drag_offset_y = mouse_pos[1] - scrollbar_rect.y

                #Check if one of the buttons was clicked
                for i, rect in enumerate(button_rects):
                    if rect.collidepoint(mouse_pos):
                        if i == 0:  #Go to the beginning
                            while current_move_index >= 0:
                                move = move_history[current_move_index]
                                board.pop()
                                animate_move(board, move, reverse=True)
                                current_move_index -= 1
                            game_over_message = None
                            game_over = False

                        elif i == 1:  #Step backward (equivalent to left arrow key)
                            if current_move_index >= 0:
                                move = move_history[current_move_index]
                                board.pop()
                                animate_move(board, move, reverse=True)
                                current_move_index -= 1
                                game_over_message = None
                                game_over = False
                        elif i == 2:  #Random button
                            if not game_over:
                                move = AI.AI_move(board)
                                if move:
                                    board.push(move)
                                    move_history.append(move)
                                    current_move_index += 1
                                    move_made = True
                                move_history.append(board.peek())
                                current_move_index += 1
                                move_made = True

                        elif i == 3:  #Step forward (equivalent to right arrow key)
                            if current_move_index < len(move_history) - 1:
                                current_move_index += 1
                                move = move_history[current_move_index]
                                animate_move(board, move)
                                board.push(move)

                        elif i == 4:  #Go to the last move
                            while current_move_index < len(move_history) - 1:
                                current_move_index += 1
                                move = move_history[current_move_index]
                                animate_move(board, move)
                                board.push(move)

                        break  #Avoid doing anything else after a button click
                if event.button == 4: #Scroll up
                    scroll_offset = max(0, scroll_offset - scroll_speed)
                elif event.button == 5: #Scroll down
                    #Calculate the total possible scroll height
                    moves_per_line = 2
                    line_height = 30
                    total_lines = (len(san_history) + 1) // 2
                    content_height = total_lines * line_height
                    max_offset = max(0, content_height - scroll_area_rect.height)
                    scroll_offset = min(max_offset, scroll_offset + scroll_speed)

                location = pygame.mouse.get_pos()
                if location[0] < BOARD_WIDTH and location[1] < HEIGHT:
                    col = location[0] // (BOARD_WIDTH // 8)
                    row = 7 - (location[1] // (HEIGHT // 8))
                    square = chess.square(col, row)


                if board.piece_at(square) and (board.turn == board.piece_at(square).color):
                    if selected_square == square:
                        selected_square = None  #Deselect the piece if it is already selected
                    else:
                        selected_square = square  #Select a new piece
                else:
                    if selected_square is not None:
                        move = chess.Move(selected_square, square)
                        if move in board.legal_moves:
                            animate_move(board, move)  #Apply the animation
                            board.push(move)
                            move_history = move_history[:current_move_index + 1]
                            move_history.append(move)
                            current_move_index += 1
                            move_made = True
                            selected_square = None
                        elif board.piece_at(selected_square) is not None and board.piece_at(selected_square).piece_type == chess.PAWN: #to include pawns reaching the last rank but not pinned pieces on the last rank
                            promotion_moves = [move for move in board.legal_moves if move.from_square == selected_square and move.to_square == square and move.promotion]
                            if promotion_moves:
                                promotion_piece = choose_promotion_piece(board, square)

                                promotion_move = chess.Move.from_uci(chess.square_name(selected_square) + chess.square_name(square) + promotion_piece)
                                if promotion_move in board.legal_moves:
                                    animate_move(board, promotion_move) #Apply the animation
                                    board.push(promotion_move)
                                    move_history = move_history[:current_move_index + 1]
                                    move_history.append(promotion_move)
                                    current_move_index += 1
                                    move_made = True
                            selected_square = None
                    else:
                        selected_square = None

            elif event.type == pygame.MOUSEBUTTONUP:
                scrollbar_dragging = False

            elif event.type == pygame.MOUSEMOTION:
                if scrollbar_dragging and scrollbar_rect:
                    mouse_y = pygame.mouse.get_pos()[1]
                    #Calculate the new position based on the mouse and initial offset
                    new_scrollbar_y = mouse_y - drag_offset_y
                    scroll_area_height = scroll_area_rect.height
                    total_lines = (len(san_history) + 1) // 2
                    content_height = total_lines * 30
                    max_scroll_offset = max(0, content_height - scroll_area_height)
                    max_scrollbar_y = scroll_area_height - scrollbar_rect.height
                    new_scrollbar_y = max(0, min(max_scrollbar_y, new_scrollbar_y))
                    #Update scroll_offset based on the scrollbar's relative position
                    scroll_offset = int(new_scrollbar_y * content_height / scroll_area_height)

                
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_u:
                    if board.move_stack:
                        board.pop()
                        current_move_index -= 1

                elif event.key == pygame.K_LEFT:
                    left_arrow_pressed = True
                    arrow_press_start_time = pygame.time.get_ticks()

                elif event.key == pygame.K_RIGHT:
                    right_arrow_pressed = True
                    arrow_press_start_time = pygame.time.get_ticks()

            elif event.type == pygame.KEYUP:
                if event.key == pygame.K_LEFT:
                    left_arrow_pressed = False

                elif event.key == pygame.K_RIGHT:
                    right_arrow_pressed = False

        #Handle long press on left and right arrow keys
        current_time = pygame.time.get_ticks()
        if left_arrow_pressed and current_time - arrow_press_start_time >= arrow_press_interval:
            if current_move_index >= 0:
                move = move_history[current_move_index]
                board.pop()
                animate_move(board, move, reverse=True)  #Apply reverse animation to go backward
                current_move_index -= 1
                arrow_press_start_time = current_time
                if game_over_message and not (board.is_checkmate() or board.is_stalemate() or board.is_insufficient_material() or board.can_claim_threefold_repetition() or board.can_claim_fifty_moves()):
                    game_over_message = None
                    game_over = False

        if right_arrow_pressed and current_time - arrow_press_start_time >= arrow_press_interval:
            if current_move_index < len(move_history) - 1:
                current_move_index += 1
                move = move_history[current_move_index]
                animate_move(board, move)  #Apply animation to go forward
                board.push(move)
                arrow_press_start_time = current_time

        if move_made:
            if not game_over:
                game_over_message = check_special_states(board, game_over_message)
            move_made = False
    pygame.quit()

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

if __name__ == "__main__":
    main()