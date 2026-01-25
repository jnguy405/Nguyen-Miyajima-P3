"""
BEHAVIOR TREE BOT - PLANET WARS

SCORING SYSTEM OVERVIEW:
------------------------

The bot uses a multi-factor scoring system to prioritize targets for both 
attack and expansion strategies. Scores are calculated based on the formula:

SCORE = (GrowthRate * GROWTH_WEIGHT) + 
        (1/Distance * DISTANCE_WEIGHT) - 
        (EnemyShips * SHIPS_WEIGHT)

Where:
- GrowthRate: Planet's production rate (ships/turn)
- Distance: Travel time between source and target planets
- EnemyShips: Number of ships currently on target planet
- Weights: GROWTH_WEIGHT=3.0, DISTANCE_WEIGHT=2.0, SHIPS_WEIGHT=1.5

DANGER LEVEL CALCULATION:
-------------------------
For defensive decisions, we calculate a danger level for each planet:

DANGER = Σ(Incoming Fleets: (1000/(Distance+1) * 5.0 + Ships * 3.0) +
        Σ(Enemy Planets: Distance * 3.0 + Ships * 1.0)

Where:
- Incoming fleets are weighted more heavily (closer = more dangerous)
- Nearby enemy planets with large fleets increase danger
- Used to prioritize which planets need reinforcement

HELPER FUNCTIONS:
-----------------
- get_strongest_planet(): Returns planet with most ships
- get_weakest_planet(): Returns weakest from list of planets
- get_closest_planet(): Returns nearest planet from a list
- average_ally_power(): Average ship count across owned planets
- danger_level(): Calculates threat level for a planet
- calculate_target_score(): Main scoring function
- find_best_enemy_target(): Applies scoring to enemy planets
- find_best_neutral_target(): Applies scoring to neutral planets
- deployable_planets(): array of tuples (planets above average ally power, surplus)

ATTACK STRATEGIES:
------------------
1. attack_best_target(): Uses scoring system to select optimal enemy planet
2. attack_weakest_enemy_planet(): Targets weakest enemy (simpler fallback)

EXPANSION STRATEGIES:
---------------------
1. expand_to_valuable_neutral(): Uses scoring for high-growth neutrals
2. spread_to_weakest_neutral_planet(): Targets weakest neutral (fallback)

DEFENSE STRATEGIES:
-------------------
1. defend_under_attack_planet(): Reinforces planets with incoming fleets
2. reinforce_frontline(): Strengthens planets closest to enemy territory
3. defend_using_danger_level(): Uses danger scoring for smart defense
"""

import sys
sys.path.insert(0, '../')
from planet_wars import issue_order

# HELPERS AND UTILITIES --------------------------------------------------------

def get_strongest_planet(state):
    return max(state.my_planets(), key=lambda p: p.num_ships, default=None)

def get_weakest_planet(planets):
    return min(planets, key=lambda p: p.num_ships, default=None)

def get_closest_planet(state, source_planet, planets):
    if not source_planet or not planets:
        return None
    return min(planets, key=lambda p: state.distance(source_planet.ID, p.ID))

def average_ally_power(state):

    planets = [planet.num_ships for planet in state.my_planets()]

    # safe guard from crashing
    if not planets:
        return 0
    
    return sum(planets)/len(planets)

# Calculate a danger score for a planet
def danger_level(state, planet):
    # calculate using fleets' distances and ship counts, 
    # as well as enemty planets distance and ship counts'

    fleet_dist_weight = 5.0
    fleet_ship_weight = 3.0
    planet_dist_weight = 3.0
    planet_ship_weight = 1.0

    incoming_fleets = [
        fleet for fleet in state.enemy_fleets()
        if fleet.destination_planet == planet.ID
    ]
    enemy_planets = state.enemy_planets()
    score = 0

    if not planet:
        return 0

    for fleet in incoming_fleets:
        #num ships, turns_remaining
        ships = fleet.num_ships # the bigger the more dangerous
        dist = fleet.turns_remaining # the lesser the more dangerous
        # score += (1000/(dist+1)) * fleet_dist_weight + ships*fleet_ship_weight 
        # #should come out like <=1
        # Normalize values between 0-1
        normalized_dist = 1.0 / (dist + 1)  # Already between 0-1
        normalized_ships = ships / (ships + 100)  # Scale ship count

    score += normalized_dist * fleet_dist_weight + normalized_ships * fleet_ship_weight

    for p in enemy_planets:
        ships = p.num_ships
        dist = state.distance(p.ID,planet.ID)
        #the same as before
        score += dist*planet_dist_weight + ships*planet_ship_weight

    return score

def calculate_target_score(state, source_planet, target_planet):

    if not source_planet or not target_planet:
        return -float('inf')
    
    distance = state.distance(source_planet.ID, target_planet.ID)

    if distance == 0:
        return -float('inf')
    
    # Score formula: prioritize high growth, close distance, low enemy ships
    growth_weight = 3.0
    distance_weight = 2.0
    ships_weight = 1.5
    
    score = (target_planet.growth_rate * growth_weight) + \
            (1 / distance * distance_weight) - \
            (target_planet.num_ships * ships_weight)
    
    return score

def find_best_enemy_target(state, source_planet):
    if not source_planet:
        return None
    
    best_score = -float('inf')
    best_target = None

    for planet in state.enemy_planets():
        score = calculate_target_score(state, source_planet, planet)
        if score > best_score:
            best_score = score
            best_target = planet

    return best_target

def find_best_neutral_target(state, source_planet):
    if not source_planet:
        return None
    
    best_score = -float('inf')
    best_target = None

    for planet in state.neutral_planets():
        score = calculate_target_score(state, source_planet, planet)
        if score > best_score:
            best_score = score
            best_target = planet

    return best_target

def deployable_planets(state):
    power = average_ally_power(state)
    return [(p,(p.ships-power)) for p in state.my_planets()
            if p.ships > power]

# ATTACK BEHAVIORS --------------------------------------------------------

def attack_weakest_enemy_planet(state):
    # Find my strongest planet
    strongest_planet = get_strongest_planet(state)
    if not strongest_planet:
        return False
    
    # Find weakest enemy planet
    weakest_enemy = get_weakest_planet(state.enemy_planets())
    if not weakest_enemy:
        return False
    
    # Send enough ships to capture + safety margin
    required_ships = weakest_enemy.num_ships + 1
    if strongest_planet.num_ships > required_ships + 10:  # Keep some for defense
        return issue_order(state, strongest_planet.ID, weakest_enemy.ID, required_ships)
    return False

def attack_best_target(state):

    strongest_planet = get_strongest_planet(state)
    if not strongest_planet or strongest_planet.num_ships < 10:
        return False
    
    best_target = find_best_enemy_target(state, strongest_planet)
    if not best_target:
        return False
    
    required_ships = best_target.num_ships + 1
    if strongest_planet.num_ships > required_ships + 15:
        return issue_order(state, strongest_planet.ID, best_target.ID, required_ships)
    
    return False

def spread_to_weakest_neutral_planet(state):

    strongest_planet = get_strongest_planet(state)
    if not strongest_planet:
        return False
    
    weakest_neutral = get_weakest_planet(state.neutral_planets())
    if not weakest_neutral:
        return False
    
    required_ships = weakest_neutral.num_ships + 1
    if strongest_planet.num_ships > required_ships + 5:
        return issue_order(state, strongest_planet.ID, weakest_neutral.ID, required_ships)
    
    return False

def expand_to_valuable_neutral(state):
    strongest_planet = get_strongest_planet(state)
    if not strongest_planet or strongest_planet.num_ships < 15:
        return False
    
    best_target = find_best_neutral_target(state, strongest_planet)
    if not best_target:
        return False
    
    required_ships = best_target.num_ships + 1
    if strongest_planet.num_ships > required_ships + 10:
        return issue_order(state, strongest_planet.ID, best_target.ID, required_ships)
    
    return False

# DEFENSE BEHAVIORS --------------------------------------------------------

def defend_under_attack_planet(state):
    # Check for planets under attack
    for my_planet in state.my_planets():
        # Look for incoming enemy fleets
        incoming_fleets = [
            fleet for fleet in state.enemy_fleets()
            if fleet.destination_planet == my_planet.ID
        ]
        
        if incoming_fleets:
            total_incoming = sum(f.num_ships for f in incoming_fleets)
            # If we're going to lose this planet, try to reinforce
            if total_incoming >= my_planet.num_ships:
                # Find nearest strong planet to send reinforcements
                reinforcing_planets = [
                    p for p in state.my_planets() 
                    if p.ID != my_planet.ID and p.num_ships > total_incoming + 5
                ]
                if reinforcing_planets:
                    closest_reinforcer = get_closest_planet(state, my_planet, reinforcing_planets)
                    if closest_reinforcer:
                        ships_to_send = total_incoming - my_planet.num_ships + 5
                        if ships_to_send > 0 and closest_reinforcer.num_ships > ships_to_send + 5:
                            return issue_order(
                                state, 
                                closest_reinforcer.ID, 
                                my_planet.ID, 
                                ships_to_send
                            )
    return False

def reinforce_frontline(state):
    # Find planets on the "frontline" - closest to enemy planets
    if not state.enemy_planets() or not state.my_planets():
        return False
    
    # Find the planet closest to enemy territory
    frontline_planet = None
    min_distance = float('inf')
    
    for my_planet in state.my_planets():
        for enemy_planet in state.enemy_planets():
            distance = state.distance(my_planet.ID, enemy_planet.ID)
            if distance < min_distance:
                min_distance = distance
                frontline_planet = my_planet
    
    if not frontline_planet:
        return False
    
    # Find a strong planet to send reinforcements from
    reinforcing_planets = [
        p for p in state.my_planets() 
        if p.ID != frontline_planet.ID and p.num_ships > frontline_planet.num_ships + 10
    ]
    
    if reinforcing_planets:
        strongest_reinforcer = max(reinforcing_planets, key=lambda p: p.num_ships)
        ships_to_send = min(strongest_reinforcer.num_ships - 10, 20)
        if ships_to_send > 5:
            return issue_order(
                state, 
                strongest_reinforcer.ID, 
                frontline_planet.ID, 
                ships_to_send
            )
    return False