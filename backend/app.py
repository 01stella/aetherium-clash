from flask import Flask, request
from flask_cors import CORS
from flask_socketio import SocketIO, emit

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

CHARACTER_STATS = { # for testing purposes hp is lowered
    'Aha': {'hp': 400, 'dmg': 130, 'skill_dmg': 170}, # original hp 1000
    'Lan': {'hp': 550, 'dmg': 100, 'skill_dmg': 140}, # original hp 1250
    'Yaoshi': {'hp': 700, 'dmg': 80, 'skill_dmg': 120}, # original hp 1800
}


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

                emit('match_start', {
                    'message': 'Match is starting!',
                    'hp_data': current_hp,
                    'sp_data': current_sp }, broadcast=True)
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
                else:
                    winner = 'Player2'
                    loser = 'Player1'

                emit('game_update', {'message': f'{winner} wins the RPS round!'}, broadcast=True)
                current_wagers.clear()
                emit('turn_start', {'turn': winner}, broadcast=True)



@socketio.on('player_action')
def handle_player_action(data):
    session_id = request.sid
    attacker = connected_players.get(session_id, 'Unknown')

    if attacker in ['Player1', 'Player2']:
        defender = 'Player2' if attacker == 'Player1' else 'Player1'
        attack_type = data.get('attack_type') # 'Basic' or 'Skill'

        if current_hp.get(attacker, 0) <= 0 or current_hp.get(defender, 0) <= 0:
            return

        attacker_char = player_characters.get(attacker)
        
        if attack_type == 'Skill':
            if current_sp.get(attacker, 0) < 2:
                return
            
            damagePoints = CHARACTER_STATS[attacker_char]['skill_dmg']
            current_sp[attacker] -= 2
            action_desc = 'used their SKILL'
        else:
            damagePoints = CHARACTER_STATS[attacker_char]['dmg']
            if current_sp.get(attacker, 0) < 5:
                current_sp[attacker] += 1
            action_desc = 'performed a BASIC attack'

        current_hp[defender] -= damagePoints
        if current_hp[defender] < 0:
            current_hp[defender] = 0
        
        emit('hp_update', {'hp_data': current_hp}, broadcast=True)
        emit('sp_update', {'sp_data': current_sp}, broadcast=True)

        emit('game_update', {'message': f'{attacker} {action_desc} and dealt {damagePoints} damage! {defender} has {current_hp[defender]} HP remaining.'}, broadcast=True)

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

    emit ('game_reset', {'message': 'Game state has been reset!'}, broadcast=True)
    
if __name__ == '__main__':
    socketio.run(app, debug=True, port=5000)