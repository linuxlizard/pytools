
#!/usr/bin/env python3

# davep 21-Jul-2015 ;  

import sys
# require Python 3.x because reasons
if sys.version_info.major < 3:
    raise Exception("Requires Python 3.x")
import random

from ttt import Board

unique_boards = {}

def _print(board):
    s = "|".join(board[0:3])
    print(s)
    print("- - -")
    s = "|".join(board[3:6])
    print(s)
    print("- - -")
    s = "|".join(board[6:])
    print(s)

def bprint(board,postfix="\n"):
    print("|{0}|".format("".join(board)))
    return
    _print(board)
    if postfix:
        print(postfix)

depth=0
def next_board(curr_node,board,char):

    global depth
    depth += 1
#    print("depth={0} char={1} board={2}".format(depth,char,str(curr_node)))
#    print(curr_node)

#    if depth > 4 : 
#        depth -= 1
##        print("(skip)")
#        return

    c1 = board.count('X')
    c2 = board.count('O')
    assert abs(c1-c2) <= 1, (c1,c2)

    next_char = 'X' if char=='O' else 'O'

    # open spaces
    avail_moves = [ n for n in range(9) if board[n]==' ' ]

    for move in avail_moves : 
        board[move] = char
        node = Node(board)
#        print(depth,node)
        curr_node.add_child(node)

#        bprint(board)

        next_board(node,board[:],next_char)
        board[move] = ' '

    depth -= 1
    
class Node(object):
    def __init__(self,board):
        self.board = board[:]
        self.children = []

    def add_child(self,child):
        self.children.append(child)

    def __str__(self):
        return "[{0}]".format("".join(self.board)).replace(" ",".")

    def print_tree(self,indent=0):
        print("{0}{1}".format("| "*indent,str(self)))
#        print("{0}{1}".format("."*indent,str(self)))
        for c in self.children :
            c.print_tree(indent+1)

board = [' '] * 9
#bprint(board)

root = Node(board)
#print(root)
# X moves first
next_board(root,board[:],'X')
# O moves first
next_board(root,board[:],'O')

root.print_tree()

