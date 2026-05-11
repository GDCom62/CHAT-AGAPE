import os
import json
import datetime
import redis
from flask import Flask, render_template, request, url_for, send_from_directory, jsonify
from flask_socketio import SocketIO, emit
from werkzeug.utils import secure_filename

# Configuração flexível: procura na pasta 'templates' ou na raiz '.'
base_dir = os.path.abspath(os.path.dirname(__file__))
dirs = [os.path.join(base_dir, 'templates'), base_dir]

app = Flask(__name__, template_folder=dirs) # Agora ele olha em dois lugares!
app.secret_key = 'agape_secret_key_123'

# --- REDIS ---
REDIS_URL = os.environ.get('REDIS_URL', 'rediss://default:gQAAAAAAAcePAAIgcDFiYzVlZTAzZGZiNTg0OWFlYjUxZDdhY2E3Mzg0ODQ2Mg@calm-kangaroo-116623.upstash.io:6379')
try:
    r = redis.from_url(REDIS_URL, decode_responses=True)
    r.ping()
except:
    r = None

socketio = SocketIO(app, cors_allowed_origins="*", async_mode='gevent')

@app.route('/')
def index():
    user = request.args.get('user', 'Irmão')
    room = request.args.get('room', 'Geral')
    
    # Busca histórico
    history = []
    if r:
        try:
            history_raw = r.lrange(f"chat:{room}", 0, -1)
            history = [json.loads(m) for m in history_raw]
        except: pass
            
    return render_template('chat.html', user=user, room=room, history=history)

# Rota de Upload
@app.route('/upload', methods=['POST'])
def upload_file():
    file = request.files.get('file')
    if file:
        filename = secure_filename(f"{datetime.datetime.now().strftime('%M%S')}_{file.filename}")
        os.makedirs('uploads', exist_ok=True)
        path = os.path.join('uploads', filename)
        file.save(path)
        
        file_url = url_for('uploaded_file', filename=filename, _external=True)
        payload = {"user": request.form.get('user'), "text": f'📎 <a href="{file_url}" target="_blank">Arquivo: {file.filename}</a>', "time": datetime.datetime.now().strftime("%H:%M")}
        
        if r: r.rpush(f"chat:{request.form.get('room')}", json.dumps(payload))
        socketio.emit('receive_message', payload)
        return jsonify({"status": "ok"})
    return jsonify({"error": "fail"}), 400

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory('uploads', filename)

@socketio.on('send_message')
def handle_message(data):
    payload = {"user": data.get('user'), "text": data.get('message'), "time": datetime.datetime.now().strftime("%H:%M")}
    if r: 
        r.rpush(f"chat:{data.get('room')}", json.dumps(payload))
        r.ltrim(f"chat:{data.get('room')}", -50, -1)
    emit('receive_message', payload, broadcast=True)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    socketio.run(app, host='0.0.0.0', port=port)
