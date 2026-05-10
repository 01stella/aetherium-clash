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
        if character_name in CHARACTER_STATS:
            player_characters[user_role] = character_name
            print(f"{user_role} selected character: {character_name}")
            emit('game_update', {'message': f'{user_role} selected {character_name}'}, broadcast=True)
        else:
            print(f"{user_role} attempted to select an invalid character: {character_name}")
    else:
        print(f"{user_role} attempted to select a character, but is not a player.")

@socketio.on('player_action')
def handle_player_action(data):
    session_id = request.sid
    user_role = connected_players.get(session_id, 'Unknown')

    print(f"Received action from {user_role} ({session_id}): {data}")
    emit('game_update', {'message': f'{user_role} performed an action: {data}'}, broadcast=True)

if __name__ == '__main__':
    socketio.run(app, debug=True, port=5000)