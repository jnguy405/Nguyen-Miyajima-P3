#!/usr/bin/env python
#

"""
// There is already a basic strategy in place here. You can use it as a
// starting point, or you can throw it out entirely and replace it with your
// own.
"""
import logging, traceback, sys, os, inspect
logging.basicConfig(filename=__file__[:-3] +'.log', filemode='w', level=logging.DEBUG)
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.append(parentdir)

from behavior_tree_bot.behaviors import *
from behavior_tree_bot.checks import *
from behavior_tree_bot.bt_nodes import Selector, Sequence, Action, Check

from planet_wars import PlanetWars, finish_turn

# You have to improve this tree or create an entire new one that is capable
# of winning against all the 5 opponent bots

# SIMPLE CHECKS --------------------------------------------------------
def enemies_exist(state):
    return len(state.enemy_planets()) > 0

def need_build_up(state):
    strong = strongest_planet(state)
    return strong and strong.num_ships < 30

def can_expand_safe(state):
    return neutrals_available(state) and should_expand(state) and safe_to_expand(state)

# BEHAVIOR TREE --------------------------------------------------------
def setup_behavior_tree():
    root = Selector(name='Winner')
    
    # SIMPLE CHECKS
    def enemies_exist(state):
        return len(state.enemy_planets()) > 0
    
    # 1. DEFENSE
    def_seq = Sequence(name='Defend')
    def_seq.child_nodes = [
        Check(enemy_fleets_incoming),
        Action(defend_attacked)
    ]
    
    # 2. CONSTANT ATTACK
    attack_seq = Sequence(name='Attack')
    attack_seq.child_nodes = [
        Check(enemies_exist),
        Action(constant_attack)
    ]
    
    # 3. EXPAND (only when no enemies)
    expand_seq = Sequence(name='Expand')
    expand_seq.child_nodes = [
        Check(lambda s: len(s.enemy_planets()) == 0),
        Check(neutrals_available),
        Action(expand_neutral)
    ]
    
    root.child_nodes = [
        Check(fleets_not_flying),
        def_seq,      # 1. Defend if attacked
        attack_seq,   # 2. CONSTANT ATTACK (main strategy)
        expand_seq    # 3. Expand if safe
    ]
    
    logging.info('\n' + root.tree_to_string())
    return root

# You don't need to change this function
def do_turn(state):
    behavior_tree.execute(planet_wars)

if __name__ == '__main__':
    logging.basicConfig(filename=__file__[:-3] + '.log', filemode='w', level=logging.DEBUG)

    behavior_tree = setup_behavior_tree()
    try:
        map_data = ''
        while True:
            current_line = input()
            if len(current_line) >= 2 and current_line.startswith("go"):
                planet_wars = PlanetWars(map_data)
                do_turn(planet_wars)
                finish_turn()
                map_data = ''
            else:
                map_data += current_line + '\n'

    except KeyboardInterrupt:
        print('ctrl-c, leaving ...')
    except Exception:
        traceback.print_exc(file=sys.stdout)
        logging.exception("Error in bot.")