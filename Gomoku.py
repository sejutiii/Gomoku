import numpy as np
import pygame
import asyncio
import platform
import time
from pygame import Vector2

FPS = 60

class Gomoku:
    def __init__(self, size=10):
        self.size = size
        self.board = np.zeros((size, size), dtype=int)  # 0: empty, 1: player, 2: AI
        self.current_player = 1
        self.directions = [(0, 1), (1, 0), (1, 1), (1, -1)]
        self.game_over = False
        self.winner = None

    def is_valid_move(self, row, col):
        return 0 <= row < self.size and 0 <= col < self.size and self.board[row][col] == 0

    def make_move(self, row, col, player):
        if self.is_valid_move(row, col):
            self.board[row][col] = player
            return True
        return False

    def check_winner(self, player):
        for row in range(self.size):
            for col in range(self.size):
                if self.board[row][col] != player:
                    continue
                for dr, dc in self.directions:
                    count = 1
                    for k in range(1, 5):
                        r, c = row + dr * k, col + dc * k
                        if 0 <= r < self.size and 0 <= c < self.size and self.board[r][c] == player:
                            count += 1
                        else:
                            break
                    if count >= 5:
                        return True
        return False

    def is_board_full(self):
        return not np.any(self.board == 0)

    def check_immediate_threat(self, player):
        for row in range(self.size):
            for col in range(self.size):
                if self.board[row][col] != 0:
                    continue
                self.board[row][col] = player
                if self.check_winner(player):
                    self.board[row][col] = 0
                    return (row, col)
                self.board[row][col] = 0
        return None

    def has_open_three(self, player):
        for row in range(self.size):
            for col in range(self.size):
                if self.board[row][col] != player:
                    continue
                for dr, dc in self.directions:
                    count = 1
                    blocked_ends = 0
                    for k in range(1, 4):
                        r, c = row + dr * k, col + dc * k
                        if 0 <= r < self.size and 0 <= c < self.size:
                            if self.board[r][c] == player:
                                count += 1
                            elif self.board[r][c] != 0:
                                blocked_ends += 1
                                break
                            else:
                                break
                        else:
                            blocked_ends += 1
                            break
                    for k in range(1, 4):
                        r, c = row - dr * k, col - dc * k
                        if 0 <= r < self.size and 0 <= c < self.size:
                            if self.board[r][c] == player:
                                count += 1
                            elif self.board[r][c] != 0:
                                blocked_ends += 1
                                break
                            else:
                                break
                        else:
                            blocked_ends += 1
                            break
                    if count == 3 and blocked_ends == 0:
                        return True
        return False

    def has_open_four(self, player):
        for row in range(self.size):
            for col in range(self.size):
                if self.board[row][col] != player:
                    continue
                for dr, dc in self.directions:
                    count = 1
                    blocked_ends = 0
                    for k in range(1, 5):
                        r, c = row + dr * k, col + dc * k
                        if 0 <= r < self.size and 0 <= c < self.size:
                            if self.board[r][c] == player:
                                count += 1
                            elif self.board[r][c] != 0:
                                blocked_ends += 1
                                break
                            else:
                                break
                        else:
                            blocked_ends += 1
                            break
                    for k in range(1, 5):
                        r, c = row - dr * k, col - dc * k
                        if 0 <= r < self.size and 0 <= c < self.size:
                            if self.board[r][c] == player:
                                count += 1
                            elif self.board[r][c] != 0:
                                blocked_ends += 1
                                break
                            else:
                                break
                        else:
                            blocked_ends += 1
                            break
                    if count == 4 and blocked_ends == 0:
                        return True
        return False

    def create_open_four(self, player):
        for row in range(self.size):
            for col in range(self.size):
                if self.board[row][col] != 0:
                    continue
                self.board[row][col] = player
                if self.has_open_four(player):
                    self.board[row][col] = 0
                    return (row, col)
                self.board[row][col] = 0
        return None

    def block_open_three(self, player):
        for row in range(self.size):
            for col in range(self.size):
                if self.board[row][col] != 0:
                    continue
                self.board[row][col] = 2
                if not self.has_open_three(player):
                    self.board[row][col] = 0
                    return (row, col)
                self.board[row][col] = 0
        return None

    def evaluate_player(self, player):
        score = 0
        for row in range(self.size):
            for col in range(self.size):
                if self.board[row][col] != player:
                    continue
                for dr, dc in self.directions:
                    count = 1
                    blocked = 0
                    for k in range(1, 5):
                        r, c = row + dr * k, col + dc * k
                        if 0 <= r < self.size and 0 <= c < self.size:
                            if self.board[r][c] == player:
                                count += 1
                            elif self.board[r][c] != 0:
                                blocked += 1
                                break
                            else:
                                break
                        else:
                            blocked += 1
                            break
                    for k in range(1, 5):
                        r, c = row - dr * k, col - dc * k
                        if 0 <= r < self.size and 0 <= c < self.size:
                            if self.board[r][c] == player:
                                count += 1
                            elif self.board[r][c] != 0:
                                blocked += 1
                                break
                            else:
                                break
                        else:
                            blocked += 1
                            break
                    if count >= 5:
                        score += 1000000
                    elif count == 4 and blocked == 0:
                        score += 2000000  # Increased to prioritize creating open four
                    elif count == 4 and blocked == 1:
                        score += 1000
                    elif count == 3 and blocked == 0:
                        score += 100
                    elif count == 3 and blocked == 1:
                        score += 50
                    elif count == 2 and blocked == 0:
                        score += 10
        return score

    def evaluate_board(self):
        player_score = self.evaluate_player(1)
        ai_score = self.evaluate_player(2)
        threat = self.check_immediate_threat(1 if self.current_player == 2 else 2)
        if threat:
            if self.current_player == 2:
                return -10000000
            else:
                return 10000000
        if self.has_open_three(1):
            return ai_score - player_score - 750000
        return ai_score - player_score

    def get_possible_moves(self):
        moves = []
        radius = 1
        for i in range(self.size):
            for j in range(self.size):
                if self.board[i][j] == 0:
                    near_stone = False
                    for di in range(-radius, radius + 1):
                        for dj in range(-radius, radius + 1):
                            ni, nj = i + di, j + dj
                            if 0 <= ni < self.size and 0 <= nj < self.size and self.board[ni][nj] != 0:
                                near_stone = True
                                break
                        if near_stone:
                            break
                    if near_stone:
                        moves.append((i, j))
        return moves if moves else [(self.size // 2, self.size // 2)]

    def minimax(self, depth, alpha, beta, maximizing_player):
        if depth == 0 or self.check_winner(1) or self.check_winner(2) or self.is_board_full():
            return self.evaluate_board()
        moves = self.get_possible_moves()
        if maximizing_player:
            max_eval = float('-inf')
            for move in moves:
                row, col = move
                self.board[row][col] = 2
                eval = self.minimax(depth - 1, alpha, beta, False)
                self.board[row][col] = 0
                max_eval = max(max_eval, eval)
                alpha = max(alpha, eval)
                if beta <= alpha:
                    break
            return max_eval
        else:
            min_eval = float('inf')
            for move in moves:
                row, col = move
                self.board[row][col] = 1
                eval = self.minimax(depth - 1, alpha, beta, True)
                self.board[row][col] = 0
                min_eval = min(min_eval, eval)
                beta = min(beta, eval)
                if beta <= alpha:
                    break
            return min_eval

    def find_best_move(self, depth=2):
        # Check if AI can win immediately
        ai_win = self.check_immediate_threat(2)
        if ai_win:
            return ai_win
        # Check if player can win immediately
        threat = self.check_immediate_threat(1)
        if threat:
            return threat
        # Check if AI can create an open four (leads to a guaranteed win)
        open_four_move = self.create_open_four(2)
        if open_four_move:
            return open_four_move
        # Check if player has an open three and block it
        if self.has_open_three(1):
            block_move = self.block_open_three(1)
            if block_move:
                return block_move
        # Otherwise, use Minimax
        best_score = float('-inf')
        best_move = None
        moves = self.get_possible_moves()
        for move in moves:
            row, col = move
            self.board[row][col] = 2
            score = self.minimax(depth - 1, float('-inf'), float('inf'), False)
            self.board[row][col] = 0
            if score > best_score:
                best_score = score
                best_move = move
        return best_move if best_move else moves[0]

class GomokuGame:
    def __init__(self):
        pygame.init()
        self.cell_size = 60
        self.board_size = 10 * self.cell_size
        self.screen_width = self.board_size
        self.screen_height = self.board_size + 100
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
        pygame.display.set_caption("Gomoku")
        self.font = pygame.font.SysFont("Arial", 24)
        self.game = Gomoku(size=10)
        self.status = "Player's Turn"
        self.restart_button = pygame.Rect(self.screen_width - 120, self.screen_height - 80, 100, 40)

    def draw_board(self):
        self.screen.fill((255, 255, 255))
        for i in range(self.game.size):
            pygame.draw.line(self.screen, (0, 0, 0),
                             (0, i * self.cell_size), (self.board_size, i * self.cell_size), 2)
            pygame.draw.line(self.screen, (0, 0, 0),
                             (i * self.cell_size, 0), (i * self.cell_size, self.board_size), 2)
        for row in range(self.game.size):
            for col in range(self.game.size):
                if self.game.board[row][col] == 1:
                    pygame.draw.circle(self.screen, (0, 0, 0),
                                       (col * self.cell_size + self.cell_size // 2,
                                        row * self.cell_size + self.cell_size // 2), 25)
                elif self.game.board[row][col] == 2:
                    pygame.draw.circle(self.screen, (255, 255, 255),
                                       (col * self.cell_size + self.cell_size // 2,
                                        row * self.cell_size + self.cell_size // 2), 25)
                    pygame.draw.circle(self.screen, (0, 0, 0),
                                       (col * self.cell_size + self.cell_size // 2,
                                        row * self.cell_size + self.cell_size // 2), 25, 2)
        status_text = self.font.render(self.status, True, (0, 0, 0))
        self.screen.blit(status_text, (10, self.board_size + 10))
        pygame.draw.rect(self.screen, (200, 200, 200), self.restart_button)
        restart_text = self.font.render("Restart", True, (0, 0, 0))
        self.screen.blit(restart_text, (self.restart_button.x + 10, self.restart_button.y + 10))

    def handle_click(self, pos):
        if self.game.game_over:
            if self.restart_button.collidepoint(pos):
                self.game = Gomoku(size=10)
                self.status = "Player's Turn"
            return
        x, y = pos
        if y < self.board_size:
            row = y // self.cell_size
            col = x // self.cell_size
            if self.game.make_move(row, col, 1):
                self.status = "AI's Turn"
                if self.game.check_winner(1):
                    self.status = "Player Wins!"
                    self.game.game_over = True
                    self.game.winner = 1
                elif self.game.is_board_full():
                    self.status = "Draw!"
                    self.game.game_over = True
                else:
                    self.ai_move()

    def ai_move(self):
        start_time = time.time()
        move = self.game.find_best_move(depth=2)
        end_time = time.time()
        if move:
            row, col = move
            self.game.make_move(row, col, 2)
            self.status = f"Player's Turn (AI moved in {end_time - start_time:.2f}s)"
            if self.game.check_winner(2):
                self.status = "AI Wins!"
                self.game.game_over = True
                self.game.winner = 2
            elif self.game.is_board_full():
                self.status = "Draw!"
                self.game.game_over = True

    def update_loop(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return
            if event.type == pygame.MOUSEBUTTONDOWN and self.game.current_player == 1:
                self.handle_click(event.pos)
        self.draw_board()
        pygame.display.flip()

def setup():
    global game
    game = GomokuGame()

async def main():
    setup()
    while True:
        game.update_loop()
        await asyncio.sleep(1.0 / FPS)

if platform.system() == "Emscripten":
    asyncio.ensure_future(main())
else:
    if __name__ == "__main__":
        asyncio.run(main())