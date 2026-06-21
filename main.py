import os
import sys
from flask import Flask
from flask_cors import CORS
from backend.controllers.rotas import rotas_bp

# Inicialização do aplicativo Flask apontando para a estrutura da interface
app = Flask(
    __name__,
    template_folder=os.path.join(os.path.dirname(__file__), "frontend/templates"),
    static_folder=os.path.join(os.path.dirname(__file__), "frontend/static")
)
CORS(app)

# Registro do Blueprint de rotas do controlador (carrega todas as APIs do sistema)
app.register_blueprint(rotas_bp)

if __name__ == "__main__":
    # Resgata os parâmetros de inicialização definidos no arquivo .env
    port = int(os.environ.get("PORT", 5000))
    debug_mode = os.environ.get("FLASK_DEBUG", "true").lower() == "true"
    
    print("===================================================")
    print(" Iniciando a Interface Web do EletroReverso...")
    print(" Arquitetura modular MVC/Repository carregada.")
    print(f" Servidor ativo em: http://localhost:{port}")
    print("===================================================")
    
    app.run(host="0.0.0.0", port=port, debug=debug_mode)