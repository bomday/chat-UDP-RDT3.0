<a name="readme-top"></a>
# <p align="center">Chat de sala única com UDP e RDT3.0</p>

> Servidor de chat de sala única, onde os clientes se conectam à sala, recebendo e enviando mensagens para outros usuários.

```
Projeto composto por duas etapas:
1. Desenvolvimento de uma ferramenta de troca de arquivos .txt e reverberação disso em um chat de mensagens, utilizando comunicação com UDP;
2. Implementação de um protocolo de transferência confiável ao chat básico de troca de mensagens já feito, utilizando UDP e o método RDT 3.0 apresentado em sala de aula.
```
> Baseado em um projeto da disciplina de Redes de Computadores do curso de Sistemas de Informação da UFPE.

<details>
  <summary>Tabela de Conteúdos</summary>
    <ol>
        <li><a href="#requisitos-preliminares">Requisitos preliminares</a></li>
        <li>
        <a href="#implementação">Implementação</a>
        <ul>
            <li><a href="#linguagem-utilizada">Linguagem Utilizada</a></li>
            <li><a href="#funcionalidades">Funcionalidades</a></li>
            <li><a href="#bibliotecas-utilizadas">Bibliotecas Utilizadas</a></li>
            <li><a href="#github">GitHub</a></li>
        </ul>
        </li>
        <li><a href="#contatos">Contatos</a></li>
    </ol>
</details>

## Requisitos preliminares

Antes de começar, verifique se você atendeu aos seguintes requisitos:

* Clone o projeto e abra em seu editor de código favorito;
* Certifique que você está com o `python 3.10+` instalado;
* Certifique que você está com todos os plugins, nescessários para rodar um projeto python, instalados em seu editor de código;
* Inicialmente, você deve abrir seu terminal na pasta `chat-udp-rdt3.0`;
* Em seguida, você deve executar o arquivo `server.py` nesse terminal.
* Para conectar um usuário ao chat, execute o arquivo `client.py` em um teminal separado (esse terminal também deve ser aberto na pasta `real-time-upd-chat`)

OBS: Você pode adicionar outros clientes duplicando o arquivo client.py e executando cada cliente em um terminal separado.

### Como Executar o Projeto

1. Primeiro, o usuário deve rodar simultaneamente os dois principais arquivos (nesta ordem) em terminais diferentes:
   - Rodar o arquivo _server.py_
   - Rodar o arquivo _client.py_

2. A partir disso, o primeiro usuário poderá usar o chat.

3. Caso outro usuário deseje usar o chat, é preciso rodar o _client.py_ novamente em outro terminal, de modo que haverá um terminal com _client.py_ para cada pessoa que estiver utilizando o chat.

## Implementação

### Linguagem Utilizada

Linguagem de programação Python

### Funcionalidades

1. Chat UDP de sala única para múltiplos usuários com transferência confiável RDT 3.0; 
2. Cliente e Servidor;
3. Troca de arquivos em formato de texto (.txt);
4. Conectar, sair e enviar mensagens na sala;
5. Implementação RDT 3.0: 3 Way Handshake (SYN-ACK), processo de finalização (FYN-ACK), checksum, timeout e tratamento de perda ou corrupção de pacotes de dados e de reconhecimento.

### Bibliotecas utilizadas

- `Datetime`: Manipula datas e horas.

- `OS`: Biblioteca para manipulação de arquivos e diretórios.

- `Queue`: Aplicamos a biblioteca _tkinter_ para criar interfaces gráficas de usuário (GUI).
  
- `Random`: Utilizado para gerar números de porta aleatórios.

- `Socket`: Cria sockets para comunicação em uma rede.

- `Struct`: Bilioteca que interpreta bytes como dados binários compactados.

- `Threading`: Cria threads, que são úteis para executar operações simultâneas.

### GitHub

Link para o repositório: 
https://github.com/bomday/chat-UDP-RDT3.0

<p align="right">(<a href="#readme-top">voltar ao topo</a>)</p>

## Contatos
#### Dayane Lima
- Linkedin: https://www.linkedin.com/in/dayane-lima-5b2558199/
- Email: dayanecamilelima@gmail.com 

<p align="right">(<a href="#readme-top">voltar ao topo</a>)</p>
