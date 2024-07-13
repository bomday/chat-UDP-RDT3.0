# Importando bibliotecas python 
import socket # Cria sockets par comunicação em uma rede
import random # Possibilita gerar números aleatórios
import struct # Possibilita empacotar e desempacotar dados binários
import threading # Cria threads, que são úteis para executar operações simultâneas

# Importando arquivos do código
import utils.constants as c
from utils.init import init

# Inicializando
clients_port = set() # Armazena clients' port existentes
ack = 0 #Armazena ack do cliente
seq = 0 # Armazena seq number do cliente
nickname = "" # Nickname do usuário
msg_count = 0 # Número de arquivos txt enviados por socket
is_conected = False # Conexão cliente com servidor
ack_received = False # Ack recebido
server_msg_received = [] # Guarda mensagem recebida do servidor

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
    path_file = f"./data/client/{file_name}.txt" 
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
        sum = (sum & 0xFFFF) + (sum >> 16)

    # Calcula o complemento de 1 da soma
    checksum = ~sum & 0xFFFF
    return checksum

# Função de recebimento de pacotes
def receive():  
    global ack, seq, ack_received, server_msg_received 

    while True:
        received_encoded_message, _ = client.recvfrom(c.BUFF_SIZE) # Recebe mensagem do servidor
        header = received_encoded_message[:c.HEADER_SIZE] # Separando o Header
        message_received = received_encoded_message[c.HEADER_SIZE:] # Separando a mensagem
        (frag_index, frag_count, seq_recv, ack_recv, checksum) = struct.unpack('!IIIII', header) # Desempacotando o header

        checksum_check = calculate_checksum(message_received) # Calcula checksum da mensagem recebida
        message = message_received.decode() # Decodifica mensagem

        # Confere recebimento de ack
        if message == '':
            # Desativar o timeout após receber ack da mensagem
            client.settimeout(None)

            # Confere se é checksum e ack esperado
            if (checksum_check == checksum) and (seq == ack_recv):
                # Alterna o seq num para próximo pacote
                seq = 1 if (seq == 0) else 0 

            ack_received = True

        # Confere recebimento de pacote   
        else:
            # Prepara lista para receber fragmentos de mensagens do servidor
            if server_msg_received == []:
                server_msg_received = [[] for i in range(frag_count)]

            # Confere se é checksum e pacote esperado
            if (checksum_check == checksum) and (seq_recv == ack):
                server_msg_received[frag_index].append(message) # Adiciona mensagem recebida a lista de fragmentos para mensagem completa se não for pacote duplicado
                ack_send = ack
                ack = 1 if (ack == 0) else 0 # Alterna o ack para próximo pacote
            
            # Pacote corrompido ou duplicado
            else: 
                # Alterna o ack para pedir reenvio de pacote
                ack_send = 1 if (ack_recv == 0) else 0
            
            message_ack = ''
            message_ack_enconded = message_ack.encode()
            checksum = calculate_checksum(message_ack_enconded) # Calcula checksum
            header = struct.pack('!IIIII', 0, 1, seq, ack_send, checksum) # Estrutura o cabeçalho do pacote
            pack = header + message_ack_enconded

            client.sendto(pack, (client_ip, c.SERVER_ADRR[1]))

            # Confere se lista com fragmentos da mensagem está completa
            if not any(isinstance(sublist, list) and len(sublist) == 0 for sublist in server_msg_received):
                joined_msg = ''.join(sum(server_msg_received, []))
                print(joined_msg)
                server_msg_received = []

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

        # Calcula número de fragmentos da mensagem
        frag_count = msg_size//c.FRAG_SIZE + 1
        # Calcula índice de pacotes para garantir entrega na ordem
        frag_index = 0

        for fragment in range(0, msg_size, c.FRAG_SIZE):
            end_fragment = min(fragment + c.FRAG_SIZE, msg_size) # Calcula limite do fragmento
            message = message_file[fragment:end_fragment+1] # Delimita mensagem a ser enviada no pacote
            checksum = calculate_checksum(message) # Calcula checksum
            header = struct.pack('!IIIII', frag_index, frag_count, seq, ack, checksum) # Estrutura o cabeçalho do pacote
            pack = header + message
            seq_sended = seq

            while seq_sended == seq:
                # Envia fragmentos da mensagem para o Servidor
                try:
                    # Ativar o timeout
                    client.settimeout(c.TIMEOUT)

                    client.sendto(pack, (client_ip, c.SERVER_ADRR[1]))

                    # Aguarda receber ack da mensagem
                    while not ack_received:
                        pass
                    
                except socket.timeout:
                    print("Timeout: Falha ao enviar mensagem")
                except Exception as e:
                    print(f"Erro enviando mensagem: {e}") 
            
            # Acrescenta índice para próximo pacote 
            frag_index += 1
            # Reseta ack recebido
            ack_received = False

        if message == "bye":
            is_conected = False