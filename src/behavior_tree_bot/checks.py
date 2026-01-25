# CONFIGURATION CONSTANTS --------------------------------------------------------

# Attack strength thresholds
ATTACK_SAFETY_RATIO = 1.5        # Need X times enemy strength to attack safely
HARD_ATTACK_RATIO = 2.0          # Need X times total strength for hard attack
STRONG_PLANET_THRESHOLD = 20     # Minimum ships to be considered "strong"

# Defense thresholds
DANGER_LEVEL_THRESHOLD = 50      # Danger score threshold for high danger
FRONTLINE_DISTANCE = 20          # Distance to enemy to be considered "frontline"
FRONTLINE_WEAKNESS_RATIO = 0.6   # Frontline is weak if < X% of average strength

# Safety/Expansion thresholds
EXPANSION_SAFE_DISTANCE = 15     # Enemy within this distance is dangerous
EXPANSION_ENEMY_STRENGTH_RATIO = 0.7  # Enemy too strong if > X% of our strength
INCOMING_DANGER_TIME = 10        # Fleets arriving within X turns are imminent
INCOMING_DANGER_RATIO = 0.3      # Incoming ships > X% of our strength is dangerous

# Game phase thresholds
EARLY_GAME_PLANET_COUNT = 2      # Max planets for early game phase

# CHECK FUNCTIONS --------------------------------------------------------

#
# Checks if there are any neutral planets available to capture
#
def if_neutral_planet_available(state):
    return any(state.neutral_planets())

#
# Check if we have the largest fleet
#
def have_largest_fleet(state):
    return sum(planet.num_ships for planet in state.my_planets()) \
             + sum(fleet.num_ships for fleet in state.my_fleets()) \
           > sum(planet.num_ships for planet in state.enemy_planets()) \
             + sum(fleet.num_ships for fleet in state.enemy_fleets())

#
# Check if any enemy fleets are headed to our planets
#
def if_enemy_fleet_incoming(state):
    my_planet_ids = {p.ID for p in state.my_planets()}
    for fleet in state.enemy_fleets():
        if fleet.destination_planet in my_planet_ids:
            return True
    return False

#
# Check if we have sufficient strength for a safe attack
#
def if_strong_enough_to_attack(state):
    if not state.my_planets() or not state.enemy_planets():
        return False
    
    # Need at least one strong planet to launch attack from
    strongest_planet = max(state.my_planets(), key=lambda p: p.num_ships)
    weakest_enemy = min(state.enemy_planets(), key=lambda p: p.num_ships)
    
    if not strongest_planet or not weakest_enemy:
        return False
    
    # Need at least ATTACK_SAFETY_RATIO times the enemy's ships to attack safely
    return strongest_planet.num_ships > weakest_enemy.num_ships * ATTACK_SAFETY_RATIO

#
# Check if no strong enemy threats are nearby for safe expansion
#
def if_safe_to_expand(state):
    if not state.my_planets():
        return False
    
    # Check our strongest planet's safety
    strongest_planet = max(state.my_planets(), key=lambda p: p.num_ships)
    
    # Check nearby enemy planets
    for enemy_planet in state.enemy_planets():
        distance = state.distance(strongest_planet.ID, enemy_planet.ID)
        if (distance < EXPANSION_SAFE_DISTANCE and 
            enemy_planet.num_ships > strongest_planet.num_ships * EXPANSION_ENEMY_STRENGTH_RATIO):
            return False  # Too close and too strong
    
    # Check incoming fleets
    my_planet_ids = {p.ID for p in state.my_planets()}
    incoming_danger = sum(
        fleet.num_ships for fleet in state.enemy_fleets()
        if (fleet.destination_planet in my_planet_ids and 
            fleet.turns_remaining < INCOMING_DANGER_TIME)
    )
    
    # If significant incoming danger, don't expand
    return incoming_danger < strongest_planet.num_ships * INCOMING_DANGER_RATIO

#
# Check if we have high advantage over enemy (for blitz/hard attack)
#
def hard_attack(state):
    if len(state.my_planets()) < 2:
        return False

    my_total = sum(p.num_ships for p in state.my_planets())
    enemy_total = sum(p.num_ships for p in state.enemy_planets())

    # Need HARD_ATTACK_RATIO advantage for hard attack
    return my_total > enemy_total * HARD_ATTACK_RATIO

#
# Check if we are in early game phase
#
def if_early_game(state):
    return (len(state.my_planets()) <= EARLY_GAME_PLANET_COUNT and 
            len(state.enemy_planets()) <= EARLY_GAME_PLANET_COUNT)

#
# Check if any of our planets are in high danger
#
def if_high_danger_planet(state):
    from behavior_tree_bot.behaviors import danger_level
    
    for planet in state.my_planets():
        if danger_level(state, planet) > DANGER_LEVEL_THRESHOLD:
            return True
    return False

#
# Check if we need reinforcements on frontline planets
#
def needReinforcements(state):
    if len(state.my_planets()) < 2:
        return False
    
    # Find average strength of all planets
    planets = state.my_planets()
    avg_strength = sum(p.num_ships for p in planets) / len(planets)
    
    # Find frontline planets (closest to enemy)
    if not state.enemy_planets():
        return False
    
    frontline_strengths = []
    for my_planet in planets:
        # Calculate minimum distance to any enemy
        min_dist = min(
            state.distance(my_planet.ID, enemy.ID) 
            for enemy in state.enemy_planets()
        )
        if min_dist < FRONTLINE_DISTANCE:  # Consider this frontline
            frontline_strengths.append(my_planet.num_ships)
    
    if not frontline_strengths:
        return False
    
    # Check if frontline is significantly weaker
    avg_frontline = sum(frontline_strengths) / len(frontline_strengths)
    return avg_frontline < avg_strength * FRONTLINE_WEAKNESS_RATIO

#
# Check if we have at least one strong planet
#
def if_has_strong_planet(state):
    if not state.my_planets():
        return False
    
    strongest = max(state.my_planets(), key=lambda p: p.num_ships)
    return strongest.num_ships >= STRONG_PLANET_THRESHOLD