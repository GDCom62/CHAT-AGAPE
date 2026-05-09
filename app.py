import os
import sqlite3
from flask import Flask, render_template, request, send_from_directory, jsonify
from flask_socketio import SocketIO, emit, join_room
from werkzeug.utils import secure_filename

# Configuração de caminhos para o Flask não se perder
base_dir = os.path.abspath(os.path.dirname(__file__))
template_dir = os.path.join(base_dir, 'templates')
upload_dir = os.path.join(base_dir, 'uploads')

app = Flask(__name__, template_folder=template_dir)
app.config['SECRET_KEY'] = 'chave_segura_whatsapp'
app.config['UPLOAD_FOLDER'] = upload_dir

# Inicializa o SocketIO
socketio = SocketIO(app, cors_allowed_origins="*")

# Cria a pasta de uploads se não existir
if not os.path.exists(upload_dir):
    os.makedirs(upload_dir)

# --- BANCO DE DADOS ---
def init_db():
    conn = sqlite3.connect('chat_database.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            room TEXT,
            username TEXT,
            message TEXT
        )
    ''')
    conn.commit()
    conn.close()

# --- ROTAS ---
@app.route('/')
def index():
    user = request.args.get('user', 'Membro')
    room = request.args.get('room', 'Geral')
    return render_template('chat.html', user=user, room=room)

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'Nenhum arquivo'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'Nome vazio'}), 400
    
    filename = secure_filename(file.filename)
    file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
    return jsonify({'url': f'/uploads/{filename}', 'name': filename})

@app.route('/uploads/<filename>')
def serve_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# --- EVENTOS SOCKET.IO ---
@socketio.on('join')
def on_join(data):
    username = data['user']
    room = data['room']
    join_room(room)
    
    # Carrega histórico do banco
    conn = sqlite3.connect('chat_database.db')
    cursor = conn.cursor()
    cursor.execute('SELECT username, message FROM messages WHERE room = ? ORDER BY id ASC', (room,))
    history = [{"user": row[0], "msg": row[1]} for row in cursor.fetchall()]
    conn.close()
    
    emit('load_history', history)

@socketio.on('send_message')
def handle_message(data):
    room = data['room']
    user = data['user']
    msg = data['msg']
    
    # Salva no banco de dados
    conn = sqlite3.connect('chat_database.db')
    cursor = conn.cursor()
    cursor.execute('INSERT INTO messages (room, username, message) VALUES (?, ?, ?)', (room, user, msg))
    conn.commit()
    conn.close()
    
    # Envia para todos na sala
    emit('receive_message', data, to=room)

if __name__ == '__main__':
    init_db()
    print("Servidor rodando em http://127.0.0.1:5000")
    # USAR 127.0.0.1 É ESSENCIAL PARA EVITAR O ERRO DE SEGURANÇA
    socketio.run(app, host='127.0.0.1', port=5000, debug=True)
