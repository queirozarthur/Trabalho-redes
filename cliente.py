import socket

from checksum import calcular_checksum
from config import BUFFER_SIZE, ENDERECO_SERVIDOR, TAM_TEXTO_MIN, PAYLOAD_MAX, TIMEOUT, TIPO_DADOS, TIPO_ACK, TIPO_FIM
from protocolo_mensagem import desmontar, montar, fragmentar, montar_pacote, desmontar_pacote


def enviar_dados(sock, seq, payload):
    chk = calcular_checksum(payload)
    pacote = montar_pacote(TIPO_DADOS, {"SEQ": seq, "CHK": chk}, payload)
    sock.sendto(pacote.encode(), ENDERECO_SERVIDOR)
    print(f"[DADOS] SEQ={seq} CHK={chk} PAYLOAD={payload!r}")


def receber_ack(sock):
    dados, _ = sock.recvfrom(BUFFER_SIZE)
    tipo, campos, _ = desmontar_pacote(dados.decode())
    print(f"[{tipo}] {campos}")
    return tipo, campos


modo = input("Modo (INDIVIDUAL/LOTE): ").strip().upper()
controle = input("Controle (GBN/SR): ").strip().upper()  
tam_texto = int(input("Tamanho do texto: "))

if tam_texto < TAM_TEXTO_MIN:
    print(f"Aviso: tamanho abaixo do minimo de {TAM_TEXTO_MIN}, o servidor deve recusar")

sock_cliente = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

mensagem = montar("TUDO_BEM", {
    "MODO": modo,
    "CTRL": controle,
    "TAM_TEXTO": tam_texto
})

sock_cliente.sendto(mensagem.encode(), ENDERECO_SERVIDOR)
print(f"Enviado: {mensagem}")

dados, endereco_servidor = sock_cliente.recvfrom(BUFFER_SIZE)
tipo, campos = desmontar(dados.decode())

print(f"Recebido de {endereco_servidor}: {dados.decode()}")

if tipo == "TUDO_BEM_SIM":
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

    fragmentos = fragmentar(texto, PAYLOAD_MAX)
    print(f"Texto dividido em {len(fragmentos)} fragmentos")

    sock_cliente.settimeout(TIMEOUT)

    ack_cumulativo = (controle == "GBN")

    if ack_cumulativo:
        print("Controle ativo: GBN (servidor confirma em grupo, ACK cumulativo)")
    else:
        print("Controle ativo: SR (servidor confirma cada pacote individualmente)")

    base = 0
    proximo = 0
    confirmados = set() 

    while base < len(fragmentos):
        tam_janela = 1 if modo == "INDIVIDUAL" else janela

        while proximo < len(fragmentos) and proximo < base + tam_janela:
            enviar_dados(sock_cliente, proximo, fragmentos[proximo])
            proximo += 1

        try:
            tipo, campos = receber_ack(sock_cliente)
            seq_confirmado = int(campos["SEQ"])
            janela = max(1, min(5, int(campos["JANELA"]))) 
        except socket.timeout:
            print(f"[TIMEOUT] nenhuma confirmacao em {TIMEOUT}s (retransmissao fica para o CP3)")
            continue
        except (KeyError, ValueError) as erro:
            print(f"Confirmacao veio estranha, ignorando: {erro}")
            continue

        if tipo != TIPO_ACK:
            print(f"SEQ={seq_confirmado} nao confirmado (retransmissao fica para o CP3)")
            continue

        if ack_cumulativo:
            if seq_confirmado >= base:
                base = seq_confirmado + 1
        else:
            confirmados.add(seq_confirmado)
            while base in confirmados:
                base += 1

        print(f"Janela: base={base} proximo={proximo} tamanho={tam_janela}")

    fim = montar_pacote(TIPO_FIM, {"TOTAL": len(fragmentos)})
    sock_cliente.sendto(fim.encode(), ENDERECO_SERVIDOR)
    print(f"[FIM] TOTAL={len(fragmentos)}")
else:
    print(f"Conexao recusada. Motivo: {campos['MOTIVO']}")

sock_cliente.close()