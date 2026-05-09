import os
import sqlite3
from flask import Flask, render_template, request, send_from_directory, jsonify
from flask_socketio import SocketIO, emit, join_room
from werkzeug.utils import secure_filename

# 1. Configurações de Caminho (Garante que o Flask ache as pastas)
base_dir = os.path.abspath(os.path.dirname(__file__))
template_dir = os.path.join(base_dir, 'templates')
upload_dir = os.path.join(base_dir, 'uploads')

app = Flask(__name__, template_folder=template_dir)
app.config['SECRET_KEY'] = 'zap_python_secret_99'
app.config['UPLOAD_FOLDER'] = upload_dir

# 2. Inicializa o SocketIO (Para mensagens em tempo real)
socketio = SocketIO(app, cors_allowed_origins="*")

# 3. Cria a pasta de uploads se ela não existir
if not os.path.exists(upload_dir):
    os.makedirs(upload_dir)

# 4. Banco de Dados (Salva o histórico das conversas)
def init_db():
    db_path = os.path.join(base_dir, 'chat_database.db')
    conn = sqlite3.connect(db_path)
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

# 5. Rotas do Site
@app.route('/')
def index():
    user = request.args.get('user', 'Membro')
    room = request.args.get('room', 'Geral')
    return render_template('chat.html', user=user, room=room)

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'Sem arquivo'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'Nome vazio'}), 400
    
    filename = secure_filename(file.filename)
    file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
    return jsonify({'url': f'/uploads/{filename}', 'name': filename})

@app.route('/uploads/<filename>')
def serve_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# 6. Eventos do Chat (Socket.IO)
@socketio.on('join')
def on_join(data):
    username = data['user']
    room = data['room']
    join_room(room)
    
    # Carrega histórico do banco de dados ao entrar
    db_path = os.path.join(base_dir, 'chat_database.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('SELECT username, message FROM messages WHERE room = ? ORDER BY id ASC', (room,))
    history = [{"user": row[0], "msg": row[1]} for row in cursor.fetchall()]
    conn.close()
    
    # Envia o histórico apenas para quem acabou de entrar
    emit('load_history', history)

@socketio.on('send_message')
def handle_message(data):
    room = data['room']
    user = data['user']
    msg = data['msg']
    
    # Salva a nova mensagem no banco
    db_path = os.path.join(base_dir, 'chat_database.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('INSERT INTO messages (room, username, message) VALUES (?, ?, ?)', (room, user, msg))
    conn.commit()
    conn.close()
    
    # Envia a mensagem em tempo real para todos na sala
    emit('receive_message', data, to=room)

# 7. Início do Servidor
if __name__ == '__main__':
    init_db()
    print("\n" + "="*50)
    print("SERVIDOR INICIADO COM SUCESSO!")
    print("Acesse no Chrome: http://127.0.0")
    print("="*50 + "\n")
    
    # IMPORTANTE: host='127.0.0.1' evita o erro ERR_CONNECTION_TIMED_OUT
    socketio.run(app, host='127.0.0.1', port=5000, debug=True)
