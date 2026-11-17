import os


def carregar_chave():
    valor = os.environ.get("REDES_CHAVE_HEX", "")
    if len(valor) != 32 or any(c not in "0123456789abcdefABCDEF" for c in valor):
        raise ValueError("Defina REDES_CHAVE_HEX com uma chave de 32 digitos hexadecimais")
    return bytes.fromhex(valor)


CRIPTOGRAFIA = "AES128-CTR"
IP = "127.0.0.1"
PORTA= 8082
JANELA_DEFAULT= 5
TAM_TEXTO_MIN = 30
BUFFER_SIZE = 1024 #valor de bytes maximo que a funcao recvfrom puxa para receber pacote
PAYLOAD_MAX = 4 #maximo de caracteres uteis por pacote, usado na fragmentacao a partir do CP2
TIMEOUT = 2 #segundos que o cliente espera uma confirmacao antes de retransmitir

ENDERECO_SERVIDOR = (IP, PORTA)

#tipos de mensagem depois do handshake
TIPO_DADOS = "DADOS"
TIPO_ACK = "ACK"
TIPO_NACK = "NACK"
TIPO_FIM = "FIM"
TIPO_FIM_ACK = "FIM_ACK"
TIPO_FIM_CONFIRM = "FIM_CONFIRM"
