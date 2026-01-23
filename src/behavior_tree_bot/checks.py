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
# Check if any enemy fleets are headed to our planets ??
# Although, I think we can check in the behavior directly?
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
    
    # Need at least one strong planet to launch attack from, but by how much??
    # Maybe we need a range factor instead of just strongest vs weakest?
    strongest_planet = max(state.my_planets(), key=lambda p: p.num_ships)
    weakest_enemy = min(state.enemy_planets(), key=lambda p: p.num_ships)
    
    if not strongest_planet or not weakest_enemy:
        return False
    
    # Need at least 1.5x the enemy's ships to attack safely
    return strongest_planet.num_ships > weakest_enemy.num_ships * 1.5

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
        if distance < 15 and enemy_planet.num_ships > strongest_planet.num_ships * 0.7:
            return False  # means it's close and too strong
    
    # Check incoming fleets
    my_planet_ids = {p.ID for p in state.my_planets()}
    incoming_danger = sum(
        fleet.num_ships for fleet in state.enemy_fleets()
        if fleet.destination_planet in my_planet_ids and fleet.turns_remaining < 10
    )
    
    # If there is a significant amount of incoming danger, don't expand
    return incoming_danger < strongest_planet.num_ships * 0.3

#
# Check if we have high advantage over enemy?
# def hard_attack(state):
#

#
# def if_early_game(state):
#

#
# def if_high_danger_planet(state):
#

#
# def needReinforcements(state): ??
#

#
# def if_enemy_weak(state): ??
#
