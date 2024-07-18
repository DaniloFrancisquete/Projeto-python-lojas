from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
from datetime import date
from functools import wraps

app = Flask(__name__)
app.config['SECRET_KEY'] = 'chave_secreta'

# Inicializa o banco de dados SQLite
def init_db():
    conn = sqlite3.connect('lojista.db')
    cursor = conn.cursor()

    # Criação das tabelas se não existirem
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS usuarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL UNIQUE,
        password TEXT NOT NULL
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS produtos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL,
        preco REAL NOT NULL,
        quantidade INTEGER NOT NULL
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS vendas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        produto_id INTEGER NOT NULL,
        quantidade INTEGER NOT NULL,
        valor_total REAL NOT NULL,
        data TEXT NOT NULL,
        FOREIGN KEY(produto_id) REFERENCES produtos(id)
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS vendas_diarias (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        produto_id INTEGER NOT NULL,
        quantidade INTEGER NOT NULL,
        valor_total REAL NOT NULL,
        data TEXT NOT NULL,
        FOREIGN KEY(produto_id) REFERENCES produtos(id)
    )
    ''')

    # Insere um usuário de exemplo (melhorar para ambiente real)
    cursor.execute('INSERT OR IGNORE INTO usuarios (username, password) VALUES (?, ?)', ('admin', 'password'))
    
    conn.commit()
    conn.close()

# Função para verificar se o usuário está autenticado
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('logged_in'):
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function
    

@app.route('/login', methods=['GET', 'POST'])

def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = sqlite3.connect('lojista.db')
        cursor = conn.cursor()

        cursor.execute('SELECT password FROM usuarios WHERE username = ?', (username,))
        user = cursor.fetchone()

        if user and user[0] == password:
            session['logged_in'] = True
            return redirect(url_for('base'))
        else:
            return 'Credenciais inválidas. Por favor, tente novamente.'

    return render_template('login.html')

@app.route('/index')
@login_required
def base():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    return render_template('index.html')

@app.route('/index')
def index():
    return render_template('index.html')

@app.route('/logout')
def logout():
    session.clear()  # Limpa todas as informações da sessão
    return redirect(url_for('login'))

@app.route('/cadastrar_produto', methods=['GET', 'POST'])
@login_required
def cadastrar_produto():
    if request.method == 'POST':
        nome = request.form['nome']
        preco = float(request.form['preco'])
        quantidade = int(request.form['quantidade'])

        conn = sqlite3.connect('lojista.db')
        cursor = conn.cursor()

        cursor.execute('INSERT INTO produtos (nome, preco, quantidade) VALUES (?, ?, ?)', (nome, preco, quantidade))

        conn.commit()
        conn.close()

        return redirect(url_for('controle_estoque'))

    return render_template('cadastrar_produto.html')

@app.route('/cadastro', methods=['GET', 'POST'])
@login_required
def cadastro():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = sqlite3.connect('lojista.db')
        cursor = conn.cursor()

        cursor.execute('SELECT id FROM usuarios WHERE username = ?', (username,))
        existing_user = cursor.fetchone()

        if existing_user:
            return 'Usuário já existe. Escolha outro nome de usuário.'

        cursor.execute('INSERT INTO usuarios (username, password) VALUES (?, ?)', (username, password))
        conn.commit()
        conn.close()

        return redirect(url_for('login'))

    return render_template('cadastro.html')

@app.route('/excluir_venda/<int:venda_id>', methods=['GET', 'POST'])
@login_required
def excluir_venda(venda_id):
    conn = sqlite3.connect('lojista.db')
    cursor = conn.cursor()

    cursor.execute('DELETE FROM vendas WHERE id = ?', (venda_id,))

    conn.commit()
    conn.close()

    return redirect(url_for('registrar_venda'))

@app.route('/excluir_produto/<int:produto_id>', methods=['GET'])
def excluir_produto(produto_id):
    conn = sqlite3.connect('lojista.db')
    cursor = conn.cursor()

    cursor.execute('DELETE FROM produtos WHERE id = ?', (produto_id,))

    conn.commit()
    conn.close()

    return redirect(url_for('controle_estoque'))


@app.route('/fechar_caixa', methods=['POST'])
@login_required
def fechar_caixa():
    conn = sqlite3.connect('lojista.db')
    cursor = conn.cursor()

    # Obtém todas as vendas registradas hoje
    cursor.execute('SELECT * FROM vendas WHERE data = ?', (date.today().isoformat(),))
    vendas_diarias = cursor.fetchall()

    # Insere as vendas diárias na tabela vendas_diarias
    for venda in vendas_diarias:
        cursor.execute('INSERT INTO vendas_diarias (produto_id, quantidade, valor_total, data) VALUES (?, ?, ?, ?)',
                       (venda[1], venda[2], venda[3], venda[4]))

    # Limpa a tabela de vendas diárias para o próximo dia
    cursor.execute('DELETE FROM vendas WHERE data = ?', (date.today().isoformat(),))

    conn.commit()
    conn.close()

    return redirect(url_for('index'))


@app.route('/editar_produto/<int:produto_id>', methods=['GET', 'POST'])
@login_required
def editar_produto(produto_id):
    if request.method == 'POST':
        nome = request.form['nome']
        preco = float(request.form['preco'])
        quantidade = int(request.form['quantidade'])

        conn = sqlite3.connect('lojista.db')
        cursor = conn.cursor()

        cursor.execute('UPDATE produtos SET nome = ?, preco = ?, quantidade = ? WHERE id = ?', 
                       (nome, preco, quantidade, produto_id))

        conn.commit()
        conn.close()

        return redirect(url_for('controle_estoque'))

    conn = sqlite3.connect('lojista.db')
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM produtos WHERE id = ?', (produto_id,))
    produto = cursor.fetchone()

    conn.close()

    return render_template('editar_produto.html', produto=produto)

@app.route('/editar_venda/<int:venda_id>', methods=['GET', 'POST'])
@login_required
def editar_venda(venda_id):
    if request.method == 'POST':
        quantidade = int(request.form['quantidade'])
        conn = sqlite3.connect('lojista.db')
        cursor = conn.cursor()

        cursor.execute('SELECT produto_id, quantidade FROM vendas WHERE id = ?', (venda_id,))
        venda_atual = cursor.fetchone()
        produto_id = venda_atual[0]
        quantidade_atual = venda_atual[1]

        cursor.execute('SELECT preco FROM produtos WHERE id = ?', (produto_id,))
        preco_unitario = cursor.fetchone()[0]
        valor_total = quantidade * preco_unitario

        cursor.execute('SELECT quantidade FROM produtos WHERE id = ?', (produto_id,))
        estoque_atual = cursor.fetchone()[0]
        novo_estoque = estoque_atual + quantidade_atual - quantidade

        if novo_estoque < 0:
            return "Estoque insuficiente para realizar esta venda."

        cursor.execute('UPDATE produtos SET quantidade = ? WHERE id = ?', (novo_estoque, produto_id))
        cursor.execute('UPDATE vendas SET quantidade = ?, valor_total = ? WHERE id = ?', (quantidade, valor_total, venda_id))

        conn.commit()
        conn.close()

        return redirect(url_for('registrar_venda'))

    conn = sqlite3.connect('lojista.db')
    cursor = conn.cursor()

    cursor.execute('''
    SELECT vendas.id, produtos.nome, vendas.valor_total / vendas.quantidade AS preco_unitario, 
           vendas.valor_total, vendas.quantidade
    FROM vendas
    JOIN produtos ON vendas.produto_id = produtos.id
    WHERE vendas.id = ?
    ''', (venda_id,))
    venda = cursor.fetchone()

    conn.close()

    return render_template('editar_venda.html', venda=venda)

@app.route('/vendas_diarias', methods=['GET', 'POST'])
@login_required
def vendas_diarias():
    conn = sqlite3.connect('lojista.db')
    cursor = conn.cursor()

    cursor.execute('''
        SELECT vendas_diarias.id, produtos.nome, vendas_diarias.quantidade, 
               vendas_diarias.valor_total, vendas_diarias.data
        FROM vendas_diarias
        JOIN produtos ON vendas_diarias.produto_id = produtos.id
    ''')
    vendas_diarias = cursor.fetchall()

    conn.close()

    return render_template('vendas_diarias.html', vendas_diarias=vendas_diarias)


@app.route('/limpar_vendas_diarias', methods=['POST'])
@login_required
def limpar_vendas_diarias():
    conn = sqlite3.connect('lojista.db')
    cursor = conn.cursor()

    cursor.execute('DELETE FROM vendas_diarias')

    conn.commit()
    conn.close()

    return redirect(url_for('vendas_diarias'))


# Função para obter todas as vendas registradas
def obter_vendas():
    conn = sqlite3.connect('lojista.db')
    cursor = conn.cursor()

    cursor.execute('''
    SELECT vendas.id, produtos.nome, vendas.valor_total / vendas.quantidade AS preco_unitario, 
           vendas.valor_total, vendas.quantidade
    FROM vendas
    JOIN produtos ON vendas.produto_id = produtos.id
    ''')
    vendas = cursor.fetchall()

    total_preco = sum(venda[3] for venda in vendas)
    total_quantidade = sum(venda[4] for venda in vendas)

    conn.close()

    return vendas, total_preco, total_quantidade

# Rota para registrar uma nova venda
@app.route('/registrar_venda', methods=['GET', 'POST'])
@login_required
def registrar_venda():
    if request.method == 'POST':
        produto_id = int(request.form['produto_id'])
        quantidade = int(request.form['quantidade'])

        conn = sqlite3.connect('lojista.db')
        cursor = conn.cursor()

        # Verifica se há estoque suficiente para realizar a venda
        cursor.execute('SELECT quantidade FROM produtos WHERE id = ?', (produto_id,))
        estoque_atual = cursor.fetchone()[0]

        if quantidade > estoque_atual:
            return "Estoque insuficiente para realizar esta venda."

        # Obtém o preço unitário do produto
        cursor.execute('SELECT preco FROM produtos WHERE id = ?', (produto_id,))
        preco_unitario = cursor.fetchone()[0]

        # Calcula o valor total da venda
        valor_total = quantidade * preco_unitario

        # Atualiza o estoque do produto
        novo_estoque = estoque_atual - quantidade
        cursor.execute('UPDATE produtos SET quantidade = ? WHERE id = ?', (novo_estoque, produto_id))

        # Insere a venda no banco de dados
        cursor.execute('INSERT INTO vendas (produto_id, quantidade, valor_total, data) VALUES (?, ?, ?, date("now"))',
                       (produto_id, quantidade, valor_total))

        conn.commit()
        conn.close()

        # Redireciona para a mesma página para atualizar os dados
        return redirect(url_for('registrar_venda'))

    # Se for método GET, carrega a página inicial de registro de vendas
    conn = sqlite3.connect('lojista.db')
    cursor = conn.cursor()

    # Obtém todos os produtos disponíveis
    cursor.execute('SELECT * FROM produtos')
    produtos = cursor.fetchall()

    # Obtém todas as vendas registradas
    vendas, total_preco, total_quantidade = obter_vendas()

    conn.close()

    return render_template('registrar_venda.html', produtos=produtos, vendas=vendas, total_preco=total_preco, total_quantidade=total_quantidade)




@app.route('/controle_estoque')
@login_required
def controle_estoque():
    conn = sqlite3.connect('lojista.db')
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM produtos')
    produtos = cursor.fetchall()

    conn.close()

    return render_template('controle_estoque.html', produtos=produtos)

@app.route('/')
def inicial():
    return redirect(url_for('login'))

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
