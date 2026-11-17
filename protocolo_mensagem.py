from checksum import calcular_checksum, checksum_valido


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
        if not chave or chave in campos:
            raise ValueError("Campo vazio ou repetido no cabecalho")
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


def conteudo_checksum(tipo, campos, payload):
    ordenados = {}
    for chave in sorted(campos):
        if chave != "CHK":
            ordenados[chave] = campos[chave]
    return montar_pacote(tipo, ordenados, payload).encode("utf-8")


def montar_pacote_integro(tipo, campos, payload=""):
    campos = campos.copy()
    campos.pop("CHK", None)
    campos["CHK"] = calcular_checksum(conteudo_checksum(tipo, campos, payload))
    return montar_pacote(tipo, campos, payload)


def desmontar_pacote_integro(pacote):
    tipo, campos, payload = desmontar_pacote(pacote)
    try:
        checksum = int(campos["CHK"])
    except (KeyError, ValueError):
        raise ValueError("Pacote sem checksum valido") from None
    if not checksum_valido(conteudo_checksum(tipo, campos, payload), checksum):
        raise ValueError("Checksum nao confere")
    return tipo, campos, payload
