from flask import Flask
from flask_cors import CORS
from flask_socketio import SocketIO, emit

app = Flask(__name__)
CORS(app)
app.config['SECRET_KEY'] = 'your_secret_key'
socketio = SocketIO(app, cors_allowed_origins="*")

@app.route('/')
def index():
    return "Welcome to Aetherium Clash Backend!"

@socketio.on('connect')
def test_connect():
    print('Client connected')
    emit('response', {'message': 'Connected to Aetherium Clash Backend!'}
    )

@socketio.on('player_action')
def handle_player_action(data):
    print(f"Received player action: {data}")
    # Process the player action and update game state accordingly
    # For example, you can broadcast the updated game state to all clients
    emit('game_update', {'message': 'Game state updated!'}, broadcast=True)

if __name__ == '__main__':
    socketio.run(app, debug=True, port=5000)