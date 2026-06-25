"""
==============================================================================
Arquivo: cadastro_repo.py
Descrição: Repositório de inserção de dados (Camada de Escrita).

Tratamento de Vulnerabilidades:
Todas as funções neste arquivo utilizam a parametrização de consultas (uso de 
marcadores '%s') para o tratamento de vulnerabilidades provenientes da entrada 
de dados do usuário, prevenindo ativamente ataques de SQL Injection. O motor do 
banco recebe a estrutura SQL e os dados separadamente.

2. Controle Transacional Simples e Tratamento de Erros do SGBD:
Este módulo (operando em conjunto com o helper run_query) contém o coração do 
controle transacional diário. A garantia de atomicidade (ACID) foi implementada 
desativando o autocommit e usando blocos explícitos de try...except...finally 
associados a commit() e rollback(). 

As funções acionam fluxos que interceptam exceções específicas do banco (como 
psycopg2.DatabaseError, violação de chaves primárias ou restrições de FK). 
Caso uma exceção ocorra no nível do SGBD, aplica-se o conn.rollback() para 
proteger a base de dados contra estados corrompidos, e o sistema retorna uma 
mensagem amigável para o frontend. O conn.commit() só é disparado se todas 
as operações da transação derem certo.
==============================================================================
"""

from backend.config.database import run_query

def inserir_ponto_coleta(rua: str, cidade: str, cep: str, estado: str, capacidade_max: float):
    """Cadastra um novo Ponto de Coleta no sistema."""
    # Prevenção de SQL Injection: O SQL puro é definido com '%s'.
    # Nenhuma variável recebida da interface web é concatenada diretamente na string.
    sql = """
        INSERT INTO PontoColeta (Rua, Cidade, CEP, Estado, CapacidadeMax)
        VALUES (%s, %s, %s, %s, %s)
    """
    # A tupla empacota a entrada do usuário para ser sanitizada pelo psycopg2.
    params = (rua, cidade, cep, estado, capacidade_max)
    # Controle Transacional (fetch=False): Avisa a infraestrutura que esta é uma 
    # operação DML (escrita). Se o endereço já existir, o try/except captura a 
    # violação de UNIQUE/PK, faz rollback() e impede que o SGBD trave.
    return run_query(sql, params, fetch=False)

def inserir_lote_coleta(id_lote: int, rua: str, cidade: str, cep: str, estado: str, data_coleta: str):
    """Registra um novo Lote de Coleta originado de um Ponto de Coleta existente."""
    # Validação via SGBD: Ao tentar inserir, o banco verificará a Constraint FK 
    # ligando este lote ao Ponto de Coleta correspondente (Rua, Cidade, CEP, Estado).
    sql = """
        INSERT INTO LoteColeta (IdLote, Rua, Cidade, CEP, Estado, DataColeta)
        VALUES (%s, %s, %s, %s, %s, %s)
    """
    params = (id_lote, rua, cidade, cep, estado, data_coleta)
    # Se a chave estrangeira do Ponto de Coleta não existir no banco, o SGBD 
    # lança uma exceção. O controle transacional faz o rollback(), aborta a inserção 
    # do lote fantasma e o usuário recebe o alerta apropriado no frontend.
    return run_query(sql, params, fetch=False)

def inserir_dispositivo_lote(id_lote: int, dispositivo: str, quantidade: float):
    """Registra a quantidade de um dispositivo eletrônico dentro de um Lote de Coleta."""
    # Operação Associativa: Insere um registro na tabela QtdProdutoLote (N:M).
    sql = """
        INSERT INTO QtdProdutoLote (Lote, DispositivoEletronico, Quantidade)
        VALUES (%s, %s, %s)
    """
    params = (id_lote, dispositivo, quantidade)
    # Atomicidade garantida: O commit() final só será executado se o 'Lote' e o 
    # 'Dispositivo' inseridos existirem previamente no catálogo e a inserção for bem-sucedida.
    return run_query(sql, params, fetch=False)