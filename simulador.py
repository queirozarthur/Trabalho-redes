"""Simulador deterministico de erros e perdas (lado cliente).

O usuario escolhe, antes do envio, quais SEQs sofrem cada tipo de falha.
A sintaxe aceita "SEQ" ou "SEQ:VEZES", separados por virgula:

    2,5     -> a 1a transmissao dos SEQs 2 e 5 sofre a falha
    3:2     -> as 2 primeiras transmissoes do SEQ 3 sofrem a falha

Cada falha e consumida quando acontece, entao as retransmissoes seguintes
passam normalmente. Assim o mesmo cenario sempre produz o mesmo resultado.
"""


def ler_falhas(texto):
    falhas = {}
    for item in texto.replace(" ", "").split(","):
        if not item:
            continue
        if ":" in item:
            seq, vezes = item.split(":", 1)
        else:
            seq, vezes = item, "1"
        seq, vezes = int(seq), int(vezes)
        if seq < 0 or vezes < 1:
            raise ValueError(f"Falha invalida: {item}")
        falhas[seq] = falhas.get(seq, 0) + vezes
    return falhas


def consumir(falhas, seq):
    try:
        seq = int(seq)
    except (TypeError, ValueError):
        return False
    if falhas.get(seq, 0) > 0:
        falhas[seq] -= 1
        return True
    return False


def corromper(pacote):
    """Troca o ultimo caractere do payload (ou do cabecalho, se vazio).

    O checksum continua o original, entao o servidor detecta a diferenca.
    """
    posicao = len(pacote) - 1
    original = pacote[posicao]
    trocado = "0" if original != "0" else "1"
    return pacote[:posicao] + trocado + pacote[posicao + 1:]


def configurar():
    print("--- Simulador de erros (Enter = nenhum) ---")
    print("Formato: SEQ ou SEQ:VEZES separados por virgula. Ex: 2,5:2")
    while True:
        try:
            return {
                "perder_dados": ler_falhas(input("Perder DADOS dos SEQs: ")),
                "corromper_dados": ler_falhas(input("Corromper DADOS dos SEQs: ")),
                "perder_ack": ler_falhas(input("Descartar ACK/NACK com SEQ: ")),
            }
        except ValueError as erro:
            print(f"Entrada invalida ({erro}), tente de novo")
