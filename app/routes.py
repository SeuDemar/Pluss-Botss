from flask_restx import Namespace, Resource, fields
from flask import request
from .sheets import add_to_sheet
from flask import Response
from twilio.twiml.messaging_response import MessagingResponse

ns = Namespace('Webhook', description='Endpoints do webhook')

message_model = ns.model('Message', {
    'From': fields.String(required=True, description='Número do remetente'),
    'Body': fields.String(required=True, description='Conteúdo da mensagem'),
})

@ns.route('')
class Webhook(Resource):
    @ns.expect(message_model, validate=True)
    def post(self):
        data = request.json
        from_number = data.get('From')
        body = data.get('Body')

        print(f'Mensagem de {from_number}: {body}')
        
        add_to_sheet([from_number, body])
        
        return {'status': 'received'}, 200
    
@ns.route('/twilio')
class WebhookTwilio(Resource):
    def post(self):
        from_number = request.form.get('From')
        body = request.form.get('Body')

        if not from_number or not body:
            return {'error': 'Missing From or Body in form data'}, 400

        print(f'Mensagem Twilio de {from_number}: {body}')

        # Salva na planilha (número e mensagem)
        add_to_sheet([from_number, body])

        # Cria resposta de boas-vindas sempre
        resposta = MessagingResponse()
        resposta.message(
            "Olá! 👋\n"
            "Bem-vindo(a) ao PlussBots. Estou aqui para ajudar você.\n"
            "Por favor, envie os dados que deseja registrar, e eu cuidarei do resto."
        )

        return Response(str(resposta), mimetype="application/xml")
    
    
