import os
import psycopg2
import psycopg2.extras
from dotenv import load_dotenv

# Carrega as variáveis de ambiente do arquivo .env
load_dotenv()

# Configuração centralizada obtida com segurança através do ambiente
DB_CONFIG = {
    "host":     os.environ.get("DB_HOST",     "localhost"),
    "port":     int(os.environ.get("DB_PORT", "5432")),
    "dbname":   os.environ.get("DB_NAME",     "eletroreverso"),
    "user":     os.environ.get("DB_USER",     "postgres"),
    "password": os.environ.get("DB_PASSWORD", ""),
}

def get_conn():
    """Abre uma conexão com o PostgreSQL garantindo autocommit desativado para o controle transacional."""
    conn = psycopg2.connect(**DB_CONFIG)
    conn.autocommit = False
    return conn

def run_query(sql: str, params: tuple = (), fetch: bool = True):
    """
    Executa uma query parametrizada com controle transacional explícito.
    - Se a operação for bem-sucedida, realiza o COMMIT.
    - Se houver erro no SGBD, realiza o ROLLBACK para evitar inconsistências.
    
    Toda a parametrização via '%s' previne contra ataques de SQL Injection.
    """
    conn = get_conn()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(sql, params)
            if fetch and cur.description:
                columns = [desc[0] for desc in cur.description]
                rows = [list(row.values()) for row in cur.fetchall()]
                conn.commit()
                return {"columns": columns, "rows": rows}
            
            affected = cur.rowcount
            conn.commit()
            return {"affected": affected}
    except psycopg2.Error as e:
        conn.rollback()
        msg = e.pgerror.strip() if e.pgerror else str(e)
        raise RuntimeError(f"[{e.pgcode}] {msg}")
    finally:
        conn.close()