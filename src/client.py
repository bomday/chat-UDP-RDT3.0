# Importando bibliotecas python 
import math
import socket # Cria sockets par comunicação em uma rede
import random # Possibilita gerar números aleatórios
import threading # Cria threads, que são úteis para executar operações simultâneas
from threading import Lock  # Importa a classe Lock do módulo threading para sincronização.
from time import time  # Importa a função time do módulo time para medir o tempo.

# Importando arquivos do código
import utils.constants as c
from utils.init import init

# Inicializando
clients_port = set() # Armazena clients' port existentes
client_ack_seq = [0, 0] # Armazena ack e seq number de cada cliente
data_lock = Lock()  # Cria um bloqueio (lock) para evitar acesso simultâneo a variáveis compartilhadas entre as threads.
nickname = "" # Nickname do usuário
msg_count = 0 # Número de arquivos txt enviados por socket
is_conected = False # Conexão cliente com servidor

# Criação do socket UDP
client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# Atribuição de uma porta aleatória entre 1000 e 9998
CLIENT_PORT = random.randint(1000, 9998)

# Garante que Client Adress seja sempre único
while CLIENT_PORT in clients_port:
    CLIENT_PORT = random.randint(1000, 9998)

# Finaliza configuração de socket
clients_port.add(CLIENT_PORT)
client.bind((c.SERVER_ADRR[0], CLIENT_PORT))
client_ip = client.getsockname()[0]

# Função responsável por salvar string em arquivo .txt
def convert_string_to_txt(client_port, string):
    global msg_count

    file_name = f'{client_port}{msg_count}'
    path_file = f"./udp-ajustado/data/client/{file_name}.txt"
    msg_count += 1

    # Salvando string em arquivo .txt
    file = open(path_file, "a")
    file.write(string)

    # Retornando o caminho do arquivo
    return path_file

def calculate_checksum(message):
    # Inicializa a soma
    sum = 0

    # Faz soma de mensagem em pares de bytes (16 bits)
    for i in range(0, len(message), 2):
        # Extrai dois bytes e faz a soma no formato de 16 bits
        if i + 1 < len(message):
            two_bytes = (message[i] << 8) + message[i + 1]
        else:
            two_bytes = message[i] << 8

        # Soma os pares de bytes
        sum += two_bytes

        # Adiciona carry over se a soma for maior que 16 bits
        # (sum & 0xFFFF) garante a separação dos bits menos significativos, ou seja, mais a direita
        # (sum >> 16) garante a separação dos excedentes
        sum = (sum & 0xFFFF) + (sum >> 16)

    # Calcula o complemento de 1 da soma
    checksum = ~sum & 0xFFFF
    return checksum

# Função de recebimento de pacotes
def receive():    
    while True:
        received_encoded_message, _ = client.recvfrom(c.BUFF_SIZE)
        message = received_encoded_message.decode()
        checksum = calculate_checksum(received_encoded_message)
        print(f"Received message: {message}, checksum {checksum}")
        print(message)

#    ack_expected = client_ack_seq[0]
#
#    if received_message == ack_expected:
#        client_ack_seq[0] = '1' if (client_ack_seq[0] == '0') else '0'  # Alterna o seq num do pacote

# Inicia uma thread para as funções de recebimento
receive_thread = threading.Thread(target=receive)
receive_thread.start()

# Iniciando cliente
init()

# Loop principal para envio de mensagens
while True:
    # Solicita ao usuário para inserir uma mensagem
    message = input()

    # Converte string em txt
    path_file = convert_string_to_txt(CLIENT_PORT, message)

    # Lendo o conteúdo do arquivo .txt
    file = open(path_file,"rb")
    message_file = file.read()

    msg_size = len(message_file)
    
    if message == "":
        print("Insira sua mensagem!")
    
    # Se não estiver conectado, exibe mensagem de que não está conectado
    elif not is_conected and message == "bye": 
        print("Você não está conectado à sala!")

    # Se já estiver conectado, exibe mensagem de que já está conectado
    elif is_conected and message.startswith("hi, meu nome eh "):
        print("Você já está conectado à sala!")

    # Caso não esteja conectado e a mensagem não seja um comando, exibe mensagem de comando inválido
    elif not is_conected and not message.startswith("hi, meu nome eh "):
        print("Comando inválido!")

    else:
        # Separa mensagem em fragmentos para envio de pacotes
        if message.startswith("hi, meu nome eh "):
            nickname = message[16:] 
            is_conected = True 

        for fragment in range(0, msg_size, c.FRAG_SIZE):
            # Calcula limite do fragmento
            end_fragment = min(fragment + c.FRAG_SIZE, msg_size)
            message = message_file[fragment:end_fragment]
            checksum = calculate_checksum(message)
            # Envia fragmentos da mensagem para o Servidor
            client.sendto(message, (client_ip, c.SERVER_ADRR[1]))
            print(f"Sended data: CLIENT, fragment {fragment//c.FRAG_SIZE + 1}, checksum {checksum}")

        if message == "bye":
            is_conected = False




    #time_start = time()  # Armazena o tempo inicial do envio da mensagem
    #for i in range(0, msg_size, c.FRAG_SIZE):
    #    frag = encoded_message[i:i + c.FRAG_SIZE]
    #    current_ack = client_ack_seq[0]
    #
    #    while client_ack_seq[0] == current_ack:
    #        time_curr = time() # Armazena o tempo atual do envio da mensagem
    #        if (time_curr - time_start >= c.TIMEOUT):  # Verifica se o tempo decorrido é maior que timeout
    #            client.sendto(frag, (client_ip, c.SERVER_ADRR[1]))  # Reenvia a mensagem em caso de timeout
    #            continue

        # Define novo sequence number
    #    seq_num = '1' if (client_ack_seq[1] == '0') else '0'  # Alterna o seq num do pacote
    #    client_ack_seq[1] = seq_num

    #    time_start = time()  # Reseta o tempo inicial