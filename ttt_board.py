#!/usr/bin/env python3

import sys
# require Python 3.x because reasons
if sys.version_info.major < 3:
    raise Exception("Requires Python 3.x")

from ttt_types import *

class Board(object):
    def __init__(self):
        self.board = [' '] * 9
        self.winner = None

#    def _print(self,fields):
#        s = "|".join(fields[0:3])
#        print(s)
#        print("- - -")
#        s = "|".join(fields[3:6])
#        print(s)
#        print("- - -")
#        s = "|".join(fields[6:])
#        print(s)

    def __print(self,fields):
        s = "|".join(fields[0:3]) \
            + "\n- - -\n" \
            + "|".join(fields[3:6])\
            + "\n- - -\n" \
            + "|".join(fields[6:])
        return s

#    def print(self,postfix=""):
#        self._print(self.board)
#        if postfix:
#            print(postfix)

    def print(self,postfix=""):
        print(self)
        if postfix:
            print(postfix)

    def help(self):
        print(self.__print( [str(n) for n in range(1,10)] ))

    def move(self,player,location):
        idx = location - 1
        if idx < 0 or idx >= 9 :
            raise InvalidMove
        if self.board[idx] != ' ' :
            raise InvalidMove

        self.board[location-1] = player

    def score(self):
        self.winner = None

        # horizontal
        for row in range(0,10,3):
            s = "".join(self.board[row:row+3])
            if s==x_win or s==o_win : 
                self.winner = s[0]
                return

        # vertical
        for col in range(3):
            s = "".join( (self.board[col],self.board[col+3],self.board[col+3+3]) )
            if s==x_win or s==o_win : 
                self.winner = s[0]
                return

        # diagonal upper left to lower right
        s = "".join((self.board[0],self.board[4],self.board[8]))
        if s==x_win or s==o_win : 
            self.winner = s[0]
            return

        # diagonal upper right to lower left
        s = "".join((self.board[2],self.board[4],self.board[6]))
        if s==x_win or s==o_win : 
            self.winner = s[0]
            return

    def open_moves(self):
        """return list of available moves"""
        return [ n+1 for n in range(9) if self.board[n]==' ']


