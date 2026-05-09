from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit, join_room, leave_room

app = Flask(__name__)
app.config['SECRET_KEY'] = 'zap_secret'
socketio = SocketIO(app, cors_allowed_origins="*")

# Dicionário para guardar: { 'nome_da_sala': ['User1', 'User2'] }
users_online = {}

@app.route('/')
def index():
    user = request.args.get('user', 'Membro')
    room = request.args.get('room', 'Geral')
    return render_template('chat.html', user=user, room=room)

@socketio.on('join')
def on_join(data):
    user = data['user']
    room = data['room']
    join_room(room)
    
    # Adiciona usuário à lista da sala
    if room not in users_online:
        users_online[room] = []
    if user not in users_online[room]:
        users_online[room].append(user)
    
    # Avisa a sala para atualizar a lista visual
    emit('update_users', users_online[room], to=room)
    print(f"{user} online em {room}")

@socketio.on('disconnect')
def on_disconnect():
    # Lógica simples para remover (em apps reais usaríamos o SID)
    # Para este exemplo, o ideal é atualizar ao sair da página
    pass

if __name__ == '__main__':
    socketio.run(app, debug=True)
