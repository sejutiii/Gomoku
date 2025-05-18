import pygame
import time
import os
from Logic import GomokuLogic

class GomokuGame:
    def __init__(self):
        pygame.init()
        self.cell_size = 60
        self.board_size = 10 * self.cell_size
        self.screen_width = self.board_size
        self.screen_height = self.board_size + 100
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
        pygame.display.set_caption("Gomoku")
        
        try:
            self.title_font = pygame.font.Font("fonts/PressStart2P-Regular.ttf", 54)
            self.button_font = pygame.font.Font("fonts/PressStart2P-Regular.ttf", 24)
            self.status_font = pygame.font.Font("fonts/PressStart2P-Regular.ttf", 24)
        except FileNotFoundError as e:
            print(f"Font file not found: {e}. Falling back to monospace font.")
            self.title_font = pygame.font.SysFont("monospace", 54, bold=True)
            self.button_font = pygame.font.SysFont("monospace", 24, bold=True)
            self.status_font = pygame.font.SysFont("monospace", 24, bold=True)
        
        # Load background image
        self.background = None
        webp_path = "images/neongrid.webp"
        png_path = "images/neongrid.png"
        try:
            if os.path.exists(webp_path):
                self.background = pygame.image.load(webp_path).convert_alpha()
                print(f"Loaded {webp_path} successfully.")
            elif os.path.exists(png_path):
                self.background = pygame.image.load(png_path).convert_alpha()
                print(f"Loaded {png_path} successfully.")
            else:
                raise FileNotFoundError("Neither neongrid.webp nor neongrid.png found in images/.")
            self.background = pygame.transform.scale(self.background, (self.screen_width, self.screen_height))
            self.background.set_alpha(128)  # 50% opacity
        except (FileNotFoundError, pygame.error) as e:
            print(f"Failed to load background image: {e}. Falling back to gradient background.")
            self.background = pygame.Surface((self.screen_width, self.screen_height))
            for y in range(self.screen_height):
                t = y / self.screen_height
                r = int(10 * (1 - t) + 0 * t)  # Dark blue to black
                g = int(30 * (1 - t) + 0 * t)
                b = int(45 * (1 - t) + 0 * t)
                pygame.draw.line(self.background, (r, g, b), (0, y), (self.screen_width, y))
        
        self.state = "start"
        self.game = None
        self.status = ""
        self.restart_button = pygame.Rect(self.screen_width - 140, self.screen_height - 80, 120, 40)
        self.menu_button = pygame.Rect(self.screen_width - 280, self.screen_height - 80, 120, 40)
        self.pvai_button = pygame.Rect(self.screen_width // 2 - 150, self.screen_height // 2 - 80, 300, 50)
        self.pvp_button = pygame.Rect(self.screen_width // 2 - 150, self.screen_height // 2 + 10, 300, 50)
        self.button_alpha = 0
        self.title_alpha = 0
        self.button_scale = 1.0
        self.animation_start = time.time()
        self.board_alpha = 0
        self.colors = {
            "bg": (60, 20, 90),
            "board_lines": (255, 255, 255),
            "board_lines_glow": (0, 191, 255, 128),
            "player1": (0, 109, 119),
            "player2": (245, 246, 245),
            "player2_outline": (0, 191, 255),
            "button_normal": (100, 50, 100),
            "button_hover": (80, 30 , 80),
            "text": (200, 191, 255),
            "hover_tile": (0, 191, 255, 128)
        }

    def draw_start_screen(self):
        self.screen.blit(self.background, (0, 0))  # Draw background image or gradient
        elapsed = time.time() - self.animation_start
        if elapsed < 0.5:
            self.title_alpha = min(255, self.title_alpha + 255 * (1 / 60))
            self.button_alpha = min(255, self.button_alpha + 255 * (1 / 60))
            self.button_scale = 1.0 + 0.1 * (1 - elapsed / 0.5)
        else:
            self.title_alpha = 255
            self.button_alpha = 255
            self.button_scale = 1.0
        title_text = self.title_font.render("Gomoku", True, self.colors["text"])
        shadow_text = self.title_font.render("Gomoku", True, (0, 0, 0))
        title_x = self.screen_width // 2 - title_text.get_width() // 2
        self.screen.blit(shadow_text, (title_x + 2, 52))
        self.screen.blit(title_text, (title_x, 50))

        pvai_surface = pygame.Surface((300, 50), pygame.SRCALPHA)
        pvp_surface = pygame.Surface((300, 50), pygame.SRCALPHA)
        mouse_pos = pygame.mouse.get_pos()
        pvai_color = self.colors["button_hover"] if self.pvai_button.collidepoint(mouse_pos) else self.colors["button_normal"]
        pvp_color = self.colors["button_hover"] if self.pvp_button.collidepoint(mouse_pos) else self.colors["button_normal"]
        pvai_scale = 1.1 if self.pvai_button.collidepoint(mouse_pos) else self.button_scale
        pvp_scale = 1.1 if self.pvp_button.collidepoint(mouse_pos) else self.button_scale
        pygame.draw.rect(pvai_surface, (*pvai_color, int(self.button_alpha)), (0, 0, 300, 50), border_radius=10)
        pygame.draw.rect(pvp_surface, (*pvp_color, int(self.button_alpha)), (0, 0, 300, 50), border_radius=10)
        pvai_text = self.button_font.render("Player VS AI", True, self.colors["text"])
        pvp_text = self.button_font.render("Player VS Player", True, self.colors["text"])
        pvai_surface.blit(pvai_text, (150 - pvai_text.get_width() // 2, 25 - pvai_text.get_height() // 2))
        pvp_surface.blit(pvp_text, (150 - pvp_text.get_width() // 2, 25 - pvp_text.get_height() // 2))
        scaled_pvai = pygame.transform.scale(pvai_surface, (int(300 * pvai_scale), int(50 * pvai_scale)))
        scaled_pvp = pygame.transform.scale(pvp_surface, (int(300 * pvp_scale), int(50 * pvp_scale)))
        self.screen.blit(scaled_pvai, (self.screen_width // 2 - int(150 * pvai_scale), self.screen_height // 2 - int(80 * pvai_scale)))
        self.screen.blit(scaled_pvp, (self.screen_width // 2 - int(150 * pvp_scale), self.screen_height // 2 - int(25 * pvp_scale)))

    def draw_board(self):
        self.screen.fill(self.colors["bg"])
        board_surface = pygame.Surface((self.board_size, self.board_size), pygame.SRCALPHA)
        if self.board_alpha < 255:
            self.board_alpha += 255 * (1 / 60)
        for i in range(self.game.size):
            pygame.draw.line(board_surface, self.colors["board_lines_glow"],
                             (0, i * self.cell_size), (self.board_size, i * self.cell_size), 5)
            pygame.draw.line(board_surface, self.colors["board_lines_glow"],
                             (i * self.cell_size, 0), (i * self.cell_size, self.board_size), 5)
            pygame.draw.line(board_surface, self.colors["board_lines"],
                             (0, i * self.cell_size), (self.board_size, i * self.cell_size), 3)
            pygame.draw.line(board_surface, self.colors["board_lines"],
                             (i * self.cell_size, 0), (i * self.cell_size, self.board_size), 3)
        for row in range(self.game.size):
            for col in range(self.game.size):
                if self.game.board[row][col] == 1:
                    pygame.draw.circle(board_surface, self.colors["player1"],
                                       (col * self.cell_size + self.cell_size // 2,
                                        row * self.cell_size + self.cell_size // 2), 25)
                elif self.game.board[row][col] == 2:
                    pygame.draw.circle(board_surface, self.colors["player2"],
                                       (col * self.cell_size + self.cell_size // 2,
                                        row * self.cell_size + self.cell_size // 2), 25)
                    pygame.draw.circle(board_surface, self.colors["player2_outline"],
                                       (col * self.cell_size + self.cell_size // 2,
                                        row * self.cell_size + self.cell_size // 2), 25, 2)
        mouse_x, mouse_y = pygame.mouse.get_pos()
        if mouse_y < self.board_size and not self.game.game_over:
            row = mouse_y // self.cell_size
            col = mouse_x // self.cell_size
            if self.game.is_valid_move(row, col):
                hover_color = self.colors["hover_tile"] if self.game.current_player == 1 else (*self.colors["player2"], 128)
                pygame.draw.circle(board_surface, hover_color,
                                   (col * self.cell_size + self.cell_size // 2,
                                    row * self.cell_size + self.cell_size // 2), 25)

        # Draw strike-through line for winning sequence
        if self.game.game_over and self.game.winner is not None and hasattr(self.game, 'winning_sequence'):
            if self.game.winning_sequence and len(self.game.winning_sequence) >= 5:
                # Get the first and last points of the winning sequence
                start_pos = self.game.winning_sequence[0]
                end_pos = self.game.winning_sequence[-1]
                # Convert board coordinates to pixel coordinates (center of cells)
                start_x = start_pos[1] * self.cell_size + self.cell_size // 2
                start_y = start_pos[0] * self.cell_size + self.cell_size // 2
                end_x = end_pos[1] * self.cell_size + self.cell_size // 2
                end_y = end_pos[0] * self.cell_size + self.cell_size // 2
                # Draw the strike-through line
                pygame.draw.line(board_surface, (255, 0, 0), (start_x, start_y), (end_x, end_y), 5)

        board_surface.set_alpha(int(self.board_alpha))
        self.screen.blit(board_surface, (0, 0))
        status_text = self.status_font.render(self.status, True, self.colors["text"])
        shadow_text = self.status_font.render(self.status, True, (0, 0, 0))
        self.screen.blit(shadow_text, (12, self.board_size + 12))
        self.screen.blit(status_text, (10, self.board_size + 10))
        mouse_pos = pygame.mouse.get_pos()
        restart_color = self.colors["button_hover"] if self.restart_button.collidepoint(mouse_pos) else self.colors["button_normal"]
        restart_surface = pygame.Surface((120, 40), pygame.SRCALPHA)
        restart_scale = 1.1 if self.restart_button.collidepoint(mouse_pos) else 1.0
        pygame.draw.rect(restart_surface, restart_color, (0, 0, 120, 40), border_radius=10)
        restart_text = self.button_font.render("Restart", True, self.colors["text"])
        restart_surface.blit(restart_text, (60 - restart_text.get_width() // 2, 20 - restart_text.get_height() // 2))
        scaled_restart = pygame.transform.scale(restart_surface, (int(120 * restart_scale), int(40 * restart_scale)))
        self.screen.blit(scaled_restart, (self.screen_width - int(140 * restart_scale), self.screen_height - int(80 * restart_scale)))
        menu_color = self.colors["button_hover"] if self.menu_button.collidepoint(mouse_pos) else self.colors["button_normal"]
        menu_surface = pygame.Surface((120, 40), pygame.SRCALPHA)
        menu_scale = 1.1 if self.menu_button.collidepoint(mouse_pos) else 1.0
        pygame.draw.rect(menu_surface, menu_color, (0, 0, 120, 40), border_radius=10)
        menu_text = self.button_font.render("Menu", True, self.colors["text"])
        menu_surface.blit(menu_text, (60 - menu_text.get_width() // 2, 20 - menu_text.get_height() // 2))
        scaled_menu = pygame.transform.scale(menu_surface, (int(120 * menu_scale), int(40 * menu_scale)))
        self.screen.blit(scaled_menu, (self.screen_width - int(280 * menu_scale), self.screen_height - int(80 * menu_scale)))

    def handle_click(self, pos):
        if self.state == "start":
            if self.pvai_button.collidepoint(pos):
                self.game = GomokuLogic(size=10, game_mode="Player VS AI")
                self.state = "game"
                self.status = "Player's Turn"
                self.board_alpha = 0
            elif self.pvp_button.collidepoint(pos):
                self.game = GomokuLogic(size=10, game_mode="Player VS Player")
                self.state = "game"
                self.status = "Player 1's Turn"
                self.board_alpha = 0
        elif self.state == "game":
            if self.restart_button.collidepoint(pos):
                print("Restart button clicked")
                self.game = GomokuLogic(size=10, game_mode=self.game.game_mode)
                self.status = "Player's Turn" if self.game.game_mode == "Player VS AI" else "Player 1's Turn"
                self.board_alpha = 0
                return
            if self.menu_button.collidepoint(pos):
                print("Menu button clicked")
                self.game = None
                self.state = "start"
                self.status = ""
                self.button_alpha = 0
                self.title_alpha = 0
                self.animation_start = time.time()
                return
            if self.game.game_over:
                return
            x, y = pos
            if y < self.board_size:
                row = y // self.cell_size
                col = x // self.cell_size
                if self.game.make_move(row, col, self.game.current_player):
                    print(f"Player {self.game.current_player} moved at ({row}, {col})")
                    if self.game.check_winner(self.game.current_player):
                        self.status = "Player Wins!" if self.game.game_mode == "Player VS AI" and self.game.current_player == 1 else "AI Wins!" if self.game.game_mode == "Player VS AI" else f"Player {self.game.current_player} Wins!"
                        self.game.game_over = True
                        self.game.winner = self.game.current_player
                        print(f"Winner: Player {self.game.current_player}")
                    elif self.game.is_board_full():
                        self.status = "Draw!"
                        self.game.game_over = True
                        print("Game ended in a draw")
                    else:
                        self.game.current_player = 2 if self.game.current_player == 1 else 1
                        self.status = "AI's Turn" if self.game.game_mode == "Player VS AI" and self.game.current_player == 2 else "Player's Turn" if self.game.game_mode == "Player VS AI" else f"Player {self.game.current_player}'s Turn"
                        print(f"Next turn: {self.status}")
                        if self.game.game_mode == "Player VS AI" and self.game.current_player == 2:
                            self.ai_move()

    def ai_move(self):
        if self.game.game_mode != "Player VS AI" or self.game.current_player != 2:
            print("AI move skipped: Wrong mode or turn")
            return
        start_time = time.time()
        move = self.game.find_best_move(depth=2)
        end_time = time.time()
        if move:
            row, col = move
            self.game.make_move(row, col, 2)
            print(f"AI moved at ({row}, {col}) in {end_time - start_time:.2f}s")
            if self.game.check_winner(2):
                self.status = "AI Wins!"
                self.game.game_over = True
                self.game.winner = 2
                print("AI wins")
            elif self.game.is_board_full():
                self.status = "Draw!"
                self.game.game_over = True
                print("Game ended in a draw")
            else:
                self.game.current_player = 1
                self.status = "Player's Turn"
                print("Player's turn")
        else:
            print("No valid AI move found")

    def update_loop(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return
            if event.type == pygame.MOUSEBUTTONDOWN:
                self.handle_click(event.pos)
        if self.state == "start":
            self.draw_start_screen()
        else:
            self.draw_board()
        pygame.display.flip()