"""
==============================================================================
Arquivo: rotas.py
Descrição: Controlador da Aplicação (Camada 'Controller' do MVC).
Arquitetura: Este módulo atua como o maestro do sistema. Ele não executa 
             comandos SQL diretamente; sua responsabilidade é receber as requisições 
             HTTP do frontend (View), validar as entradas do usuário, delegar o 
             trabalho pesado para os Repositórios (Model) e retornar as 
             respostas empacotadas no formato JSON padrão da API.
==============================================================================
"""

from backend.repositories import cadastro_repo
from flask import Blueprint, request, jsonify, render_template
from backend.repositories import consultas_repo
from backend.config.database import run_query

# Inicialização do Blueprint de rotas do sistema
# Por que: O Blueprint modulariza a aplicação Flask. Ele permite agrupar todas 
# as rotas em um único objeto que será "acoplado" ao main.py posteriormente, 
# mantendo o código organizado e escalável.
rotas_bp = Blueprint("rotas", __name__)

# ==============================================================================
# Funções Auxiliares (Helpers de Resposta da API)
# Por que: Padronizar o contrato de comunicação entre o Frontend (JavaScript) 
# e o Backend (Python). Isso evita respostas inconsistentes e facilita o 
# tratamento de estados na interface do usuário.
# ==============================================================================

def ok(data: dict):
    """Auxiliar para retorno de respostas bem-sucedidas."""
    # Retorna o código HTTP 200 (OK) injetando a flag "ok": True para o frontend.
    return jsonify({"ok": True, **data}), 200

def err(msg: str, code: int = 400):
    """Auxiliar para tratamento e retorno de mensagens de erro."""
    # Retorna o código HTTP 400 (Bad Request) por padrão, sinalizando falha do lado do cliente.
    return jsonify({"ok": False, "error": msg}), code

# ---------------------------------------------------------------------------
# Página Principal e Status de Conexão
# ---------------------------------------------------------------------------

@rotas_bp.route("/")
def index():
    # Renderiza a interface gráfica do sistema (Single Page Application).
    return render_template("index.html")

@rotas_bp.route("/api/status")
def status():
    # Como e Por que: Rota de "Health Check". Executa uma query inofensiva ("SELECT 1") 
    # apenas para testar se o SGBD está online e respondendo antes de operar o sistema.
    try:
        run_query("SELECT 1", fetch=True)
        return ok({"message": "Conectado ao banco de dados."})
    except Exception as e:
        # HTTP 503 (Service Unavailable): Informa que a infraestrutura caiu.
        return err(str(e), 503)

# ---------------------------------------------------------------------------
# Módulo de Cadastros (Inclusões de Dados)
# Validação e Sanitização (Prevenção de Erros 500 no Servidor)
# ---------------------------------------------------------------------------

@rotas_bp.route("/api/cadastro/ponto-coleta", methods=["POST"])
def cad_ponto_coleta():
    # Extrai o corpo da requisição JSON enviada pelo formulário web.
    d = request.json or {}
    # Validação rigorosa: Garante que o usuário não burlou o HTML e enviou dados vazios.
    required = ["rua", "cidade", "cep", "estado", "capacidade_max"]
    missing = [k for k in required if not d.get(k)]
    if missing:
        return err(f"Campos obrigatórios ausentes: {', '.join(missing)}")
    
    try:
        # Sanitização e Cast de Tipos: Converte a capacidade para float e 
        # força o estado a ter no máximo 2 caracteres maiúsculos (ex: "sp" -> "SP")
        # para respeitar a constraint CHAR(2) do banco de dados.
        cadastro_repo.inserir_ponto_coleta(
            d["rua"], d["cidade"], d["cep"],
            d["estado"][:2].upper(), float(d["capacidade_max"])
        )
        return ok({"message": "Ponto de coleta cadastrado com sucesso."})
    except Exception as e:
        # Intercepta exceções do banco (ex: Violação de Unique/Primary Key) e 
        # devolve como texto tratável para o usuário, não derrubando o servidor.
        return err(str(e))

@rotas_bp.route("/api/cadastro/lote-coleta", methods=["POST"])
def cad_lote_coleta():
    d = request.json or {}
    required = ["id_lote", "rua", "cidade", "cep", "estado", "data_coleta"]
    missing = [k for k in required if not str(d.get(k, "")).strip()]
    if missing:
        return err(f"Campos obrigatórios ausentes: {', '.join(missing)}")
    
    try:
        # Conversão explícita de tipos (int) previne incompatibilidades com o SGBD.
        cadastro_repo.inserir_lote_coleta(
            int(d["id_lote"]), d["rua"], d["cidade"],
            d["cep"], d["estado"][:2].upper(), d["data_coleta"]
        )
        return ok({"message": f"Lote #{d['id_lote']} registrado com sucesso."})
    except Exception as e:
        return err(str(e))

@rotas_bp.route("/api/cadastro/dispositivo-lote", methods=["POST"])
def cad_dispositivo_lote():
    d = request.json or {}
    required = ["id_lote", "dispositivo", "quantidade"]
    missing = [k for k in required if not str(d.get(k, "")).strip()]
    if missing:
        return err(f"Campos obrigatórios ausentes: {', '.join(missing)}")
    try:
        cadastro_repo.inserir_dispositivo_lote(
            int(d["id_lote"]), d["dispositivo"], float(d["quantidade"])
        )
        return ok({"message": "Dispositivo registrado no lote com sucesso."})
    except Exception as e:
        return err(str(e))

# ---------------------------------------------------------------------------
# Módulo de Consultas Complexas (Relatórios)
# Isolamento de Responsabilidade: As lógicas de junção e extração de dados 
# não ficam no controlador, ele apenas aciona os repositórios e entrega o JSON.
# ---------------------------------------------------------------------------

@rotas_bp.route("/api/consulta/divisao-relacional")
def consulta_divisao():
    try:
        return ok(consultas_repo.buscar_centros_todos_materiais_criticos())
    except Exception as e:
        return err(str(e))

@rotas_bp.route("/api/consulta/lotes-sem-triagem")
def consulta_lotes_sem_triagem():
    try:
        return ok(consultas_repo.buscar_lotes_sem_triagem())
    except Exception as e:
        return err(str(e))

@rotas_bp.route("/api/consulta/centros-acima-media")
def consulta_centros_media():
    try:
        return ok(consultas_repo.buscar_centros_acima_media())
    except Exception as e:
        return err(str(e))

@rotas_bp.route("/api/consulta/rastrear-por-material")
def consulta_rastrear_material():
    # Extração de Query Parameters da URL (ex: ?material=Cobre).
    material = request.args.get("material", "").strip()
    if not material:
        return err("Parâmetro 'material' é obrigatório.")
    try:
        # O parâmetro sanitizado é encaminhado para o repositório, que fará 
        # o 'binding' seguro (%s) no SQL para evitar injeção.
        return ok(consultas_repo.rastrear_origem_por_material(material))
    except Exception as e:
        return err(str(e))

@rotas_bp.route("/api/consulta/tempo-medio-transporte")
def consulta_tempo_medio():
    try:
        return ok(consultas_repo.calcular_tempo_medio_transportadoras())
    except Exception as e:
        return err(str(e))

# ---------------------------------------------------------------------------
# Módulo de Dados Auxiliares (Preenchimento de Seleções de Interface)
# Por que: Estas rotas são consumidas ativamente pelos seletores (<select>) no 
# frontend para garantir que o usuário só escolha opções que já existam no banco, 
# evitando erros de restrição de Chave Estrangeira (FK Constraint) durante o cadastro.
# ---------------------------------------------------------------------------

@rotas_bp.route("/api/dados/pontos-coleta")
def dados_pontos_coleta():
    try:
        return ok(consultas_repo.listar_pontos_coleta())
    except Exception as e:
        return err(str(e))

@rotas_bp.route("/api/dados/dispositivos")
def dados_dispositivos():
    try:
        return ok(consultas_repo.listar_dispositivos())
    except Exception as e:
        return err(str(e))

@rotas_bp.route("/api/dados/lotes")
def dados_lotes():
    try:
        return ok(consultas_repo.listar_lotes())
    except Exception as e:
        return err(str(e))

@rotas_bp.route("/api/dados/materiais")
def dados_materiais():
    try:
        return ok(consultas_repo.listar_materiais())
    except Exception as e:
        return err(str(e))

@rotas_bp.route("/api/dados/centros-triagem")
def dados_centros_triagem():
    try:
        return ok(consultas_repo.listar_centros_triagem())
    except Exception as e:
        return err(str(e))

@rotas_bp.route("/api/dados/centros-reciclagem")
def dados_centros_reciclagem():
    try:
        return ok(consultas_repo.listar_centros_reciclagem())
    except Exception as e:
        return err(str(e))

@rotas_bp.route("/api/dados/transportadoras")
def dados_transportadoras():
    try:
        return ok(consultas_repo.listar_transportadoras())
    except Exception as e:
        return err(str(e))