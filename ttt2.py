#!/usr/bin/env python3

# davep 06-Aug-2015 ;  

import sys
# require Python 3.x because reasons
if sys.version_info.major < 3:
    raise Exception("Requires Python 3.x")
import random

class InvalidMove(Exception):
    pass

class Board(object):
    def __init__(self):
        self.board = [' '] * 9
        self.winner = None
        self.X = 0
        self.O = 0

    def __XO(self,bit):
        if self.X & bit :
            return "X"
        if self.O & bit : 
            return "O"
        return " "

    def __print(self,fields):
        s = "|".join(fields[0:3]) \
            + "\n- - -\n" \
            + "|".join(fields[3:6])\
            + "\n- - -\n" \
            + "|".join(fields[6:])
        return s

    def draw_board(self):
        for pos in range(9):
            self.board[pos] = self.__XO(1<<pos)

    def __str__(self):
        self.draw_board()
        return self.__print(self.board)

    def print(self,postfix=""):
        print(self)
        if postfix:
            print(postfix)

    def move(self,player,location):
        bit = location - 1
        if bit < 0 or bit >= 9 :
            raise InvalidMove

        m = (1<<bit)
        if player=="X":
            if self.X & m :
                raise InvalidMove
            self.X = self.X | m

        if player=="O":
            if self.O & m :
                raise InvalidMove
            self.O = self.O | m

    def score(self):
        self.winner = None

        # note: octal!
        horiz = 0o07
        vert = 0o111
        diag_left = 0o124
        diag_right = 0o421
        
        assert self.X & self.O == 0, (oct(self.X),oct(self.O))

        if self.O & diag_left == diag_left : 
            self.winner = "O"
            return
        if self.X & diag_left == diag_left : 
            self.winner = "X"
            return
        if self.O & diag_right == diag_right : 
            self.winner = "O"
            return
        if self.X & diag_right == diag_right : 
            self.winner = "X"
            return

        for n in range(3):
            if self.X & horiz == horiz or \
               self.X & vert==vert :
                self.winner = "X"
                return 

            if (self.O & horiz == horiz) or \
               (self.O & vert==vert):
                self.winner = "O"
                return 

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
    
if __name__=='__main__':
    test()


