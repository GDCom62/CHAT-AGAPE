import os
import redis
import json
import datetime
from flask import Flask, Response, render_template, request

app = Flask(__name__)
app.secret_key = 'agape_secret_key_123'

# CONFIGURAÇÃO REDIS VIA URL (Sua URL do Upstash)
# O código tenta pegar a URL do ambiente (configuração no Render) ou usa a sua fixa
REDIS_URL = os.environ.get('REDIS_URL', 'rediss://default:gQAAAAAAAcePAAIgcDFiYzVlZTAzZGZiNTg0OWFlYjUxZDdhY2E3Mzg0ODQ2Mg@calm-kangaroo-116623.upstash.io:6379')

# Conecta ao Redis usando a URL completa
r = redis.from_url(REDIS_URL, decode_responses=True)

@app.route('/')
def index():
    user = request.args.get('user', 'Irmão')
    room = request.args.get('room', 'Geral')
    
    # Busca histórico das últimas 50 mensagens
    history_raw = r.lrange(f"chat:{room}", 0, -1)
    history = [json.loads(m) for m in history_raw]
    
    return render_template('chat.html', user=user, room=room, history=history)

@app.route('/post', methods=['POST'])
def post():
    msg = request.form.get('message')
    user = request.form.get('user')
    room = request.form.get('room')
    
    if msg:
        payload = json.dumps({
            "user": user, 
            "text": msg, 
            "time": datetime.datetime.now().strftime("%H:%M")
        })
        r.rpush(f"chat:{room}", payload)
        r.ltrim(f"chat:{room}", -50, -1)
        r.publish(f"canal:{room}", payload)
        
    return Response(status=204)

@app.route('/stream/<room>')
def stream(room):
    def event_stream():
        pubsub = r.pubsub(ignore_subscribe_messages=True)
        pubsub.subscribe(f"canal:{room}")
        yield "data: {\"status\": \"connected\"}\n\n"
        for message in pubsub.listen():
            yield f"data: {message['data']}\n\n"
            
    return Response(event_stream(), mimetype="text/event-stream")

if __name__ == '__main__':
    # Mudamos de 0.0.0.0 para 127.0.0.1 para evitar o erro de segurança do Chrome
    socketio.run(app, host='127.0.0.1', port=5000, debug=True)

    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
