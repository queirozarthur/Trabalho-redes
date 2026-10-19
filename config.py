IP = "127.0.0.1"
PORTA= 8082
JANELA_DEFAULT= 5
TAM_TEXTO_MIN = 30
BUFFER_SIZE = 1024 #valor de bytes maximo que a funcao recvfrom puxa para receber pacote
PAYLOAD_MAX = 4 #maximo de caracteres uteis por pacote, usado na fragmentacao a partir do CP2
TIMEOUT = 2 #segundos que o cliente espera uma confirmacao antes de retransmitir

ENDERECO_SERVIDOR = (IP, PORTA)

#tipos de mensagem depois do handshake
TIPO_DADOS = "DADOS"
TIPO_ACK = "ACK"
TIPO_NACK = "NACK"
TIPO_FIM = "FIM"
TIPO_FIM_ACK = "FIM_ACK"
TIPO_FIM_CONFIRM = "FIM_CONFIRM"
