import sys
sys.path.insert(0, '../')
from planet_wars import issue_order

# HELPERS

def get_strongest_planet(state):
    return max(state.my_planets(), key=lambda p: p.num_ships, default=None)

def get_weakest_planet(planets):
    return min(planets, key=lambda p: p.num_ships, default=None)

def get_closest_planet(state, source_planet, planets):
    if not source_planet or not planets:
        return None
    return min(planets, key=lambda p: state.distance(source_planet.ID, p.ID))

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

# ATTACK BEHAVIORS

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

# DEFENSE BEHAVIORS