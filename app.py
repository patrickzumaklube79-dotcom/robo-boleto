from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

@app.route('/buscar-boleto/<cpf>')
def buscar(cpf):
    # BUSCA BOLETO JÁ GERADO NO INTER
    url = f"https://cdpj.partners.bancointer.com.br/cobranca/v3/cobrancas?cpfCnpj={cpf}"
    r = requests.get(url, cert=('Intercert.crt', 'Intercert.key'))
    dados = r.json()

    ultimo = dados['cobrancas'][0] if dados['cobrancas'] else None

    return jsonify({
        "linha": ultimo['linhaDigitavel'] if ultimo else "não achou",
        "pdf": ultimo['linkBoleto'] if ultimo else "",
        "valor": ultimo['valorNominal'] if ultimo else 0
    })

@app.route('/')
def ok():
    return "ROBO NO AR - BUSCANDO BOLETO"
