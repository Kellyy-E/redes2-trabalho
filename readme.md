# Análise de Desempenho e Confiabilidade: TCP vs. R-UDP

Este projeto consiste numa aplicação cliente/servidor desenvolvida em **Python 3.14** para a disciplina de **Redes de Computadores II** da **Universidade Federal do Piauí (UFPI)**. O principal objetivo é implementar e avaliar comparativamente a transferência de ficheiros utilizando o protocolo nativo orientado à conexão (**TCP**) contra uma camada de transporte customizada confiável construída sobre o protocolo UDP (**R-UDP - Reliable UDP**), utilizando validação cruzada através de capturas de tráfego físico.

O ambiente simula condições dinâmicas de degradação de rede através do utilitário `tc` (*Traffic Control* do Linux) empacotado dentro de contêineres isolados em ambiente **Docker**.

---

## 🚀 Arquitetura do Protocolo R-UDP

Visto que o protocolo UDP nativo é um protocolo não confiável, sem garantias de entrega ou controlo de erros, foi implementada uma camada de fiabilidade na aplicação baseada na estratégia clássica **Stop-and-Wait**.

### 🛠️ Estrutura do Pacote Customizado
Cada pacote de aplicação transmitido via R-UDP possui um cabeçalho fixo empacotado binariamente utilizando a biblioteca `struct` do Python, com o seguinte formato estrutural (`!IHB64s`):

1. **Número de Sequência (`Seq` - 4 Bytes):** Inteiro não assinalado para controlo de ordenação e duplicados.
2. **Checksum (2 Bytes):** Inteiro de 16 bits para deteção de corrupção de dados através do complemento para um.
3. **Flags (1 Byte):** Identificação do estado de controlo da mensagem:
   - `0` (`FLAG_DATA`): Bloco de dados padrão do ficheiro.
   - `1` (`FLAG_ACK`): Confirmação de receção (sem dados úteis).
   - `2` (`FLAG_SYN`): Sincronização inicial / Abertura de canal.
   - `3` (`FLAG_FIN`): Encerramento de transmissão do ficheiro.
4. **Token de Autenticação (`X-Custom-Auth` - 64 Bytes):** Hash SHA-256 gerado dinamicamente com base na concatenação dos dados identificadores do aluno (Matrícula + Nome), garantindo a integridade transacional de quem efetuou o teste.

### 🔄 Mecanismo de Confiabilidade
- **Timeout Dinâmico:** Definido rigidamente em `500ms` (`0.5s`) no cliente. Caso o `ACK` correspondente não seja recebido neste intervalo, ocorre o disparo automático da retransmissão do pacote corrente.
- **Validação de Checksum:** Se o servidor detetar inconsistência de bits através do recálculo do Checksum, o pacote é imediatamente descartado em silêncio, forçando o cliente a atingir o timeout e retransmitir.
- **Controlo de Duplicados:** O servidor monitoriza ativamente os números de sequência esperados. Se receber um pacote duplicado, descarta os dados para evitar corrupção, mas reenvia o `ACK` associado para desbloquear o cliente.

---

## 📂 Estrutura do Projeto

```text
redes2-trabalho/
├── data/                             # Dados de entrada, arquivos recebidos, capturas e logs da aplicação
│   ├── arquivo_teste.bin             # Ficheiro binário padrão usado nas transmissões
│   ├── recebido_rudp.bin             # Ficheiro final gravado via transporte R-UDP
│   └── capturasCSV/                  # Ficheiros processados extraídos do Wireshark
├── docker/                           # Configuração do ambiente isolado de simulação
│   └── scripts/
│       ├── docker-compose.yml        # Definição dos nós de infraestrutura (Cliente/Servidor)
│       └── simular_rede.sh           # Script Bash para injeção de faltas com tc qdisc
├── src/                              # Código fonte modular da aplicação
│   ├── common/
│   │   └── utils.py                  # Definições de pacotes, Checksum, hash de segurança e logs
│   ├── tcp/
│   │   ├── cliente_tcp.py            # Emissor de dados baseado em sockets TCP nativos
│   │   └── servidor_tcp.py           # Recetor orientado a fluxo contínuo TCP
│   └── rudp/
│       ├── cliente_rudp.py           # Emissor adaptado com Stop-and-Wait e controlo de perdas
│       └── servidor_rudp.py          # Recetor R-UDP com validação de cabeçalho customizado
├── analysis/                         # Scripts analíticos de dados e geração de gráficos
│   ├── gera_estatisticas.py          # Processamento estatístico e geração de plots via Matplotlib
│   └── graficos/                     # Outputs visuais comparativos gerados autonomamente
├── orquestrador_testes.py            # Automação de bateria de testes sequenciais nos cenários
├── Dockerfile                        # Configuração da imagem Linux base com suporte a rede iproute2
└── arquivo_recebido_tcp.bin          # Ficheiro final gravado via transporte TCP
