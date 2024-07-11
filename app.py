from flask import Flask, render_template, request, redirect, url_for
import sqlite3
from datetime import date


app = Flask(__name__)
app.config['SECRET_KEY'] = 'chave_secreta'

# Inicializa o banco de dados SQLite
def init_db():
    conn = sqlite3.connect('lojista.db')
    cursor = conn.cursor()
    
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
    
    conn.commit()
    conn.close()

# Função para cadastrar um novo produto no banco de dados
@app.route('/cadastrar_produto', methods=['GET', 'POST'])
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
        
        return redirect(url_for('index'))
    
    return render_template('cadastrar_produto.html')

# Função para excluir um produto do banco de dados
@app.route('/excluir_produto/<int:produto_id>', methods=['POST'])
def excluir_produto(produto_id):
    conn = sqlite3.connect('lojista.db')
    cursor = conn.cursor()
    
    cursor.execute('DELETE FROM produtos WHERE id = ?', (produto_id,))
    
    conn.commit()
    conn.close()
    
    return redirect(url_for('registrar_venda'))

# Função para fechar o dia e gerar relatório
@app.route('/fechar_dia', methods=['POST'])
def fechar_dia():
    conn = sqlite3.connect('lojista.db')
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM vendas WHERE data = date("now")')
    vendas_do_dia = cursor.fetchall()
    
    for venda in vendas_do_dia:
        cursor.execute('INSERT INTO vendas_diarias (produto_id, quantidade, valor_total, data) VALUES (?, ?, ?, ?)',
                       (venda[1], venda[2], venda[3], venda[4]))
    
    conn.commit()
    conn.close()
    
    return redirect(url_for('gerar_relatorio'))

# Função para obter vendas realizadas
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
    
    conn.close()
    
    return vendas

# Função para registrar uma venda e atualizar o estoque
@app.route('/registrar_venda', methods=['GET', 'POST'])
def registrar_venda():
    if request.method == 'POST':
        produto_id = int(request.form['produto_id'])
        quantidade = int(request.form['quantidade'])
        
        conn = sqlite3.connect('lojista.db')
        cursor = conn.cursor()
        
        cursor.execute('SELECT quantidade FROM produtos WHERE id = ?', (produto_id,))
        estoque_atual = cursor.fetchone()[0]
        
        if quantidade > estoque_atual:
            return "Estoque insuficiente para realizar esta venda."
        
        cursor.execute('SELECT preco FROM produtos WHERE id = ?', (produto_id,))
        preco_unitario = cursor.fetchone()[0]
        valor_total = quantidade * preco_unitario
        
        novo_estoque = estoque_atual - quantidade
        cursor.execute('UPDATE produtos SET quantidade = ? WHERE id = ?', (novo_estoque, produto_id))
        
        cursor.execute('INSERT INTO vendas (produto_id, quantidade, valor_total, data) VALUES (?, ?, ?, date("now"))',
                       (produto_id, quantidade, valor_total))
        
        conn.commit()
        conn.close()
        
        return redirect(url_for('registrar_venda'))
    
    conn = sqlite3.connect('lojista.db')
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM produtos')
    produtos = cursor.fetchall()
    
    vendas = obter_vendas()
    
    conn.close()
    
    return render_template('registrar_venda.html', produtos=produtos, vendas=vendas)

# Função para gerar relatórios de produtos e vendas
@app.route('/gerar_relatorio')
def gerar_relatorio():
    conn = sqlite3.connect('lojista.db')
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM vendas WHERE data = date("now")')
    vendas_do_dia = cursor.fetchall()
    
    cursor.execute('''
    SELECT data, COUNT(id) AS total_vendas, SUM(valor_total) AS total_valor
    FROM vendas
    WHERE strftime('%Y-%m', data) = strftime('%Y-%m', date('now'))
    GROUP BY data
    ''')
    vendas_do_mes = cursor.fetchall()
    
    conn.close()
    
    vendas_do_mes = [
        (data, total_vendas, float(total_valor) if total_valor is not None else 0.0)
        for data, total_vendas, total_valor in vendas_do_mes
    ]
    
    return render_template('gerar_relatorio.html', vendas_do_dia=vendas_do_dia, vendas_do_mes=vendas_do_mes)

# Função para exibir o controle de estoque
@app.route('/controle_estoque')
def controle_estoque():
    conn = sqlite3.connect('lojista.db')
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM produtos')
    produtos = cursor.fetchall()
    
    conn.close()
    
    return render_template('controle_estoque.html', produtos=produtos)



@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
