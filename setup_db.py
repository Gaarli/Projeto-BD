import os
import psycopg2
from dotenv import load_dotenv

# Carrega as credenciais do .env
load_dotenv()

DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "eletroreverso")

print(2)

def executar_setup():
    print("Iniciando configuração do banco de dados...")

    # 1. Conecta no banco padrão (postgres) para criar o banco do projeto
    try:
        conn = psycopg2.connect(dbname="postgres", user=DB_USER, password=DB_PASSWORD, host=DB_HOST, port=DB_PORT)
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

    # 2. Conecta no novo banco para rodar o esquema e os dados
    try:
        conn = psycopg2.connect(dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD, host=DB_HOST, port=DB_PORT)
        cur = conn.cursor()

        with open("sql/esquema.sql", "r", encoding="utf-8") as f:
            cur.execute(f.read())
        print("✅ Tabelas criadas (esquema.sql executado).")

        with open("sql/dados.sql", "r", encoding="utf-8") as f:
            cur.execute(f.read())
        print("✅ Dados fictícios inseridos (dados.sql executado).")

        conn.commit()
        print("🚀 Setup do banco concluído! O sistema já pode ser iniciado.")
    except Exception as e:
        conn.rollback()
        print(f"❌ Erro ao rodar os scripts SQL: {e}")
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    executar_setup()