import csv
import os
import sys

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

OUT_DIR = os.path.dirname(os.path.abspath(__file__))

COR_TCP  = '#1a6faf'
COR_RUDP = '#c0392b'

plt.rcParams.update({
    'font.family':      'DejaVu Sans',
    'font.size':        10,
    'axes.titlesize':   11,
    'axes.labelsize':   10,
    'axes.spines.top':  False,
    'axes.spines.right':False,
    'axes.grid':        True,
    'grid.alpha':       0.3,
    'figure.dpi':       150,
})

CENARIOS   = ['A', 'B', 'C']
LABELS_CEN = ['Cenário A\n(0% perda)', 'Cenário B\n(5% perda)', 'Cenário C\n(10% perda)']
COL_DUR    = 'Duracao(s)'
COL_TP     = 'Throughput(KB/s)'


def carregar_dados():
    def abrir(nome):
        path = os.path.join(OUT_DIR, nome)
        if not os.path.isfile(path):
            print(f'[ERRO] Arquivo não encontrado: {path}')
            sys.exit(1)
        return pd.read_csv(path)

    rudp_app = abrir('R-UDPmetricas_desempenho.csv')
    tcp_app  = abrir('TCPmetricas_desempenho.csv')
    rudp_ws  = abrir('rudp_estatisticas_wireshark.csv')
    tcp_ws   = abrir('tcp_estatisticas_wireshark.csv')

    cenarios = ['A'] * 20 + ['B'] * 20 + ['C'] * 20
    rudp_app['Cenario'] = cenarios
    tcp_app['Cenario']  = cenarios

    # Normalizar coluna de duração (pode ter acento)
    for df in [rudp_app, tcp_app]:
        df.rename(columns={c: COL_DUR for c in df.columns
                            if 'ur' in c.lower() and 's)' in c and c != COL_DUR},
                  inplace=True)

    return rudp_app, tcp_app, rudp_ws, tcp_ws


def stats(df, cenario, col):
    s = df[df['Cenario'] == cenario][col]
    return s.min(), s.mean(), s.max(), s.std()


def calcular_stats_todos(rudp_app, tcp_app, rudp_ws, tcp_ws):
    rows_tp, rows_dur = [], []
    for cen in CENARIOS:
        for proto, df_app, df_ws in [
            ('TCP',   tcp_app,  tcp_ws),
            ('R-UDP', rudp_app, rudp_ws),
        ]:
            for origem, df in [('Aplicação (Python)', df_app),
                                ('Rede (Wireshark)',   df_ws)]:
                mn, me, mx, dp = stats(df, cen, COL_TP)
                rows_tp.append({'Protocolo': proto, 'Cenário': cen, 'Origem': origem,
                                 'Mínima': round(mn, 2), 'Média': round(me, 2),
                                 'Máxima': round(mx, 2), 'Desvio Padrão': round(dp, 2)})
                mn, me, mx, dp = stats(df, cen, COL_DUR)
                rows_dur.append({'Protocolo': proto, 'Cenário': cen, 'Origem': origem,
                                  'Mínima': round(mn, 4), 'Média': round(me, 4),
                                  'Máxima': round(mx, 4), 'Desvio Padrão': round(dp, 4)})
    return pd.DataFrame(rows_tp), pd.DataFrame(rows_dur)


# ── Gráficos ───────────────────────────────────────────────────────────────────
def fig_throughput_medio(rudp_app, tcp_app):
    x, w = np.arange(3), 0.35
    tcp_m,  tcp_d  = zip(*[stats(tcp_app,  c, COL_TP)[1::2] for c in CENARIOS])
    rudp_m, rudp_d = zip(*[stats(rudp_app, c, COL_TP)[1::2] for c in CENARIOS])

    fig, ax = plt.subplots(figsize=(7, 4))
    ax.bar(x-w/2, tcp_m,  w, yerr=tcp_d,  label='TCP',   color=COR_TCP,  capsize=5)
    ax.bar(x+w/2, rudp_m, w, yerr=rudp_d, label='R-UDP', color=COR_RUDP, capsize=5)
    ax.set_yscale('log')
    ax.set_xticks(x); ax.set_xticklabels(LABELS_CEN)
    ax.set_ylabel('Throughput Médio (KB/s) — Escala Log')
    ax.set_title('Throughput Médio ± Desvio Padrão (Métricas da Aplicação)')
    ax.legend()
    for xi, (tv, rv) in enumerate(zip(tcp_m, rudp_m)):
        ax.text(xi-w/2, tv*1.6, f'{tv:,.1f}', ha='center', fontsize=8, color=COR_TCP)
        ax.text(xi+w/2, rv*1.6, f'{rv:,.1f}', ha='center', fontsize=8, color=COR_RUDP)
    plt.tight_layout()
    _salvar('fig1_throughput_medio.png')


def fig_tempo_medio(rudp_app, tcp_app):
    x, w = np.arange(3), 0.35
    tcp_m,  tcp_d  = zip(*[stats(tcp_app,  c, COL_DUR)[1::2] for c in CENARIOS])
    rudp_m, rudp_d = zip(*[stats(rudp_app, c, COL_DUR)[1::2] for c in CENARIOS])

    fig, ax = plt.subplots(figsize=(7, 4))
    ax.bar(x-w/2, tcp_m,  w, yerr=tcp_d,  label='TCP',   color=COR_TCP,  capsize=5)
    ax.bar(x+w/2, rudp_m, w, yerr=rudp_d, label='R-UDP', color=COR_RUDP, capsize=5)
    ax.set_xticks(x); ax.set_xticklabels(LABELS_CEN)
    ax.set_ylabel('Tempo Médio de Transferência (s)')
    ax.set_title('Tempo de Transferência Médio ± Desvio Padrão (Métricas da Aplicação)')
    ax.legend()
    for xi, (tv, rv, td, rd) in enumerate(zip(tcp_m, rudp_m, tcp_d, rudp_d)):
        ax.text(xi-w/2, tv+td+max(rudp_m)*0.01, f'{tv:.3f}s', ha='center', fontsize=8)
        ax.text(xi+w/2, rv+rd+max(rudp_m)*0.01, f'{rv:.3f}s', ha='center', fontsize=8)
    plt.tight_layout()
    _salvar('fig2_tempo_medio.png')


def fig_desvio_padrao(rudp_app, tcp_app):
    x, w = np.arange(3), 0.35
    tcp_d  = [stats(tcp_app,  c, COL_TP)[3] for c in CENARIOS]
    rudp_d = [stats(rudp_app, c, COL_TP)[3] for c in CENARIOS]

    fig, ax = plt.subplots(figsize=(7, 4))
    ax.bar(x-w/2, tcp_d,  w, label='TCP',   color=COR_TCP)
    ax.bar(x+w/2, rudp_d, w, label='R-UDP', color=COR_RUDP)
    ax.set_xticks(x); ax.set_xticklabels(LABELS_CEN)
    ax.set_ylabel('Desvio Padrão do Throughput (KB/s)')
    ax.set_title('Instabilidade de Vazão: Desvio Padrão por Cenário')
    ax.legend()
    for xi, (tv, rv) in enumerate(zip(tcp_d, rudp_d)):
        ax.text(xi-w/2, tv + max(tcp_d)*0.02, f'{tv:.1f}', ha='center', fontsize=8)
        ax.text(xi+w/2, rv + max(tcp_d)*0.02, f'{rv:.1f}', ha='center', fontsize=8)
    plt.tight_layout()
    _salvar('fig3_desvio_padrao_throughput.png')


def fig_validacao_cruzada(app_df, ws_df, protocolo, fig_num, col, ylabel, fname_sufixo):
    x, w = np.arange(3), 0.35
    app_m, app_d = zip(*[stats(app_df, c, col)[1::2] for c in CENARIOS])
    ws_m,  ws_d  = zip(*[stats(ws_df,  c, col)[1::2] for c in CENARIOS])

    cor = COR_TCP if protocolo == 'TCP' else COR_RUDP
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.bar(x-w/2, app_m, w, yerr=app_d, label='Aplicação (Python)',
           color=cor, alpha=0.9, capsize=5)
    ax.bar(x+w/2, ws_m,  w, yerr=ws_d,  label='Rede (Wireshark)',
           color=cor, alpha=0.45, capsize=5)
    ax.set_xticks(x); ax.set_xticklabels(LABELS_CEN)
    ax.set_ylabel(ylabel)
    ax.set_title(f'Validação Cruzada — {ylabel.split("(")[0].strip()}: Protocolo {protocolo}')
    ax.legend()
    ref = max(max(app_m), max(ws_m))
    for xi, (av, wv) in enumerate(zip(app_m, ws_m)):
        ax.text(xi-w/2, av + app_d[xi] + ref*0.01, f'{av:,.2f}', ha='center', fontsize=8)
        ax.text(xi+w/2, wv + ws_d[xi]  + ref*0.01, f'{wv:,.2f}', ha='center', fontsize=8)
    plt.tight_layout()
    _salvar(f'fig{fig_num}_validacao_{fname_sufixo}_{protocolo.lower().replace("-","")}.png')


# ── Tabelas ────────────────────────────────────────────────────────────────────
def tabela_overhead_bytes():
    """Breakdown do overhead de 71 bytes por camada no protocolo R-UDP."""
    rows = [
        {'Camada': 'Rede (IPv4)',       'Campo': 'Cabeçalho IP',              'Tamanho (bytes)': 20},
        {'Camada': 'Transporte (UDP)',  'Campo': 'Cabeçalho UDP',             'Tamanho (bytes)': 8},
        {'Camada': 'Aplicação (R-UDP)', 'Campo': 'Número de Sequência (seq)', 'Tamanho (bytes)': 4},
        {'Camada': 'Aplicação (R-UDP)', 'Campo': 'Checksum',                  'Tamanho (bytes)': 2},
        {'Camada': 'Aplicação (R-UDP)', 'Campo': 'Flags de controle',         'Tamanho (bytes)': 1},
        {'Camada': 'Aplicação (R-UDP)', 'Campo': 'X-Custom-Auth (SHA-256)',   'Tamanho (bytes)': 36},
        {'Camada': 'TOTAL',             'Campo': '—',                         'Tamanho (bytes)': 71},
    ]
    _salvar_csv(pd.DataFrame(rows), 'tabela_overhead_bytes.csv')


def tabela_volume_capturado():
    """
    Compara bytes úteis (1 MB × 20 sessões) com bytes brutos capturados pelo
    Wireshark (campo Length de todos os frames do arquivo .pcap exportado como CSV).
    O overhead aumenta com a taxa de perda por causa das retransmissões.
    """
    BYTES_UTEIS = 1024 * 1024
    N_SESSOES   = 20

    arquivos = {
        ('TCP',   'A'): 'capturaTCP_cenA.csv',
        ('TCP',   'B'): 'capturaTCP_cenB.csv',
        ('TCP',   'C'): 'capturaTCP_cenC.csv',
        ('R-UDP', 'A'): 'capturaRUDP_cenA.csv',
        ('R-UDP', 'B'): 'capturaRUDP_cenB.csv',
        ('R-UDP', 'C'): 'capturaRUDP_cenC.csv',
    }

    rows = []
    for (proto, cen), fname in arquivos.items():
        fpath = os.path.join(OUT_DIR, fname)
        if not os.path.isfile(fpath):
            print(f'  [AVISO] Não encontrado: {fpath}')
            continue
        with open(fpath, newline='', encoding='utf-8') as f:
            total_cap = sum(int(r['Length']) for r in csv.DictReader(f))

        uteis    = BYTES_UTEIS * N_SESSOES
        overhead = (total_cap - uteis) / uteis * 100
        rows.append({'Protocolo': proto, 'Cenário': cen,
                     'Bytes úteis': uteis,
                     'Bytes capturados': total_cap,
                     'Overhead rede (%)': round(overhead, 2)})

    _salvar_csv(
        pd.DataFrame(rows, columns=['Protocolo','Cenário','Bytes úteis',
                                    'Bytes capturados','Overhead rede (%)']),
        'tabela_volume_capturado.csv')


# ── Utilitários ────────────────────────────────────────────────────────────────
def _salvar(nome):
    path = os.path.join(OUT_DIR, nome)
    plt.savefig(path)
    plt.close()
    print(f'  Salvo: {path}')


def _salvar_csv(df, nome):
    path = os.path.join(OUT_DIR, nome)
    df.to_csv(path, index=False)
    print(f'  Salvo: {path}')


def main():
    print('Carregando dados...')
    rudp_app, tcp_app, rudp_ws, tcp_ws = carregar_dados()

    print('\nGerando tabelas estatísticas...')
    df_tp, df_dur = calcular_stats_todos(rudp_app, tcp_app, rudp_ws, tcp_ws)
    _salvar_csv(df_tp,  'tabela_throughput_stats.csv')
    _salvar_csv(df_dur, 'tabela_duracao_stats.csv')
    tabela_overhead_bytes()
    tabela_volume_capturado()

    print('\nGerando gráficos...')
    fig_throughput_medio(rudp_app, tcp_app)
    fig_tempo_medio(rudp_app, tcp_app)
    fig_desvio_padrao(rudp_app, tcp_app)
    fig_validacao_cruzada(tcp_app,  tcp_ws,  'TCP',   4, COL_TP,  'Throughput Médio (KB/s)',          'tp')
    fig_validacao_cruzada(rudp_app, rudp_ws, 'R-UDP', 5, COL_TP,  'Throughput Médio (KB/s)',          'tp')
    fig_validacao_cruzada(tcp_app,  tcp_ws,  'TCP',   6, COL_DUR, 'Tempo Médio de Transferência (s)', 'dur')
    fig_validacao_cruzada(rudp_app, rudp_ws, 'R-UDP', 7, COL_DUR, 'Tempo Médio de Transferência (s)', 'dur')

    print(f'\nConcluído! Todos os arquivos gerados em: {OUT_DIR}')


if __name__ == '__main__':
    main()