def multiplicar(a, b):
    resultado = 0
    for _ in range(8):
        if b & 1:
            resultado ^= a
        passou_do_byte = a & 0x80
        a = a << 1
        if passou_do_byte:
            a = a ^ 0x11B
        a = a & 0xFF
        b >>= 1
    return resultado


def substituir_byte(valor):
    inverso = 1
    for _ in range(254):
        inverso = multiplicar(inverso, valor)
    resultado = inverso ^ 0x63
    for deslocamento in range(1, 5):
        esquerda = inverso << deslocamento
        direita = inverso >> (8 - deslocamento)
        rotacao = (esquerda | direita) & 0xFF
        resultado = resultado ^ rotacao
    return resultado


SBOX = tuple(substituir_byte(valor) for valor in range(256))


def expandir_chave(chave):
    if len(chave) != 16:
        raise ValueError("A chave AES-128 precisa ter 16 bytes")
    expandida = list(chave)
    constante = 1
    while len(expandida) < 176:
        palavra = expandida[-4:]
        if len(expandida) % 16 == 0:
            palavra = palavra[1:] + palavra[:1]
            for i in range(4):
                palavra[i] = SBOX[palavra[i]]
            palavra[0] ^= constante
            constante = multiplicar(constante, 2)
        for valor in palavra:
            expandida.append(expandida[-16] ^ valor)
    chaves = []
    for inicio in range(0, 176, 16):
        chaves.append(expandida[inicio:inicio + 16])
    return chaves


def deslocar_linhas(estado):
    resultado = []
    for coluna in range(4):
        for linha in range(4):
            coluna_original = (coluna + linha) % 4
            posicao = 4 * coluna_original + linha
            resultado.append(estado[posicao])
    return resultado


def misturar_colunas(estado):
    resultado = []
    for inicio in range(0, 16, 4):
        a, b, c, d = estado[inicio:inicio + 4]
        resultado.extend([
            multiplicar(a, 2) ^ multiplicar(b, 3) ^ c ^ d,
            a ^ multiplicar(b, 2) ^ multiplicar(c, 3) ^ d,
            a ^ b ^ multiplicar(c, 2) ^ multiplicar(d, 3),
            multiplicar(a, 3) ^ b ^ c ^ multiplicar(d, 2),
        ])
    return resultado


def adicionar_chave(estado, chave):
    resultado = []
    for i in range(16):
        resultado.append(estado[i] ^ chave[i])
    return resultado


def cifrar_bloco(bloco, chaves):
    if len(bloco) != 16:
        raise ValueError("O bloco AES precisa ter 16 bytes")
    estado = adicionar_chave(bloco, chaves[0])
    for rodada in range(1, 11):
        for i in range(16):
            estado[i] = SBOX[estado[i]]
        estado = deslocar_linhas(estado)
        if rodada != 10:
            estado = misturar_colunas(estado)
        estado = adicionar_chave(estado, chaves[rodada])
    return bytes(estado)


def aplicar_fragmento(dados, nonce, sequencia, chaves):
    if len(nonce) != 12:
        raise ValueError("O nonce da sessao precisa ter 12 bytes")
    if not 0 <= sequencia < 4294967296:
        raise ValueError("A sequencia precisa caber em 32 bits")
    if len(dados) > 16:
        raise ValueError("Cada fragmento cifrado aceita no maximo 16 bytes")
    contador = nonce + sequencia.to_bytes(4, "big")
    mascara = cifrar_bloco(contador, chaves)
    resultado = []
    for i in range(len(dados)):
        resultado.append(dados[i] ^ mascara[i])
    return bytes(resultado)
