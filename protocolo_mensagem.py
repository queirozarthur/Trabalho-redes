SEPARADOR = ";"
IGUAL = "="
SEPARADOR_PAYLOAD = "|"

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

def montar_pacote(tipo, campos, payload=""):
    return montar(tipo, campos) + SEPARADOR_PAYLOAD + payload

def desmontar_pacote(pacote):
    cabecalho, payload = pacote.split(SEPARADOR_PAYLOAD, 1)
    tipo, campos = desmontar(cabecalho)
    return tipo, campos, payload

def fragmentar(texto, tamanho):
    return [texto[i:i + tamanho] for i in range(0, len(texto), tamanho)]