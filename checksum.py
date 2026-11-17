def calcular_checksum(dados):
    if isinstance(dados, str):
        dados = dados.encode("utf-8")
    soma = 0
    for i in range(0, len(dados), 2):
        if i + 1 < len(dados):
            palavra = (dados[i] << 8) + dados[i + 1]
        else:
            palavra = dados[i] << 8
        soma += palavra
        soma = (soma & 0xFFFF) + (soma >> 16)
    return ~soma & 0xFFFF

def checksum_valido(dados, checksum_recebido):
    if not isinstance(checksum_recebido, int) or not 0 <= checksum_recebido <= 0xFFFF:
        return False
    return calcular_checksum(dados) == checksum_recebido
