import os
import sqlite3
from flask import Flask, render_template, request, send_from_directory, jsonify
from flask_socketio import SocketIO, emit, join_room
from werkzeug.utils import secure_filename

# Configuração para garantir que o Flask ache a pasta templates
base_dir = os.path.abspath(os.path.dirname(__file__))
app = Flask(__name__, 
            template_folder=os.path.join(base_dir, 'templates'),
            static_folder=os.path.join(base_dir, 'uploads'))

app.config['SECRET_KEY'] = 'chave_mestra_123'
app.config['UPLOAD_FOLDER'] = os.path.join(base_dir, 'uploads')
socketio = SocketIO(app, cors_allowed_origins="*")

if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

def init_db():
    conn = sqlite3.connect('database.db')
    conn.execute('CREATE TABLE IF NOT EXISTS msgs (id INTEGER PRIMARY KEY AUTOINCREMENT, room TEXT, user TEXT, msg TEXT)')
    conn.close()

@app.route('/')
def index():
    user = request.args.get('user', 'Membro')
    room = request.args.get('room', 'Geral')
    return render_template('chat.html', user=user, room=room)

@app.route('/upload', methods=['POST'])
def upload():
    if 'file' not in request.files: return jsonify({'err': 'no file'}), 400
    file = request.files['file']
    fname = secure_filename(file.filename)
    file.save(os.path.join(app.config['UPLOAD_FOLDER'], fname))
    return jsonify({'url': f'/uploads/{fname}', 'name': fname})

@app.route('/uploads/<filename>')
def files(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@socketio.on('join')
def on_join(data):
    room = data['room']
    join_room(room)
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('SELECT user, msg FROM msgs WHERE room = ? ORDER BY id ASC', (room,))
    emit('load_history', [{"user": r[0], "msg": r[1]} for r in cursor.fetchall()])
    conn.close()

@socketio.on('send_message')
def handle(data):
    conn = sqlite3.connect('database.db')
    conn.execute('INSERT INTO msgs (room, user, msg) VALUES (?, ?, ?)', (data['room'], data['user'], data['msg']))
    conn.commit()
    conn.close()
    emit('receive_message', data, to=data['room'])

if __name__ == '__main__':
    init_db()
    # Usando 127.0.0.1 para evitar erros de segurança do Chrome
    socketio.run(app, host='127.0.0.1', port=5000, debug=True)
