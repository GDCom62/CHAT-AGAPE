import os
import redis
import json
import datetime
from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit

app = Flask(__name__)
app.secret_key = 'agape_secret_key_123'

# Configuração do Redis
REDIS_URL = os.environ.get('REDIS_URL', 'rediss://default:gQAAAAAAAcePAAIgcDFiYzVlZTAzZGZiNTg0OWFlYjUxZDdhY2E3Mzg0ODQ2Mg@calm-kangaroo-116623.upstash.io:6379')
r = redis.from_url(REDIS_URL, decode_responses=True)

# Inicializa o SocketIO (Mais eficiente que EventSource para chat)
socketio = SocketIO(app, cors_allowed_origins="*")

@app.route('/')
def index():
    user = request.args.get('user', 'Irmão')
    room = request.args.get('room', 'Geral')
    
    # Busca histórico (últimas 50 mensagens)
    history_raw = r.lrange(f"chat:{room}", 0, -1)
    history = [json.loads(m) for m in history_raw]
    
    return render_template('chat.html', user=user, room=room, history=history)

# Evento quando alguém envia mensagem via SocketIO
@socketio.on('send_message')
def handle_message(data):
    room = data.get('room', 'Geral')
    payload = {
        "user": data.get('user', 'Anônimo'),
        "text": data.get('message'),
        "time": datetime.datetime.now().strftime("%H:%M")
    }
    
    # Salva no Redis
    r.rpush(f"chat:{room}", json.dumps(payload))
    r.ltrim(f"chat:{room}", -50, -1)
    
    # Envia para todos na sala
    emit('receive_message', payload, broadcast=True)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    # Use socketio.run em vez de app.run
    socketio.run(app, host='0.0.0.0', port=port, debug=True)
