#!/usr/bin/env python3

# davep 21-Jul-2015 ;  

import sys
# require Python 3.x because reasons
if sys.version_info.major < 3:
    raise Exception("Requires Python 3.x")
import random

x_win = "XXX"
o_win = "OOO"

PLAYER_WIN=1
COMPUTER_WIN=2
QUIT_GAME = 3
NO_WINNER = 4

class InvalidMove(Exception):
    pass

class Board(object):
    def __init__(self):
        self.board = [' '] * 9
        self.winner = None

    def _print(self,fields):
        s = "|".join(fields[0:3])
        print(s)
        print("- - -")
        s = "|".join(fields[3:6])
        print(s)
        print("- - -")
        s = "|".join(fields[6:])
        print(s)

    def print(self,postfix=""):
        self._print(self.board)
        if postfix:
            print(postfix)

    def help(self):
        self._print( [str(n) for n in range(1,10)] )
        print("\n")

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
        # return list of available moves
        return [ n+1 for n in range(9) if self.board[n]==' ']

class ComputerPlayer(object):
    def __init__(self,board,the_char):
        self.board = board

        # computer's X or O
        assert the_char in ("X","O"),the_char
        self.char = the_char

    def get_move(self):
        # for now, just move randomly
        open_moves = self.board.open_moves()
        return random.choice(open_moves)

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
    print("player is {0}".format(player))
    
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

