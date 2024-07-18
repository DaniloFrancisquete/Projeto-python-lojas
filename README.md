Sistema de Gestão de Loja com Flask
Este é um projeto de sistema de gestão de loja desenvolvido em Python utilizando o framework Flask e SQLite para persistência de dados.

Funcionalidades Principais
Autenticação de Usuários: Login seguro e cadastro de novos usuários.
Cadastro de Produtos: Adição, edição e exclusão de produtos com nome, preço e quantidade.
Registro de Vendas: Registro de vendas com controle de estoque automático e cálculo do valor total.
Controle de Estoque: Visualização atualizada dos produtos disponíveis.
Relatórios Diários: Geração automática de relatórios diários de vendas.
Segurança: Utilização de chave secreta para proteger sessões de usuário.
Estrutura do Projeto
app.py: Arquivo principal contendo as rotas e a lógica do sistema.
lojista.db: Banco de dados SQLite para armazenamento de usuários, produtos, vendas e vendas diárias.
static/: Diretório para arquivos estáticos como CSS, JavaScript, etc.
templates/: Diretório contendo os templates HTML renderizados pelo Jinja2.
Configuração e Execução
Instalação de Dependências:

bash
Copiar código
pip install flask
Inicialização do Banco de Dados:

bash
Copiar código
python app.py
