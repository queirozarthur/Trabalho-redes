import socket
from config import ENDERECO_SERVIDOR, BUFFER_SIZE, JANELA_DEFAULT, TAM_TEXTO_MIN

sock_servidor = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

sock_servidor.bind((ENDERECO_SERVIDOR))
print("Aguardando conexao...")
dados, endereco_cliente = sock_servidor.recvfrom(BUFFER_SIZE)

print(dados)

mensagem = dados.decode()

print(mensagem)



