@app.route('/')
def index():
    # Isso vai listar os arquivos no log do Railway
    import os
    arquivos_na_raiz = os.listdir('.')
    pasta_templates_existe = os.path.exists('templates')
    conteudo_templates = os.listdir('templates') if pasta_templates_existe else "Pasta não encontrada"

    debug_msg = f"""
    <h1>Diagnóstico do Servidor</h1>
    <p><b>Arquivos na Raiz:</b> {arquivos_na_raiz}</p>
    <p><b>Pasta 'templates' existe?</b> {pasta_templates_existe}</p>
    <p><b>Conteúdo da pasta 'templates':</b> {conteudo_templates}</p>
    <hr>
    <p>Se você vê o 'chat.html' na lista acima, tente <a href="/chat_teste">clicar aqui</a>.</p>
    """
    return debug_msg

@app.route('/chat_teste')
def chat_teste():
    return render_template('chat.html', user="Teste", room="Geral", history=[])
