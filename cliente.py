import socket
from config import ENDERECO_SERVIDOR, BUFFER_SIZE, TAM_TEXTO_MIN
from protocolo_mensagem import montar, desmontar

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
else:
    print(f"Conexao recusada. Motivo: {campos['MOTIVO']}")

sock_cliente.close()