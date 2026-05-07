import os
import redis
import json
import datetime
from flask import Flask, Response, render_template, request

app = Flask(__name__)
app.secret_key = 'agape_secret_key_123'

# 1. CONFIGURAÇÃO DO REDIS
# Tenta pegar a URL das configurações do Render. Se não houver, usa a sua URL direta.
REDIS_URL = os.environ.get('REDIS_URL', 'rediss://default:gQAAAAAAAcePAAIgcDFiYzVlZTAzZGZiNTg0OWFlYjUxZDdhY2E3Mzg0ODQ2Mg@calm-kangaroo-116623.upstash.io:6379')

try:
    # Conectando ao Redis (SSL ativado automaticamente pelo prefixo rediss://)
    r = redis.from_url(REDIS_URL, decode_responses=True)
    r.ping() # Testa a conexão no início
    print("✅ Conectado ao Redis com sucesso!")
except Exception as e:
    print(f"❌ Erro na conexão Redis: {e}")

# 2. ROTA PRINCIPAL (CARREGA O CHAT)
@app.route('/')
def index():
    # Recebe os dados do Portal Ágape via Link (?user=Nome&room=Geral)
    user = request.args.get('user', 'Membro')
    room = request.args.get('room', 'Geral')
    
    # Busca as últimas 50 mensagens salvas no Redis para mostrar ao entrar
    try:
        history_raw = r.lrange(f"chat:{room}", 0, -1)
        history = [json.loads(m) for m in history_raw]
    except:
        history = []
    
    return render_template('chat.html', user=user, room=room, history=history)

# 3. ROTA PARA POSTAR MENSAGENS
@app.route('/post', methods=['POST'])
def post():
    msg = request.form.get('message')
    user = request.form.get('user')
    room = request.form.get('room')
    
    if msg and msg.strip():
        payload = json.dumps({
            "user": user, 
            "text": msg.strip(), 
            "time": datetime.datetime.now().strftime("%H:%M")
        })
        # Salva na lista do histórico e publica para quem está online agora
        r.rpush(f"chat:{room}", payload)
        r.ltrim(f"chat:{room}", -50, -1) # Mantém apenas as últimas 50 mensagens
        r.publish(f"canal:{room}", payload)
        
    return Response(status=204)

# 4. ROTA DE STREAMING (TEMPO REAL VIA SSE)
@app.route('/stream/<room>')
def stream(room):
    def event_stream():
        pubsub = r.pubsub(ignore_subscribe_messages=True)
        pubsub.subscribe(f"canal:{room}")
        # Envia sinal de "conectado" para o navegador
        yield "data: {\"status\": \"connected\"}\n\n"
        
        for message in pubsub.listen():
            # Sempre que o Redis receber um r.publish, este loop envia para o chat
            yield f"data: {message['data']}\n\n"
            
    return Response(event_stream(), mimetype="text/event-stream")

# 5. INICIALIZAÇÃO
if __name__ == '__main__':
    # O Render exige que o app rode na porta definida por eles ($PORT)
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
