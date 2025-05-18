import numpy as np

class GomokuLogic:
    def __init__(self, size=10, game_mode="Player VS AI"):
        self.size = size
        self.board = np.zeros((size, size), dtype=int)  # 0: empty, 1: player, 2: AI
        self.current_player = 1
        self.directions = [(0, 1), (1, 0), (1, 1), (1, -1)]
        self.game_over = False
        self.winner = None
        self.last_move = None
        # Cache for pattern detection
        self.pattern_cache = {}
        # Store move history for faster relevant move generation
        self.move_history = []
        # Transposition table for minimax
        self.transposition_table = {}
        self.game_mode = game_mode  # Added for compatibility with UI.py
        # Track the winning sequence
        self.winning_sequence = []

    def is_valid_move(self, row, col):
        return 0 <= row < self.size and 0 <= col < self.size and self.board[row][col] == 0

    def make_move(self, row, col, player):
        if self.is_valid_move(row, col):
            self.board[row][col] = player
            self.last_move = (row, col)
            self.move_history.append((row, col))
            # Clear the pattern cache when a move is made
            self.pattern_cache = {}
            return True
        return False

    def check_winner(self, player, last_move=None):
        if last_move is None:
            if self.last_move:
                last_move = self.last_move
            else:
                return False
            
        row, col = last_move
        if self.board[row][col] != player:
            return False
        
        # Check if this position was already evaluated
        cache_key = (row, col, player)
        if cache_key in self.pattern_cache:
            result = self.pattern_cache[cache_key].get('winner', False)
            if result:
                self.winning_sequence = self.pattern_cache[cache_key].get('sequence', [])
            return result
        
        for dr, dc in self.directions:
            count = 1
            sequence = [last_move]
            # Check forward
            for k in range(1, 5):
                r, c = row + dr * k, col + dc * k
                if 0 <= r < self.size and 0 <= c < self.size and self.board[r][c] == player:
                    count += 1
                    sequence.append((r, c))
                else:
                    break
            # Check backward
            for k in range(1, 5):
                r, c = row - dr * k, col - dc * k
                if 0 <= r < self.size and 0 <= c < self.size and self.board[r][c] == player:
                    count += 1
                    sequence.append((r, c))
                else:
                    break
            if count >= 5:
                # Sort the sequence from top-left to bottom-right or similar order
                sequence.sort(key=lambda pos: (pos[0], pos[1]) if dr >= 0 else (-pos[0], pos[1]))
                self.winning_sequence = sequence
                self.pattern_cache[cache_key] = {'winner': True, 'sequence': sequence}
                return True
        
        self.pattern_cache[cache_key] = {'winner': False}
        return False

    def is_board_full(self):
        return len(self.move_history) >= self.size * self.size

    def _count_stones_in_direction(self, row, col, player, dr, dc, max_count=5):
        """Helper function to count consecutive stones in a direction"""
        count = 0
        empty_spots = []
        for k in range(1, max_count):
            r, c = row + dr * k, col + dc * k
            if 0 <= r < self.size and 0 <= c < self.size:
                if self.board[r][c] == player:
                    count += 1
                elif self.board[r][c] == 0:
                    empty_spots.append((r, c))
                    break
                else:
                    break
            else:
                break
        return count, empty_spots

    def check_immediate_threat(self, player):
        """Find winning move for a player"""
        # Cache key for this evaluation
        cache_key = ('threat', player, hash(self.board.tobytes()))
        if cache_key in self.pattern_cache:
            return self.pattern_cache[cache_key]
        
        # Only check empty spots near existing stones (within 2 cells)
        checked_positions = set()
        for r, c in self.move_history:
            for dr in range(-2, 3):
                for dc in range(-2, 3):
                    check_r, check_c = r + dr, c + dc
                    if (0 <= check_r < self.size and 0 <= check_c < self.size and 
                        self.board[check_r][check_c] == 0 and 
                        (check_r, check_c) not in checked_positions):
                        
                        checked_positions.add((check_r, check_c))
                        self.board[check_r][check_c] = player
                        if self.check_winner(player, last_move=(check_r, check_c)):
                            self.board[check_r][check_c] = 0
                            self.pattern_cache[cache_key] = (check_r, check_c)
                            return (check_r, check_c)
                        self.board[check_r][check_c] = 0
        
        self.pattern_cache[cache_key] = None
        return None

    def find_open_four_move(self, player):
        """Find a move that creates an open four (leads to guaranteed win)"""
        cache_key = ('open_four', player, hash(self.board.tobytes()))
        if cache_key in self.pattern_cache:
            return self.pattern_cache[cache_key]
        
        # Check each empty position near existing stones
        checked_positions = set()
        for r, c in self.move_history:
            for dr in range(-2, 3):
                for dc in range(-2, 3):
                    check_r, check_c = r + dr, c + dc
                    if (0 <= check_r < self.size and 0 <= check_c < self.size and 
                        self.board[check_r][check_c] == 0 and 
                        (check_r, check_c) not in checked_positions):
                        
                        checked_positions.add((check_r, check_c))
                        self.board[check_r][check_c] = player
                        
                        # Check if this move creates an open four
                        has_open_four = False
                        for direction in self.directions:
                            dr, dc = direction
                            # Check for patterns like: O X X X X O (where O are empty spaces)
                            consecutive = 1  # Start with 1 for the current stone
                            blocked_ends = 0
                            
                            # Count one direction
                            for k in range(1, 5):
                                r, c = check_r + dr * k, check_c + dc * k
                                if 0 <= r < self.size and 0 <= c < self.size:
                                    if self.board[r][c] == player:
                                        consecutive += 1
                                    elif self.board[r][c] == 0:
                                        break
                                    else:  # Opponent stone
                                        blocked_ends += 1
                                        break
                                else:
                                    blocked_ends += 1
                                    break
                            
                            # Count opposite direction
                            for k in range(1, 5):
                                r, c = check_r - dr * k, check_c - dc * k
                                if 0 <= r < self.size and 0 <= c < self.size:
                                    if self.board[r][c] == player:
                                        consecutive += 1
                                    elif self.board[r][c] == 0:
                                        break
                                    else:  # Opponent stone
                                        blocked_ends += 1
                                        break
                                else:
                                    blocked_ends += 1
                                    break
                            
                            # Check for open four (4 consecutive with no blocked ends)
                            if consecutive >= 4 and blocked_ends == 0:
                                has_open_four = True
                                break
                        
                        self.board[check_r][check_c] = 0
                        if has_open_four:
                            self.pattern_cache[cache_key] = (check_r, check_c)
                            return (check_r, check_c)
        
        self.pattern_cache[cache_key] = None
        return None

    def check_open_three(self, player):
        """Find positions where player has an open three"""
        cache_key = ('has_open_three', player, hash(self.board.tobytes()))
        if cache_key in self.pattern_cache:
            return self.pattern_cache[cache_key]
        
        open_three_positions = []
        
        # Check positions near existing stones
        for r, c in self.move_history:
            if self.board[r][c] != player:
                continue
                
            for dr, dc in self.directions:
                # Check for patterns with 3 consecutive stones with open ends
                count = 1  # Start with 1 for the current stone
                blocked_ends = 0
                empty_spots = []
                
                # Forward direction
                for k in range(1, 4):
                    check_r, check_c = r + dr * k, c + dc * k
                    if 0 <= check_r < self.size and 0 <= check_c < self.size:
                        if self.board[check_r][check_c] == player:
                            count += 1
                        elif self.board[check_r][check_c] == 0:
                            empty_spots.append((check_r, check_c))
                            break
                        else:  # Opponent stone
                            blocked_ends += 1
                            break
                    else:
                        blocked_ends += 1
                        break
                
                # Backward direction
                for k in range(1, 4):
                    check_r, check_c = r - dr * k, c - dc * k
                    if 0 <= check_r < self.size and 0 <= check_c < self.size:
                        if self.board[check_r][check_c] == player:
                            count += 1
                        elif self.board[check_r][check_c] == 0:
                            empty_spots.append((check_r, check_c))
                            break
                        else:  # Opponent stone
                            blocked_ends += 1
                            break
                    else:
                        blocked_ends += 1
                        break
                
                # If we found an open three (3 consecutive with no blocked ends)
                if count == 3 and blocked_ends == 0 and empty_spots:
                    open_three_positions.extend(empty_spots)
        
        self.pattern_cache[cache_key] = open_three_positions
        return open_three_positions

    def find_block_open_three_move(self, player):
        """Find a move to block opponent's open three"""
        opponent = 3 - player  # Switch between 1 and 2
        open_three_positions = self.check_open_three(opponent)
        
        if open_three_positions:
            return open_three_positions[0]  # Return first blocking position
        return None

    def evaluate_position(self, row, col, player):
        """Evaluate the value of a single position for the given player"""
        if self.board[row][col] != player:
            return 0
            
        score = 0
        for dr, dc in self.directions:
            consecutive = 1
            blocked_ends = 0
            
            # Forward direction
            for k in range(1, 5):
                r, c = row + dr * k, col + dc * k
                if 0 <= r < self.size and 0 <= c < self.size:
                    if self.board[r][c] == player:
                        consecutive += 1
                    elif self.board[r][c] == 0:
                        break
                    else:  # Opponent stone
                        blocked_ends += 1
                        break
                else:
                    blocked_ends += 1
                    break
            
            # Backward direction
            for k in range(1, 5):
                r, c = row - dr * k, col - dc * k
                if 0 <= r < self.size and 0 <= c < self.size:
                    if self.board[r][c] == player:
                        consecutive += 1
                    elif self.board[r][c] == 0:
                        break
                    else:  # Opponent stone
                        blocked_ends += 1
                        break
                else:
                    blocked_ends += 1
                    break
            
            # Score based on pattern
            if consecutive >= 5:
                score += 1000000  # Win
            elif consecutive == 4 and blocked_ends == 0:
                score += 100000   # Open four
            elif consecutive == 4 and blocked_ends == 1:
                score += 10000    # Closed four
            elif consecutive == 3 and blocked_ends == 0:
                score += 1000     # Open three
            elif consecutive == 3 and blocked_ends == 1:
                score += 100      # Closed three
            elif consecutive == 2 and blocked_ends == 0:
                score += 10       # Open two
        
        return score

    def evaluate_board(self):
        """Evaluate the entire board state"""
        cache_key = ('evaluate', hash(self.board.tobytes()))
        if cache_key in self.pattern_cache:
            return self.pattern_cache[cache_key]
            
        ai_score = 0
        player_score = 0
        
        # Only evaluate positions with stones
        for r, c in self.move_history:
            if self.board[r][c] == 1:
                player_score += self.evaluate_position(r, c, 1)
            elif self.board[r][c] == 2:
                ai_score += self.evaluate_position(r, c, 2)
        
        # Check for immediate threats
        if self.check_immediate_threat(1):
            player_score += 500000
        if self.check_immediate_threat(2):
            ai_score += 500000
            
        result = ai_score - player_score
        self.pattern_cache[cache_key] = result
        return result

    def get_relevant_moves(self):
        """Get empty positions that are relevant for the current game state"""
        if not self.move_history:
            return [(self.size // 2, self.size // 2)]  # First move in center
            
        # Look for empty spots near existing stones
        potential_moves = set()
        radius = 2  # Consider spots within 2 cells of any existing stone
        
        for r, c in self.move_history:
            for dr in range(-radius, radius + 1):
                for dc in range(-radius, radius + 1):
                    check_r, check_c = r + dr, c + dc
                    if (0 <= check_r < self.size and 0 <= check_c < self.size and 
                        self.board[check_r][check_c] == 0):
                        potential_moves.add((check_r, check_c))
        
        # Sort moves by a quick heuristic evaluation
        moves_with_score = []
        for move in potential_moves:
            row, col = move
            # Try the move for AI
            self.board[row][col] = 2
            score = self.quick_evaluate_move(row, col)
            self.board[row][col] = 0
            moves_with_score.append((move, score))
        
        # Sort by score in descending order
        moves_with_score.sort(key=lambda x: x[1], reverse=True)
        
        # Return the top 12 moves at most (or all if fewer)
        return [move for move, _ in moves_with_score[:12]]

    def quick_evaluate_move(self, row, col):
        """Quick heuristic evaluation of a position"""
        score = 0
        
        # Check for winning move
        if self.check_winner(2, (row, col)):
            return 1000000
            
        # Check patterns in all directions
        for dr, dc in self.directions:
            # Count AI stones (player 2)
            ai_count = 1  # Start with 1 for the current position
            ai_blocked = 0
            
            # Forward
            for k in range(1, 5):
                r, c = row + dr * k, col + dc * k
                if 0 <= r < self.size and 0 <= c < self.size:
                    if self.board[r][c] == 2:
                        ai_count += 1
                    elif self.board[r][c] == 1:  # Blocked by player
                        ai_blocked += 1
                        break
                    else:
                        break
                else:
                    ai_blocked += 1
                    break
                    
            # Backward
            for k in range(1, 5):
                r, c = row - dr * k, col - dc * k
                if 0 <= r < self.size and 0 <= c < self.size:
                    if self.board[r][c] == 2:
                        ai_count += 1
                    elif self.board[r][c] == 1:  # Blocked by player
                        ai_blocked += 1
                        break
                    else:
                        break
                else:
                    ai_blocked += 1
                    break
            
            # Score AI patterns
            if ai_count >= 5:
                score += 100000
            elif ai_count == 4 and ai_blocked == 0:
                score += 10000
            elif ai_count == 4 and ai_blocked == 1:
                score += 1000
            elif ai_count == 3 and ai_blocked == 0:
                score += 500
            elif ai_count == 3 and ai_blocked == 1:
                score += 100
            elif ai_count == 2 and ai_blocked == 0:
                score += 50
            
            # Now look for defensive moves (blocking player patterns)
            # Reset for player stones (player 1)
            self.board[row][col] = 1  # Temporarily switch to check player patterns
            player_count = 1
            player_blocked = 0
            
            # Forward
            for k in range(1, 5):
                r, c = row + dr * k, col + dc * k
                if 0 <= r < self.size and 0 <= c < self.size:
                    if self.board[r][c] == 1:
                        player_count += 1
                    elif self.board[r][c] == 2:  # Blocked by AI
                        player_blocked += 1
                        break
                    else:
                        break
                else:
                    player_blocked += 1
                    break
                    
            # Backward
            for k in range(1, 5):
                r, c = row - dr * k, col - dc * k
                if 0 <= r < self.size and 0 <= c < self.size:
                    if self.board[r][c] == 1:
                        player_count += 1
                    elif self.board[r][c] == 2:  # Blocked by AI
                        player_blocked += 1
                        break
                    else:
                        break
                else:
                    player_blocked += 1
                    break
            
            # Score defensive value (blocking player)
            if player_count >= 5:
                score += 90000  # High but slightly less than AI win
            elif player_count == 4 and player_blocked == 0:
                score += 9000
            elif player_count == 4 and player_blocked == 1:
                score += 900
            elif player_count == 3 and player_blocked == 0:
                score += 450
            elif player_count == 3 and player_blocked == 1:
                score += 90
            elif player_count == 2 and player_blocked == 0:
                score += 45
                
            self.board[row][col] = 2  # Switch back to AI stone for next direction check
        
        # Reset the position to empty
        self.board[row][col] = 0
        
        return score

    def minimax(self, depth, alpha, beta, maximizing_player):
        """Minimax algorithm with alpha-beta pruning and transposition table"""
        # Create a unique hash for the current board state
        board_hash = hash(self.board.tobytes())
        tt_key = (board_hash, depth, maximizing_player)
        
        # Check transposition table
        if tt_key in self.transposition_table:
            return self.transposition_table[tt_key]
            
        # Check terminal conditions
        if depth == 0 or self.check_winner(1, self.last_move) or self.check_winner(2, self.last_move) or self.is_board_full():
            eval_score = self.evaluate_board()
            self.transposition_table[tt_key] = eval_score
            return eval_score
            
        moves = self.get_relevant_moves()
        
        if maximizing_player:
            max_eval = float('-inf')
            for move in moves:
                row, col = move
                self.board[row][col] = 2
                self.last_move = (row, col)
                eval = self.minimax(depth - 1, alpha, beta, False)
                self.board[row][col] = 0
                max_eval = max(max_eval, eval)
                alpha = max(alpha, eval)
                if beta <= alpha:
                    break
            self.transposition_table[tt_key] = max_eval
            return max_eval
        else:
            min_eval = float('inf')
            for move in moves:
                row, col = move
                self.board[row][col] = 1
                self.last_move = (row, col)
                eval = self.minimax(depth - 1, alpha, beta, True)
                self.board[row][col] = 0
                min_eval = min(min_eval, eval)
                beta = min(beta, eval)
                if beta <= alpha:
                    break
            self.transposition_table[tt_key] = min_eval
            return min_eval

    def find_best_move(self, depth=3):
        """Find the best move using prioritized strategy"""
        # Optimization: Clear cache for new evaluation
        self.pattern_cache = {}
        self.transposition_table = {}
        
        # 1. Check if AI can win immediately
        ai_win = self.check_immediate_threat(2)
        if ai_win:
            return ai_win
            
        # 2. Check if player can win immediately
        threat = self.check_immediate_threat(1)
        if threat:
            return threat
            
        # 3. Check if AI can create an open four
        open_four_move = self.find_open_four_move(2)
        if open_four_move:
            return open_four_move
            
        # 4. Check if player has an open three and block it
        block_move = self.find_block_open_three_move(2)
        if block_move:
            return block_move
            
        # 5. Use minimax with alpha-beta pruning for other situations
        best_score = float('-inf')
        best_move = None
        moves = self.get_relevant_moves()
        
        # Use iterative deepening if there are many moves to consider
        actual_depth = min(depth, 4 if len(moves) < 8 else 3)
        
        for move in moves:
            row, col = move
            self.board[row][col] = 2
            self.last_move = (row, col)
            score = self.minimax(actual_depth - 1, float('-inf'), float('inf'), False)
            self.board[row][col] = 0
            if score > best_score:
                best_score = score
                best_move = move
                
        return best_move if best_move else moves[0]