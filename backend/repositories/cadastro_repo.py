from backend.config.database import run_query

def inserir_ponto_coleta(rua: str, cidade: str, cep: str, estado: str, capacidade_max: float):
    """Cadastra um novo Ponto de Coleta no sistema."""
    sql = """
        INSERT INTO PontoColeta (Rua, Cidade, CEP, Estado, CapacidadeMax)
        VALUES (%s, %s, %s, %s, %s)
    """
    params = (rua, cidade, cep, estado, capacidade_max)
    return run_query(sql, params, fetch=False)

def inserir_lote_coleta(id_lote: int, rua: str, cidade: str, cep: str, estado: str, data_coleta: str):
    """Registra um novo Lote de Coleta originado de um Ponto de Coleta existente."""
    sql = """
        INSERT INTO LoteColeta (IdLote, Rua, Cidade, CEP, Estado, DataColeta)
        VALUES (%s, %s, %s, %s, %s, %s)
    """
    params = (id_lote, rua, cidade, cep, estado, data_coleta)
    return run_query(sql, params, fetch=False)

def inserir_dispositivo_lote(id_lote: int, dispositivo: str, quantidade: float):
    """Registra a quantidade de um dispositivo eletrônico dentro de um Lote de Coleta."""
    sql = """
        INSERT INTO QtdProdutoLote (Lote, DispositivoEletronico, Quantidade)
        VALUES (%s, %s, %s)
    """
    params = (id_lote, dispositivo, quantidade)
    return run_query(sql, params, fetch=False)