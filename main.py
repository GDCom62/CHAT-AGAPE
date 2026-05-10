import os
import json
import datetime
import redis
from flask import Flask, render_template, request, url_for, send_from_directory, jsonify
from flask_socketio import SocketIO, emit
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'agape_secret_key_123'

# Configuração de Upload de Arquivos
UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Configuração do Redis (Railway pegará da variável de ambiente)
REDIS_URL = os.environ.get('REDIS_URL', 'rediss://default:sua_senha_aqui@calm-kangaroo-116623.upstash.io:6379')
r = redis.from_url(REDIS_URL, decode_responses=True)

# Inicializa o SocketIO com gevent (para evitar o erro do eventlet)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='gevent')

@app.route('/')
def index():
    user = request.args.get('user', 'Irmão')
    room = request.args.get('room', 'Geral')
    
    # Busca histórico do Redis
    try:
        history_raw = r.lrange(f"chat:{room}", 0, -1)
        history = [json.loads(m) for m in history_raw]
    except:
        history = []
        
    return render_template('chat.html', user=user, room=room, history=history)

# Rota para baixar/visualizar arquivos anexados
@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# Rota para processar o upload do arquivo
@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"error": "No file"}), 400
    
    file = request.files['file']
    user = request.form.get('user')
    room = request.form.get('room')
    
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    if file:
        filename = secure_filename(f"{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}_{file.filename}")
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        
        file_url = url_for('uploaded_file', filename=filename, _external=True)
        
        payload = {
            "user": user,
            "text": f'📎 <a href="{file_url}" target="_blank" style="color: #007bff;">Arquivo: {file.filename}</a>',
            "time": datetime.datetime.now().strftime("%H:%M")
        }
        
        # Salva no Redis e avisa o chat
        r.rpush(f"chat:{room}", json.dumps(payload))
        socketio.emit('receive_message', payload)
        
        return jsonify({"status": "success", "url": file_url})

# Evento de recebimento de mensagem via SocketIO
@socketio.on('send_message')
def handle_message(data):
    room = data.get('room', 'Geral')
    payload = {
        "user": data.get('user'),
        "text": data.get('message'),
        "time": datetime.datetime.now().strftime("%H:%M")
    }
    
    r.rpush(f"chat:{room}", json.dumps(payload))
    r.ltrim(f"chat:{room}", -50, -1)
    
    emit('receive_message', payload, broadcast=True)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    socketio.run(app, host='0.0.0.0', port=port)
