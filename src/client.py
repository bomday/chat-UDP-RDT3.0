# Importando bibliotecas python 
import os # Biblioteca para manipulação de arquivos e diretórios
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
syn_ack = False # SYN-ACK recebido
fin_ack = False # FIN-ACK recebido
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

def check_previous_users(nickname):
    path_folder = f'./data/client/{nickname}'
    return os.path.exists(path_folder)

# Função responsável por salvar string em arquivo .txt
def convert_string_to_txt(client_port, nickname, string):
    global msg_count
    
    path_folder = f'./data/client/{nickname}/'

    if not os.path.exists(path_folder):
        os.makedirs(path_folder)

    file_name = f'{client_port}{msg_count}'
    path_file = f"{path_folder}{file_name}.txt"
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
    global ack, seq, nickname, msg_count, ack_received, syn_ack, fin_ack, server_msg_received, is_conected

    while True:
        received_encoded_message, _ = client.recvfrom(c.BUFF_SIZE) # Recebe mensagem do servidor
        header = received_encoded_message[:c.HEADER_SIZE] # Separando o Header
        message_received = received_encoded_message[c.HEADER_SIZE:] # Separando a mensagem
        (frag_index, frag_count, seq_recv, ack_recv, checksum) = struct.unpack('!IIIII', header) # Desempacotando o header

        checksum_check = calculate_checksum(message_received) # Calcula checksum da mensagem recebida
        message = message_received.decode() # Decodifica mensagem

        # Confere recebimento de ack
        if message == '' or message == 'SYN-ACK':
            # Desativar o timeout após receber ack da mensagem
            client.settimeout(None)
            
            if message == 'SYN-ACK':
                syn_ack = True

            # Confere se é checksum e ack esperado
            if checksum_check == checksum and seq == ack_recv and message != 'SYN-ACK':
                # Alterna o seq num para próximo pacote
                seq = 1 if (seq == 0) else 0 

            ack_received = True
        # Confere recebimento de pacote   
        else:
            if message == 'Voce saiu da sala':
                # Reseta o timeout
                client.settimeout(None)

                fin_ack = True
                ack_received = True

                message_ack = 'ACK'
                ack_send = ack
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

            if message_ack == 'ACK':
                while is_conected: # Aguarda timeout de finalização, onde cliente não recebe mais pacotes do servidor
                    try:
                        # Ativar o timeout
                        client.settimeout(c.TIMEOUT)

                        client.sendto(pack, (client_ip, c.SERVER_ADRR[1]))
                        
                        # Aguarda se vai receber pacote ou pode finalizar conexão
                        received_encoded_message, _ = client.recvfrom(c.BUFF_SIZE) # Recebe mensagem do servidor
                    # Finaliza conexão se não tem resposta, pois significa que ACK de finalização foi recebido  
                    except socket.timeout:
                        # Desativar o timeout
                        client.settimeout(None)

                        # Reseta tudo
                        is_conected = False # Conexão cliente com servidor 
                        ack = 0 # Reseta ack do cliente
                        seq = 0 # Reseta seq number do cliente
                        nickname = "" # Reseta Nickname do usuário
                        msg_count = 0 # Reseta Número de arquivos txt enviados por socket
                        ack_received = False # Reseta Ack recebido
                        syn_ack = False # Reseta SYN-ACK recebido
                        fin_ack = False # Reseta FIN-ACK recebido
                        server_msg_received = [] # Reseta mensagens recebida do servidor
                        print('Voce saiu da sala')
                    except Exception as e:
                        print(f"Erro enviando mensagem: {e}")
            else:
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
    
    if message == "":
        print("Insira sua mensagem!")
    
    # Se não estiver conectado, exibe mensagem de que não está conectado
    elif not is_conected and message == "bye": 
        print("Você não está conectado à sala!")

    # Se já estiver conectado, exibe mensagem de que já está conectado
    elif is_conected and message.startswith("hi, meu nome eh "):
        print("Você já está conectado à sala!")

    # Caso não esteja conectado e a mensagem não seja um comando, exibe mensagem de comando inválido
    elif (not is_conected and not message.startswith("hi, meu nome eh ")) or (message == "ACK" or message == "FIN" or message == "SYN"):
        print("Comando inválido!")

    else:
        if message.startswith("hi, meu nome eh "):
            nickname = message[16:] 

        if check_previous_users(nickname) and message.startswith("hi, meu nome eh "):
            print("Usuário já cadastrado anteriormente. Digite outro nome de usuário.")
        else:
            # Converte string em txt
            path_file = convert_string_to_txt(CLIENT_PORT, nickname, message)

            # Lendo o conteúdo do arquivo .txt
            file = open(path_file,"rb")
            message_file = file.read()

            msg_size = len(message_file)

            if message == 'bye':
                message_syn_ack = 'FIN'
                message_syn_ack_enconded = message_syn_ack.encode()
                checksum = calculate_checksum(message_syn_ack_enconded) # Calcula checksum
                header = struct.pack('!IIIII', 0, 1, seq, ack, checksum) # Estrutura o cabeçalho do pacote
                pack = header + message_syn_ack_enconded

                while not fin_ack:
                    try:
                        # Ativar o timeout
                        client.settimeout(c.TIMEOUT)

                        client.sendto(pack, (client_ip, c.SERVER_ADRR[1]))
                        
                        # Aguarda receber ack da mensagem
                        while not ack_received:
                            pass

                        ack_received = False
                        
                    except socket.timeout:
                        print("Timeout: Falha ao enviar mensagem")
                    except Exception as e:
                        print(f"Erro enviando mensagem: {e}") 
            else:
                # Three way handshake
                if message.startswith("hi, meu nome eh "):
                    message_syn_ack = 'SYN'
                    message_syn_ack_enconded = message_syn_ack.encode()
                    checksum = calculate_checksum(message_syn_ack_enconded) # Calcula checksum
                    header = struct.pack('!IIIII', 0, 1, seq, ack, checksum) # Estrutura o cabeçalho do pacote
                    pack = header + message_syn_ack_enconded
                    
                    while not syn_ack:
                        try:
                            # Ativar o timeout
                            client.settimeout(c.TIMEOUT)

                            client.sendto(pack, (client_ip, c.SERVER_ADRR[1]))
                            
                            # Aguarda receber ack da mensagem
                            while not ack_received:
                                pass

                            ack_received = False
                            nickname = message[16:] 
                            is_conected = True 
                            
                        except socket.timeout:
                            print("Timeout: Falha ao enviar mensagem")
                        except Exception as e:
                            print(f"Erro enviando mensagem: {e}")
                            
                if is_conected:
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

                else:
                    print("Tente se conectar novamente")