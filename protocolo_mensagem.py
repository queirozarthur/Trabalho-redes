SEPARADOR = ";"
IGUAL = "="

def montar(tipo, campos):
    partes = [tipo]
    for chave, valor in campos.items():
        partes.append(f"{chave}{IGUAL}{valor}")
    return SEPARADOR.join(partes)

def desmontar(mensagem):
    partes = mensagem.split(SEPARADOR)
    tipo = partes[0]
    campos = {}
    for parte in partes[1:]:
        chave, valor = parte.split(IGUAL, 1)
        campos[chave] = valor
    return tipo, campos