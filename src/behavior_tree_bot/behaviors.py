"""
BEHAVIOR TREE BOT - PLANET WARS

SIMPLE BOT STRATEGY OVERVIEW:
-----------------------------
This bot implements basic planet wars strategies without complex scoring systems.
It uses simple heuristics for attack, expansion, and defense.

CONFIGURATION CONSTANTS:
------------------------
- MIN_ATTACK_STRENGTH: Minimum ships needed to launch attacks (15)
- MIN_EXPAND_STRENGTH: Minimum ships needed to expand to neutrals (20)
- MIN_DEFENSE_KEEP: Minimum ships to keep when sending fleets (10)
- WAVE_SIZE: Fixed number of ships for wave attacks (20)
- SAFETY_MARGIN: Buffer for various operations (5)
- CONSOLIDATE_THRESHOLD: Unused in current implementation

HELPER FUNCTIONS:
-----------------
- strongest_planet(): Returns strongest friendly planet (most ships)
- weakest_planet(): Returns weakest planet from a list

ATTACK BEHAVIORS:
-----------------
1. attack_weakest(): Strongest planet attacks weakest enemy planet
   - Calculates required ships: enemy ships + distance*growth_rate + 1
   - Sends only if we have ships beyond SAFETY_MARGIN

2. constant_attack(): Strongest planet attacks closest enemy
   - Sends half of strongest planet's ships
   - Requires at least 10 ships to send

3. attack_wave(): Strongest planet sends fixed WAVE_SIZE to weakest enemy
   - Only if strongest has > WAVE_SIZE + MIN_DEFENSE_KEEP ships

4. attack_any(): Any friendly planet attacks any enemy planet if feasible
   - Iterates through all friendly/enemy combinations
   - Uses same calculation as attack_weakest()

EXPANSION BEHAVIORS:
--------------------
1. expand_neutral(): Strongest planet captures highest growth neutral
   - Accounts for fleets already in transit
   - Prioritizes neutral planets by growth rate
   - Sends required ships (neutral ships + 1 - fleets already sent)

DEFENSE BEHAVIORS:
------------------
1. defend_attacked(): Reinforces planets under attack
   - Sends help when total incoming enemies >= current defenders
   - Helper planets send enough to cover deficit + SAFETY_MARGIN

2. reinforce(): Strongest planet helps weakest friendly planet
   - Only if strength difference > 20 ships
   - Sends up to 20 ships or strong.num_ships - MIN_DEFENSE_KEEP

3. consolidate(): Weak planets send ships to strongest planet
   - Each weak planet sends all but 3 ships to strongest
   - Helps concentrate forces
"""

import sys
sys.path.insert(0, '../')
from planet_wars import issue_order

# CONFIGURATION CONSTANTS
MIN_ATTACK_STRENGTH = 15
MIN_EXPAND_STRENGTH = 20
MIN_DEFENSE_KEEP = 10
WAVE_SIZE = 20
SAFETY_MARGIN = 5
CONSOLIDATE_THRESHOLD = 30

# HELPERS AND UTILITIES --------------------------------------------------------

def strongest_planet(state):
    return max(state.my_planets(), key=lambda p: p.num_ships, default=None)

def weakest_planet(planets):
    return min(planets, key=lambda p: p.num_ships, default=None)

# ATTACK BEHAVIORS --------------------------------------------------------

def attack_weakest(state):
    src = strongest_planet(state)
    if not src:
        return False
    
    tgt = weakest_planet(state.enemy_planets())
    if not tgt:
        return False
    
    req = tgt.num_ships + 1
    dist = state.distance(src.ID, tgt.ID)
    req += dist * tgt.growth_rate
    
    if src.num_ships > req + SAFETY_MARGIN:
        return issue_order(state, src.ID, tgt.ID, req)
    
    return False

# Determines how to perform constant attacks by strongest planet
def constant_attack(state):
    strongest = strongest_planet(state)
    if not strongest or strongest.num_ships < 10:
        return False
    
    enemies = state.enemy_planets()
    if not enemies:
        return False
    
    # Attack closest enemy
    target = min(enemies, key=lambda e: state.distance(strongest.ID, e.ID))
    
    # Send half our ships
    ships_to_send = strongest.num_ships // 2
    if ships_to_send > 5:
        return issue_order(state, strongest.ID, target.ID, ships_to_send)
    
    return False

# Determines how to launch a wave attack by strongest planet
def attack_wave(state):
    src = strongest_planet(state)
    if not src or src.num_ships < MIN_ATTACK_STRENGTH:
        return False
    
    enemies = state.enemy_planets()
    if not enemies:
        return False
    
    # Attack weakest enemy
    tgt = weakest_planet(enemies)
    
    # Fixed wave attack
    if src.num_ships > WAVE_SIZE + MIN_DEFENSE_KEEP:
        return issue_order(state, src.ID, tgt.ID, WAVE_SIZE)
    
    return False

# Determines how to attack any enemy planet from any friendly planet
def attack_any(state):
    if not state.enemy_planets():
        return False
    
    for src in state.my_planets():
        if src.num_ships < 10:
            continue
            
        for tgt in state.enemy_planets():
            req = tgt.num_ships + 1
            dist = state.distance(src.ID, tgt.ID)
            req += dist * tgt.growth_rate
            
            if src.num_ships > req + 3:
                return issue_order(state, src.ID, tgt.ID, req)
    
    return False

# EXPANSION BEHAVIORS --------------------------------------------------------

# Deteremines how to expand to neutral planets by strongest planet
def expand_neutral(state):
    if not state.my_planets() or not state.neutral_planets():
        return False
    
    src = strongest_planet(state)
    if not src or src.num_ships < MIN_EXPAND_STRENGTH:
        return False
    
    # Find viable targets
    targets = []
    for tgt in state.neutral_planets():
        fleets_sent = sum(
            f.num_ships for f in state.my_fleets()
            if f.destination_planet == tgt.ID
        )
        
        if fleets_sent >= tgt.num_ships + 1:
            continue
            
        req = tgt.num_ships + 1 - fleets_sent
        if req > 0 and req < src.num_ships - MIN_DEFENSE_KEEP:
            targets.append((tgt, req))
    
    if not targets:
        return False
    
    # Take highest growth target
    targets.sort(key=lambda x: x[0].growth_rate, reverse=True)
    tgt, req = targets[0]
    
    return issue_order(state, src.ID, tgt.ID, req)

# DEFENSE BEHAVIORS --------------------------------------------------------

def defend_attacked(state):
    for my_p in state.my_planets():
        incoming = [f for f in state.enemy_fleets() 
                   if f.destination_planet == my_p.ID]
        
        if incoming:
            total = sum(f.num_ships for f in incoming)
            if total >= my_p.num_ships:
                for helper in state.my_planets():
                    if helper.ID != my_p.ID and helper.num_ships > total + SAFETY_MARGIN:
                        send = total - (my_p.num_ships + SAFETY_MARGIN)
                        if send > 0:
                            return issue_order(state, helper.ID, my_p.ID, send)
    return False

# Takes strongest planet to help weakest friendly planet
def reinforce(state):
    if len(state.my_planets()) < 2:
        return False
    
    weak = weakest_planet(state.my_planets())
    strong = strongest_planet(state)
    
    if weak and strong and weak.ID != strong.ID:
        if strong.num_ships > weak.num_ships + 20:
            send = min(strong.num_ships - MIN_DEFENSE_KEEP, 20)
            if send > SAFETY_MARGIN:
                return issue_order(state, strong.ID, weak.ID, send)
    return False

# Consolidates weak planets to strongest planet
def consolidate(state):
    if len(state.my_planets()) < 2:
        return False
    
    strong = strongest_planet(state)
    weak_planets = [p for p in state.my_planets() 
                   if p.ID != strong.ID and p.num_ships > 5]
    
    for weak in weak_planets:
        send = weak.num_ships - 3
        if send > 0:
            return issue_order(state, weak.ID, strong.ID, send)
    
    return False