"""
EletroReverso — Backend (Flask + psycopg2)
SCC0240 - Bases de Dados | USP ICMC | 1º Semestre 2026

Arquivo : backend/app.py
Função  : Servidor HTTP com rotas para cadastro e consultas ao PostgreSQL.
          Toda comunicação com o banco usa queries parametrizadas (%s),
          protegendo contra SQL Injection.
          Controle transacional explícito em cada operação.

Uso:
    python backend/app.py
    As credenciais são lidas de variáveis de ambiente (ou valores padrão).
"""

import os
import json
import psycopg2
import psycopg2.extras
from flask import Flask, request, jsonify, render_template, send_from_directory
from flask_cors import CORS

# ---------------------------------------------------------------------------
# Configuração
# ---------------------------------------------------------------------------

app = Flask(
    __name__,
    template_folder=os.path.join(os.path.dirname(__file__), "../frontend/templates"),
    static_folder=os.path.join(os.path.dirname(__file__), "../frontend/static"),
)
CORS(app)

DB_CONFIG = {
    "host":     os.environ.get("DB_HOST",     "localhost"),
    "port":     int(os.environ.get("DB_PORT", "5432")),
    "dbname":   os.environ.get("DB_NAME",     "eletroreverso"),
    "user":     os.environ.get("DB_USER",     "postgres"),
    "password": os.environ.get("DB_PASSWORD", ""),
}


# ---------------------------------------------------------------------------
# Utilitário de banco
# ---------------------------------------------------------------------------

def get_conn():
    """Abre uma conexão com o PostgreSQL. Lança exceção em caso de falha."""
    conn = psycopg2.connect(**DB_CONFIG)
    conn.autocommit = False
    return conn


def run_query(sql: str, params: tuple = (), fetch: bool = True):
    """
    Executa uma query parametrizada com controle transacional completo.
    - SELECT  → retorna {"columns": [...], "rows": [...]}
    - DML     → retorna {"affected": N}
    - Erro    → lança RuntimeError com mensagem do SGBD
    Localização: backend/app.py · função run_query()
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


def ok(data: dict):
    return jsonify({"ok": True, **data}), 200


def err(msg: str, code: int = 400):
    return jsonify({"ok": False, "error": msg}), code


# ---------------------------------------------------------------------------
# Página principal
# ---------------------------------------------------------------------------

@app.route("/")
def index():
    return render_template("index.html")


# ---------------------------------------------------------------------------
# Status de conexão
# ---------------------------------------------------------------------------

@app.route("/api/status")
def status():
    try:
        run_query("SELECT 1", fetch=True)
        return ok({"message": "Conectado ao banco de dados."})
    except Exception as e:
        return err(str(e), 503)


# ---------------------------------------------------------------------------
# CADASTROS
# ---------------------------------------------------------------------------

@app.route("/api/cadastro/ponto-coleta", methods=["POST"])
def cad_ponto_coleta():
    """
    Cadastra um novo Ponto de Coleta.
    Parâmetros (JSON): rua, cidade, cep, estado, capacidade_max
    SQL: INSERT INTO PontoColeta ... VALUES (%s, %s, %s, %s, %s)
    Localização: backend/app.py · rota /api/cadastro/ponto-coleta
    """
    d = request.json or {}
    required = ["rua", "cidade", "cep", "estado", "capacidade_max"]
    missing = [k for k in required if not d.get(k)]
    if missing:
        return err(f"Campos obrigatórios ausentes: {', '.join(missing)}")
    try:
        sql = """
            INSERT INTO PontoColeta (Rua, Cidade, CEP, Estado, CapacidadeMax)
            VALUES (%s, %s, %s, %s, %s)
        """
        run_query(sql, (
            d["rua"], d["cidade"], d["cep"],
            d["estado"][:2].upper(), float(d["capacidade_max"])
        ), fetch=False)
        return ok({"message": "Ponto de coleta cadastrado com sucesso."})
    except RuntimeError as e:
        return err(str(e))


@app.route("/api/cadastro/lote-coleta", methods=["POST"])
def cad_lote_coleta():
    """
    Registra um novo Lote de Coleta originado de um Ponto de Coleta.
    Parâmetros (JSON): id_lote, rua, cidade, cep, estado, data_coleta
    SQL: INSERT INTO LoteColeta (IdLote, Rua, Cidade, CEP, Estado, DataColeta)
         VALUES (%s, %s, %s, %s, %s, %s)
    Localização: backend/app.py · rota /api/cadastro/lote-coleta
    """
    d = request.json or {}
    required = ["id_lote", "rua", "cidade", "cep", "estado", "data_coleta"]
    missing = [k for k in required if not str(d.get(k, "")).strip()]
    if missing:
        return err(f"Campos obrigatórios ausentes: {', '.join(missing)}")
    try:
        sql = """
            INSERT INTO LoteColeta (IdLote, Rua, Cidade, CEP, Estado, DataColeta)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        run_query(sql, (
            int(d["id_lote"]), d["rua"], d["cidade"],
            d["cep"], d["estado"][:2].upper(), d["data_coleta"]
        ), fetch=False)
        return ok({"message": f"Lote #{d['id_lote']} registrado com sucesso."})
    except (RuntimeError, ValueError) as e:
        return err(str(e))


@app.route("/api/cadastro/dispositivo-lote", methods=["POST"])
def cad_dispositivo_lote():
    """
    Registra a quantidade de um dispositivo eletrônico em um Lote de Coleta.
    Parâmetros (JSON): id_lote, dispositivo, quantidade
    SQL: INSERT INTO QtdProdutoLote (Lote, DispositivoEletronico, Quantidade)
         VALUES (%s, %s, %s)
    Localização: backend/app.py · rota /api/cadastro/dispositivo-lote
    """
    d = request.json or {}
    required = ["id_lote", "dispositivo", "quantidade"]
    missing = [k for k in required if not str(d.get(k, "")).strip()]
    if missing:
        return err(f"Campos obrigatórios ausentes: {', '.join(missing)}")
    try:
        sql = """
            INSERT INTO QtdProdutoLote (Lote, DispositivoEletronico, Quantidade)
            VALUES (%s, %s, %s)
        """
        run_query(sql, (int(d["id_lote"]), d["dispositivo"], float(d["quantidade"])), fetch=False)
        return ok({"message": "Dispositivo registrado no lote com sucesso."})
    except (RuntimeError, ValueError) as e:
        return err(str(e))


# ---------------------------------------------------------------------------
# CONSULTAS
# ---------------------------------------------------------------------------

@app.route("/api/consulta/divisao-relacional")
def consulta_divisao():
    """
    DIVISÃO RELACIONAL (obrigatória):
    Retorna Centros de Reciclagem que processaram TODOS os materiais
    com TipoMaterial = 'Critico', via duplo NOT EXISTS (equivalente
    semântico da divisão relacional em SQL).

    Eficiência: NOT EXISTS permite ao PostgreSQL usar Hash Anti Join ou
    Nested Loop Anti Join, interrompendo a busca ao achar o primeiro match,
    evitando leituras desnecessárias.

    Localização: backend/app.py · rota /api/consulta/divisao-relacional
    """
    try:
        sql = """
            SELECT CR.CNPJ, CR.Nome, CR.Cidade, CR.Estado
            FROM CentroReciclagem CR
            WHERE NOT EXISTS (
                SELECT 1
                FROM Material M
                WHERE M.TipoMaterial = 'Critico'
                AND NOT EXISTS (
                    SELECT 1
                    FROM TransporteTriReciclagem TTR
                    JOIN LoteTriado          LT  ON TTR.codRastreio       = LT.TransporteTriReciclagem
                    JOIN ProcessoReciclagem  PR  ON LT.LoteColeta         = PR.LoteColeta
                                                AND LT.pinLoteTri         = PR.PinLoteTri
                    JOIN MaterialProcessado  MP  ON PR.DataProcessamento  = MP.DataProcessamento
                                                AND PR.TipoDeProcessamento = MP.TipoDeProcessamento
                    WHERE TTR.CentroReciclagem = CR.CNPJ
                      AND MP.Material = M.Nome
                )
            )
            ORDER BY CR.Nome
        """
        return ok(run_query(sql))
    except RuntimeError as e:
        return err(str(e))


@app.route("/api/consulta/lotes-sem-triagem")
def consulta_lotes_sem_triagem():
    """
    Lotes de Coleta que chegaram a um Centro de Triagem mas ainda não
    originaram nenhum Lote Triado. Usa anti-join via NOT EXISTS.

    Eficiência: chaves primárias/estrangeiras com índices B-Tree garantem
    acesso eficiente; NOT EXISTS encerra ao primeiro match.

    Localização: backend/app.py · rota /api/consulta/lotes-sem-triagem
    """
    try:
        sql = """
            SELECT
                LC.IdLote        AS id_lote,
                LC.DataColeta    AS data_coleta,
                LC.Cidade        AS cidade_origem,
                CT.Nome          AS centro_triagem,
                T.DataChegada    AS chegada_ao_centro
            FROM LoteColeta LC
            JOIN TransporteColetaTri TCT ON LC.Transporte   = TCT.codRastreio
            JOIN Transporte          T   ON TCT.codRastreio  = T.codRastreio
            JOIN CentroTriagem       CT  ON TCT.CentroTriagem = CT.CNPJ
            WHERE NOT EXISTS (
                SELECT 1 FROM LoteTriado LT WHERE LT.LoteColeta = LC.IdLote
            )
            ORDER BY T.DataChegada
        """
        return ok(run_query(sql))
    except RuntimeError as e:
        return err(str(e))


@app.route("/api/consulta/centros-acima-media")
def consulta_centros_media():
    """
    Centros de Reciclagem com Licença Ambiental cujo volume total de lotes
    triados recebidos supera a média nacional. Usa CTE para calcular a média
    uma única vez (sem subconsulta correlacionada repetida).

    Eficiência: CTE materializada → agregação executada uma única vez;
    Hash Aggregate em memória pelo GROUP BY sobre CNPJ.

    Localização: backend/app.py · rota /api/consulta/centros-acima-media
    """
    try:
        sql = """
            WITH VolumePorCentro AS (
                SELECT
                    CR.CNPJ,
                    CR.Nome,
                    CR.LicencaAmbiental,
                    SUM(LT.PesoExato) AS volume_total
                FROM CentroReciclagem        CR
                JOIN TransporteTriReciclagem TTR ON CR.CNPJ          = TTR.CentroReciclagem
                JOIN LoteTriado              LT  ON TTR.codRastreio   = LT.TransporteTriReciclagem
                WHERE CR.LicencaAmbiental IS NOT NULL
                GROUP BY CR.CNPJ, CR.Nome, CR.LicencaAmbiental
            )
            SELECT
                CNPJ              AS cnpj,
                Nome              AS nome,
                LicencaAmbiental  AS licenca_ambiental,
                volume_total
            FROM VolumePorCentro
            WHERE volume_total > (SELECT AVG(volume_total) FROM VolumePorCentro)
            ORDER BY volume_total DESC
        """
        return ok(run_query(sql))
    except RuntimeError as e:
        return err(str(e))


@app.route("/api/consulta/rastrear-por-material")
def consulta_rastrear_material():
    """
    PARAMETRIZADA: dado um nome de material, rastreia quais Pontos de Coleta
    foram origem dos dispositivos que geraram aquele material.

    Parâmetro de URL: ?material=Cobre
    SQL: filtro direto via WHERE MP.Material = %s (parametrizado — sem SQL Injection)

    Eficiência: filtro antecipado no WHERE reduz o conjunto nas junções
    subsequentes; DISTINCT elimina duplicatas de múltiplos relacionamentos.

    Localização: backend/app.py · rota /api/consulta/rastrear-por-material
    """
    material = request.args.get("material", "").strip()
    if not material:
        return err("Parâmetro 'material' é obrigatório.")
    try:
        sql = """
            SELECT DISTINCT
                PC.Rua    AS rua,
                PC.Cidade AS cidade,
                PC.CEP    AS cep,
                PC.Estado AS estado
            FROM PontoColeta PC
            JOIN LoteColeta        LC ON PC.Rua    = LC.Rua
                                     AND PC.Cidade  = LC.Cidade
                                     AND PC.CEP     = LC.CEP
                                     AND PC.Estado  = LC.Estado
            JOIN ProcessoReciclagem PR ON LC.IdLote             = PR.LoteColeta
            JOIN MaterialProcessado MP ON PR.DataProcessamento   = MP.DataProcessamento
                                      AND PR.TipoDeProcessamento = MP.TipoDeProcessamento
            WHERE MP.Material = %s
            ORDER BY PC.Cidade, PC.Rua
        """
        return ok(run_query(sql, (material,)))
    except RuntimeError as e:
        return err(str(e))


@app.route("/api/consulta/tempo-medio-transporte")
def consulta_tempo_medio():
    """
    Tempo médio (em dias) de viagem Coleta→Triagem por transportadora.
    INNER JOIN com TransporteColetaTri atua como filtro natural indexado,
    sem necessidade de cláusula WHERE extra.

    Eficiência: subtração nativa DATE-DATE no PostgreSQL; Hash Aggregate
    por CNPJ para AVG().

    Localização: backend/app.py · rota /api/consulta/tempo-medio-transporte
    """
    try:
        sql = """
            SELECT
                Tr.CNPJ                                     AS cnpj,
                Tr.Nome                                     AS nome,
                ROUND(AVG(T.DataChegada - T.DataEnvio), 2) AS media_dias
            FROM Transportadora      Tr
            JOIN Transporte          T   ON Tr.CNPJ        = T.Transportadora
            JOIN TransporteColetaTri TCT ON T.codRastreio  = TCT.codRastreio
            GROUP BY Tr.CNPJ, Tr.Nome
            ORDER BY media_dias
        """
        return ok(run_query(sql))
    except RuntimeError as e:
        return err(str(e))


# ---------------------------------------------------------------------------
# DADOS AUXILIARES (para preencher selects no frontend)
# ---------------------------------------------------------------------------

@app.route("/api/dados/pontos-coleta")
def dados_pontos_coleta():
    try:
        return ok(run_query("SELECT Rua, Cidade, CEP, Estado FROM PontoColeta ORDER BY Cidade, Rua"))
    except RuntimeError as e:
        return err(str(e))


@app.route("/api/dados/dispositivos")
def dados_dispositivos():
    try:
        return ok(run_query(
            "SELECT Nome, PesoMedio, Categoria FROM DispositivoEletronico ORDER BY Nome"
        ))
    except RuntimeError as e:
        return err(str(e))


@app.route("/api/dados/lotes")
def dados_lotes():
    try:
        return ok(run_query(
            "SELECT IdLote, DataColeta, Cidade, Estado FROM LoteColeta ORDER BY IdLote"
        ))
    except RuntimeError as e:
        return err(str(e))


@app.route("/api/dados/materiais")
def dados_materiais():
    try:
        return ok(run_query("SELECT Nome, TipoMaterial FROM Material ORDER BY Nome"))
    except RuntimeError as e:
        return err(str(e))


@app.route("/api/dados/centros-triagem")
def dados_centros_triagem():
    try:
        return ok(run_query("SELECT CNPJ, Nome, Cidade FROM CentroTriagem ORDER BY Nome"))
    except RuntimeError as e:
        return err(str(e))


@app.route("/api/dados/centros-reciclagem")
def dados_centros_reciclagem():
    try:
        return ok(run_query(
            "SELECT CNPJ, Nome, Cidade, LicencaAmbiental FROM CentroReciclagem ORDER BY Nome"
        ))
    except RuntimeError as e:
        return err(str(e))


@app.route("/api/dados/transportadoras")
def dados_transportadoras():
    try:
        return ok(run_query("SELECT CNPJ, Nome FROM Transportadora ORDER BY Nome"))
    except RuntimeError as e:
        return err(str(e))


# ---------------------------------------------------------------------------
# Ponto de entrada
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_DEBUG", "true").lower() == "true"
    print(f"  EletroReverso — servidor iniciado em http://localhost:{port}")
    print(f"  Banco: {DB_CONFIG['host']}:{DB_CONFIG['port']} / {DB_CONFIG['dbname']}")
    app.run(host="0.0.0.0", port=port, debug=debug)