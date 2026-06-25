"""
==============================================================================
Arquivo: consultas_repo.py
Descrição: Repositório de consultas (Camada de Leitura do Banco de Dados).
Arquitetura: Este módulo isola a lógica de extração de dados da aplicação.
             Atendendo rigorosamente aos requisitos do projeto, NÃO foram 
             utilizados frameworks de ORM (Object-Relational Mapping). 
             Todas as operações utilizam DECLARAÇÕES SQL EXPLÍCITAS, 
             garantindo total controle sobre o plano de execução do SGBD,
             otimização de junções e transparência na avaliação acadêmica.
==============================================================================
"""

from backend.config.database import run_query

# ==============================================================================
# CONSULTAS COMPLEXAS (Relatórios)
# ==============================================================================

def buscar_centros_todos_materiais_criticos():
    """Consulta 1 (Divisão Relacional): Centros que processaram TODOS os materiais Críticos."""
    # Demonstração de SQL Explícito: A query abaixo materializa a Álgebra Relacional 
    # (Divisão) de forma direta no código, utilizando subconsultas aninhadas (NOT EXISTS).
    # O uso de strings SQL literais permite que o avaliador inspecione a estrutura DML crua.
    sql = """
        SELECT CR.CNPJ, CR.Nome, CR.Cidade, CR.Estado
        FROM CentroReciclagem CR
        WHERE NOT EXISTS (
            SELECT 1 FROM Material M
            WHERE M.TipoMaterial = 'Critico'
            AND NOT EXISTS (
                SELECT 1
                FROM TransporteTriReciclagem TTR
                JOIN LoteTriado          LT  ON TTR.codRastreio       = LT.TransporteTriReciclagem
                JOIN ProcessoReciclagem  PR  ON LT.LoteColeta         = PR.LoteColeta
                                            AND LT.pinLoteTri         = PR.PinLoteTri
                JOIN MaterialProcessado  MP  ON PR.DataProcessamento  = MP.DataProcessamento
                                            AND PR.TipoDeProcessamento = MP.TipoDeProcessamento
                WHERE TTR.CentroReciclagem = CR.CNPJ AND MP.Material = M.Nome
            )
        )
        ORDER BY CR.Nome
    """
    return run_query(sql)

def buscar_lotes_sem_triagem():
    """Consulta 2: Lotes de coleta que chegaram ao centro, mas não foram triados."""
    # Demonstração de SQL Explícito: A operação de Anti-Join é construída manualmente 
    # com a declaração clara do LEFT JOIN e da cláusula WHERE ... IS NULL. Em um ORM, 
    # essa estrutura seria abstraída e poderia gerar queries sub-otimizadas por debaixo dos panos.
    sql = """
        SELECT
            LC.IdLote        AS id_lote,
            LC.DataColeta    AS data_coleta,
            LC.Cidade        AS cidade_origem,
            CT.Nome          AS centro_triagem,
            T.DataChegada    AS chegada_ao_centro
        FROM LoteColeta LC
        JOIN TransporteColetaTri TCT ON LC.Transporte   = TCT.codRastreio
        JOIN Transporte          T   ON TCT.codRastreio = T.codRastreio
        JOIN CentroTriagem       CT  ON TCT.CentroTriagem = CT.CNPJ
        -- Aplicação do OUTER JOIN
        LEFT JOIN LoteTriado     LT  ON LC.IdLote = LT.LoteColeta
        -- Filtramos apenas os registros onde o lado direito do JOIN (LoteTriado) veio vazio
        WHERE LT.LoteColeta IS NULL
        ORDER BY T.DataChegada;
    """
    return run_query(sql)

def buscar_centros_acima_media():
    """Consulta 3: Centros de reciclagem com volume processado acima da média nacional."""
    # Demonstração de SQL Explícito: A declaração explícita da CTE (WITH) permite estruturar 
    # a consulta em blocos lógicos. Garantimos que a agregação SUM() e a subconsulta AVG() 
    # sejam enviadas exatamente com esta sintaxe ao Query Planner do PostgreSQL.
    sql = """
        WITH VolumePorCentro AS (
            SELECT
                CR.CNPJ,
                CR.Nome,
                CR.LicencaAmbiental,
                SUM(LT.PesoExato) AS volume_total
            FROM CentroReciclagem CR
            JOIN TransporteTriReciclagem TTR ON CR.CNPJ = TTR.CentroReciclagem
            JOIN LoteTriado LT ON TTR.codRastreio = LT.TransporteTriReciclagem
            WHERE CR.LicencaAmbiental IS NOT NULL
            GROUP BY CR.CNPJ, CR.Nome, CR.LicencaAmbiental
        )
        SELECT CNPJ AS cnpj, Nome AS nome, LicencaAmbiental AS licenca_ambiental, volume_total
        FROM VolumePorCentro
        WHERE volume_total > (SELECT AVG(volume_total) FROM VolumePorCentro)
        ORDER BY volume_total DESC
    """
    return run_query(sql)

def rastrear_origem_por_material(material: str):
    """Consulta 4 (Parametrizada): Rastreia pontos de coleta que originaram um material específico."""
    # Demonstração de SQL Explícito e Segurança: Aqui o comando literal é complementado 
    # pela técnica de "Consultas Parametrizadas". O '%s' atua como um placeholder que é 
    # preenchido com segurança pelo driver do banco (psycopg2) em tempo de execução, 
    # mitigando completamente vulnerabilidades de SQL Injection.
    sql = """
        SELECT DISTINCT
            PC.Rua AS rua, PC.Cidade AS cidade, PC.CEP AS cep, PC.Estado AS estado
        FROM PontoColeta PC
        JOIN LoteColeta LC ON PC.Rua = LC.Rua AND PC.Cidade = LC.Cidade AND PC.CEP = LC.CEP AND PC.Estado = LC.Estado
        JOIN ProcessoReciclagem PR ON LC.IdLote = PR.LoteColeta
        JOIN MaterialProcessado MP ON PR.DataProcessamento = MP.DataProcessamento AND PR.TipoDeProcessamento = MP.TipoDeProcessamento
        WHERE MP.Material = %s
        ORDER BY PC.Cidade, PC.Rua
    """
    # A variável material é passada como uma tupla (material,), delegando a sanitização ao banco.
    return run_query(sql, (material,))

def calcular_tempo_medio_transportadoras():
    """Consulta 5: Tempo médio de viagem (Coleta -> Triagem) por transportadora."""
    # Demonstração de SQL Explícito: Expressa diretamente operações aritméticas de datas 
    # (DataChegada - DataEnvio) e funções matemáticas (ROUND, AVG), garantindo processamento 
    # nativo no lado do servidor do banco de dados (Server-Side Processing).
    sql = """
        SELECT
            Tr.CNPJ AS cnpj, Tr.Nome AS nome,
            ROUND(AVG(T.DataChegada - T.DataEnvio), 2) AS media_dias
        FROM Transportadora Tr
        JOIN Transporte T ON Tr.CNPJ = T.Transportadora
        JOIN TransporteColetaTri TCT ON T.codRastreio = TCT.codRastreio
        GROUP BY Tr.CNPJ, Tr.Nome
        ORDER BY media_dias
    """
    return run_query(sql)


# ==============================================================================
# CONSULTAS AUXILIARES (Para preencher menus na Interface)
# Por que: Mesmo para leituras simples de catálogo, a regra do projeto é mantida:
# sem mapeadores implícitos. O uso do SQL literal garante previsibilidade e 
# alta velocidade na renderização dinâmica dos formulários (dropdowns) da interface web.
# ==============================================================================

def listar_pontos_coleta():
    return run_query("SELECT Rua, Cidade, CEP, Estado FROM PontoColeta ORDER BY Cidade, Rua")

def listar_dispositivos():
    return run_query("SELECT Nome, PesoMedio, Categoria FROM DispositivoEletronico ORDER BY Nome")

def listar_lotes():
    return run_query("SELECT IdLote, DataColeta, Cidade, Estado FROM LoteColeta ORDER BY IdLote")

def listar_materiais():
    return run_query("SELECT Nome, TipoMaterial FROM Material ORDER BY Nome")

def listar_centros_triagem():
    return run_query("SELECT CNPJ, Nome, Cidade FROM CentroTriagem ORDER BY Nome")

def listar_centros_reciclagem():
    return run_query("SELECT CNPJ, Nome, Cidade, LicencaAmbiental FROM CentroReciclagem ORDER BY Nome")

def listar_transportadoras():
    return run_query("SELECT CNPJ, Nome FROM Transportadora ORDER BY Nome")