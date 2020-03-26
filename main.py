import arcade
import numpy as np
import time
from timeit import timeit
import copy

SCREEN_WIDTH = 600
SCREEN_HEIGHT = 600
SCREEN_TITLE = "Checkers"

GAME_COLS = 8
GAME_ROWS = 8

CELL_WIDTH = SCREEN_WIDTH//GAME_COLS
CELL_HEIGHT = SCREEN_HEIGHT//GAME_ROWS


class Cell(arcade.Sprite):
    def __init__(self, x, y):
        if (x+y) % 2 == 0:
            super().__init__("resources/wood_textures/wood4.png", scale=0.1465)
            self.left = CELL_WIDTH * x
            self.bottom = CELL_HEIGHT * y
        else:
            super().__init__("resources/wood_textures/wood5.png", scale=0.1465)
            self.left = CELL_WIDTH * x
            self.bottom = CELL_HEIGHT * y
        self.occupied = False
        self.cell_id = (x, y)


class Piece(arcade.Sprite):
    def __init__(self, x, y, player_id):
        self.player_id = player_id
        if self.player_id == 1:
            super().__init__("resources/pieces/normal_red.png", scale=0.15)
            self.normal_moves = [[1, 1], [-1, 1]]
            self.capture_moves = [[2, 2], [-2, 2]]
        if self.player_id == 2:
            super().__init__("resources/pieces/normal_blue.png", scale=0.15)
            self.normal_moves = [[1, -1], [-1, -1]]
            self.capture_moves = [[2, -2], [-2, -2]]
        self.grid_pos = x, y
        self._set_position(((x+0.5)*CELL_WIDTH, (y+0.5)*CELL_HEIGHT))
        self.type = "normal"

    def set_grid_pos(self, x, y):
        self.grid_pos = x, y
        self._set_position(((x+0.5)*CELL_WIDTH, (y+0.5)*CELL_HEIGHT))

    def get_grid_pos(self):
        return self.grid_pos

    def promote(self):
        self.type = "king"
        self.normal_moves = [[1, 1], [-1, 1], [1, -1], [-1, -1]]
        self.capture_moves = [[2, 2], [-2, 2], [2, -2], [-2, -2]]
        if self.player_id == 1:
            self.texture = arcade.load_texture(
                "resources/pieces/king_red.png", scale=0.15)
        if self.player_id == 2:
            self.texture = arcade.load_texture(
                "resources/pieces/king_blue.png", scale=0.15)


class GameLogic():
    def __init__(self):
        self.board = None
        self.pieces = None
        self.dragged_piece = None
        self.player_turn = None
        self.possible_moves = None

    def get_cell_at_pos(self, x, y):
        """ This functions returns the cell of the game board at the coordinates x, y. """
        return [cell for cell in self.board if cell.cell_id == (x, y)][0]

    def get_piece_at_pos(self, x, y):
        """ This functions returns the piece at the coordinates x, y of the game board. """
        return [piece for piece in self.pieces if piece.get_grid_pos() == (x, y)][0]

    def setup(self):
        self.board = self.setup_board()
        self.pieces = self.setup_pieces()
        self.player_turn = 1
        self.possible_moves = self.get_possible_player_moves(self.player_turn)

    def setup_board(self):
        """ This function creates an arcade.SpriteList() that contains 
        Cell Objects that make up the game board """
        board = arcade.SpriteList()
        for y in range(GAME_ROWS):
            for x in range(GAME_COLS):
                board.append(Cell(x, y))
        return board

    def setup_pieces(self):
        """ This function creates the pieces of both players and returns
        them in an arcade.SpriteList()"""
        pieces = arcade.SpriteList()
        for y in range(GAME_ROWS):
            for x in range(GAME_COLS):
                if y < 3 and (x+y) % 2 == 0:
                    pieces.append(Piece(x, y, 1))
                    self.get_cell_at_pos(x, y).occupied = True
                if y >= GAME_ROWS-3 and (x+y) % 2 == 0:
                    pieces.append(Piece(x, y, 2))
                    self.get_cell_at_pos(x, y).occupied = True
        return pieces

    def is_valid_move(self, piece, end_pos):
        """ This function checks if a move is allowed by checking
        if the desired position is occupied or not and by examining
        if a cell, that is intended to be jumped, is occupied or not
        and by which player. """

        start_pos = piece.get_grid_pos()
        move = [end_pos[0]-start_pos[0], end_pos[1]-start_pos[1]]

        if move in piece.normal_moves:
            cell = self.get_cell_at_pos(*end_pos)
            if not cell.occupied:
                return True
            else:
                return False

        elif move in piece.capture_moves:
            cell = self.get_cell_at_pos(*end_pos)
            rel_coordinate_of_jumped_cell = (
                np.sign(move[0])*1, np.sign(move[1])*1)
            coordinate_of_jumped_cell = tuple(np.add(
                piece.get_grid_pos(), rel_coordinate_of_jumped_cell))
            jumped_cell = self.get_cell_at_pos(*coordinate_of_jumped_cell)
            if not cell.occupied and jumped_cell.occupied:
                jumped_piece = self.get_piece_at_pos(
                    *coordinate_of_jumped_cell)
                if jumped_piece.player_id != piece.player_id:
                    return True
                else:
                    return False
            else:
                return False
        else:
            return False

    def get_possible_piece_moves(self, piece):
        # Get the current position of the piece
        pos = piece.get_grid_pos()
        # Create a list that saves the possible positions the piece could move to
        end_pos_list = []
        move_list = []
        # First check possible capture moves
        for move in piece.capture_moves:
            end_pos = tuple(np.add(pos, move))
            # Check if the position is really on the playing board
            if not any(i < 0 or i > GAME_COLS-1 for i in end_pos):
                end_pos_list.append(end_pos)
        for end_pos in end_pos_list:
            # Check if the move is allowed by the games rules
            if self.is_valid_move(piece, end_pos):
                move_list.append([end_pos, "capture"])
        if not move_list == []:
            return move_list
        # Then check standard moves
        for move in piece.normal_moves:
            end_pos = tuple(np.add(pos, move))
            if not any(i < 0 or i > GAME_COLS-1 for i in end_pos):
                end_pos_list.append(end_pos)
        for end_pos in end_pos_list:
            if self.is_valid_move(piece, end_pos):
                move_list.append([end_pos, "normal"])
        return move_list

    def get_possible_player_moves(self, player_id):
        capture_is_possible = False
        player_moves = []
        player_pieces = (
            piece for piece in self.pieces if piece.player_id == player_id)
        for piece in player_pieces:
            piece_moves = self.get_possible_piece_moves(piece)
            for move in piece_moves:
                if move[1] == "capture":
                    capture_is_possible = True
            if piece_moves != []:
                player_moves.append([piece.get_grid_pos(), piece_moves])

        if capture_is_possible:
            adjusted_player_moves = []
            for piece_pos, piece_moves in player_moves:
                moves = []
                for move in piece_moves:
                    if move[1] == "capture":
                        moves.append(move)
                if moves != []:
                    adjusted_player_moves.append([piece_pos, moves])
            player_moves = adjusted_player_moves

        return player_moves

    def set_dragged_piece(self, x, y):
        if self.dragged_piece == None:
            for move in self.possible_moves:
                if move[0] == (x, y):
                    self.dragged_piece = self.get_piece_at_pos(x, y)
                    self.possible_moves = [move]
                    break

    def convert_mouse_pos_to_board_loc(self, x, y):
        pt = arcade.Point(x, y)
        collision_list = arcade.get_sprites_at_point(pt, self.board)
        if collision_list != []:
            return collision_list[0].cell_id
        else:
            return None

    def perform_player_turn(self, x, y, output=False):
        moves = self.possible_moves[0][1]
        start_pos = self.possible_moves[0][0]
        end_pos = None
        move_type = None
        continue_jumping = False
        promoted = False

        for move in moves:
            if move[0] == (x, y):
                end_pos = move[0]
                move_type = move[1]
                if end_pos[1] in [0, GAME_ROWS-1]:
                    promoted = True
                if output:
                    print(
                        f"Player {self.player_turn}: {start_pos} --> {end_pos}")
                break

        if move_type == "capture":
            rel_coordinate_of_jumped_cell = np.sign(
                [end_pos[0]-start_pos[0], end_pos[1]-start_pos[1]])
            coordinate_of_jumped_cell = tuple(
                np.add(start_pos, rel_coordinate_of_jumped_cell))
            self.get_cell_at_pos(*coordinate_of_jumped_cell).occupied = False
            self.get_piece_at_pos(
                *coordinate_of_jumped_cell).remove_from_sprite_lists()

            self.get_cell_at_pos(*start_pos).occupied = False
            self.get_cell_at_pos(*end_pos).occupied = True
            self.dragged_piece.set_grid_pos(*end_pos)
            if promoted:
                self.dragged_piece.promote()
            else:
                piece_moves = self.get_possible_piece_moves(self.dragged_piece)
                if not piece_moves == []:
                    if piece_moves[0][1] == "capture":
                        self.possible_moves = [[end_pos, piece_moves]]
                        continue_jumping = True

        elif move_type == "normal":
            self.get_cell_at_pos(*start_pos).occupied = False
            self.get_cell_at_pos(*end_pos).occupied = True
            self.dragged_piece.set_grid_pos(*end_pos)
            if promoted:
                self.dragged_piece.promote()

        else:
            self.dragged_piece.set_grid_pos(*start_pos)
            self.possible_moves = self.get_possible_player_moves(
                self.player_turn)
            self.dragged_piece = None
            return

        self.dragged_piece = None
        
        if not continue_jumping:
            self.next_player()
        else:
            move = self.possible_moves[0]
            start_pos = move[0]
            end_pos = move[1][0][0]
            self.set_dragged_piece(*start_pos)
            self.perform_player_turn(*end_pos, output)

    def next_player(self):
        if self.player_turn == 1:
            self.player_turn = 2
        else:
            self.player_turn = 1
        self.possible_moves = self.get_possible_player_moves(
            self.player_turn)

    def get_input(self, x, y):
        pos = self.convert_mouse_pos_to_board_loc(x, y)
        if pos:
            if self.dragged_piece:
                self.perform_player_turn(*pos, output=True)
            else:
                self.set_dragged_piece(*pos)

    def get_score(self):
        score = 0
        center_1 = [(3, 3), (4, 4)]
        center_2 = [(2, 4), (5, 3)]
        for piece in self.pieces:
            if piece.player_id == 2:
                if piece.type == "normal":
                    score += 10
                else:
                    score += 30
                if piece.get_grid_pos() in center_1:
                    score += 5
                if piece.get_grid_pos() in center_2:
                    score += 3
            else:
                if piece.type == "normal":
                    score -= 10
                else:
                    score -= 30
                if piece.get_grid_pos() in center_1:
                    score -= 5
                if piece.get_grid_pos() in center_2:
                    score -= 3
        return score


def get_move_scores(game_logic, depth):
    moves = game_logic.possible_moves
    pred_step = []
    for move in moves:
        for end_pos in move[1]:
            pred = copy.deepcopy(game_logic)
            pred.set_dragged_piece(*move[0])
            pred.perform_player_turn(*end_pos[0])
            pred_step.append(pred)

    if depth > 0:
        if game_logic.player_turn == 2:
            return [max(get_move_scores(x, depth-1)) for x in pred_step]
        if game_logic.player_turn == 1:
            return [min(get_move_scores(x, depth-1)) for x in pred_step]
    else:
        return [x.get_score() for x in pred_step]


@timeit
def get_AI_move(game_logic, depth):
    moves = game_logic.possible_moves
    pred_move = []
    for move in moves:
        for end_pos in move[1]:
            pred_move.append([move[0], end_pos[0]])
    move_scores = get_move_scores(game_logic, depth)
    index_of_best_move = np.argmax(move_scores)
    return pred_move[index_of_best_move]


class Game(arcade.Window):
    def __init__(self):
        super().__init__(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE)
        self.board = None
        self.game_logic = None
        self.mouse_pos = None, None

    def setup(self):
        arcade.set_background_color(arcade.color.WHITE)
        self.game_logic = GameLogic()
        self.game_logic.setup()
        self.board = self.game_logic.board
        self.pieces = self.game_logic.pieces

    def on_update(self, delta_time):
        if self.game_logic.dragged_piece:
            self.game_logic.dragged_piece._set_position(self.mouse_pos)

    def on_draw(self):
        arcade.start_render()
        self.board.draw()
        self.pieces.draw()

        if self.game_logic.dragged_piece:
            for piece_moves in self.game_logic.possible_moves:
                if self.game_logic.dragged_piece.get_grid_pos() == piece_moves[0]:
                    for move in piece_moves[1]:
                        arcade.draw_circle_outline(
                            (move[0][0]+0.5)*CELL_WIDTH, (move[0][1]+0.5)*CELL_HEIGHT, 40, arcade.color.GREEN, border_width=5)

            self.game_logic.dragged_piece.draw()
        else:
            for piece_moves in self.game_logic.possible_moves:
                arcade.draw_circle_outline(
                    (piece_moves[0][0]+0.5)*CELL_WIDTH, (piece_moves[0][1]+0.5)*CELL_HEIGHT, 40, arcade.color.GREEN, border_width=5)

        arcade.finish_render()

    def on_mouse_motion(self, x: float, y: float, dx: float, dy: float):
        self.mouse_pos = x, y

    def on_mouse_press(self, x: float, y: float, button: int, modifiers: int):
        if self.game_logic.player_turn == 1:
            self.game_logic.get_input(x, y)
        if self.game_logic.player_turn == 2:
            best_move = get_AI_move(self.game_logic, depth=1)
            self.game_logic.set_dragged_piece(*best_move[0])
            self.game_logic.perform_player_turn(*best_move[1], output=True)


if __name__ == "__main__":
    game = Game()
    game.setup()
    arcade.run()
