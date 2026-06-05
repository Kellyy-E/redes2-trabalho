import csv
import os
import sys

# ── Configurações ──────────────────────────────────────────────────────────────

ARQUIVOS = {
    'A': 'capturaTCP_cenA.csv',
    'B': 'capturaTCP_cenB.csv',
    'C': 'capturaTCP_cenC.csv',
}

PORTA_SERVIDOR = '5000'
PROTOCOLO      = 'TCP'
SAIDA          = 'tcp_estatisticas_wireshark.csv'


def extrair_src_dst(info: str):
    if '>' not in info:
        return None, None
    if info.startswith('['):
        info = info.split(']', 1)[-1].strip()
    partes = info.split('>')
    if len(partes) < 2:
        return None, None
    src = partes[0].strip()
    dst = partes[1].strip().split()[0]
    return src, dst


def extrair_payload(info: str) -> int:
    """
    Extrai o tamanho do payload TCP (Len=XXXX) da coluna Info.
    Retorna 0 para pacotes de controle puro (SYN, ACK, FIN sem dados).
    """
    if 'Len=' not in info:
        return 0
    try:
        return int(info.split('Len=')[1].strip().split()[0])
    except (IndexError, ValueError):
        return 0



def processar_arquivo(caminho: str, cenario: str) -> list[dict]:

    if not os.path.isfile(caminho):
        print(f'[ERRO] Arquivo não encontrado: {caminho}')
        sys.exit(1)

    with open(caminho, newline='', encoding='utf-8') as f:
        rows = list(csv.DictReader(f))

    sessoes_abertas: dict[str, dict] = {}   # porta_cliente → {t_inicio, bytes}
    sessoes_concluidas: list[dict]   = []

    for row in rows:
        info = row['Info'].strip()
        t    = float(row['Time'])

        # ── Início de sessão: SYN do cliente ──────────────────────────────
        if ('[SYN]' in info
                and '[SYN, ACK]' not in info
                and '[TCP Retransmission]' not in info):
            src, dst = extrair_src_dst(info)
            if dst == PORTA_SERVIDOR and src and src not in sessoes_abertas:
                sessoes_abertas[src] = {'t_inicio': t, 'bytes': 0}
            continue

        src, dst = extrair_src_dst(info)
        if src is None:
            continue

        if dst == PORTA_SERVIDOR and src in sessoes_abertas:
            sessoes_abertas[src]['bytes'] += extrair_payload(info)

        if '[FIN, ACK]' in info and src == PORTA_SERVIDOR and dst in sessoes_abertas:
            sess       = sessoes_abertas.pop(dst)
            duracao    = t - sess['t_inicio']
            throughput = (sess['bytes'] / 1024) / duracao if duracao > 0 else 0.0
            sessoes_concluidas.append({
                '_t_inicio':        sess['t_inicio'],
                'Protocolo':        PROTOCOLO,
                'Cenario':          cenario,
                'Repeticao':        0,
                'Duracao(s)':       round(duracao, 6),
                'Throughput(KB/s)': round(throughput, 4),
            })

    sessoes_concluidas.sort(key=lambda s: s['_t_inicio'])
    for i, s in enumerate(sessoes_concluidas, start=1):
        s['Repeticao'] = i
        del s['_t_inicio']

    return sessoes_concluidas



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
            print(f"     Rep {d['Repeticao']:>2}: {d['Duracao(s)']:.4f}s  |  {d['Throughput(KB/s)']:.2f} KB/s")
        linhas.extend(dados)

    with open(SAIDA, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=campos)
        writer.writeheader()
        writer.writerows(linhas)

    print(f'\nConcluído! {len(linhas)} linhas salvas em: {SAIDA}')


if __name__ == '__main__':
    main()