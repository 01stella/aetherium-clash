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

CHARACTER_STATS = {
    'Aha': {'hp': 1000, 'dmg': 130, 'speed': 60},
    'Lan': {'hp': 1250, 'dmg': 100, 'speed': 80},
    'Yaoshi': {'hp': 1800, 'dmg': 80, 'speed': 40},
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

                emit('match_start', {
                    'message': 'Match is starting!',
                    'hp_data': current_hp }, broadcast=True)
        else:
            print(f"{user_role} attempted to select an invalid character: {character_name}")
    else:
        print(f"{user_role} attempted to select a character, but is not a player.")

@socketio.on('player_action')
def handle_player_action(data):
    session_id = request.sid
    attacker = connected_players.get(session_id, 'Unknown')

    if attacker in ['Player1', 'Player2']:
        defender = 'Player2' if attacker == 'Player1' else 'Player1'

        if current_hp.get(attacker, 0) <= 0 or current_hp.get(defender, 0) <= 0:
            return

        attacker_char = player_characters.get(attacker)
        damager = CHARACTER_STATS[attacker_char]['dmg']

        current_hp[defender] -= damager

        if current_hp[defender] < 0:
            current_hp[defender] = 0

        emit('game_update', {'message': f'{attacker} ({attacker_char}) performed an action: {data} and dealt {damager} damage!'}, broadcast=True)

        if current_hp[defender] == 0:
            emit ('game_update', {'message': f'{defender} has been defeated! {attacker} wins!'}, broadcast=True)

            emit('match_end', {'message': f'Match ended! {attacker} wins!'}, broadcast=True)
        
        
@socketio.on('submit_wager')
def handle_wager(data):
    session_id = request.sid
    user_role = connected_players.get(session_id, 'Unknown')
    
    if user_role in ['Player1', 'Player2']:
        wager = data.get('wager') # 'Rock', 'Paper', or 'Scissors'
        
        # Save their bet in the vault
        current_wagers[user_role] = wager
        print(f"{user_role} locked in a blind wager.")
        
        # Tell their specific frontend that the bet was received
        emit('wager_received', {'message': 'Wager locked! Waiting for opponent...'}, to=session_id)
        
        if len(current_wagers) == 2:
            print(f"Clash ready! P1: {current_wagers.get('Player1')} vs P2: {current_wagers.get('Player2')}")
            
            # math here later to determine
            
            # Clear the vault for the next round
            current_wagers.clear()

if __name__ == '__main__':
    socketio.run(app, debug=True, port=5000)