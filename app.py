import os
import sqlite3
from flask import Flask, render_template, request, send_from_directory, jsonify
from flask_socketio import SocketIO, emit, join_room
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['SECRET_KEY'] = 'chave_zap_completa'
app.config['UPLOAD_FOLDER'] = 'uploads'
socketio = SocketIO(app, cors_allowed_origins="*")

# Garante que a pasta de uploads exista
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

# --- BANCO DE DADOS ---
def init_db():
    conn = sqlite3.connect('chat_data.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS messages 
                      (id INTEGER PRIMARY KEY AUTOINCREMENT, room TEXT, user TEXT, msg TEXT)''')
    conn.commit()
    conn.close()

def save_msg(room, user, msg):
    conn = sqlite3.connect('chat_data.db')
    cursor = conn.cursor()
    cursor.execute('INSERT INTO messages (room, user, msg) VALUES (?, ?, ?)', (room, user, msg))
    conn.commit()
    conn.close()

def get_history(room):
    conn = sqlite3.connect('chat_data.db')
    cursor = conn.cursor()
    cursor.execute('SELECT user, msg FROM messages WHERE room = ? ORDER BY id ASC', (room,))
    rows = cursor.fetchall()
    conn.close()
    return [{"user": r[0], "msg": r[1]} for r in rows]

# --- ROTAS ---
@app.route('/')
def index():
    user = request.args.get('user', 'Membro')
    room = request.args.get('room', 'Geral')
    return render_template('chat.html', user=user, room=room)

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files: return jsonify({'error': 'Sem arquivo'}), 400
    file = request.files['file']
    if file.filename == '': return jsonify({'error': 'Sem nome'}), 400
    
    filename = secure_filename(file.filename)
    file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
    return jsonify({'url': f'/uploads/{filename}', 'name': filename})

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# --- SOCKETS ---
rooms_users = {}

@socketio.on('join')
def on_join(data):
    user, room, sid = data['user'], data['room'], request.sid
    join_room(room)
    if room not in rooms_users: rooms_users[room] = {}
    rooms_users[room][sid] = user
    emit('load_history', get_history(room))
    emit('update_users', list(set(rooms_users[room].values())), to=room)

@socketio.on('send_message')
def handle_message(data):
    save_msg(data['room'], data['user'], data['msg'])
    emit('receive_message', data, to=data['room'])

@socketio.on('disconnect')
def on_disconnect():
    sid = request.sid
    for room, users in rooms_users.items():
        if sid in users:
            del users[sid]
            emit('update_users', list(set(users.values())), to=room)
            break

if __name__ == '__main__':
    init_db()
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
