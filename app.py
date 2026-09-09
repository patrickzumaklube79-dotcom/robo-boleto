from flask import Flask, request
import requests

app = Flask(__name__)

INTER_CLIENT_ID = "c6232197-ac45-4943-99b4-053730562d3d"
INTER_CLIENT_SECRET = "42c1334d-12dc-4671-93e5-9600387f0156"
INTER_CERT_CRT = "./InterCert.crt"
INTER_CERT_KEY = "./InterCert.key"

WHATSAPP_TOKEN = "COLOCA_AQUI_SEU_TOKEN_DO_META"
WHATSAPP_PHONE_ID = "COLOCA_AQUI_SEU_PHONE_ID"

def buscar_boleto_inter(cpf):
    url_token = "https://cdpj.partners.bancointer.com.br/oauth/v2/token"
    data = {
        "client_id": INTER_CLIENT_ID,
        "client_secret": INTER_CLIENT_SECRET,
        "scope": "boleto-cobranca.read",
        "grant_type": "client_credentials"
    }
    r = requests.post(url_token, data=data, cert=(INTER_CERT_CRT, INTER_CERT_KEY))
    token = r.json()["access_token"]

    url = f"https://cdpj.partners.bancointer.com.br/cobranca/v3/cobrancas?cpfCnpj={cpf}&situacao=A_RECEBER"
    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.get(url, headers=headers, cert=(INTER_CERT_CRT, INTER_CERT_KEY))
    return resp.json()

def enviar_whatsapp(numero, texto):
    url = f"https://graph.facebook.com/v20.0/{WHATSAPP_PHONE_ID}/messages"
    headers = {"Authorization": f"Bearer {WHATSAPP_TOKEN}"}
    payload = {
        "messaging_product": "whatsapp",
        "to": numero,
        "type": "text",
        "text": {"body": texto}
    }
    requests.post(url, json=payload, headers=headers)

@app.route("/webhook", methods=["POST","GET"])
def webhook():
    if request.method == "GET":
        return request.args.get("hub.challenge", "OK")
    data = request.json
    try:
        msg = data['entry'][0]['changes'][0]['value']['messages'][0]
        numero = msg['from']
        texto = msg['text']['body'].lower()

        if "boleto" in texto:
            enviar_whatsapp(numero, "Perfeito! Me envia seu CPF só com números que já busco seu boleto 🔍")
        elif texto.replace(".","").replace("-","").isdigit() and len(texto) >= 11:
            cpf_limpo = texto.replace(".","").replace("-","")
            enviar_whatsapp(numero, "Buscando... só um segundo...")
            resultado = buscar_boleto_inter(cpf_limpo)
            cobrancas = resultado.get('cobrancas', []) if isinstance(resultado, dict) else resultado
            if cobrancas and len(cobrancas) > 0:
                b = cobrancas[0]['cobranca']
                msg_final = f"Encontrei! ✅\nValor: R$ {b.get('valorNominal')}\nVenc: {b.get('dataVencimento')}\n\nLink: {b.get('linkBoleto')}\n\nLinha: {b.get('linhaDigitavel')}"
                enviar_whatsapp(numero, msg_final)
            else:
                enviar_whatsapp(numero, "Não achei boleto em aberto pra esse CPF. Confere o número?")
    except Exception as e:
        print(e)
    return "OK", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
