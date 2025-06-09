from flask import Flask
from flask_restx import Api

def create_app():
    app = Flask(__name__)
    
    # Configurações (exemplo)
    app.config['SWAGGER_UI_DOC_EXPANSION'] = 'list'
    
    api = Api(
        app, version='1.0', title='PlussBots API',
              description='API para receber mensagens e salvar no Google Sheets')
    
    # Importa e registra namespaces de rotas
    from .routes import ns as webhook_namespace
    api.add_namespace(webhook_namespace, path='/webhook')
    
    return app
