#!/usr/bin/env python3

# davep 15-Jul-2015

import sys
# require Python 3.x because reasons
if sys.version_info.major < 3:
    raise Exception("Requires Python 3.x")
import random

spade=0
diamond=1
club=2
hearts=3
suits_names = ( "S","D","C","H" )

ace=0
two=1
three=2
four=3
five=4
six=5
seven=6
eight=7
nine=8
ten=9
jack=10
queen=11
king=12
value_names = ( "A","2","3","4","5","6","7","8","9","10","J","Q","K")

BUSTED = -1

# note Ace at can be 1 or 11 but this special case will be handled in code
# rather than here
blackjack_values = ( 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 10, 10, 10 )

suits = ( spade, diamond, club, hearts )
values = ( ace, two, three, four, five, six, seven, eight, nine, ten, jack,
            queen, king, )

DEALER_WIN=0
PLAYER_WIN=1
GAME_PUSH=-1
PLAYER_BLACKJACK=-2

class Card(object):
    def __init__(self,suit,value):
        self.suit = suit
        self.value = value

    def __str__(self):
        return "{1}-{0}".format(suits_names[self.suit],value_names[self.value])
        
class Deck(object):
    def __init__(self):
        self.deck = [ Card(s,v) for s in suits for v in values ]

    def shuffle(self):
        random.shuffle(self.deck)

    def __str__(self):
        return " ".join([str(c) for c in self.deck])

    def __iter__(self):
        return iter(self.deck)

class Hand(object):
    def __init__(self):
        self.hand = []

    def add(self,card):
        self.hand.append(card)

    def __str__(self):
        return " ".join( [ str(c) for c in self.hand ] )

class BlackjackCard(Card):
    def __init__(self,suit,value):
        super().__init__(suit,value)

    def numerical_value(self):
        return blackjack_values[self.value]

class BlackjackDeck(Deck):
    def __init__(self):
        self.deck = [ BlackjackCard(s,v) for s in suits for v in values ]

class Node(object):
    # handle the ace 1/11 duality by making a tree of every possible hand
    # value. Descend the tree depth-first. The leaf nodes will be the hand
    # summation.
    def __init__(self,value):
        self.value = value
        self.children = None

        self.depth = 0

    def add_leaves(self, new_children_values):
        # build the tree by adding new_children_values to EVERY leaf node 
        if not self.children : 
            # add children nodes with the card's possible values
            self.children = [ Node(v) for v in new_children_values ]
        else:
            # not a leaf; recursive descend to find the leaf nodes
            for c in self.children : 
                c.add_leaves(new_children_values)

    def summation(self,the_sum,node,all_sums):
        # Calulate the sum of the tree with a depth-first search.
        # Running sim written into the array all_sums.
        the_sum += node.value
        if node.children : 
            for c in node.children:
                self.summation(the_sum,c,all_sums)
        else:
            all_sums.append(the_sum)

class BlackjackBusted(Exception):
    def __init__(self,hand):
        # the hand that busted
        self.hand = hand
        
class BlackjackHand(Hand):
    def __init__(self):
        super().__init__()
        self.hand_sums = []

    def summation(self):
        self.hand_sums = []

        # because ace is 1 or 11 we have to return multiple values, a different
        # sum for each possible combination of 1/11
        nonace_sum = 0
        ace_count = 0
        for c in self.hand :
            if c.value == ace : 
                ace_count += 1
            else:
                nonace_sum += c.numerical_value()

        # no aces in this had so return now
        # Note return an array even when a single value
        if ace_count==0 : 
            self.hand_sums = [ nonace_sum, ]
            if nonace_sum > 21 : 
                raise BlackjackBusted(self)
            return self.hand_sums

        # build a tree of possible values for the aces
        root = Node(0)
        for c in self.hand :
            if c.value==ace : 
                root.add_leaves( (1,11) )

        root.summation(nonace_sum,root,self.hand_sums )

        # did we bust?
        safe_hands = [ n for n in self.hand_sums if n < 21 ] 
        if len(safe_hands)==0 :
            raise BlackjackBusted(self)

        return self.hand_sums 

    def is_blackjack(self):
        if len(self.hand)==2:
            if self.hand[0].numerical_value() == 10 and self.hand[1].value==ace :
                return True 
            if self.hand[1].numerical_value() == 10 and self.hand[0].value==ace :
                return True 
        return False
        
def calc_blackjack_results(hands_list):
    # for each hand, calculate sum or BUSTED (-1)
    # return full list of results and an index of overall winner
    result_list = []
    winner_idx = 0
    for hand in hands_list : 
        hand_result = hand.summation()
        non_bust = [ n for n in hand_result if n <= 21 ]
        if len(non_bust)==0 :
            result_list.append(BUSTED)
        else:
            result_list.append(max(non_bust))
        if result_list[winner_idx] < result_list[-1] : 
            winner_idx = len(result_list)-1

    return winner_idx, result_list

def test():
    # hand of all aces to test the summation code
    all_aces = [ BlackjackCard(s,ace) for s in suits ]
    #print(all_aces)
    aces_hand = BlackjackHand()
    [ aces_hand.add(c) for c in all_aces ]
    #print(aces_hand)
    print(aces_hand.summation())

    # 
    # get cards until bust
    # 
    deck = BlackjackDeck()
    deck.shuffle()
    dealer = iter(deck)

    hand = BlackjackHand()
    # start with two cards
    hand.add(next(dealer))
    hand.add(next(dealer))
    hand.summation()
    print("Deal. hand={0} sum={1}".format(hand,hand.hand_sums))
    try : 
        while 1 : 
            hand.add(next(dealer))
            hand.summation()
            print("Hit. hand={0} sum={1}".format(hand,hand.hand_sums))
    except BlackjackBusted :
        print("Busted! hand={0} sum={1}".format(hand,hand.hand_sums))
        pass

def play_hand():
    deck = BlackjackDeck()
    deck.shuffle()

    dealer = iter(deck)

    dealer_hand = BlackjackHand()
    player_hand = BlackjackHand()

    # deal two cards, player first
    for i in range(2):
        player_hand.add( next(dealer) )
        dealer_hand.add( next(dealer) )

    # dealer first card always stays hidden
    print("dealer shows {0} player={1}".format(dealer_hand.hand[1],player_hand))

    # check if anyone got blackjack
    if player_hand.is_blackjack() : 
        print( "Player hits BLACKJACK!")
        if dealer_hand.is_blackjack() : 
            print("dealer={0}".format(dealer_hand))
            print("Dealer hits BLACKJACK!")
            return GAME_PUSH
        return PLAYER_BLACKJACK

    while 1 : 
        s = input("take a card? y/n " )
        if s=='y':
            print("Player says hit me.")
            player_hand.add(next(dealer))
            print("player={0}".format(player_hand))
            try : 
                player_hand_value = player_hand.summation()
            except BlackjackBusted:
                print( "Player busted! You lose!" )
                return DEALER_WIN
        elif s=='n':
            break
        else:
            print("please answer with y or n")
        
    if dealer_hand.is_blackjack() : 
        print("dealer={0}".format(dealer_hand))
        print("Dealer hits BLACKJACK!")
        return DEALER_WIN

    # dealer has to hit on 16 stand on 17
    dealer_hand_value = dealer_hand.summation()
    while max(dealer_hand_value) < 17 : 
        print("dealer takes card")
        dealer_hand.add(next(dealer))
        try : 
            dealer_hand_value = dealer_hand.summation()
        except BlackjackBusted:
            print("dealer={0} player={1}".format(dealer_hand,player_hand))
            print( "Dealer busted! You win!" )
            return PLAYER_WIN
        dealer_cards = " ".join( [str(c) for c in dealer_hand.hand[1:]] )
        print("dealer shows {0} player={1}".format(dealer_cards,player_hand))

    winner_idx, card_sums = calc_blackjack_results((dealer_hand,player_hand))

    print("dealer={0} player={1}".format(dealer_hand,player_hand))

    if card_sums[0]==card_sums[1] :
        print("It's a tie. Push!")
        return GAME_PUSH

    if winner_idx==0 :
        print("Dealer wins!")
        return DEALER_WIN

    print("Player wins!")
    return PLAYER_WIN

def main():
#    test()

    player_money = 100
    while player_money > 0 : 
        print("player has ${0}".format(player_money))
        s = input("(q to quit) wager? " )
        if s=='q':
            break
        try : 
            wager = int(s)
        except ValueError:
            print("That is not a number.")
            continue
        if wager > player_money :
            print("Your ${0} bet exceeds your holdings of ${1}".format(
                wager, player_money))
            continue

        winner = play_hand()

        if winner == PLAYER_WIN:
            player_money += wager
        elif winner==DEALER_WIN :
            player_money -= wager
        elif winner==PLAYER_BLACKJACK :
            player_money += int(round(1.5*wager))
        else:
            assert winner == GAME_PUSH, winner

        if player_money==0 :
            print("You went broke! Time to go to the ATM.")

if __name__=='__main__':
    main()

