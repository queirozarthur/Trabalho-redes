import socket
from config import (ENDERECO_SERVIDOR, BUFFER_SIZE, JANELA_DEFAULT, TAM_TEXTO_MIN, TIPO_DADOS, TIPO_ACK, TIPO_NACK, TIPO_FIM)
from protocolo_mensagem import montar, desmontar, montar_pacote, desmontar_pacote
from checksum import checksum_valido

MODOS_VALIDOS = ["INDIVIDUAL", "LOTE"]
CONTROLES_VALIDOS = ["GBN", "SR"]

sock_servidor = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock_servidor.bind(ENDERECO_SERVIDOR)
print("Aguardando conexao...")

dados, endereco_cliente = sock_servidor.recvfrom(BUFFER_SIZE)
tipo, campos = desmontar(dados.decode())

print(f"Recebido de {endereco_cliente}: tipo={tipo} campos={campos}")

aceito = False

if tipo != "TUDO_BEM":
    resposta = montar("RECUSADO", {"MOTIVO": "TIPO_DESCONHECIDO"})
else:
    modo = campos["MODO"]
    controle = campos["CTRL"]
    tam_texto = int(campos["TAM_TEXTO"])

    if modo not in MODOS_VALIDOS:
        resposta = montar("RECUSADO", {"MOTIVO": "MODO_INVALIDO"})
    elif controle not in CONTROLES_VALIDOS:
        resposta = montar("RECUSADO", {"MOTIVO": "CTRL_INVALIDO"})
    elif tam_texto < TAM_TEXTO_MIN:
        resposta = montar("RECUSADO", {"MOTIVO": "TAM_TEXTO_MENOR_QUE_MINIMO"})
    else:
        resposta = montar("TUDO_BEM_SIM", {
            "MODO": modo,
            "CTRL": controle,
            "TAM_TEXTO": tam_texto,
            "JANELA": JANELA_DEFAULT
        })
        aceito = True

sock_servidor.sendto(resposta.encode(), endereco_cliente)
print(f"Respondido: {resposta}")

if aceito:
    recebidos = {}

    while True:
        dados, endereco = sock_servidor.recvfrom(BUFFER_SIZE)
        tipo, campos, payload = desmontar_pacote(dados.decode())

        if tipo == TIPO_FIM:
            break

        if tipo == TIPO_DADOS:
            seq = int(campos["SEQ"])
            checksum = int(campos["CHECKSUM"])
            integro = checksum_valido(payload, checksum)

            status = "OK" if integro else "CORROMPIDO"
            print(f"[DADOS] SEQ={seq} CHECKSUM={checksum} PAYLOAD={payload!r} {status}")

            if integro:
                recebidos[seq] = payload
                confirmacao = montar_pacote(TIPO_ACK, {"SEQ": seq})
            else:
                confirmacao = montar_pacote(TIPO_NACK, {"SEQ": seq})

            sock_servidor.sendto(confirmacao.encode(), endereco)
            print(f"Enviado: {confirmacao}")

    texto = "".join(recebidos[seq] for seq in sorted(recebidos))
    print(f"Texto completo: {texto}")

sock_servidor.close()