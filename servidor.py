import socket
import time

from checksum import checksum_valido
from config import (
    BUFFER_SIZE,
    ENDERECO_SERVIDOR,
    JANELA_DEFAULT,
    PAYLOAD_MAX,
    TAM_TEXTO_MIN,
    TIMEOUT,
    TIPO_ACK,
    TIPO_DADOS,
    TIPO_FIM,
    TIPO_FIM_ACK,
    TIPO_FIM_CONFIRM,
    TIPO_NACK,
)
from protocolo_mensagem import desmontar, desmontar_pacote, montar, montar_pacote


MODOS_VALIDOS = ["INDIVIDUAL", "LOTE"]
CONTROLES_VALIDOS = ["GBN", "SR"]


def aguardar_confirmacao_final(sock, endereco_cliente, total):
    confirmacao = montar_pacote(TIPO_FIM_ACK, {"TOTAL": total})
    prazo = time.monotonic() + 2 * TIMEOUT

    while True:
        restante = prazo - time.monotonic()
        if restante <= 0:
            print("[TIMEOUT] cliente não confirmou o FIM_CONFIRM")
            return

        sock.settimeout(restante)
        try:
            dados, endereco = sock.recvfrom(BUFFER_SIZE)
        except socket.timeout:
            print("[TIMEOUT] cliente não confirmou o FIM_CONFIRM")
            return

        if endereco != endereco_cliente:
            continue

        try:
            tipo, campos, _ = desmontar_pacote(dados.decode())
            total_recebido = int(campos["TOTAL"])
        except (UnicodeDecodeError, ValueError, KeyError, IndexError):
            continue

        if tipo == TIPO_FIM_CONFIRM and total_recebido == total:
            print(f"[FIM_CONFIRM] TOTAL={total}")
            return

        if tipo == TIPO_FIM and total_recebido == total:
            sock.sendto(confirmacao.encode(), endereco_cliente)
            print(f"[FIM_ACK] reenviado TOTAL={total}")
            prazo = time.monotonic() + 2 * TIMEOUT


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
            "JANELA": JANELA_DEFAULT,
        })
        aceito = True

sock_servidor.sendto(resposta.encode(), endereco_cliente)
print(f"Respondido: {resposta}")

if aceito:
    recebidos = {}
    esperado = 0
    total_maximo = (tam_texto + PAYLOAD_MAX - 1) // PAYLOAD_MAX
    finalizado = False

    while not finalizado:
        dados, endereco = sock_servidor.recvfrom(BUFFER_SIZE)
        if endereco != endereco_cliente:
            continue

        try:
            tipo, campos, payload = desmontar_pacote(dados.decode())
        except (UnicodeDecodeError, ValueError, IndexError) as erro:
            print(f"Pacote veio estranho, ignorando: {erro}")
            continue

        if tipo == TIPO_FIM:
            try:
                total = int(campos["TOTAL"])
            except (KeyError, ValueError):
                print("Pacote FIM sem TOTAL valido, ignorando")
                continue

            todos_recebidos = (
                0 <= total <= total_maximo
                and len(recebidos) == total
                and all(seq in recebidos for seq in range(total))
            )
            if not todos_recebidos:
                print(f"FIM TOTAL={total} rejeitado: fragmentos incompletos")
                continue

            texto = "".join(recebidos[seq] for seq in range(total))
            print(f"Texto completo: {texto}")

            confirmacao = montar_pacote(TIPO_FIM_ACK, {"TOTAL": total})
            sock_servidor.sendto(confirmacao.encode(), endereco_cliente)
            print(f"[FIM_ACK] TOTAL={total}")
            aguardar_confirmacao_final(sock_servidor, endereco_cliente, total)
            finalizado = True
            continue

        if tipo != TIPO_DADOS:
            continue

        try:
            seq = int(campos["SEQ"])
            checksum = int(campos["CHK"])
        except (KeyError, ValueError):
            print("Pacote DADOS sem SEQ/CHK valido, ignorando")
            continue

        if seq < 0 or seq >= total_maximo or len(payload) > PAYLOAD_MAX:
            print(f"Pacote invalido descartado: SEQ={seq}")
            continue

        integro = checksum_valido(payload, checksum)
        status = "OK" if integro else "CORROMPIDO"
        print(f"[DADOS] SEQ={seq} CHECKSUM={checksum} PAYLOAD={payload!r} {status}")

        if not integro:
            confirmacao = montar_pacote(TIPO_NACK, {"SEQ": seq, "JANELA": JANELA_DEFAULT})
        elif controle == "GBN":
            if seq == esperado:
                recebidos[seq] = payload
                esperado += 1
            else:
                print(f"Fora de ordem (esperado SEQ={esperado}), descartado")
            confirmacao = montar_pacote(TIPO_ACK, {"SEQ": esperado - 1, "JANELA": JANELA_DEFAULT})
        else:
            if seq >= esperado + JANELA_DEFAULT:
                print(f"SEQ={seq} fora da janela [{esperado}, {esperado + JANELA_DEFAULT - 1}], descartado")
                continue
            if seq >= esperado:
                recebidos[seq] = payload
                while esperado in recebidos:
                    esperado += 1
            confirmacao = montar_pacote(TIPO_ACK, {"SEQ": seq, "JANELA": JANELA_DEFAULT})

        sock_servidor.sendto(confirmacao.encode(), endereco_cliente)
        print(f"Enviado: {confirmacao}")

sock_servidor.close()
