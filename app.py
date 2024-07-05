from flask import Flask, render_template, request, redirect, url_for
import sqlite3

app = Flask(__name__)

def init_db():
    conn = sqlite3.connect('lojista.db')
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS produtos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT,
        preco REAL,
        quantidade INTEGER
    )
    ''')
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS vendas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        produto_id INTEGER,
        quantidade INTEGER,
        valor_total REAL,
        data TEXT,
        FOREIGN KEY(produto_id) REFERENCES produtos(id)
    )
    ''')

    # Verifica e adiciona a coluna valor_total se ainda não existir
    cursor.execute("PRAGMA table_info(vendas)")
    columns = cursor.fetchall()
    column_names = [col[1] for col in columns]
    if 'valor_total' not in column_names:
        cursor.execute('ALTER TABLE vendas ADD COLUMN valor_total REAL;')

    conn.commit()
    conn.close()

def format_currency(value):
    if value is None:
        return "R$0,00"

    try:
        numeric_value = float(value)
        return f"R${numeric_value:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
    except (TypeError, ValueError):
        return "Valor inválido"

# Registrando o filtro format_currency no ambiente Jinja2
app.jinja_env.filters['format_currency'] = format_currency

@app.route('/')
def index():
    conn = sqlite3.connect('lojista.db')
    cursor = conn.cursor()

    # Consulta para obter os produtos cadastrados
    cursor.execute('SELECT * FROM produtos')
    produtos = cursor.fetchall()

    # Consulta para obter as vendas por produto com valor total
    cursor.execute('''
    SELECT vendas.id, vendas.produto_id, SUM(vendas.quantidade) as quantidade, SUM(vendas.valor_total) as valor_total, vendas.data, produtos.preco, produtos.nome
    FROM vendas
    INNER JOIN produtos ON vendas.produto_id = produtos.id
    GROUP BY vendas.produto_id
    ''')
    vendas = cursor.fetchall()

    # Consulta para obter o valor total de todas as vendas
    cursor.execute('SELECT SUM(valor_total) FROM vendas')
    soma_total_vendas = cursor.fetchone()[0] or 0.0  # Se não houver vendas, retorna 0.0

    conn.close()

    return render_template('index.html', produtos=produtos, vendas=vendas, soma_total_vendas=soma_total_vendas)

@app.route('/cadastrar_produto', methods=['POST'])
def cadastrar_produto():
    nome = request.form['nome']
    preco = float(request.form['preco'])
    quantidade = int(request.form['quantidade'])

    conn = sqlite3.connect('lojista.db')
    cursor = conn.cursor()
    cursor.execute('INSERT INTO produtos (nome, preco, quantidade) VALUES (?, ?, ?)', (nome, preco, quantidade))
    conn.commit()
    conn.close()

    return redirect(url_for('index'))

@app.route('/registrar_venda', methods=['POST'])
def registrar_venda():
    conn = sqlite3.connect('lojista.db')
    cursor = conn.cursor()

    produto_id = request.form['produto_id']
    quantidade = int(request.form['quantidade'])

    # Obter preço do produto
    cursor.execute('SELECT preco FROM produtos WHERE id = ?', (produto_id,))
    preco = cursor.fetchone()[0]

    # Calcular valor total da venda
    valor_total = quantidade * preco

    # Inserir venda no banco de dados
    cursor.execute('''
    INSERT INTO vendas (produto_id, quantidade, valor_total, data)
    VALUES (?, ?, ?, date('now'))
    ''', (produto_id, quantidade, valor_total))

    conn.commit()
    conn.close()

    return redirect('/')

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
