import uuid
from datetime import datetime
from flask_restx import Namespace, Resource
from flask import request, Response
from twilio.twiml.messaging_response import MessagingResponse
from .sheets import add_to_sheet

ns = Namespace('Webhook', description='Endpoints do webhook')

# Estado dos usuários (em memória)
user_states = {}

# Campos que queremos coletar (adicionado 'observacoes')
fields = ['nome', 'cnpj', 'qtd_faixas', 'qtd_lateral', 'observacoes']
questions = {
    'nome': 'Por favor, informe seu *nome completo*:',
    'cnpj': 'Informe seu *CNPJ*:',
    'qtd_faixas': 'Quantas *faixas* deseja?',
    'qtd_lateral': 'Quantas *laterais* deseja?',
    'observacoes': 'Por favor, insira suas *observações do pedido*:'
}

# Preços (exemplo)
precos = (
    "*Tabela de Preços:*\n\n"
    "• Faixa: R$ 50,00 cada\n"
    "• Lateral: R$ 30,00 cada\n"
    "\n"
    "_Valores podem variar conforme quantidade ou personalização._"
)

# Menu inicial
saudacao = "Boa tarde! Esse é um atendimento automático, gostaria de agilizar o seu processo de pedido?"
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

        # Se é a primeira mensagem, apresenta a saudação + opções
        if from_number not in user_states:
            user_states[from_number] = {'status': 'menu'}
            response.message(saudacao + opcoes_menu)
            return Response(str(response), mimetype="application/xml")

        user_state = user_states[from_number]

        # Usuário está no menu
        if user_state['status'] == 'menu':
            if body in ['1', 'fazer cadastro', 'cadastro']:
                user_state['status'] = 'cadastro'
                user_state['step'] = 0
                user_state['data'] = {}
                # Gera e armazena o ID
                user_state['id'] = str(uuid.uuid4())
                response.message("Perfeito! Vamos começar seu cadastro.\n\n" + questions[fields[0]])

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

        # Se está no fluxo de cadastro
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
                linha = [
                    user_state['id'],  # ID único
                    from_number,       # Telefone do usuário
                    dados['nome'],
                    dados['cnpj'],
                    dados['qtd_faixas'],
                    dados['qtd_lateral'],
                    dados['observacoes'],
                    datetime.now().isoformat()  # Data e hora da criação em ISO 8601
                ]
                try:
                    add_to_sheet(linha)
                    response.message(
                        "*Cadastro concluído com sucesso!*\n"
                        "Entraremos em contato com seu pedido assim que possível."
                    )
                except Exception as e:
                    response.message(
                        "*Ocorreu um erro ao salvar seu cadastro.*\nPor favor, tente novamente."
                    )
                    print(f"Erro ao salvar na planilha: {e}")

                # Volta para o menu após finalizar
                user_states[from_number] = {'status': 'menu'}
                response.message("Se desejar, você pode recorrer a outra opção:\n\n" + opcoes_menu)

            return Response(str(response), mimetype="application/xml")
