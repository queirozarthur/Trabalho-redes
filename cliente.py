import secrets
import socket
import time

import simulador
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
    desmontar_pacote_integro,
    fragmentar,
    montar,
    montar_pacote_integro,
)


def enviar_dados(sock, seq, pacote, retransmissao=False):
    rotulo = "[RETRANSMISSAO]" if retransmissao else "[DADOS]"

    if simulador.consumir(cenario["perder_dados"], seq):
        print(f"{rotulo} SEQ={seq} [SIMULADO: PERDIDO] pacote nao saiu do cliente")
        return

    if simulador.consumir(cenario["corromper_dados"], seq):
        pacote = simulador.corromper(pacote)
        rotulo += " [SIMULADO: CORROMPIDO]"

    sock.sendto(pacote.encode(), ENDERECO_SERVIDOR)
    print(f"{rotulo} SEQ={seq} PACOTE={pacote}")


def receber_controle(sock):
    dados, endereco = sock.recvfrom(BUFFER_SIZE)
    if endereco != ENDERECO_SERVIDOR:
        return None, {}

    try:
        tipo, campos, _ = desmontar_pacote_integro(dados.decode())
    except (UnicodeDecodeError, ValueError, IndexError):
        return None, {}

    if tipo in (TIPO_ACK, TIPO_NACK) and simulador.consumir(cenario["perder_ack"], campos.get("SEQ")):
        print(f"[{tipo}] {campos} [SIMULADO: PERDIDO] confirmacao descartada")
        return None, {}

    print(f"[{tipo}] {campos}")
    return tipo, campos


def retransmitir(sock, sequencias, pacotes, tempos_envio):
    agora = time.monotonic()
    for seq in sequencias:
        enviar_dados(sock, seq, pacotes[seq], retransmissao=True)
        tempos_envio[seq] = agora


try:
    chave = carregar_chave()
    chaves = expandir_chave(chave)
except ValueError as erro:
    raise SystemExit(str(erro)) from None

nonce = secrets.token_bytes(12)
modo = input("Modo (INDIVIDUAL/LOTE): ").strip().upper()
controle = input("Controle (GBN/SR): ").strip().upper()
tam_texto = int(input("Tamanho do texto: "))

if tam_texto < TAM_TEXTO_MIN:
    print(f"Aviso: tamanho abaixo do minimo de {TAM_TEXTO_MIN}, o servidor deve recusar")

sock_cliente = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

mensagem = montar("TUDO_BEM", {
    "MODO": modo,
    "CTRL": controle,
    "TAM_TEXTO": tam_texto,
    "CRIPTO": CRIPTOGRAFIA,
    "NONCE": nonce.hex(),
})

sock_cliente.sendto(mensagem.encode(), ENDERECO_SERVIDOR)
print(f"Enviado: {mensagem}")

dados, endereco_servidor = sock_cliente.recvfrom(BUFFER_SIZE)
tipo, campos = desmontar(dados.decode())

print(f"Recebido de {endereco_servidor}: {dados.decode()}")

if tipo == "TUDO_BEM_SIM":
    resposta_valida = (
        endereco_servidor == ENDERECO_SERVIDOR
        and campos.get("CRIPTO") == CRIPTOGRAFIA
        and campos.get("NONCE") == nonce.hex()
    )
    if not resposta_valida:
        sock_cliente.close()
        raise SystemExit("Resposta com endereco, criptografia ou nonce inesperado")
    modo = campos["MODO"]
    controle = campos["CTRL"]
    tam_texto = int(campos["TAM_TEXTO"])
    janela = int(campos["JANELA"])
    print(f"Conexao aceita. Modo={modo} Ctrl={controle} TamTexto={tam_texto} Janela={janela}")

    while True:
        texto = input(f"Digite o texto (até {tam_texto} caracteres): ")

        if not texto:
            print("O texto não pode ser vazio.")
        elif len(texto) > tam_texto:
            print(f"O texto ultrapassa o limite de {tam_texto} caracteres.")
        else:
            break

    cenario = simulador.configurar()

    fragmentos = fragmentar(texto, PAYLOAD_MAX)
    pacotes = []
    for seq, fragmento in enumerate(fragmentos):
        dados_fragmento = fragmento.encode("utf-8")
        cifrado = aplicar_fragmento(dados_fragmento, nonce, seq, chaves)
        pacote = montar_pacote_integro(TIPO_DADOS, {"SEQ": seq}, cifrado.hex())
        pacotes.append(pacote)
    print(f"Texto dividido em {len(fragmentos)} fragmentos")

    ack_cumulativo = controle == "GBN"
    if ack_cumulativo:
        print("Controle ativo: GBN (ACK cumulativo)")
    else:
        print("Controle ativo: SR (ACK individual por pacote)")

    base = 0
    proximo = 0
    confirmados = set()
    pendentes = {}
    tempos_envio = {}
    temporizador_gbn = None

    while base < len(fragmentos):
        tamanho_janela = 1 if modo == "INDIVIDUAL" else janela

        while proximo < len(fragmentos) and proximo < base + tamanho_janela:
            enviar_dados(sock_cliente, proximo, pacotes[proximo])
            pendentes[proximo] = pacotes[proximo]
            tempos_envio[proximo] = time.monotonic()
            if ack_cumulativo and temporizador_gbn is None:
                temporizador_gbn = tempos_envio[proximo]
            proximo += 1

        agora = time.monotonic()
        if ack_cumulativo:
            prazo = temporizador_gbn + TIMEOUT
        else:
            prazo = min(tempos_envio[seq] + TIMEOUT for seq in pendentes)
        sock_cliente.settimeout(max(0.001, prazo - agora))

        try:
            tipo, campos = receber_controle(sock_cliente)
        except socket.timeout:
            agora = time.monotonic()
            if ack_cumulativo:
                if temporizador_gbn is not None and agora >= temporizador_gbn + TIMEOUT:
                    retransmitir(sock_cliente, range(base, proximo), pendentes, tempos_envio)
                    temporizador_gbn = agora
            else:
                expirados = [
                    seq for seq in pendentes
                    if agora >= tempos_envio[seq] + TIMEOUT
                ]
                retransmitir(sock_cliente, expirados, pendentes, tempos_envio)
            continue

        if tipo not in (TIPO_ACK, TIPO_NACK):
            continue

        try:
            seq_confirmado = int(campos["SEQ"])
            janela_recebida = int(campos.get("JANELA", janela))
        except (KeyError, ValueError):
            print(f"Confirmacao veio estranha, ignorando: {campos}")
            continue

        janela_nova = max(1, min(JANELA_DEFAULT, janela_recebida))
        if janela_nova != janela:
            print(f"[JANELA] servidor ajustou a janela: {janela} -> {janela_nova}")
        janela = janela_nova

        if tipo == TIPO_NACK:
            if ack_cumulativo:
                retransmitir(sock_cliente, range(base, proximo), pendentes, tempos_envio)
                temporizador_gbn = time.monotonic()
            elif seq_confirmado in pendentes:
                retransmitir(sock_cliente, [seq_confirmado], pendentes, tempos_envio)
            continue

        if ack_cumulativo:
            if base <= seq_confirmado < proximo:
                base = seq_confirmado + 1
                for seq in list(pendentes):
                    if seq < base:
                        pendentes.pop(seq)
                        tempos_envio.pop(seq)
                temporizador_gbn = time.monotonic() if base < proximo else None
        elif seq_confirmado in pendentes:
            pendentes.pop(seq_confirmado)
            tempos_envio.pop(seq_confirmado)
            confirmados.add(seq_confirmado)
            while base in confirmados:
                confirmados.remove(base)
                base += 1

        print(f"Janela: base={base} proximo={proximo} tamanho={tamanho_janela}")

    total = len(fragmentos)
    fim = montar_pacote_integro(TIPO_FIM, {"TOTAL": total})
    confirmacao_fim = montar_pacote_integro(TIPO_FIM_CONFIRM, {"TOTAL": total})
    fim_confirmado = False

    while not fim_confirmado:
        if simulador.consumir_vez(cenario, "perder_fim"):
            print(f"[FIM] TOTAL={total} [SIMULADO: PERDIDO] pacote nao saiu do cliente")
        else:
            sock_cliente.sendto(fim.encode(), ENDERECO_SERVIDOR)
            print(f"[FIM] TOTAL={total}")
        prazo = time.monotonic() + TIMEOUT

        while time.monotonic() < prazo:
            sock_cliente.settimeout(max(0.001, prazo - time.monotonic()))
            try:
                tipo, campos = receber_controle(sock_cliente)
            except socket.timeout:
                break

            if tipo != TIPO_FIM_ACK:
                continue

            if simulador.consumir_vez(cenario, "perder_fim_ack"):
                print("[SIMULADO: PERDIDO] FIM_ACK descartado")
                continue

            try:
                total_confirmado = int(campos["TOTAL"])
            except (KeyError, ValueError):
                continue

            if total_confirmado == total:
                sock_cliente.sendto(confirmacao_fim.encode(), ENDERECO_SERVIDOR)
                print(f"[FIM_CONFIRM] TOTAL={total}")
                fim_confirmado = True
                break

        if not fim_confirmado:
            print(f"[TIMEOUT] sem FIM_ACK em {TIMEOUT}s; retransmitindo FIM")
else:
    print(f"Conexao recusada. Motivo: {campos['MOTIVO']}")

sock_cliente.close()
