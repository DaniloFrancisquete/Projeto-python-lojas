from flask import Flask, render_template, request, redirect, url_for
import sqlite3
from datetime import datetime

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
        data TEXT,
        FOREIGN KEY(produto_id) REFERENCES produtos(id)
    )
    ''')
    conn.commit()
    conn.close()

@app.route('/')
def index():
    conn = sqlite3.connect('lojista.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM produtos')
    produtos = cursor.fetchall()
    cursor.execute('SELECT * FROM vendas')
    vendas = cursor.fetchall()
    conn.close()
    return render_template('index.html', produtos=produtos, vendas=vendas)

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
    cursor.execute('INSERT INTO vendas (produto_id, quantidade, data) VALUES (?, ?, ?)', (produto_id, quantidade, data))
    cursor.execute('UPDATE produtos SET quantidade = quantidade - ? WHERE id = ?', (quantidade, produto_id))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
