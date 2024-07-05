from flask import Flask, render_template, request, redirect, url_for
import sqlite3
from datetime import datetime

app = Flask(__name__)

# Definindo o filtro personalizado
def format_currency(value):
    if value is None or value == '':
        return "R$0,00"
    return f"R${value:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')

app.jinja_env.filters['format_currency'] = format_currency

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

@app.route('/')
def index():
    conn = sqlite3.connect('lojista.db')
    cursor = conn.cursor()
    
    # Seleciona vendas e calcula valor_total considerando o preço dos produtos
    cursor.execute('''
    SELECT vendas.id, vendas.produto_id, vendas.quantidade, vendas.valor_total, vendas.data, produtos.preco, produtos.nome,
           produtos.preco * vendas.quantidade AS valor_produtos
    FROM vendas
    INNER JOIN produtos ON vendas.produto_id = produtos.id
    ''')
    vendas = cursor.fetchall()

    cursor.execute('SELECT * FROM produtos')
    produtos = cursor.fetchall()
    
    conn.close()
    return render_template('index.html', vendas=vendas, produtos=produtos)

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
    produto_id = int(request.form['produto_id'])
    quantidade = int(request.form['quantidade'])
    data = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn = sqlite3.connect('lojista.db')
    cursor = conn.cursor()
    
    # Calcula o valor total da venda baseado no preço do produto e quantidade vendida
    cursor.execute('SELECT preco FROM produtos WHERE id = ?', (produto_id,))
    preco_produto = cursor.fetchone()[0]
    valor_total = preco_produto * quantidade
    
    cursor.execute('INSERT INTO vendas (produto_id, quantidade, valor_total, data) VALUES (?, ?, ?, ?)', (produto_id, quantidade, valor_total, data))
    cursor.execute('UPDATE produtos SET quantidade = quantidade - ? WHERE id = ?', (quantidade, produto_id))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
