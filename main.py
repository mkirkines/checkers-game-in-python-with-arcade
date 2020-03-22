import arcade
import numpy as np

from functools import wraps
import time


def timeit(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        print('Execution time of {}(): {}s'.format(
            func.__qualname__, round(time.time() - start, 5)))
        return result
    return wrapper


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

    def get_cell_at_pos(self, x, y):
        """ This functions returns the cell of the game board at the coordinates x, y. """
        return [cell for cell in self.board if cell.cell_id == (x, y)][0]

    def get_piece_at_pos(self, x, y):
        """ This functions returns the piece at the coordinates x, y of the game board. """
        return [piece for piece in self.pieces if piece.get_grid_pos() == (x, y)][0]

    def setup_board(self):
        """ This function creates an arcade.SpriteList() that contains 
        Cell Objects that make up the game board """
        self.board = arcade.SpriteList()
        for y in range(GAME_ROWS):
            for x in range(GAME_COLS):
                self.board.append(Cell(x, y))
        return self.board

    def setup_pieces(self):
        """ This function creates the pieces of both players and returns
        them in an arcade.SpriteList()"""
        self.pieces = arcade.SpriteList()
        for y in range(GAME_ROWS):
            for x in range(GAME_COLS):
                if y < 3 and (x+y) % 2 == 0:
                    self.pieces.append(Piece(x, y, 1))
                    self.get_cell_at_pos(x, y).occupied = True
                if y >= GAME_ROWS-3 and (x+y) % 2 == 0:
                    self.pieces.append(Piece(x, y, 2))
                    self.get_cell_at_pos(x, y).occupied = True
        return self.pieces

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

    def get_move_consequences(self, piece, end_pos):
        """ Given that a move is valid, this function takes care
        of the actions the game needs to take, especially removing pieces"""
        start_pos = piece.get_grid_pos()
        move = [end_pos[0]-start_pos[0], end_pos[1]-start_pos[1]]

        if move in piece.capture_moves:
            rel_coordinate_of_jumped_cell = (
                np.sign(move[0])*1, np.sign(move[1])*1)
            coordinate_of_jumped_cell = tuple(np.add(
                piece.get_grid_pos(), rel_coordinate_of_jumped_cell))
            return self.get_piece_at_pos(
                *coordinate_of_jumped_cell)
        return None

    def perform_move(self, piece, new_pos):
        jumped = False
        promoted = False
        piece_to_be_removed = self.get_move_consequences(piece, new_pos)
        if piece_to_be_removed != None:
            pos = piece_to_be_removed.get_grid_pos()
            self.get_cell_at_pos(*pos).occupied = False
            piece_to_be_removed.remove_from_sprite_lists()
            jumped = True
        if piece.player_id == 1 and piece.type == "normal" and new_pos[1] == GAME_ROWS-1:
            piece.promote()
            promoted = True
        if piece.player_id == 2 and piece.type == "normal" and new_pos[1] == 0:
            piece.promote()
            promoted = True
        self.get_cell_at_pos(*piece.get_grid_pos()).occupied = False
        self.get_cell_at_pos(*new_pos).occupied = True
        piece.set_grid_pos(*new_pos)
        return jumped, promoted

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

    @timeit
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


class Game(arcade.Window):
    def __init__(self):
        super().__init__(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE)
        self.board = None
        self.game_logic = None
        self.mouse_pos = None, None
        self.dragged_piece = None
        self.player_id_turn = None
        self.possible_moves = None

    def setup(self):
        arcade.set_background_color(arcade.color.WHITE)
        self.game_logic = GameLogic()
        self.board = self.game_logic.setup_board()
        self.pieces = self.game_logic.setup_pieces()
        self.player_id_turn = 1
        print("Player {}:".format(self.player_id_turn))
        self.possible_moves = self.game_logic.get_possible_player_moves(
            self.player_id_turn)

    def on_update(self, delta_time):
        if self.dragged_piece != None:
            self.dragged_piece._set_position(self.mouse_pos)

    def on_draw(self):
        arcade.start_render()
        self.board.draw()
        self.pieces.draw()

        if self.dragged_piece != None:
            for piece_moves in self.possible_moves:
                if self.dragged_piece.get_grid_pos() == piece_moves[0]:
                    for move in piece_moves[1]:
                        arcade.draw_circle_outline(
                            (move[0][0]+0.5)*CELL_WIDTH, (move[0][1]+0.5)*CELL_HEIGHT, 40, arcade.color.GREEN, border_width=5)

            self.dragged_piece.draw()
        else:
            for piece_moves in self.possible_moves:
                arcade.draw_circle_outline(
                    (piece_moves[0][0]+0.5)*CELL_WIDTH, (piece_moves[0][1]+0.5)*CELL_HEIGHT, 40, arcade.color.GREEN, border_width=5)

        arcade.finish_render()

    def on_mouse_motion(self, x: float, y: float, dx: float, dy: float):
        self.mouse_pos = x, y

    def on_mouse_press(self, x: float, y: float, button: int, modifiers: int):
        # Save mouse position as arcade.Point
        pt = arcade.Point(x, y)
        # Check if any piece is currently being dragged
        if self.dragged_piece == None:
            # If not check for collisions of mouse with any piece
            collision_list = arcade.get_sprites_at_point(pt, self.pieces)
            if not collision_list == []:
                for piece in collision_list:
                    # if the piece belongs to the player whose turn it is
                    # save the piece as the piece currently being dragged
                    for move in self.possible_moves:
                        if piece.get_grid_pos() == move[0]:
                            self.dragged_piece = piece
                            break
        # Otherwise a piece is currently being dragged and the piece should be placed
        # at the mouse position
        else:
            pt = arcade.Point(self.dragged_piece.center_x,
                              self.dragged_piece.center_y)
            collision_list = arcade.get_sprites_at_point(pt, self.board)
            if not collision_list == []:
                for cell in collision_list:
                    new_pos = cell.cell_id
                    if self.game_logic.is_valid_move(self.dragged_piece, new_pos):
                        jumped, promoted = self.game_logic.perform_move(
                            self.dragged_piece, new_pos)
                        self.possible_moves = self.game_logic.get_possible_player_moves(
                            self.player_id_turn)
                        continue_jumping = False
                        for piece_moves in self.possible_moves:
                            # piece_moves[0] would be the starting position of the piece
                            for move in piece_moves[1]:
                                if move[1] == "capture" and jumped and not promoted:
                                    continue_jumping = True
                                    break
                                break
                        # BUG if continue_jumping, the jumping piece can only move
                        if not continue_jumping:
                            if self.player_id_turn == 1:
                                self.player_id_turn = 2
                            else:
                                self.player_id_turn = 1
                        print("Player {}:".format(self.player_id_turn))
                        self.possible_moves = self.game_logic.get_possible_player_moves(
                            self.player_id_turn)
                    else:
                        self.dragged_piece.set_grid_pos(
                            *self.dragged_piece.get_grid_pos())
            else:
                # The following line ensures that a piece doesn't get stuck between cells
                self.dragged_piece.set_grid_pos(
                    *self.dragged_piece.get_grid_pos())
            self.dragged_piece = None


if __name__ == "__main__":
    game = Game()
    game.setup()
    arcade.run()
