#!/usr/bin/env python3

# davep 06-Aug-2015 ;  

import sys
# require Python 3.x because reasons
if sys.version_info.major < 3:
    raise Exception("Requires Python 3.x")
import random

from ttt_types import *
import ttt_board 

class Board(ttt_board.Board):
    # Board using integers for position record rather than strings. Should be
    # faster. 
    
    def __init__(self):
        super().__init__()
        self.X = 0
        self.O = 0

    def __XO(self,bit):
        if self.X & bit :
            return "X"
        if self.O & bit : 
            return "O"
        return " "

    def draw_board(self):
        for pos in range(9):
            self.board[pos] = self.__XO(1<<pos)

    def __str__(self):
        self.draw_board()
        return self.__print(self.board)

    def open_moves(self):
        """return list of available moves"""
        self.draw_board()
        return super().open_moves()

    def move(self,player,location):
        bit = location - 1
        if bit < 0 or bit >= 9 :
            raise InvalidMove

        m = (1<<bit)

        # spot already taken?
        if self.X & m :
            raise InvalidMove
        if self.O & m :
            raise InvalidMove

        if player=="X":
            self.X = self.X | m

        if player=="O":
            self.O = self.O | m

    def score(self):
        self.winner = None

        # note: octal!
        # Lsb is upper left (position #1) so masks are kinda backwards from
        # intuition
        horiz = 0o07  
        vert = 0o111 
        diag_left = 0o124
        diag_right = 0o421
        
        # stupid human check
        assert self.X & self.O == 0, (oct(self.X),oct(self.O))

        print( oct(self.O^diag_left),oct(self.O^diag_right))
        print( oct(self.X^diag_left),oct(self.X^diag_right))

        if self.O and self.O ^ diag_left == 0 : 
            self.winner = "O"
            return
        if self.X and self.X ^ diag_left == 0 : 
            self.winner = "X"
            return
        if self.O and self.O ^ diag_right == 0 : 
            self.winner = "O"
            return
        if self.X and self.X ^ diag_right == 0 : 
            self.winner = "X"
            return

#        if self.O & diag_left == diag_left : 
#            self.winner = "O"
#            return
#        if self.X & diag_left == diag_left : 
#            self.winner = "X"
#            return
#        if self.O & diag_right == diag_right : 
#            self.winner = "O"
#            return
#        if self.X & diag_right == diag_right : 
#            self.winner = "X"
#            return

        for n in range(3):
            print( oct(horiz), oct(vert) )
            print( oct(self.O), oct(self.O^horiz), oct(self.O^vert))
            print( oct(self.X), oct(self.X^horiz), oct(self.X^vert))
            if (self.X ^ horiz == 0 or self.X ^ vert==0) :
                self.winner = "X"
                return 

            if ( self.O^horiz==0 or self.O ^ vert==0 ):
                self.winner = "O"
                return 

#            if self.X & horiz == horiz or \
#               self.X & vert==vert :
#                self.winner = "X"
#                return 
#
#            if (self.O & horiz == horiz) or \
#               (self.O & vert==vert):
#                self.winner = "O"
#                return 

            horiz = horiz << 3
            vert  = vert << 1

def test():
    board = Board()
    board.print("\n")
    board.X += 1
    board.print("\n")
    board.X += 1
    board.print("\n")
    board.X += 1
    board.print("\n")

    p = 0o007
    for i in range(3) :
        board = Board()
        board.X = p
        board.print("\n")
        board.score()
        assert board.winner=="X", (i,oct(board.X))
        p <<= 3

    p = 0o111
    for i in range(3) :
        board = Board()
        board.X = p
        board.print("\n")
        board.score()
        assert board.winner=="X"
        p <<= 1

    return

    board.X = random.randint(0,2**9-1)
    board.O = random.randint(0,2**9-1)
    board.print("\n")

    board = Board()
    board.move("X",1)
    board.score()
    board.print("\n")
    assert board.winner == None, board.winner

    board.move("O",9)
    board.score()
    board.print("\n")
    assert board.winner == None, board.winner

    board.move("X",2)
    board.score()
    board.print("\n")
    assert board.winner == None, board.winner

    board.move("O",5)
    board.score()
    board.print("\n")
    assert board.winner == None, board.winner

    board = Board()
    board.move("X",1)
    board.move("X",4)
    board.move("X",7)
    board.score()
    board.print("\n")
    assert board.winner=="X", board.winner

    board = Board()
    board.move("X",2)
    board.move("X",5)
    board.move("X",8)
    board.score()
    board.print("\n")
    assert board.winner=="X", board.winner

    board = Board()
    while 1 : 
        board.X = random.randint(0,2**9-1)
        board.O = random.randint(0,2**9-1) & ~board.X
        board.print()
        board.score()
        if board.winner=="X":
            print("X wins!")
            break
        if board.winner=="O":
            print("O wins!")
            break
        print("no winner")

    board.help()
    
if __name__=='__main__':
    test()


