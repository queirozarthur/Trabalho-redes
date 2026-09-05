import socket
from config import ENDERECO_SERVIDOR, BUFFER_SIZE, TAM_TEXTO_MIN

modo = input("Modo (INDIVIDUAL/LOTE): ")
controle = input("Controle (GBN/SR): ") #GO-Back-N ou Repeticao Seletiva
tam_texto = int(input("Tamanho do texto: "))

if tam_texto < TAM_TEXTO_MIN:
    print("Tamanho abaixo do minimo acordado")

sock_cliente = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

mensagem = f"TUDO_BEM;MODO={modo};CTRL={controle};TAM_TEXTO={tam_texto}"

sock_cliente.sendto(mensagem.encode(), ENDERECO_SERVIDOR)
print("enviado")
sock_cliente.recvfrom(BUFFER_SIZE)
