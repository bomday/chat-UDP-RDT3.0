# Importando bibliotecas python 
import os # Biblioteca para manipulação de arquivos e diretórios
import socket # Cria sockets par comunicação em uma rede
import queue # Fila para armazenar mensagens
import struct # Possibilita empacotar e desempacotar dados binários
import threading # Cria threads, que são úteis para executar operações simultâneas
import datetime as dt # biblioteca pra manipular datas e horas

# Importando arquivos do código
import utils.constants as c

# Inicialia fila para armazenar mensagens a serem processadas
messages_broadcast = queue.Queue()
# Inicializando
clients_adress = [] # Armazena ip client e porta
clients = dict() # Armazena porta cliente e nome
seq_and_ack_controler = dict() # Armazena porta cliente e lista com seq e ack 
ack_received_controler = dict() # Armazena porta cliente e status de ack recebido
clients_msg_received = dict() # Dicionário com lista de fragmentos recebidos por cliente
msg_count = 0 

# Criação do socket UDP
server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
# Atribuição do endereço do servidor
server.bind(c.SERVER_ADRR)

def delete_client(client_adress, port):
    clients_adress.remove(client_adress) # Retira ip client e porta
    del clients[port] # Retira porta cliente e nome
    del seq_and_ack_controler[port] # Retira porta cliente e lista com seq e ack 
    del ack_received_controler[port] # Retira porta cliente e status de ack recebido
    del clients_msg_received[port] # Retira dicionário com lista de fragmentos recebidos por cliente

# Função responsável por salvar string em arquivo .txt
def convert_string_to_txt(client_port, nickname, string):
    global msg_count

    path_folder = f'./data/server/{nickname}/'

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

# Função para receber mensagens dos clientes
def receive():
    global clients_adress, clients_msg_received, seq_and_ack_controler, ack_received_controler
    
    while True:
        received_encoded_message, client_adress = server.recvfrom(c.BUFF_SIZE) # Recebe mensagem e endereço do cliente
        header = received_encoded_message[:c.HEADER_SIZE] # Separando o Header
        message_received = received_encoded_message[c.HEADER_SIZE:] # Separando a mensagem
        (frag_index, frag_count, seq_recv, ack_recv, checksum) = struct.unpack('!IIIII', header) # Desempacotando o header
        port = client_adress[1] # Guarda porta do cliente

        checksum_check = calculate_checksum(message_received) # Calcula checksum da mensagem recebida
        message = message_received.decode() # Decodifica mensagem
        
        # Confere recebimento de ack 
        if message == '':
            # Desativar o timeout após receber ack da mensagem
            server.settimeout(None)

            # Confere se é checksum e ack esperado
            if (checksum_check == checksum) and (seq == ack_recv):
                print('Recebeu reconhecimento do pacote!')

                # Alterna o seq num para próximo pacote
                seq_and_ack_controler[port][0] = 1 if (seq == 0) else 0 
            else:
                print('Recebeu ACK corrompido ou duplicado')

            ack_received_controler[port] = True

        # Confere recebimento de pacote
        else:
            if message == 'SYN':
                print('Recebeu SYN... Enviando SYN-ACK')
                message_ack = 'SYN-ACK'
                # Estabelece seq num e ack apenas para envio de 'SYN-ACK'
                seq = 0
                ack = 0 
            elif message == 'FIN':
                print('Recebeu FIN... Enviando FIN-ACK')
                message_ack = 'Voce saiu da sala'
            else:
                # Inclusão ou conferência de cliente 
                if client_adress not in clients_adress:
                    nickname = message[16:] 
                    clients[port] = nickname
                    seq_and_ack_controler[port] = [0, 0]
                    ack_received_controler[port] = False
                    clients_adress.append(client_adress)
                else:
                    if message == "ACK":
                        message = "bye"
                    else:
                        nickname = clients[port]

                clients_msg_received[port] = [[] for i in range(frag_count)]
                seq = seq_and_ack_controler[port][0]
                ack = seq_and_ack_controler[port][1]

                # Confere se é checksum e pacote esperado
                if (checksum_check == checksum) and (seq_recv == ack):
                    clients_msg_received[port][frag_index].append(message) # Adiciona mensagem recebida a lista de fragmentos para mensagem completa se não for pacote duplicado
                    if message == "bye":
                        print('ACK de finalização recebido')
                    else:
                        print("Recebeu pacote")
                    seq_and_ack_controler[port][1] = 1 if (ack == 0) else 0 # Alterna o ack para próximo pacote
                else:
                    print('Recebeu pacote corrompido ou duplicado')
                    # Alterna o ack para pedir reenvio de pacote
                    ack = 1 if (ack == 0) else 0
            
                message_ack = ''

            if message != "bye": # Se mensagem for ACK de finalização, não deve enviar outro pacote
                message_ack_enconded = message_ack.encode()
                checksum = calculate_checksum(message_ack_enconded) # Calcula checksum
                header = struct.pack('!IIIII', 0, 1, seq, ack, checksum) # Estrutura o cabeçalho do pacote
                pack = header + message_ack_enconded

                server.sendto(pack, client_adress)

                print('Enviou pacote de reconhecimento')

            if message != 'SYN' and message != 'FIN':
                # Confere se lista com fragmentos da mensagem está completa
                if not any(isinstance(sublist, list) and len(sublist) == 0 for sublist in clients_msg_received[port]):
                    joined_msg = ''.join(sum(clients_msg_received[port], []))
                    print('BROADCAST SERVER')
                    messages_broadcast.put((joined_msg, nickname, client_adress))
                    clients_msg_received[port] = []

# Função para enviar mensagens aos clientes
def broadcast():
    global clients_adress, clients, seq_and_ack_controler, ack_received_controler

    while True:
        while not messages_broadcast.empty():
            message, nickname, client_adress = messages_broadcast.get()
            current_time_and_date = dt.datetime.now().strftime("%H:%M:%S %d/%m/%Y ")
            ip = client_adress[0]
            port = client_adress[1]

            # Converte string em txt
            path_file = convert_string_to_txt(port, nickname, message)

            # Lendo o conteúdo do arquivo .txt
            file = open(path_file,"rb")
            message_file = file.read()
            message_decoded = message_file.decode()

            # Envia a mensagem recebida para todos os clientes conectados
            for client in clients_adress: 
                try:
                    if not (client == client_adress and message_decoded == "bye"): # Envia mensagem para cliente se não for o usuário saindo da sala
                        # Formatando mensagem para exibição
                        if message_decoded.startswith("hi, meu nome eh "):
                            if client == client_adress:
                                message_output = f'Voce entrou na sala'
                            else:
                                message_output = f'{nickname} entrou na sala'
                        elif message_decoded == "bye":
                            message_output = f'{nickname} saiu da sala'
                        else:
                            message_output = f'{ip}:{port}/~{nickname}: {message_decoded} {current_time_and_date}'

                        message_encoded = message_output.encode(encoding = 'ISO-8859-1')
                        msg_size = len(message_encoded)

                        port_send = client[1]
                        seq = seq_and_ack_controler[port_send][0]
                        ack = seq_and_ack_controler[port_send][1]

                        # Calcula número de fragmentos da mensagem
                        frag_count = msg_size//c.FRAG_SIZE + 1
                        # Calcula índice de pacotes para garantir entrega na ordem
                        frag_index = 0

                        for fragment in range(0, msg_size, c.FRAG_SIZE):
                            end_fragment = min(fragment + c.FRAG_SIZE, msg_size) # Calcula limite do fragmento
                            message = message_encoded[fragment:end_fragment+1] # Delimita mensagem a ser enviada no pacote
                            checksum = calculate_checksum(message) # Calcula checksum
                            header = struct.pack('!IIIII', frag_index, frag_count, seq, ack, checksum) # Estrutura o cabeçalho do pacote
                            pack = header + message

                            while seq_and_ack_controler[port_send][0] == seq:
                                # Envia fragmentos da mensagem para o Cliente
                                try:
                                    # Ativar o timeout
                                    server.settimeout(c.TIMEOUT)

                                    print(f"Envio de pacote para {clients[port_send]}")
                                    server.sendto(pack, client)

                                    # Aguarda receber ack da mensagem
                                    while not ack_received_controler[port_send]:
                                        pass
                                    
                                except socket.timeout:
                                    print("Timeout: Falha ao enviar mensagem")
                                except Exception as e:
                                    print(f"Erro enviando mensagem: {e}") 
                            
                            # Acrescenta índice para próximo pacote 
                            frag_index += 1
                            # Reseta ack recebido
                            for status in ack_received_controler:
                                ack_received_controler[status] = False

                except:
                    # Remove o cliente da lista se ocorrer um erro ao enviar a mensagem
                    delete_client(client_adress, port)

            # Exclui dados do usuário que sairá da sala
            if message_decoded == "bye":
                delete_client(client_adress, port)

# Inicia uma thread para as funções de recebimento e broadcast
receive_tread = threading.Thread(target=receive)
receive_tread.start()

broadcast_tread = threading.Thread(target=broadcast)
broadcast_tread.start()