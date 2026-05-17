from flask import Flask, request
from flask_cors import CORS
from flask_socketio import SocketIO, emit
import random

app = Flask(__name__)
CORS(app)
app.config['SECRET_KEY'] = 'your_secret_key'
socketio = SocketIO(app, cors_allowed_origins="*")

# GAME STATE
connected_players = {}
player_characters = {} # tracks who picks what character
current_wagers = {} # RPS choice tracker
current_hp = {}
current_sp = {} # tracking skill points to trigger skill
loss_streaks = {} # tracks consecutive rps losses
used_revive = {} # tracks if Yaoshi used this instance once
used_pity_heal = {} # tracks if pity heal was used for the current match

# CHARACTER_STATS = { # for testing purposes everything is nerfed
#     'Aha': {'hp': 450, 'dmg': 70, 'skill_dmg': 200}, 
#     'Lan': {'hp': 350, 'dmg': 90, 'skill_dmg': 230}, 
#     'Yaoshi': {'hp': 550, 'dmg': 60, 'skill_dmg': 170}, 
# }

# [ORIGINAL STATS]
CHARACTER_STATS = { 
    'Aha': {'hp': 950, 'dmg': 100, 'skill_dmg': 240}, 
    'Lan': {'hp': 750, 'dmg': 150, 'skill_dmg': 300}, 
    'Yaoshi': {'hp': 1200, 'dmg': 90, 'skill_dmg': 180}, 
}

# CHARACTER PASSIVES
# Aha: Every BA triggers a coin flip. Heads: 2x dmg, +1 SP. Tails: 1 dmg, +2 SP, steals 1 SP from opponent
# Aha: Every skill triggers a coin flip. Heads: Crit for fixed 360 damage. Tails: 1 dmg, refunds 2 SP.
# Lan: For every 1 SP you have, deal 10% more damage (for both Basic and Skill)
# Yaoshi: Can heal even over max HP (max to 1500), if HP drops 0, revive with 1 HP and 2SP.


@app.route('/')
def index():
    return "Welcome to Aetherium Clash Backend!"

@socketio.on('connect')
def handle_connect():
    session_id = request.sid

    active_roles = connected_players.values()

    if 'Player1' not in active_roles:
        role = 'Player1'
    elif 'Player2' not in active_roles:
        role = 'Player2'
    else:
        role = 'Spectator'

    connected_players[session_id] = role

    print(f"{session_id} connected as {role}")
    print(f"Current connected players: {connected_players}")

    emit('role_assignment', {'role': role, 'message': f'You are assigned the role: {role}'}, room=session_id)

@socketio.on('disconnect')
def handle_disconnect():
    session_id = request.sid
    if session_id in connected_players:
        role = connected_players.pop(session_id)
        print(f"{session_id} disconnected from role {role}")

        if role in player_characters:
            del player_characters[role]
        if role in current_wagers:
            del current_wagers[role]
        
        emit('game_reset', {'message': f'{role} has disconnected. Game state reset.'}, broadcast=True)
        print(f"Current connected players: {connected_players}")

@socketio.on('character_selection')
def handle_character_selection(data):
    session_id = request.sid
    user_role = connected_players.get(session_id, 'Unknown')

    if user_role in ['Player1', 'Player2']:
        character_name = data.get('character')

        if user_role in player_characters:
            print(f"{user_role} attempted to change character from {player_characters[user_role]} to {character_name}")
            return

        if character_name in CHARACTER_STATS:
            player_characters[user_role] = character_name
            print(f"{user_role} selected character: {character_name}")
            emit('game_update', {'message': f'{user_role} selected {character_name}'}, broadcast=True)

            if len(player_characters) == 2:
                print(f"Both players have selected characters: {player_characters}")
                emit('game_update', {'message': f"Both players have selected characters: {player_characters}"}, broadcast=True)

                p1_char = player_characters['Player1']
                p2_char = player_characters['Player2']

                current_hp['Player1'] = CHARACTER_STATS[p1_char]['hp']
                current_hp['Player2'] = CHARACTER_STATS[p2_char]['hp']

                current_sp['Player1'] = 3
                current_sp['Player2'] = 3

                loss_streaks['Player1'] = 0
                loss_streaks['Player2'] = 0

                used_revive.clear()
                used_pity_heal.clear()

                emit('match_start', {
                    'message': 'Match is starting!',
                    'hp_data': current_hp,
                    'sp_data': current_sp,
                    'character_data': player_characters}, broadcast=True)
        else:
            print(f"{user_role} attempted to select an invalid character: {character_name}")
    else:
        print(f"{user_role} attempted to select a character, but is not a player.")


@socketio.on('submit_wager')
def handle_wager(data):
    session_id = request.sid
    user_role = connected_players.get(session_id, 'Unknown')
    
    if user_role in ['Player1', 'Player2']:
        wager = data.get('wager') # 'Rock', 'Paper', or 'Scissors'
        
        # Save their bet in the vault
        current_wagers[user_role] = wager
        # Tell their specific frontend that the bet was received
        emit('wager_received', {'message': f'Wager {wager} locked! Waiting for opponent...'}, to=session_id)
        
        if len(current_wagers) == 2:
            p1_wager = current_wagers.get('Player1')
            p2_wager = current_wagers.get('Player2')

            # Handling a tie scenario
            if p1_wager == p2_wager:
                emit('game_update', {'message': 'It\'s a tie! Both players chose the same option.'}, broadcast=True)
                current_wagers.clear()
                emit('wager_reset', broadcast=True)

            else:
                winner = None
                if (p1_wager == 'Rock' and p2_wager == 'Scissors') or (p1_wager == 'Paper' and p2_wager == 'Rock') or (p1_wager == 'Scissors' and p2_wager == 'Paper'):
                    winner = 'Player1'
                    loser = 'Player2'
                else:
                    winner = 'Player2'
                    loser = 'Player1'
                
                loss_streaks[winner] = 0
                loss_streaks[loser] = loss_streaks.get(loser, 0) + 1

                emit('game_update', {'message': f'{winner} wins the RPS round!'}, broadcast=True)

                if loss_streaks[loser] == 3:
                    if not used_pity_heal.get(loser, False):
                        heal_amount = 250
                        loser_char = player_characters[loser]
                        max_hp = CHARACTER_STATS[loser_char]['hp']

                    # pity heal but cap at max hp
                        current_hp[loser] += heal_amount
                        if current_hp[loser] > max_hp:
                            current_hp[loser] = max_hp

                    # Mark that the pity heal has been used
                        used_pity_heal[loser] = True
                    
                        emit('hp_update', {'hp_data': current_hp}, broadcast=True)
                        emit('game_update', {'message': f"{loser}'s COMEBACK! Got one-time instant heal of 250 HP!"}, broadcast=True)

                    loss_streaks[loser] = 0

                current_wagers.clear()
                emit('turn_start', {'turn': winner}, broadcast=True)



@socketio.on('player_action')
def handle_player_action(data):
    session_id = request.sid
    attacker = connected_players.get(session_id, 'Unknown')

    if attacker in ['Player1', 'Player2']:
        defender = 'Player2' if attacker == 'Player1' else 'Player1'
        attack_type = data.get('attack_type') # 'Basic' or 'Skill'
        combo_multiplier = data.get('combo_multiplier', 1) # default to 1 if not provided

        if current_hp.get(attacker, 0) <= 0 or current_hp.get(defender, 0) <= 0:
            return

        attacker_char = player_characters.get(attacker)
        defender_char = player_characters.get(defender)

        action_desc = ''
        damagePoints = 0
        sp_gain = 0
        revive_message = None
        
        # ||| SKILL ATTACK |||
        if attack_type == 'Skill':
            if current_sp.get(attacker, 0) < 2:
                return
            
            damagePoints = CHARACTER_STATS[attacker_char]['skill_dmg']
            damagePoints = int(damagePoints * combo_multiplier)
            # AHA'S PASSIVE (SKILL VERSION)
            if attacker_char == 'Aha':
                if random.random() < 0.5:
                    damagePoints = 360
                    action_desc = f'flipped HEADS, triggered CRIT'
                else:
                    damagePoints = 120
                    current_sp[attacker] = min(current_sp.get(attacker, 0) + 1, 5) # refund 2 SP but cap at 5
                    action_desc = f'flipped TAILS, crit failed, refunded 1 SP'

            # LAN'S PASSIVE (SKILL VERSION)
            elif attacker_char == 'Lan':
                current_sp_bank = current_sp.get(attacker, 0)
                multiplier = 1.0 + (current_sp_bank * 0.20)
                damagePoints = int(damagePoints * multiplier)
                action_desc = f'triggered CHARGED LUX ARROW with {int(current_sp_bank)} SP'
            else:
                    action_desc = 'used their SKILL'
            current_sp[attacker] -= 2

        # ||| HEAL |||
        elif attack_type == 'Heal':
            # Heal costs 2 SP and restores 150 HP
            if current_sp.get(attacker, 0) < 2:
                return
            
            heal_amount = 150
            current_sp[attacker] -= 2

            max_hp = CHARACTER_STATS[attacker_char]['hp']
            current_hp[attacker] += heal_amount

            # YAOSHI'S PASSIVE
            if attacker_char == 'Yaoshi':
                if current_hp[attacker] > 1500: # !!!!!!! CHANGE THIS LATER !!!!!!
                    current_hp[attacker] = 1500

                if current_hp[attacker] > 1200:
                    action_desc = f'triggered OVERHEAL and restored {heal_amount} HP, exceeding max HP!'
                else:
                    action_desc = f'used HEAL and restored {heal_amount} HP!'
            
            else:
                if current_hp[attacker] > max_hp:
                    current_hp[attacker] = max_hp
                action_desc = f'used HEAL and restored {heal_amount} HP!'
        
        # ||| BASIC ATTACK |||
        else:
            damagePoints = CHARACTER_STATS[attacker_char]['dmg']
            sp_gain = 1

            # AHA'S PASSIVE (BASIC VERSION)
            if attacker_char == 'Aha':
                if random.random() < 0.5:
                    damagePoints *= 2
                    action_desc = f'flipped HEADS, gained 2x multiplier'
                else:
                    damagePoints = 1
                    sp_gain = 2
                    current_sp[defender] = max(0, current_sp.get(defender, 0) - 1) # steal 1 SP from opponent but not go below 0
                    action_desc = f'flipped TAILS, gained 2 SP, stole 1 SP from opponent'
            
            # LAN'S PASSIVE (BASIC VERSION)
            elif attacker_char == 'Lan':
                current_sp_bank = current_sp.get(attacker, 0)
                multiplier = 1.0 + (current_sp_bank * 0.20)
                damagePoints = int(damagePoints * multiplier)
                if current_sp_bank > 0:
                    action_desc = f'triggered CHARGED ARROW with {int(current_sp_bank)} SP'
                
                else: 
                    action_desc = 'used their BASIC attack'

            else:
                action_desc = 'used their BASIC attack'
            
            if current_sp.get(attacker, 0) + sp_gain <= 5:
                current_sp[attacker] += sp_gain
            else:
                current_sp[attacker] = 5
        
        if attack_type != 'Heal':
            current_hp[defender] -= damagePoints
            
            # YAOSHI'S PASSIVE REVIVE
            if current_hp[defender] <= 0:
                if defender_char == 'Yaoshi' and not used_revive.get(defender, False):
                    current_hp[defender] = 1
                    current_sp[defender] = min(current_sp.get(defender, 0) + 2, 5) # add 2 cap at 5
                    used_revive[defender] = True
                    revive_message = f"{defender} triggered REVIVE! Revived with 1 HP and gained 2 SP!"
                else:
                    current_hp[defender] = 0
        
            
        emit('hp_update', {'hp_data': current_hp}, broadcast=True)
        emit('sp_update', {'sp_data': current_sp}, broadcast=True)

        if attack_type == 'Heal':
            emit('game_update', {'message': f'{attacker} {action_desc}! {attacker} now has {current_hp[attacker]} HP.'}, broadcast=True)
        else:
            # announcing attack message first
            emit('game_update', {'message': f'{attacker} {action_desc} and dealt {damagePoints} damage! {defender} has {current_hp[defender]} HP remaining.'}, broadcast=True)
            
            # announcing revive message AFTER if applicable
            if revive_message:
                emit('game_update', {'message': revive_message}, broadcast=True)

        if current_hp[defender] == 0:
            emit ('game_update', {'message': f'{defender} has been defeated! {attacker} wins!'}, broadcast=True)

            emit('match_end', {'message': f'Match ended! {attacker} wins!', 'winner': attacker}, broadcast=True)
        
        else:
            emit('wager_reset', broadcast=True)


@socketio.on('reset_game')
def handle_reset_game():
    print("Resetting game state...")
    # Reset game state variables here
    player_characters.clear()
    current_hp.clear()
    current_wagers.clear()
    current_sp.clear()
    used_revive.clear()
    loss_streaks.clear()
    used_pity_heal.clear()

    emit ('game_reset', {'message': 'Game state has been reset!'}, broadcast=True)
    
if __name__ == '__main__':
    socketio.run(app, debug=True, port=5000)