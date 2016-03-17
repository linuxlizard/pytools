#!/usr/bin/env python3

# davep 21-Jul-2015 ;  

import sys
# require Python 3.x because reasons
if sys.version_info.major < 3:
    raise Exception("Requires Python 3.x")
import random

from ttt_types import *
#from ttt_board import Board
from ttt2 import Board

class ComputerPlayer(object):
    def __init__(self,board,the_char):
        self.board = board

        # computer's X or O
        assert the_char in ("X","O"),the_char
        self.char = the_char

        if self.char=="X":
            self.opponent = "O"
        else:
            self.opponent = "X"

    def get_move_random(self):
        # for now, just move randomly
        open_moves = self.board.open_moves()
        return random.choice(open_moves)

    def _find_hole(self,char,the_list,hole_to_move):
        if the_list.count(char)==2 : 
            # someone has two spots in this array
            # is there a hole?
            try:
                empty_pos = the_list.index(' ')
            except ValueError:
                # nope, no hole
                return None
            else:
                # convert the hole position to a move number
                move = hole_to_move(empty_pos)
#                print("hole at {0}".format(move))
                return move
        return None

    def _find_horizontal_hole(self,char1):
        # Find a hole in a horiontal direction.
        # Used to find a blocking move or a winning move.
        board = self.board.board
        for row_idx in range(0,10,3):
            row = board[row_idx:row_idx+3] 
            move = self._find_hole(char1,row,lambda empty_pos:row_idx+empty_pos+1)
            if move :
                return move
        return None

    def _find_vertical_hole(self,char1):
        # Find a hole in a vertical direction.
        # Used to find a blocking move or winning move.
        board = self.board.board
        for col_idx in range(3):
            col = board[col_idx],board[col_idx+3],board[col_idx+3+3] 
            move = self._find_hole(char1,col,lambda empty_pos:col_idx+empty_pos*3+1)
            if move :
                return move
        return None

    diagonal_LR_hole_fill = ( 1, 5, 9 )
    diagonal_RL_hole_fill = ( 3, 5, 7 )

    def get_move(self):
        # can I win? do I need to block?
        #
        # horizontal win?
        move = self._find_horizontal_hole(self.char)
        if move is not None :
            return move

        # vertical win?
        move = self._find_vertical_hole(self.char)
        if move is not None :
            return move

        # horizontal block?
        move = self._find_horizontal_hole(self.opponent)
        if move is not None :
            return move

        # vertical block?
        move = self._find_vertical_hole(self.opponent)
        if move is not None :
            return move

        # diagonals
        board = self.board.board
        diag_LR = "".join((board[0],board[4],board[8]))
        diag_RL = "".join((board[2],board[4],board[6]))

        # diagonal upper left to lower right - win?
        move = self._find_hole(self.char,diag_LR,lambda empty_pos:self.diagonal_LR_hole_fill[empty_pos])
        if move :
            return move

        # diagonal upper right to lower left - win?
        move = self._find_hole(self.char,diag_RL,lambda empty_pos:self.diagonal_RL_hole_fill[empty_pos])
        if move :
            return move

        # diagonal upper left to lower right - block?
        move = self._find_hole(self.opponent,diag_LR,lambda empty_pos:self.diagonal_LR_hole_fill[empty_pos])
        if move :
            return move

        # diagonal upper right to lower left - block?
        move = self._find_hole(self.opponent,diag_RL,lambda empty_pos:self.diagonal_RL_hole_fill[empty_pos])
        if move :
            return move

        return self.get_move_random()

def test():
    board = Board()
    board.print("\n")
    board.help()
    board.move('X',4)
    board.print("\n")
    board.move('O',1)
    board.print("\n")
    board.score()
    board.move('X',5)
    board.move('X',6)
    board.print("\n")
    board.score()
    print("winner={0}".format(board.winner))

    computer = ComputerPlayer(board,"O")

def play_game():
    board = Board()
    board.help()
    player = random.choice(("X","O"))
    if player=="X":
        computer= ComputerPlayer(board,"O")
    else:
        computer= ComputerPlayer(board,"X")
    print("Player is {0}".format(player))
    
    print("X always moves first.")
    
    if computer.char=="X":
        print("Computer moves first.")
        computer_move = computer.get_move()
        board.move(computer.char,computer_move)
        board.print("\n")
    else:
        print("You move first.")

    while 1 : 
        s = input("(h for help, q to quit) Move? " )
        if s=='h':
            board.help()
        elif s=='q':
            return QUIT_GAME
        else:
            try : 
                pos = int(s)
                board.move(player,pos)
            except ValueError:
                print("{0} is not a valid integer".format(s))
            except InvalidMove:
                print("{0} is an invalid move".format(s))
            else:
                board.score()
                if board.winner != None : 
                    board.print("\n")
                    print("Winner! Player wins!".format(board.winner))
                    return PLAYER_WIN

                # Are there any valid moves left?
                if len(board.open_moves())==0 :
                    print("No moves left. Game over. No winner.")
                    return NO_WINNER

                # Computer's turn
                computer_move = computer.get_move()
                board.move(computer.char,computer_move)

                board.print("\n")
            
                board.score()
                if board.winner != None : 
                    print("Winner! Computer wins!".format(board.winner))
                    return COMPUTER_WIN

                # Are there any valid moves left?
                if len(board.open_moves())==0 :
                    print("No moves left. Game over. No winner.")
                    return NO_WINNER


def play():
    computer_score = 0
    player_score = 0
    no_winner = 0
    while 1 : 
        result = play_game()
        if result==QUIT_GAME:
            break
        if result==PLAYER_WIN :
            player_score += 1
        elif result==COMPUTER_WIN:
            computer_score += 1
        elif result==NO_WINNER:
            no_winner += 1
        else:
            assert 0, result

        print("Score is computer {0} and player {1}. {2} tie games.".format(
            computer_score,player_score,no_winner))

        s = input("Another game? y/n ")
        if not (s=='y' or s=='Y') : 
            break

if __name__=='__main__':
#    test()
    play()

