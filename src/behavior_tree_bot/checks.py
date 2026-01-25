# CONFIGURATION CONSTANTS --------------------------------------------------------

ATTACK_THRESHOLD = 20   # Minimum ships to consider attacking
EXPAND_THRESHOLD = 40   # Minimum total ships to consider expanding
FRONTLINE_DISTANCE = 15 # Distance to consider a planet on the frontline

# CHECK FUNCTIONS --------------------------------------------------------

#
# Checks if there are any neutral planets available to capture
#
def neutrals_available(state):
    return any(state.neutral_planets())

#
# Check if any enemy fleets are headed to our planets
#
def enemy_fleets_incoming(state):
    my_ids = {p.ID for p in state.my_planets()}
    return any(f.destination_planet in my_ids for f in state.enemy_fleets())

#
# Check if we have sufficient strength for a safe attack
#
def can_attack(state):
    planets = state.my_planets()
    return any(p.num_ships >= ATTACK_THRESHOLD for p in planets) if planets else False

#
# Check if no strong enemy threats are nearby for safe expansion
#
def safe_to_expand(state):
    if not state.my_planets():
        return False
    
    strong = max(state.my_planets(), key=lambda p: p.num_ships)
    
    for enemy in state.enemy_planets():
        dist = state.distance(strong.ID, enemy.ID)
        if dist < FRONTLINE_DISTANCE and enemy.num_ships > strong.num_ships * 0.7:
            return False
    
    return True

#
# Check if we should expand based on our total strength
#
def should_expand(state):
    if not neutrals_available(state):
        return False
    
    total_ships = sum(p.num_ships for p in state.my_planets())
    return total_ships > EXPAND_THRESHOLD

#
# Check if we have at least one strong planet
#
def has_strong_planet(state):
    planets = state.my_planets()
    return max(p.num_ships for p in planets) >= ATTACK_THRESHOLD if planets else False

def fleets_not_flying(state):
    return len(state.my_fleets()) >= len(state.my_planets())*2