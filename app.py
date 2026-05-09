import os
import sqlite3
from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit, join_room

app = Flask(__name__)
app.config['SECRET_KEY'] = 'chave_zap_persistente'
socketio = SocketIO(app, cors_allowed_origins="*")

# --- LÓGICA DO BANCO DE DATAS ---
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

def save_message(room, user, msg):
    conn = sqlite3.connect('chat_database.db')
    cursor = conn.cursor()
    cursor.execute('INSERT INTO messages (room, username, message) VALUES (?, ?, ?)', (room, user, msg))
    conn.commit()
    conn.close()

def get_history(room):
    conn = sqlite3.connect('chat_database.db')
    cursor = conn.cursor()
    cursor.execute('SELECT username, message FROM messages WHERE room = ? ORDER BY id ASC', (room,))
    rows = cursor.fetchall()
    conn.close()
    return [{"user": row[0], "msg": row[1]} for row in rows]

# --- ROTAS E SOCKETS ---
rooms_users = {}

@app.route('/')
def index():
    user = request.args.get('user', 'Membro')
    room = request.args.get('room', 'Geral')
    return render_template('chat.html', user=user, room=room)

@socketio.on('join')
def on_join(data):
    username = data['user']
    room = data['room']
    sid = request.sid
    join_room(room)
    
    # Gerencia usuários online
    if room not in rooms_users: rooms_users[room] = {}
    rooms_users[room][sid] = username
    
    # 1. Envia histórico do banco para quem acabou de entrar
    history = get_history(room)
    emit('load_history', history)
    
    # 2. Atualiza lista de usuários
    current_users = list(set(rooms_users[room].values()))
    emit('update_users', current_users, to=room)

@socketio.on('send_message')
def handle_message(data):
    # Salva no banco de dados antes de espalhar para a sala
    save_message(data['room'], data['user'], data['msg'])
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
    init_db() # Cria o arquivo .db se não existir
    port = int(os.environ.get('PORT', 5000))
    socketio.run(app, host='0.0.0.0', port=port, debug=True)
