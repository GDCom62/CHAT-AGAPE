from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit, join_room

app = Flask(__name__)
app.config['SECRET_KEY'] = 'chave_secreta'
socketio = SocketIO(app, cors_allowed_origins="*")

@app.route('/')
def index():
    user = request.args.get('user', 'Membro')
    room = request.args.get('room', 'Geral')
    return render_template('chat.html', user=user, room=room)

# Evento para entrar na sala
@socketio.on('join')
def on_join(data):
    username = data['user']
    room = data['room']
    join_room(room) # Coloca o usuário na sala específica
    print(f"{username} entrou na sala {room}")

# Enviar mensagem apenas para a sala correta
@socketio.on('send_message')
def handle_message(data):
    room = data['room']
    # O parâmetro 'to' garante que só quem está na sala receba
    emit('receive_message', data, to=room)

if __name__ == '__main__':
    socketio.run(app, debug=True)
