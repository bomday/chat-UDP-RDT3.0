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

# Função para receber mensagens dos clientes
def receive():
    while True:
        data, client_adress = server.recvfrom(c.BUFF_SIZE)
        message = data.decode()
        
        messages_broadcast.put((message, client_adress))

        print("Received data: " + message)

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
                if message_decoded == "bye":
                    nickname = clients.pop(port)
                    clients_adress.pop(client_adress)
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
                        server.sendto(message_output.encode(encoding = 'ISO-8859-1'), client)

                except:
                    # Remove o cliente da lista se ocorrer um erro ao enviar a mensagem
                    clients.pop(client[0])
                    clients_adress.remove(client)

# Inicia uma thread para as funções de recebimento e broadcast
receive_tread = threading.Thread(target=receive)
receive_tread.start()

broadcast_tread = threading.Thread(target=broadcast)
broadcast_tread.start()