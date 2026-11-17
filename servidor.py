import socket
import time

from criptografia import aplicar_fragmento, expandir_chave
from config import (
    CRIPTOGRAFIA,
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
    carregar_chave,
)
from protocolo_mensagem import (
    desmontar,
    desmontar_pacote,
    desmontar_pacote_integro,
    montar,
    montar_pacote_integro,
)


MODOS_VALIDOS = ["INDIVIDUAL", "LOTE"]
CONTROLES_VALIDOS = ["GBN", "SR"]
JANELA_MIN = 1

janela = JANELA_DEFAULT
ultimo_buraco = None


def reduzir_janela(motivo):
    """Erro detectado: corta a janela pela metade (minimo 1)."""
    global janela
    nova = max(JANELA_MIN, janela // 2)
    if nova != janela:
        print(f"[JANELA] {janela} -> {nova} ({motivo})")
    janela = nova


def aumentar_janela():
    """Pacote novo entregue em ordem: cresce 1 (maximo JANELA_DEFAULT)."""
    global janela
    if janela < JANELA_DEFAULT:
        print(f"[JANELA] {janela} -> {janela + 1} (entrega em ordem)")
        janela += 1


def sinalizar_buraco(esperado):
    """Reduz a janela uma unica vez por buraco na sequencia."""
    global ultimo_buraco
    if ultimo_buraco != esperado:
        ultimo_buraco = esperado
        reduzir_janela(f"SEQ={esperado} faltando")


def seq_de_pacote_corrompido(texto, total_maximo):
    """Tenta ler o SEQ de um DADOS cujo checksum falhou, para mandar NACK.

    Se o cabecalho tambem estiver ilegivel, devolve None e o pacote e so
    descartado (o cliente recupera pelo timeout).
    """
    try:
        tipo, campos, _ = desmontar_pacote(texto)
        seq = int(campos["SEQ"])
    except (ValueError, KeyError, IndexError):
        return None
    if tipo != TIPO_DADOS or not 0 <= seq < total_maximo:
        return None
    return seq


def aguardar_confirmacao_final(sock, endereco_cliente, total):
    confirmacao = montar_pacote_integro(TIPO_FIM_ACK, {"TOTAL": total})
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
            tipo, campos, _ = desmontar_pacote_integro(dados.decode())
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


try:
    chave = carregar_chave()
    chaves = expandir_chave(chave)
except ValueError as erro:
    raise SystemExit(str(erro)) from None

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
    nonce_hex = campos.get("NONCE", "")
    nonce_valido = len(nonce_hex) == 24 and all(c in "0123456789abcdef" for c in nonce_hex)

    if modo not in MODOS_VALIDOS:
        resposta = montar("RECUSADO", {"MOTIVO": "MODO_INVALIDO"})
    elif controle not in CONTROLES_VALIDOS:
        resposta = montar("RECUSADO", {"MOTIVO": "CTRL_INVALIDO"})
    elif tam_texto < TAM_TEXTO_MIN:
        resposta = montar("RECUSADO", {"MOTIVO": "TAM_TEXTO_MENOR_QUE_MINIMO"})
    elif tam_texto > PAYLOAD_MAX * 4294967296:
        resposta = montar("RECUSADO", {"MOTIVO": "TAM_TEXTO_MAIOR_QUE_LIMITE"})
    elif campos.get("CRIPTO") != CRIPTOGRAFIA:
        resposta = montar("RECUSADO", {"MOTIVO": "CRIPTO_INVALIDA"})
    elif not nonce_valido:
        resposta = montar("RECUSADO", {"MOTIVO": "NONCE_INVALIDO"})
    else:
        nonce = bytes.fromhex(nonce_hex)
        resposta = montar("TUDO_BEM_SIM", {
            "MODO": modo,
            "CTRL": controle,
            "TAM_TEXTO": tam_texto,
            "JANELA": JANELA_DEFAULT,
            "CRIPTO": CRIPTOGRAFIA,
            "NONCE": nonce_hex,
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
            texto_pacote = dados.decode()
        except UnicodeDecodeError:
            print("Pacote com bytes invalidos, ignorando")
            continue

        try:
            tipo, campos, payload = desmontar_pacote_integro(texto_pacote)
        except (ValueError, IndexError) as erro:
            seq_corrompido = seq_de_pacote_corrompido(texto_pacote, total_maximo)
            if seq_corrompido is None:
                print(f"Pacote veio estranho, ignorando: {erro}")
                continue
            print(f"[ERRO] SEQ={seq_corrompido} {erro} PACOTE={texto_pacote}")
            reduzir_janela("checksum invalido")
            confirmacao = montar_pacote_integro(TIPO_NACK, {"SEQ": seq_corrompido, "JANELA": janela})
            sock_servidor.sendto(confirmacao.encode(), endereco_cliente)
            print(f"Enviado: {confirmacao}")
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

            confirmacao = montar_pacote_integro(TIPO_FIM_ACK, {"TOTAL": total})
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

        if seq < 0 or seq >= total_maximo:
            print(f"Pacote invalido descartado: SEQ={seq}")
            continue

        try:
            if not payload or len(payload) > 32 or any(c not in "0123456789abcdef" for c in payload):
                raise ValueError("Payload hexadecimal invalido")
            cifrado = bytes.fromhex(payload)
            decifrado = aplicar_fragmento(cifrado, nonce, seq, chaves)
            fragmento = decifrado.decode("utf-8")
            if not fragmento or len(fragmento) > PAYLOAD_MAX:
                raise ValueError("Fragmento fora do limite de caracteres")
        except ValueError as erro:
            print(f"Fragmento invalido SEQ={seq}: {erro}")
            reduzir_janela("fragmento invalido")
            confirmacao = montar_pacote_integro(TIPO_NACK, {"SEQ": seq, "JANELA": janela})
            sock_servidor.sendto(confirmacao.encode(), endereco_cliente)
            continue

        print(f"[DADOS] SEQ={seq} CHECKSUM={checksum} CIFRADO={payload} OK")

        if controle == "GBN":
            if seq == esperado:
                recebidos[seq] = fragmento
                esperado += 1
                aumentar_janela()
            elif seq < esperado:
                print(f"[DUPLICADO] SEQ={seq} ja entregue, reenviando ACK cumulativo")
            else:
                print(f"Fora de ordem (esperado SEQ={esperado}), descartado")
                sinalizar_buraco(esperado)
            confirmacao = montar_pacote_integro(TIPO_ACK, {"SEQ": esperado - 1, "JANELA": janela})
        else:
            # buffer de recepcao tem capacidade fixa; a janela anunciada pode ser menor
            if seq >= esperado + JANELA_DEFAULT:
                print(f"SEQ={seq} fora da janela [{esperado}, {esperado + JANELA_DEFAULT - 1}], descartado")
                continue
            if seq in recebidos:
                print(f"[DUPLICADO] SEQ={seq} ja recebido, reenviando ACK")
            else:
                recebidos[seq] = fragmento
                if seq > esperado:
                    print(f"SEQ={seq} guardado no buffer (aguardando SEQ={esperado})")
                    sinalizar_buraco(esperado)
                else:
                    aumentar_janela()
                while esperado in recebidos:
                    esperado += 1
            confirmacao = montar_pacote_integro(TIPO_ACK, {"SEQ": seq, "JANELA": janela})

        sock_servidor.sendto(confirmacao.encode(), endereco_cliente)
        print(f"Enviado: {confirmacao}")

sock_servidor.close()
