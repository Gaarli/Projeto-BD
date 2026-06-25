"""
==============================================================================
Arquivo: main.py
Descrição: Ponto de entrada (Entrypoint) da aplicação backend do EletroReverso.
Arquitetura: O sistema adota o padrão MVC (Model-View-Controller) aliado ao 
             padrão Repository. Este arquivo atua como o orquestrador principal,
             acoplando a camada de visualização (Frontend) aos controladores (Rotas).
==============================================================================
"""

import os
import sys
from flask import Flask
from flask_cors import CORS
from backend.controllers.rotas import rotas_bp

# ==============================================================================
# Inicialização do aplicativo Flask apontando para a estrutura da interface
# Como e Por que: O Flask procura por padrão as pastas 'templates' e 'static'
# no mesmo nível do script em execução. Como separamos o projeto em pastas web 
# (frontend/) e lógicas (backend/), usamos os.path.join() para mapear os caminhos
# absolutos. Isso garante que o servidor sempre encontre o HTML/CSS/JS da interface, 
# independentemente de onde o usuário rodar o comando no terminal.
# ==============================================================================
app = Flask(
    __name__,
    template_folder=os.path.join(os.path.dirname(__file__), "frontend/templates"),
    static_folder=os.path.join(os.path.dirname(__file__), "frontend/static")
)

# Aplicação do CORS (Cross-Origin Resource Sharing)
# Por que: Libera a política de segurança do navegador. Garante que as requisições 
# assíncronas (fetch/AJAX) feitas pelo JavaScript no frontend não sejam bloqueadas 
# ao tentar se comunicar com os endpoints da API no backend.
CORS(app)

# Registro do Blueprint de rotas do controlador (carrega todas as APIs do sistema)
# Por que: Em vez de poluir este arquivo principal com dezenas de definições 
# de "@app.route", delegamos o roteamento para o 'rotas_bp'. Isso respeita o 
# Princípio de Responsabilidade Única (SOLID), mantendo o Controller totalmente isolado.
app.register_blueprint(rotas_bp)

# Escopo de execução do script principal
# Por que: O teste if __name__ == "__main__": assegura que o servidor web 
# só será acionado se o arquivo for executado diretamente, impedindo que a porta
# seja ocupada acidentalmente caso o arquivo seja importado como módulo em outro script.
if __name__ == "__main__":
    # Resgata os parâmetros de inicialização definidos no arquivo .env
    # Por que: Evitar o "hardcode" (valores fixos no código) de portas e credenciais 
    # é uma prática essencial de infraestrutura e segurança. O uso do método .get() 
    # fornece valores padrão (fallback) seguros caso a variável de ambiente não exista.
    port = int(os.environ.get("PORT", 5000))
    debug_mode = os.environ.get("FLASK_DEBUG", "true").lower() == "true"
    
    print("===================================================")
    print(" Iniciando a Interface Web do EletroReverso...")
    print(" Arquitetura modular MVC/Repository carregada.")
    print(f" Servidor ativo em: http://localhost:{port}")
    print("===================================================")
    
    # Executa o servidor WSGI embutido do Flask
    # Como: O host="0.0.0.0" expõe a aplicação para toda a rede local (não apenas 
    # para localhost). O debug=debug_mode ativa o "hot-reload" durante o desenvolvimento,
    # reiniciando o servidor automaticamente a cada salvamento e detalhando erros no navegador.
    app.run(host="0.0.0.0", port=port, debug=debug_mode)