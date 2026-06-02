import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np
import os

# ── Configuração de saída ──────────────────────────────────────────────────────
OUT_DIR = r"C:\Users\eurik\Documents\redes2-trabalho\analysis\graficos_tabelas"
# ── Paleta e estilo ───────────────────────────────────────────────────────────
COR_TCP   = '#1a6faf'
COR_RUDP  = '#c0392b'
COR_WS    = '#2c8a5a'   # verde para dados Wireshark nos gráficos de validação cruzada
DIR_ENTRADA = r"C:\Users\eurik\Documents\redes2-trabalho\analysis"

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

CENARIOS       = ['A', 'B', 'C']
LABELS_CEN     = ['Cenário A\n(0% perda)', 'Cenário B\n(5% perda)', 'Cenário C\n(10% perda)']
COL_DUR        = 'Duracao(s)'
COL_TP         = 'Throughput(KB/s)'


# ── Carregar dados ─────────────────────────────────────────────────────────────
def carregar_dados():
    rudp_app = pd.read_csv(os.path.join(DIR_ENTRADA, 'R-UDPmetricas_desempenho.csv'))
    tcp_app  = pd.read_csv(os.path.join(DIR_ENTRADA, 'TCPmetricas_desempenho.csv'))
    rudp_ws  = pd.read_csv(os.path.join(DIR_ENTRADA, 'rudp_metricas_wireshark.csv'))
    tcp_ws   = pd.read_csv(os.path.join(DIR_ENTRADA, 'tcp_metricas_wireshark.csv'))

    # Adicionar coluna Cenário nos CSVs da aplicação (20 por cenário, ordem A→B→C)
    cenarios = ['A'] * 20 + ['B'] * 20 + ['C'] * 20
    rudp_app['Cenario'] = cenarios
    tcp_app['Cenario']  = cenarios

    # Normalizar nome de coluna com acento
    for df in [rudp_app, tcp_app]:
        df.rename(columns={c: COL_DUR for c in df.columns
                            if 'ur' in c.lower() and 's)' in c and c != COL_DUR},
                  inplace=True)

    return rudp_app, tcp_app, rudp_ws, tcp_ws


# ── Calcular estatísticas ──────────────────────────────────────────────────────
def stats(df, cenario, col):
    s = df[df['Cenario'] == cenario][col]
    return s.min(), s.mean(), s.max(), s.std()


def stats_todos(rudp_app, tcp_app, rudp_ws, tcp_ws):
    rows_tp, rows_dur = [], []
    for cen in CENARIOS:
        for proto, df_app, df_ws in [
            ('TCP',   tcp_app,  tcp_ws),
            ('R-UDP', rudp_app, rudp_ws),
        ]:
            for origem, df in [('Aplicação (Python)', df_app),
                                ('Rede (Wireshark)',   df_ws)]:
                mn, me, mx, dp = stats(df, cen, COL_TP)
                rows_tp.append({'Protocolo': proto, 'Cenário': cen,
                                 'Origem': origem,
                                 'Mínima': round(mn, 2), 'Média': round(me, 2),
                                 'Máxima': round(mx, 2), 'Desvio Padrão': round(dp, 2)})
                mn, me, mx, dp = stats(df, cen, COL_DUR)
                rows_dur.append({'Protocolo': proto, 'Cenário': cen,
                                  'Origem': origem,
                                  'Mínima': round(mn, 4), 'Média': round(me, 4),
                                  'Máxima': round(mx, 4), 'Desvio Padrão': round(dp, 4)})
    return pd.DataFrame(rows_tp), pd.DataFrame(rows_dur)


# ── Fig 1 — Throughput Médio ± DP (TCP vs R-UDP) ──────────────────────────────
def fig_throughput_medio(rudp_app, tcp_app):
    x     = np.arange(len(CENARIOS))
    width = 0.35

    tcp_med,   tcp_dp   = [], []
    rudp_med,  rudp_dp  = [], []
    for cen in CENARIOS:
        _, me, _, dp = stats(tcp_app,  cen, COL_TP)
        tcp_med.append(me);  tcp_dp.append(dp)
        _, me, _, dp = stats(rudp_app, cen, COL_TP)
        rudp_med.append(me); rudp_dp.append(dp)

    fig, ax = plt.subplots(figsize=(7, 4))
    ax.bar(x - width/2, tcp_med,  width, yerr=tcp_dp,  label='TCP',
           color=COR_TCP,  capsize=5, error_kw={'linewidth': 1.4})
    ax.bar(x + width/2, rudp_med, width, yerr=rudp_dp, label='R-UDP',
           color=COR_RUDP, capsize=5, error_kw={'linewidth': 1.4})

    ax.set_yscale('log')
    ax.set_xticks(x); ax.set_xticklabels(LABELS_CEN)
    ax.set_ylabel('Throughput Médio (KB/s) — Escala Log')
    ax.set_title('Throughput Médio ± Desvio Padrão (Métricas da Aplicação)')
    ax.legend()

    # Anotar médias
    for xi, (tv, rv) in enumerate(zip(tcp_med, rudp_med)):
        ax.text(xi - width/2, tv * 1.5, f'{tv:,.1f}', ha='center', va='bottom', fontsize=8, color=COR_TCP)
        ax.text(xi + width/2, rv * 1.5, f'{rv:,.1f}', ha='center', va='bottom', fontsize=8, color=COR_RUDP)

    plt.tight_layout()
    path = os.path.join(OUT_DIR, 'fig1_throughput_medio.png')
    plt.savefig(path); plt.close()
    print(f'  Salvo: {path}')


# ── Fig 2 — Tempo Médio ± DP (TCP vs R-UDP) ───────────────────────────────────
def fig_tempo_medio(rudp_app, tcp_app):
    x     = np.arange(len(CENARIOS))
    width = 0.35

    tcp_med,   tcp_dp   = [], []
    rudp_med,  rudp_dp  = [], []
    for cen in CENARIOS:
        _, me, _, dp = stats(tcp_app,  cen, COL_DUR)
        tcp_med.append(me);  tcp_dp.append(dp)
        _, me, _, dp = stats(rudp_app, cen, COL_DUR)
        rudp_med.append(me); rudp_dp.append(dp)

    fig, ax = plt.subplots(figsize=(7, 4))
    b1 = ax.bar(x - width/2, tcp_med,  width, yerr=tcp_dp,  label='TCP',
                color=COR_TCP,  capsize=5, error_kw={'linewidth': 1.4})
    b2 = ax.bar(x + width/2, rudp_med, width, yerr=rudp_dp, label='R-UDP',
                color=COR_RUDP, capsize=5, error_kw={'linewidth': 1.4})

    ax.set_xticks(x); ax.set_xticklabels(LABELS_CEN)
    ax.set_ylabel('Tempo Médio de Transferência (s)')
    ax.set_title('Tempo de Transferência Médio ± Desvio Padrão (Métricas da Aplicação)')
    ax.legend()

    for xi, (tv, rv) in enumerate(zip(tcp_med, rudp_med)):
        ax.text(xi - width/2, tv + tcp_dp[xi] + 0.5,  f'{tv:.3f}s', ha='center', fontsize=8, color=COR_TCP)
        ax.text(xi + width/2, rv + rudp_dp[xi] + 0.5, f'{rv:.3f}s', ha='center', fontsize=8, color=COR_RUDP)

    plt.tight_layout()
    path = os.path.join(OUT_DIR, 'fig2_tempo_medio.png')
    plt.savefig(path); plt.close()
    print(f'  Salvo: {path}')


# ── Fig 3 — Desvio Padrão de Throughput (gráfico dedicado) ────────────────────
def fig_desvio_padrao(rudp_app, tcp_app):
    x     = np.arange(len(CENARIOS))
    width = 0.35

    tcp_dp  = [stats(tcp_app,  c, COL_TP)[3] for c in CENARIOS]
    rudp_dp = [stats(rudp_app, c, COL_TP)[3] for c in CENARIOS]

    fig, ax = plt.subplots(figsize=(7, 4))
    ax.bar(x - width/2, tcp_dp,  width, label='TCP',   color=COR_TCP)
    ax.bar(x + width/2, rudp_dp, width, label='R-UDP', color=COR_RUDP)

    ax.set_xticks(x); ax.set_xticklabels(LABELS_CEN)
    ax.set_ylabel('Desvio Padrão do Throughput (KB/s)')
    ax.set_title('Instabilidade de Vazão: Desvio Padrão por Cenário')
    ax.legend()

    for xi, (tv, rv) in enumerate(zip(tcp_dp, rudp_dp)):
        ax.text(xi - width/2, tv + 5,  f'{tv:.1f}', ha='center', fontsize=8, color=COR_TCP)
        ax.text(xi + width/2, rv + 5,  f'{rv:.1f}', ha='center', fontsize=8, color=COR_RUDP)

    plt.tight_layout()
    path = os.path.join(OUT_DIR, 'fig3_desvio_padrao_throughput.png')
    plt.savefig(path); plt.close()
    print(f'  Salvo: {path}')


# ── Figs 4 e 5 — Validação Cruzada de Throughput ──────────────────────────────
def fig_validacao_cruzada_tp(app_df, ws_df, protocolo, fig_num):
    x     = np.arange(len(CENARIOS))
    width = 0.35

    app_med, app_dp = [], []
    ws_med,  ws_dp  = [], []
    for cen in CENARIOS:
        _, me, _, dp = stats(app_df, cen, COL_TP)
        app_med.append(me); app_dp.append(dp)
        _, me, _, dp = stats(ws_df,  cen, COL_TP)
        ws_med.append(me);  ws_dp.append(dp)

    fig, ax = plt.subplots(figsize=(7, 4))
    cor_app = COR_TCP if protocolo == 'TCP' else COR_RUDP
    ax.bar(x - width/2, app_med, width, yerr=app_dp, label='Aplicação (Python)',
           color=cor_app, alpha=0.9, capsize=5)
    ax.bar(x + width/2, ws_med,  width, yerr=ws_dp,  label='Rede (Wireshark)',
           color=cor_app, alpha=0.45, capsize=5)

    ax.set_xticks(x); ax.set_xticklabels(LABELS_CEN)
    ax.set_ylabel('Throughput Médio (KB/s)')
    ax.set_title(f'Validação Cruzada de Throughput: Protocolo {protocolo}')
    ax.legend()

    for xi, (av, wv) in enumerate(zip(app_med, ws_med)):
        ax.text(xi - width/2, av + app_dp[xi] + max(app_med)*0.01,
                f'{av:,.1f}', ha='center', fontsize=8)
        ax.text(xi + width/2, wv + ws_dp[xi]  + max(app_med)*0.01,
                f'{wv:,.1f}', ha='center', fontsize=8)

    plt.tight_layout()
    path = os.path.join(OUT_DIR, f'fig{fig_num}_validacao_tp_{protocolo.lower().replace("-","")}.png')
    plt.savefig(path); plt.close()
    print(f'  Salvo: {path}')


# ── Figs 6 e 7 — Validação Cruzada de Tempo ───────────────────────────────────
def fig_validacao_cruzada_dur(app_df, ws_df, protocolo, fig_num):
    x     = np.arange(len(CENARIOS))
    width = 0.35

    app_med, app_dp = [], []
    ws_med,  ws_dp  = [], []
    for cen in CENARIOS:
        _, me, _, dp = stats(app_df, cen, COL_DUR)
        app_med.append(me); app_dp.append(dp)
        _, me, _, dp = stats(ws_df,  cen, COL_DUR)
        ws_med.append(me);  ws_dp.append(dp)

    fig, ax = plt.subplots(figsize=(7, 4))
    cor_app = COR_TCP if protocolo == 'TCP' else COR_RUDP
    ax.bar(x - width/2, app_med, width, yerr=app_dp, label='Aplicação (Python)',
           color=cor_app, alpha=0.9, capsize=5)
    ax.bar(x + width/2, ws_med,  width, yerr=ws_dp,  label='Rede (Wireshark)',
           color=cor_app, alpha=0.45, capsize=5)

    ax.set_xticks(x); ax.set_xticklabels(LABELS_CEN)
    ax.set_ylabel('Tempo Médio de Transferência (s)')
    ax.set_title(f'Validação Cruzada de Tempo de Execução: Protocolo {protocolo}')
    ax.legend()

    for xi, (av, wv) in enumerate(zip(app_med, ws_med)):
        offset = max(app_med) * 0.015 + app_dp[xi]
        ax.text(xi - width/2, av + offset, f'{av:.3f}s', ha='center', fontsize=8)
        ax.text(xi + width/2, wv + ws_dp[xi] + max(app_med)*0.015,
                f'{wv:.3f}s', ha='center', fontsize=8)

    plt.tight_layout()
    path = os.path.join(OUT_DIR, f'fig{fig_num}_validacao_dur_{protocolo.lower().replace("-","")}.png')
    plt.savefig(path); plt.close()
    print(f'  Salvo: {path}')


# ── Tabela de overhead ─────────────────────────────────────────────────────────
def tabela_overhead():
    rows = [
        {'Camada':           'Rede (IPv4)',
         'Campo':            'Cabeçalho IP',
         'Tamanho (bytes)':  20},
        {'Camada':           'Transporte (UDP)',
         'Campo':            'Cabeçalho UDP',
         'Tamanho (bytes)':  8},
        {'Camada':           'Aplicação (R-UDP)',
         'Campo':            'Número de Sequência (seq)',
         'Tamanho (bytes)':  4},
        {'Camada':           'Aplicação (R-UDP)',
         'Campo':            'Checksum',
         'Tamanho (bytes)':  2},
        {'Camada':           'Aplicação (R-UDP)',
         'Campo':            'Flags de controle',
         'Tamanho (bytes)':  1},
        {'Camada':           'Aplicação (R-UDP)',
         'Campo':            'X-Custom-Auth (SHA-256 hex)',
         'Tamanho (bytes)':  36},
        {'Camada':           'TOTAL',
         'Campo':            '—',
         'Tamanho (bytes)':  71},
    ]
    df = pd.DataFrame(rows)
    path = os.path.join(OUT_DIR, 'tabela_overhead_bytes.csv')
    df.to_csv(path, index=False)
    print(f'  Salvo: {path}')
    return df


# ── Main ───────────────────────────────────────────────────────────────────────
def main():
    print('Carregando dados...')
    rudp_app, tcp_app, rudp_ws, tcp_ws = carregar_dados()

    print('\nGerando tabelas estatísticas...')
    df_tp, df_dur = stats_todos(rudp_app, tcp_app, rudp_ws, tcp_ws)
    path_tp  = os.path.join(OUT_DIR, 'tabela_throughput_stats.csv')
    path_dur = os.path.join(OUT_DIR, 'tabela_duracao_stats.csv')
    df_tp.to_csv(path_tp,  index=False); print(f'  Salvo: {path_tp}')
    df_dur.to_csv(path_dur, index=False); print(f'  Salvo: {path_dur}')
    tabela_overhead()

    print('\nGerando gráficos...')
    fig_throughput_medio(rudp_app, tcp_app)              # Fig 1
    fig_tempo_medio(rudp_app, tcp_app)                   # Fig 2
    fig_desvio_padrao(rudp_app, tcp_app)                 # Fig 3
    fig_validacao_cruzada_tp(tcp_app,  tcp_ws,  'TCP',   4)   # Fig 4
    fig_validacao_cruzada_tp(rudp_app, rudp_ws, 'R-UDP', 5)   # Fig 5
    fig_validacao_cruzada_dur(tcp_app,  tcp_ws,  'TCP',  6)   # Fig 6
    fig_validacao_cruzada_dur(rudp_app, rudp_ws, 'R-UDP', 7)  # Fig 7

    print('\nConcluído! Todos os arquivos gerados em:', OUT_DIR)


if __name__ == '__main__':
    main()