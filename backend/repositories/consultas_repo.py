from backend.config.database import run_query

# ==============================================================================
# CONSULTAS COMPLEXAS (Relatórios)
# ==============================================================================

def buscar_centros_todos_materiais_criticos():
    """Consulta 1 (Divisão Relacional): Centros que processaram TODOS os materiais Críticos."""
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
    return run_query(sql, (material,))

def calcular_tempo_medio_transportadoras():
    """Consulta 5: Tempo médio de viagem (Coleta -> Triagem) por transportadora."""
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