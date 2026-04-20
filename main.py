import eventlet
eventlet.monkey_patch() # Fix obligatoire pour le déploiement Cloud

from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit, join_room
import time
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'elyptia_central_v3'
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')

# Base de données volatile des agents connectés
AGENTS = {}

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('agent_join')
def on_join(data):
    agent_id = data.get('id')
    AGENTS[agent_id] = {
        'hostname': data.get('hostname', 'Unknown'),
        'ip': data.get('ip', 'Unknown'),
        'status': data.get('status', 'Online'),
        'last_seen': time.time()
    }
    join_room(agent_id)
    print(f"[+] Tactical Agent joined: {agent_id}")
    socketio.emit('update_dashboard', AGENTS)

@socketio.on('dispatch_command')
def on_command(data):
    target = data.get('target')
    command = data.get('command')
    # On dispatche la commande à l'agent (ou à tous)
    if target == 'all':
        socketio.emit('execute_command', {'cmd': command, 'time': time.strftime('%H:%M:%S')})
    else:
        socketio.emit('execute_command', {'cmd': command, 'time': time.strftime('%H:%M:%S')}, room=target)

@socketio.on('agent_response')
def on_response(data):
    # On renvoie la réponse vers le Dashboard (index.html)
    socketio.emit('display_response', data)

@socketio.on('disconnect')
def on_disconnect():
    # Ici on peut gérer le passage en offline si besoin
    pass

if __name__ == '__main__':
    # Le port est défini dynamiquement par Railway (8080 par défaut)
    port = int(os.environ.get("PORT", 80))
    socketio.run(app, host='0.0.0.0', port=port)
