import os
import json
import datetime
import redis
from flask import Flask, render_template, request, url_for, send_from_directory, jsonify
from flask_socketio import SocketIO, emit
from werkzeug.utils import secure_filename

# Configuração do Flask e caminhos
base_dir = os.path.abspath(os.path.dirname(__file__))
template_dir = os.path.join(base_dir, 'templates')

app = Flask(__name__, template_folder=template_dir)
app.secret_key = 'agape_secret_key_123'

# Configuração de Upload
UPLOAD_FOLDER = os.path.join(base_dir, 'uploads')
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Configuração do Redis (Pegando a variável do Railway)
REDIS_URL = os.environ.get('REDIS_URL', 'rediss://default:gQAAAAAAAcePAAIgcDFiYzVlZTAzZGZiNTg0OWFlYjUxZDdhY2E3Mzg0ODQ2Mg@calm-kangaroo-116623.upstash.io:6379')

try:
    r = redis.from_url(REDIS_URL, decode_responses=True)
    r.ping()
    print("✅ Conectado ao Redis com sucesso!")
except Exception as e:
    print(f"❌ Falha no Redis: {e}")
    r = None

# Inicializa o SocketIO com gevent
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='gevent')

# --- ROTA PARA O LOGO ---
@app.route('/logo.png')
def get_logo():
    # Serve o arquivo logo.png da raiz do seu projeto
    return send_from_directory(base_dir, 'logo.png')

# --- ROTAS PRINCIPAIS ---

@app.route('/')
def index():
    user = request.args.get('user', 'Irmão')
    room = request.args.get('room', 'Geral')
    
    history = []
    if r:
        try:
            history_raw = r.lrange(f"chat:{room}", 0, -1)
            history = [json.loads(m) for m in history_raw]
        except Exception as e:
            print(f"Erro ao buscar histórico: {e}")
            
    return render_template('chat.html', user=user, room=room, history=history)

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"error": "Sem arquivo"}), 400
    
    file = request.files['file']
    user = request.form.get('user', 'Anonimo')
    room = request.form.get('room', 'Geral')
    
    if file and file.filename != '':
        filename = secure_filename(f"{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}_{file.filename}")
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        
        file_url = url_for('uploaded_file', filename=filename, _external=True)
        
        payload = {
            "user": user,
            "text": f'📎 <a href="{file_url}" target="_blank" style="color:#818cf8; font-weight:bold;">Arquivo Enviado</a>',
            "time": datetime.datetime.now().strftime("%H:%M")
        }
        
        if r:
            r.rpush(f"chat:{room}", json.dumps(payload))
            r.ltrim(f"chat:{room}", -50, -1)
        
        socketio.emit('receive_message', payload)
        return jsonify({"status": "success", "url": file_url})
    
    return jsonify({"error": "Falha no upload"}), 400

# --- EVENTOS SOCKET.IO ---

@socketio.on('send_message')
def handle_message(data):
    room = data.get('room', 'Geral')
    payload = {
        "user": data.get('user', 'Anonimo'),
        "text": data.get('message'),
        "time": datetime.datetime.now().strftime("%H:%M")
    }
    
    if r:
        try:
            r.rpush(f"chat:{room}", json.dumps(payload))
            r.ltrim(f"chat:{room}", -50, -1)
        except:
            pass
    
    emit('receive_message', payload, broadcast=True)

# --- INICIALIZAÇÃO ---

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8080))
    socketio.run(app, host='0.0.0.0', port=port)
