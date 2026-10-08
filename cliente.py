import socket

from config import BUFFER_SIZE, ENDERECO_SERVIDOR, TAM_TEXTO_MIN, PAYLOAD_MAX
from protocolo_mensagem import desmontar, montar, fragmentar

modo = input("Modo (INDIVIDUAL/LOTE): ").strip().upper()
controle = input("Controle (GBN/SR): ").strip().upper()  # Go-Back-N ou Repeticao Seletiva
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

    print(f"Texto dividido em {len(fragmentos)} fragmentos:")
    for sequencia, payload in enumerate(fragmentos):
        print(f"SEQ={sequencia} | TAM={len(payload)} | PAYLOAD={payload!r}")
else:
    print(f"Conexao recusada. Motivo: {campos['MOTIVO']}")

sock_cliente.close()