def calcular_checksum(texto):
    soma = 0
    dados = texto.encode()
    for i in range(0, len(dados), 2):
        if i + 1 < len(dados):
            palavra = (dados[i] << 8) + dados[i + 1]
        else:
            palavra = dados[i] << 8
        soma += palavra
        soma = (soma & 0xFFFF) + (soma >> 16)
    return ~soma & 0xFFFF

def checksum_valido(texto, checksum_recebido):
    return calcular_checksum(texto) == checksum_recebido