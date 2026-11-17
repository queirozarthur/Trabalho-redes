def multiplicar(a, b):
    resultado = 0
    for _ in range(8):
        if b & 1:
            resultado ^= a
        a = ((a << 1) ^ (0x11B if a & 0x80 else 0)) & 0xFF
        b >>= 1
    return resultado


def substituir_byte(valor):
    inverso = 0
    if valor:
        inverso = 1
        base = valor
        expoente = 254
        while expoente:
            if expoente & 1:
                inverso = multiplicar(inverso, base)
            base = multiplicar(base, base)
            expoente >>= 1
    resultado = inverso ^ 0x63
    for deslocamento in range(1, 5):
        resultado ^= ((inverso << deslocamento) | (inverso >> (8 - deslocamento))) & 0xFF
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
            palavra = [SBOX[valor] for valor in palavra[1:] + palavra[:1]]
            palavra[0] ^= constante
            constante = multiplicar(constante, 2)
        for valor in palavra:
            expandida.append(expandida[-16] ^ valor)
    return [expandida[inicio:inicio + 16] for inicio in range(0, 176, 16)]


def deslocar_linhas(estado):
    return [estado[4 * ((coluna + linha) % 4) + linha]
            for coluna in range(4) for linha in range(4)]


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


class AES128:
    def __init__(self, chave):
        self.chaves = expandir_chave(chave)

    def cifrar_bloco(self, bloco):
        if len(bloco) != 16:
            raise ValueError("O bloco AES precisa ter 16 bytes")
        estado = [valor ^ chave for valor, chave in zip(bloco, self.chaves[0])]
        for rodada in range(1, 11):
            estado = [SBOX[valor] for valor in estado]
            estado = deslocar_linhas(estado)
            if rodada != 10:
                estado = misturar_colunas(estado)
            estado = [valor ^ chave for valor, chave in zip(estado, self.chaves[rodada])]
        return bytes(estado)

    def aplicar_ctr(self, dados, contador_inicial):
        if len(contador_inicial) != 16:
            raise ValueError("O contador CTR precisa ter 16 bytes")
        contador = int.from_bytes(contador_inicial, "big")
        blocos = (len(dados) + 15) // 16
        if contador + blocos > 1 << 128:
            raise ValueError("O contador CTR ultrapassou o limite")
        resultado = bytearray()
        for inicio in range(0, len(dados), 16):
            mascara = self.cifrar_bloco(contador.to_bytes(16, "big"))
            bloco = dados[inicio:inicio + 16]
            resultado.extend(valor ^ mascara[i] for i, valor in enumerate(bloco))
            contador += 1
        return bytes(resultado)

    def aplicar_fragmento(self, dados, nonce, sequencia):
        if len(nonce) != 12:
            raise ValueError("O nonce da sessao precisa ter 12 bytes")
        if not 0 <= sequencia < 1 << 32:
            raise ValueError("A sequencia precisa caber em 32 bits")
        if len(dados) > 16:
            raise ValueError("Cada fragmento cifrado aceita no maximo 16 bytes")
        contador = nonce + sequencia.to_bytes(4, "big")
        return self.aplicar_ctr(dados, contador)
