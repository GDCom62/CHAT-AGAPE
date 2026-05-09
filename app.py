import os
import json
import datetime
from flask import Flask, render_template, request, url_for, send_from_directory
from flask_socketio import SocketIO, emit
from werkzeug.utils import secure_filename
import redis

app = Flask(__name__)
app.secret_key = 'agape_secret_key_123'

# Configuração de Upload
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Redis
REDIS_URL = os.environ.get('REDIS_URL', 'sua_url_aqui')
r = redis.from_url(REDIS_URL, decode_responses=True)
socketio = SocketIO(app, cors_allowed_origins="*")

@app.route('/')
def index():
    user = request.args.get('user', 'Irmão')
    room = request.args.get('room', 'Geral')
    history_raw = r.lrange(f"chat:{room}", 0, -1)
    history = [json.loads(m) for m in history_raw]
    return render_template('chat.html', user=user, room=room, history=history)

# Rota para servir os arquivos enviados
@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# Rota para processar o upload
@app.route('/upload', methods=['POST'])
def upload_file():
    file = request.files['file']
    user = request.form.get('user')
    room = request.form.get('room')
    
    if file:
        filename = secure_filename(f"{datetime.datetime.now().timestamp()}_{file.filename}")
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        file_url = url_for('uploaded_file', filename=filename)
        
        payload = {
            "user": user,
            "text": f'<a href="{file_url}" target="_blank">📎 Arquivo: {file.filename}</a>',
            "time": datetime.datetime.now().strftime("%H:%M"),
            "is_file": True
        }
        r.rpush(f"chat:{room}", json.dumps(payload))
        socketio.emit('receive_message', payload)
        return {"status": "ok"}

@socketio.on('send_message')
def handle_message(data):
    room = data.get('room', 'Geral')
    payload = {
        "user": data.get('user'),
        "text": data.get('message'),
        "time": datetime.datetime.now().strftime("%H:%M")
    }
    r.rpush(f"chat:{room}", json.dumps(payload))
    emit('receive_message', payload, broadcast=True)

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000)
