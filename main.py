import os, json, datetime, redis, sqlite3
from flask import Flask, render_template, request, url_for, send_from_directory, jsonify
from flask_socketio import SocketIO, emit

app = Flask(__name__, template_folder='templates')
app.secret_key = 'agape_123'
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='gevent')

REDIS_URL = os.environ.get('REDIS_URL', 'sua_url_aqui')
r = redis.from_url(REDIS_URL, decode_responses=True)

@app.after_request
def add_header(response):
    response.headers['X-Frame-Options'] = 'ALLOWALL'
    return response

@app.route('/')
def index():
    user = request.args.get('user', 'Irmão')
    room = request.args.get('room', 'Geral')
    history = [json.loads(m) for m in r.lrange(f"chat:{room}", 0, -1)] if r else []
    return render_template('chat.html', user=user, room=room, history=history)

@app.route('/usuarios')
def listar_usuarios():
    try:
        conn = sqlite3.connect('agape_v60.db')
        usuarios = [row[0] for row in conn.execute("SELECT nome FROM membros").fetchall()]
        conn.close()
        return jsonify(usuarios)
    except: return jsonify([])

@app.route('/logo.png')
def get_logo(): return send_from_directory(os.getcwd(), 'logo.png')

@app.route('/upload', methods=['POST'])
def upload():
    file = request.files.get('file')
    if file:
        os.makedirs('uploads', exist_ok=True)
        filename = f"{datetime.datetime.now().strftime('%M%S')}_{file.filename}"
        file.save(os.path.join('uploads', filename))
        url = url_for('get_file', filename=filename, _external=True)
        payload = {"user": request.form.get('user'), "text": f'📎 <a href="{url}" target="_blank">Arquivo</a>', "time": "00:00"}
        socketio.emit('receive_message', payload); return jsonify({"ok": True})
    return jsonify({"ok": False}), 400

@app.route('/uploads/<filename>')
def get_file(filename): return send_from_directory('uploads', filename)

@socketio.on('send_message')
def handle_message(data):
    payload = {"user": data.get('user'), "text": data.get('message'), "time": datetime.datetime.now().strftime("%H:%M")}
    if r: r.rpush(f"chat:{data.get('room', 'Geral')}", json.dumps(payload))
    emit('receive_message', payload, broadcast=True)

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=int(os.environ.get("PORT", 8080)))
