# Importando bibliotecas python 
import socket # Cria sockets par comunicação em uma rede
import queue # Fila para armazenar mensagens
import threading # Cria threads, que são úteis para executar operações simultâneas
import datetime as dt # biblioteca pra manipular datas e horas

# Importando arquivos do código
import utils.constants as c

# Inicialia fila para armazenar mensagens a serem processadas
messages_broadcast = queue.Queue()
# Inicializando
clients_adress = [] # Armazena ip client e porta
clients = dict() # Armazena ip client e nome
seq_and_ack_controler = dict() # Armazena ip client e nome
msg_count = 0 

# Criação do socket UDP
server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
# Atribuição do endereço do servidor
server.bind(c.SERVER_ADRR)

# Função responsável por salvar string em arquivo .txt
def convert_string_to_txt(client_port, string):
    global msg_count

    file_name = f'{client_port}{msg_count}'
    path_file = f"./udp-ajustado/data/server/{file_name}.txt"
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

# Função para receber mensagens dos clientes
def receive():
    while True:
        received_encoded_message, client_adress = server.recvfrom(c.BUFF_SIZE)
        checksum = calculate_checksum(received_encoded_message)
        message = received_encoded_message.decode()
        
        messages_broadcast.put((message, client_adress))

        print(f"Received message: {message}, checksum {checksum}")

def broadcast():
    global clients, seq_and_ack_controler

    while True:
        while not messages_broadcast.empty():
            message, client_adress = messages_broadcast.get()
            current_time_and_date = dt.datetime.now().strftime("%H:%M:%S %d/%m/%Y ")
            ip = client_adress[0]
            port = client_adress[1]

            if client_adress not in clients_adress:
                nickname = message[16:]
                clients[port] = nickname
                # seq_and_ack_controler[port] = [0, 0]
                clients_adress.append(client_adress)
            else:
                if message == "bye":
                    nickname = clients.pop(port)
                    clients_adress.remove(client_adress)
                else:
                    nickname = clients[port]

            # Converte string em txt
            path_file = convert_string_to_txt(port, message)

            # Lendo o conteúdo do arquivo .txt
            file = open(path_file,"rb")
            message_file = file.read()
            message_decoded = message_file.decode()

            # Envia a mensagem recebida para todos os clientes conectados
            for client in clients_adress: 
                try:
                    # Formatando mensagem para exibição
                    if message_decoded.startswith("hi, meu nome eh "):
                        message_output = f'{nickname} entrou na sala'
                    elif message_decoded == "bye":
                        message_output = f'{nickname} saiu da sala'
                    else:
                        message_output = f'{ip}:{port}/~{nickname}: {message_decoded} {current_time_and_date}'

                    # Envia a mensagem para clientes
                    if not (client[1] == port and message_decoded.startswith("hi, meu nome eh ")):
                        message_encoded = message_output.encode(encoding = 'ISO-8859-1')
                        msg_size = len(message_encoded)

                        for fragment in range(0, msg_size, c.FRAG_SIZE):
                            # Calcula limite do fragmento
                            end_fragment = min(fragment + c.FRAG_SIZE, msg_size)
                            message = message_encoded[fragment:end_fragment]
                            checksum = calculate_checksum(message)
                            # Envia fragmentos da mensagem para o Cliente 
                            server.sendto(message, client)
                            print(f"Sended data: CLIENT, fragment {fragment//c.FRAG_SIZE + 1}, checksum {checksum}")

                except:
                    # Remove o cliente da lista se ocorrer um erro ao enviar a mensagem
                    clients.pop(client[0])
                    clients_adress.remove(client)

# Inicia uma thread para as funções de recebimento e broadcast
receive_tread = threading.Thread(target=receive)
receive_tread.start()

broadcast_tread = threading.Thread(target=broadcast)
broadcast_tread.start()