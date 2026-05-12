import os, json, datetime, redis
from flask import Flask, render_template, request, url_for, send_from_directory, jsonify
from flask_socketio import SocketIO, emit

app = Flask(__name__, template_folder='templates')
app.secret_key = 'agape_chat_123'
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='gevent')

REDIS_URL = os.environ.get('REDIS_URL', 'rediss://default:gQAAAAAAAcePAAIgcDFiYzVlZTAzZGZiNTg0OWFlYjUxZDdhY2E3Mzg0ODQ2Mg@calm-kangaroo-116623.upstash.io:6379')
r = redis.from_url(REDIS_URL, decode_responses=True)

@app.route('/')
def index():
    user = request.args.get('user', 'Irmão')
    r.set(f"online:{user}", "online", ex=60)
    history = [json.loads(m) for m in r.lrange("chat:Geral", 0, -1)]
    return render_template('chat.html', user=user, history=history)

@app.route('/usuarios')
def listar_usuarios():
    keys = r.keys("online:*")
    membros = [k.split(":")[1] for k in keys]
    return jsonify(membros)

@socketio.on('typing')
def handle_typing(data):
    # Envia para todos que o usuário X está digitando
    emit('is_typing', {'user': data['user'], 'typing': data['typing']}, broadcast=True, include_self=False)

@socketio.on('send_message')
def handle_message(data):
    payload = {"user": data.get('user'), "text": data.get('message'), "time": datetime.datetime.now().strftime("%H:%M")}
    r.rpush("chat:Geral", json.dumps(payload))
    emit('receive_message', payload, broadcast=True)

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=int(os.environ.get("PORT", 8080)))
