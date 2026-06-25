"""
==============================================================================
Arquivo: setup_db.py
Descrição: Script de automação de infraestrutura (Setup do Banco de Dados).
Objetivo: Recriar a base de dados do zero, aplicar o esquema relacional (DDL) 
          e inserir os dados iniciais (DML) de forma automatizada e previsível.
==============================================================================
"""

import os
import psycopg2
from dotenv import load_dotenv

# Carrega as credenciais do .env
# Por que: Isola dados sensíveis (senhas e usuários) do código-fonte. 
# É uma prática fundamental de segurança de software e facilita a implantação
# em diferentes ambientes (desenvolvimento vs. produção).
load_dotenv()

DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "eletroreverso")

print(2)

def executar_setup():
    print("Iniciando configuração do banco de dados...")

    # ==============================================================================
    # FASE 1: Recriação do Banco de Dados
    # Como e Por que: Para deletar e criar um banco no PostgreSQL, a conexão não 
    # pode estar associada ao próprio banco que será apagado. Por isso, 
    # conectamos obrigatoriamente no banco administrativo padrão chamado "postgres".
    # ==============================================================================
    try:
        conn = psycopg2.connect(dbname="postgres", user=DB_USER, password=DB_PASSWORD, host=DB_HOST, port=DB_PORT)
        
        # Por que autocommit = True? O PostgreSQL proíbe a execução de comandos DDL 
        # estruturais como 'CREATE DATABASE' e 'DROP DATABASE' dentro de blocos de 
        # transação padrão (BEGIN/COMMIT). O autocommit força o envio imediato da query.
        conn.autocommit = True # Necessário para criar bancos de dados
        cur = conn.cursor()
        
        cur.execute(f"DROP DATABASE IF EXISTS {DB_NAME}")
        cur.execute(f"CREATE DATABASE {DB_NAME}")
        print(f"✅ Banco de dados '{DB_NAME}' recriado com sucesso.")
        
        cur.close()
        conn.close()
    except Exception as e:
        print(f"❌ Erro ao criar o banco: {e}")
        return

    # ==============================================================================
    # FASE 2: Aplicação do Esquema (DDL) e Povoamento (DML)
    # Como e Por que: Agora que o banco 'eletroreverso' existe e está limpo, abrimos 
    # uma nova conexão apontando diretamente para ele. Aqui, o autocommit é desativado 
    # por padrão no psycopg2, permitindo o controle transacional explícito.
    # ==============================================================================
    try:
        conn = psycopg2.connect(dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD, host=DB_HOST, port=DB_PORT)
        cur = conn.cursor()

        # Leitura e execução do script de Definição de Dados (Criação de Tabelas)
        # Por que open(): Mantém o código Python limpo ao isolar os comandos SQL 
        # brutos em arquivos .sql separados, facilitando a manutenção e avaliação.
        with open("sql/esquema.sql", "r", encoding="utf-8") as f:
            cur.execute(f.read())
        print("✅ Tabelas criadas (esquema.sql executado).")

        # Leitura e execução do script de Manipulação de Dados (Carga Inicial)
        with open("sql/dados.sql", "r", encoding="utf-8") as f:
            cur.execute(f.read())
        print("✅ Dados fictícios inseridos (dados.sql executado).")

        # Controle Transacional (ACID - Atomicidade)
        # O commit consolida a criação do esquema e a inserção dos dados de uma só vez.
        conn.commit()
        print("🚀 Setup do banco concluído! O sistema já pode ser iniciado.")
    except Exception as e:
        # Se qualquer erro ocorrer (ex: erro de sintaxe SQL ou falha de chave estrangeira),
        # o rollback desfaz tudo, impedindo que o banco fique em um estado corrompido/pela metade.
        conn.rollback()
        print(f"❌ Erro ao rodar os scripts SQL: {e}")
    finally:
        # Prevenção de vazamento de recursos (Resource Leak)
        # O bloco finally assegura que a conexão será fechada e devolvida ao SGBD, 
        # independentemente de o processo ter sido um sucesso ou um fracasso no try/except.
        cur.close()
        conn.close()

# Garante que o script só execute a orquestração se for chamado diretamente pelo terminal
if __name__ == "__main__":
    executar_setup()