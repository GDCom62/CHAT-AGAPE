import os, json, datetime, redis
from flask import Flask, render_template, request, url_for, send_from_directory, jsonify
from flask_socketio import SocketIO, emit

app = Flask(__name__, template_folder='templates')
app.secret_key = 'agape_123'
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
    try:
        keys = r.keys("online:*")
        return jsonify([k.replace("online:", "") for k in keys])
    except: return jsonify([])

@app.route('/upload', methods=['POST'])
def upload():
    file = request.files.get('file')
    if file:
        os.makedirs('uploads', exist_ok=True)
        filename = f"{datetime.datetime.now().strftime('%M%S')}_{file.filename}"
        file.save(os.path.join('uploads', filename))
        url = url_for('get_file', filename=filename, _external=True)
        payload = {"user": request.form.get('user'), "text": f'📎 <a href="{url}" target="_blank" style="color:#4f46e5; font-weight:bold;">Arquivo Enviado</a>', "time": "00:00"}
        socketio.emit('receive_message', payload); return jsonify({"ok": True})
    return jsonify({"ok": False}), 400

@app.route('/uploads/<filename>')
def get_file(filename): return send_from_directory('uploads', filename)

@app.route('/logo.png')
def get_logo(): return send_from_directory(os.getcwd(), 'logo.png')

@socketio.on('send_message')
def handle_message(data):
    payload = {"user": data.get('user'), "text": data.get('message'), "time": datetime.datetime.now().strftime("%H:%M")}
    r.rpush("chat:Geral", json.dumps(payload))
    emit('receive_message', payload, broadcast=True)

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=int(os.environ.get("PORT", 8080)))
