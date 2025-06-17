import uuid
from datetime import datetime
from flask_restx import Namespace, Resource
from flask import request, Response
from twilio.twiml.messaging_response import MessagingResponse
from .sheets import add_to_sheet

ns = Namespace('Webhook', description='Endpoints do webhook')

user_states = {}

fields = ['nome', 'nome_empresa', 'cnpj', 'qtd_faixas', 'qtd_lateral', 'cep', 'observacoes']
questions = {
    'nome': 'Por favor, informe seu *nome completo*:',
    'nome_empresa': 'Por favor, informe o *nome da empresa*:',
    'cnpj': 'Informe seu *CNPJ*:',
    'qtd_faixas': 'Quantas *faixas* deseja?',
    'qtd_lateral': 'Quantas *laterais* deseja?',
    'cep': 'Por favor, informe seu *CEP*:',
    'observacoes': 'Por favor, insira suas *observações do pedido*:'
}

precos = (
    "*Tabela de Preços:*\n\n"
    "• Faixa  : R$ 150,00 cada\n"
    "• Lateral: R$ 50,00 cada\n"
    "\n"
    "_Valores podem variar conforme quantidade ou personalização._"
)

saudacao = "Bom dia! Esse é um atendimento automatizado da MaringáFaixas. Faça o seu pedido abaixo e nós te atenderemos o mais rápido possível!\n\n"
opcoes_menu = (
    "\n\nSelecione uma opção:\n\n"
    "1 - Cadastrar informações do pedido\n"
    "2 - Ver preços\n"
    "3 - Ignorar atendimento personalizado"
)

@ns.route('/twilio')
class WebhookTwilio(Resource):
    def post(self):
        from_number = request.form.get('From')
        body = request.form.get('Body').strip().lower()
        response = MessagingResponse()

        if from_number not in user_states:
            user_states[from_number] = {'status': 'menu'}
            response.message(saudacao + opcoes_menu)
            return Response(str(response), mimetype="application/xml")

        user_state = user_states[from_number]

        if user_state['status'] == 'menu':
            if body in ['1', 'fazer cadastro', 'cadastro']:
                user_state['status'] = 'cadastro'
                user_state['step'] = 0
                user_state['data'] = {}
                # Gera e armazena o ID
                user_state['id'] = str(uuid.uuid4())
                response.message("Perfeito! Vamos começar seu cadastro. Lembre-se de enviar apenas as informações solicitadas, nada mais ok ?\n\n" + questions[fields[0]])

            elif body in ['2', 'ver preços', 'preço', 'preços']:
                response.message(precos + opcoes_menu)  # aqui só as opções, sem saudação

            elif body in ['3', 'ignorar', 'ignorar atendimento', 'ignorar atendimento personalizado']:
                response.message(
                    "Perfeito. Sua solicitação seguirá normalmente sem o atendimento automatizado.\n\n"
                    "Se preferir, envie sua mensagem aqui que iremos responder assim que possível."
                )

            else:
                response.message(
                    "Opção inválida.\n\nPor favor, selecione uma das opções abaixo:" + opcoes_menu
                )

            return Response(str(response), mimetype="application/xml")

     
        if user_state['status'] == 'cadastro':
            step = user_state['step']
            current_field = fields[step]
            user_state['data'][current_field] = body

            step += 1

            if step < len(fields):
                user_state['step'] = step
                next_field = fields[step]
                response.message(questions[next_field])
            else:
                dados = user_state['data']
                data_criacao = datetime.now().strftime("%d/%m/%Y")  
                linha = [
                    user_state['id'],  
                    from_number,       
                    dados['nome'],
                    dados['nome_empresa'],  
                    dados['cnpj'],
                    dados['qtd_faixas'],
                    dados['qtd_lateral'],
                    dados['cep'],          
                    dados['observacoes'],
                    data_criacao         
                ]
                try:
                    add_to_sheet(linha)
                    response.message(
                        "*Cadastro concluído com sucesso!*\n"
                        "Agradecemos por fazer negócios com a MaringáFaixas. O prazo de entrega é entre 15-40 dias, logo mais nosso vendedor irá entrar em contato para envio do pix / boleto."
                    )
                except Exception as e:
                    response.message(
                        "*Ocorreu um erro ao salvar seu cadastro.*\nPor favor, tente novamente."
                    )
                    print(f"Erro ao salvar na planilha: {e}")

                # Volta para o menu após finalizar
                user_states[from_number] = {'status': 'menu'}
                response.message("Caso queira fazer mais algum pedido, siga as instruções abaixo.\n\n" + opcoes_menu)

            return Response(str(response), mimetype="application/xml")
