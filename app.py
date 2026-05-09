import os
from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit, join_room

app = Flask(__name__)
app.config['SECRET_KEY'] = 'chave_secreta_whatsapp'
socketio = SocketIO(app, cors_allowed_origins="*")

# Armazena usuários: { room: { sid: username } }
rooms_users = {}

@app.route('/')
def index():
    user = request.args.get('user', 'Membro')
    room = request.args.get('room', 'Geral')
    return render_template('chat.html', user=user, room=room)

@socketio.on('join')
def on_join(data):
    username = data['user']
    room = data['room']
    sid = request.sid
    
    join_room(room)
    
    if room not in rooms_users:
        rooms_users[room] = {}
    
    rooms_users[room][sid] = username
    
    # Envia a lista atualizada de nomes (sem duplicados) para a sala
    current_users = list(set(rooms_users[room].values()))
    emit('update_users', current_users, to=room)

@socketio.on('disconnect')
def on_disconnect():
    sid = request.sid
    for room, users in rooms_users.items():
        if sid in users:
            del users[sid]
            current_users = list(set(users.values()))
            emit('update_users', current_users, to=room)
            break

@socketio.on('send_message')
def handle_message(data):
    emit('receive_message', data, to=data['room'])

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    socketio.run(app, host='0.0.0.0', port=port, debug=True)
