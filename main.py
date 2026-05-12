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
    room = request.args.get('room', 'Geral')
    history = [json.loads(m) for m in r.lrange(f"chat:{room}", 0, -1)] if r else []
    return render_template('chat.html', user=user, room=room, history=history)

@app.route('/usuarios')
def listar_usuarios():
    # Busca a lista de membros que o Portal salvou no Redis
    try:
        membros = list(r.smembers("agape_membros_online"))
        return jsonify(membros)
    except: return jsonify([])

@app.route('/logo.png')
def get_logo(): return send_from_directory(os.getcwd(), 'logo.png')

@socketio.on('send_message')
def handle_message(data):
    payload = {"user": data.get('user'), "text": data.get('message'), "time": datetime.datetime.now().strftime("%H:%M")}
    if r: r.rpush(f"chat:{data.get('room', 'Geral')}", json.dumps(payload))
    emit('receive_message', payload, broadcast=True)

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=int(os.environ.get("PORT", 8080)))
