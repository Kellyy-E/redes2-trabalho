import csv
import os
import sys

# ── Configurações ──────────────────────────────────────────────────────────────

ARQUIVOS = {
    'A': 'capturaRUDP_cenA.csv',
    'B': 'capturaRUDP_cenB.csv',
    'C': 'capturaRUDP_cenC.csv',
}

PORTA_SERVIDOR = '5001'
PROTOCOLO      = 'R-UDP'
SAIDA          = 'rudp_estatisticas_wireshark.csv'

# Tamanho (bytes, campo Length do Wireshark) dos pacotes de controle (FIN/ACK)
TAMANHO_CONTROLE = '119'

# ── Funções auxiliares ─────────────────────────────────────────────────────────

def extrair_portas(info: str):
    """
    Retorna (src, dst) se o pacote for UDP entre cliente e servidor,
    ou (None, None) caso contrário.
    """
    if PORTA_SERVIDOR not in info or 'Len=' not in info:
        return None, None
    partes = info.split('>')
    if len(partes) != 2:
        return None, None
    src = partes[0].strip()
    dst = partes[1].strip().split()[0]
    return src, dst


def extrair_payload_len(info: str) -> int:
    """
    Extrai o valor de Len=XXXX da coluna Info do Wireshark.
    Esse é o tamanho do payload UDP, sem cabeçalhos.
    """
    try:
        return int(info.split('Len=')[1].strip())
    except (IndexError, ValueError):
        return 0


def detectar_fim_sessao(rows: list, i: int, porta_cliente: str) -> bool:
    """
    Verifica se a linha i é o FIN do cliente e as 3 linhas seguintes
    são os ACKs do servidor — padrão real do protocolo implementado.

    Padrão:
      rows[i]   → cliente → servidor  (119 bytes, FLAG_FIN)
      rows[i+1] → servidor → cliente  (119 bytes, FLAG_ACK)
      rows[i+2] → servidor → cliente  (119 bytes, FLAG_ACK)
      rows[i+3] → servidor → cliente  (119 bytes, FLAG_ACK)
    """
    if i + 3 >= len(rows):
        return False

    def eh_ack_servidor(row):
        src, dst = extrair_portas(row['Info'])
        return (row['Length'] == TAMANHO_CONTROLE and
                src == PORTA_SERVIDOR and
                dst == porta_cliente)

    return (eh_ack_servidor(rows[i + 1]) and
            eh_ack_servidor(rows[i + 2]) and
            eh_ack_servidor(rows[i + 3]))


# ── Lógica principal de processamento ─────────────────────────────────────────

def processar_arquivo(caminho: str, cenario: str) -> list[dict]:
    """
    Lê um CSV do Wireshark e retorna uma lista de dicionários,
    um por sessão (repetição) detectada via padrão FIN + 3×ACK.
    """
    if not os.path.isfile(caminho):
        print(f'[ERRO] Arquivo não encontrado: {caminho}')
        sys.exit(1)

    with open(caminho, newline='', encoding='utf-8') as f:
        rows = list(csv.DictReader(f))

    sessoes   = []       # lista de sessões concluídas
    em_sessao = False
    porta_atual = None
    t_inicio    = None
    bytes_payload = 0

    i = 0
    while i < len(rows):
        row  = rows[i]
        info = row['Info']
        src, dst = extrair_portas(info)

        if src is None:
            i += 1
            continue

        cliente_para_servidor = (dst == PORTA_SERVIDOR)
        servidor_para_cliente = (src == PORTA_SERVIDOR)

        # ── Início de nova sessão ──────────────────────────────────────────
        if cliente_para_servidor and not em_sessao:
            em_sessao     = True
            porta_atual   = src
            t_inicio      = float(row['Time'])
            bytes_payload = 0

        # ── Acumula dados da sessão corrente ──────────────────────────────
        if em_sessao and cliente_para_servidor and src == porta_atual:
            # Só conta pacotes de dados (não o FIN em si)
            payload = extrair_payload_len(info)

            # Detecta FIN: pacote de controle do cliente + 3 ACKs do servidor
            if row['Length'] == TAMANHO_CONTROLE and detectar_fim_sessao(rows, i, porta_atual):
                t_fim    = float(row['Time'])
                duracao  = t_fim - t_inicio
                throughput = (bytes_payload / 1024) / duracao if duracao > 0 else 0.0

                sessoes.append({
                    'Protocolo':        PROTOCOLO,
                    'Cenario':          cenario,
                    'Repeticao':        len(sessoes) + 1,
                    'Duracao(s)':       round(duracao, 6),
                    'Throughput(KB/s)': round(throughput, 4),
                })

                em_sessao   = False
                porta_atual = None
                i += 4   # pula o FIN + 3 ACKs
                continue
            else:
                bytes_payload += payload

        i += 1

    return sessoes


# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)

    campos = ['Protocolo', 'Cenario', 'Repeticao', 'Duracao(s)', 'Throughput(KB/s)']
    linhas = []

    for cenario, arquivo in ARQUIVOS.items():
        print(f'Processando cenário {cenario}: {arquivo}')
        dados = processar_arquivo(arquivo, cenario)
        print(f'  → {len(dados)} sessões detectadas')
        for d in dados:
            print(f"     Rep {d['Repeticao']:>2}: {d['Duracao(s)']:.3f}s  |  {d['Throughput(KB/s)']:.2f} KB/s")
        linhas.extend(dados)

    with open(SAIDA, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=campos)
        writer.writeheader()
        writer.writerows(linhas)

    print(f'\nConcluído! {len(linhas)} linhas salvas em: {SAIDA}')


if __name__ == '__main__':
    main()