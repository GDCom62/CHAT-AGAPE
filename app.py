import os
from flask import Flask, render_template, request

app = Flask(__name__)

@app.route('/')
def index():
    # Isso vai nos dizer se o Flask consegue ver a pasta templates
    user = request.args.get('user', 'Membro')
    room = request.args.get('room', 'Geral')
    
    try:
        return render_template('chat.html', user=user, room=room, history=[])
    except Exception as e:
        return f"<h1>Erro de Template!</h1><p>O Flask nao achou o arquivo: {str(e)}</p><p>Verifique se a pasta se chama 'templates' (minusculo) no GitHub.</p>"

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
