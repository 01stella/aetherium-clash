from flask import Flask, request
from flask_cors import CORS
from flask_socketio import SocketIO, emit

app = Flask(__name__)
CORS(app)
app.config['SECRET_KEY'] = 'your_secret_key'
socketio = SocketIO(app, cors_allowed_origins="*")

connected_players = {}


@app.route('/')
def index():
    return "Welcome to Aetherium Clash Backend!"

@socketio.on('connect')
def handle_connect():
    session_id = request.sid

    if len(connected_players) == 0:
        role = 'Player1'
    elif len(connected_players) == 1:
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

@socketio.on('player_action')
def handle_player_action(data):
    session_id = request.sid
    user_role = connected_players.get(session_id, 'Unknown')

    print(f"Received action from {user_role} ({session_id}): {data}")
    emit('game_update', {'message': f'{user_role} performed an action: {data}'}, broadcast=True)
    
if __name__ == '__main__':
    socketio.run(app, debug=True, port=5000)