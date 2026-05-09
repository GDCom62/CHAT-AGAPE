import os
from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit, join_room

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
# Inicializa o SocketIO
socketio = SocketIO(app, cors_allowed_origins="*")

@app.route('/')
def index():
    user = request.args.get('user', 'Membro')
    room = request.args.get('room', 'Geral')
    return render_template('chat.html', user=user, room=room)

# Quando alguém envia uma mensagem
@socketio.on('send_message')
def handle_message(data):
    # 'broadcast=True' envia para todo mundo conectado
    emit('receive_message', data, broadcast=True)

if __name__ == '__main__':
    # Importante: usar socketio.run em vez de app.run
    port = int(os.environ.get('PORT', 5000))
    socketio.run(app, host='0.0.0.0', port=port, debug=True)
