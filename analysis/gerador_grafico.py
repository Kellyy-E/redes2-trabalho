import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# 1. CONFIGURAÇÃO DE ESTILO ACADÊMICO (PADRÃO SBC)
sns.set_theme(style="whitegrid")
plt.rcParams.update({
    'font.size': 11, 'axes.labelsize': 11, 'axes.titlesize': 12,
    'xtick.labelsize': 10, 'ytick.labelsize': 10
})

def carregar_e_preparar_dados():
    pasta_script = os.path.dirname(os.path.abspath(__file__))
    raiz = os.path.abspath(os.path.join(pasta_script, ".."))
    
    # Mapeia os caminhos possíveis para os arquivos CSV
    csv_app = os.path.join(raiz, 'metricas_desempenho.csv')
    csv_wire = os.path.join(raiz, 'metricas_via_wireshark.csv')
    
    if not os.path.exists(csv_app): csv_app = os.path.join(pasta_script, 'metricas_desempenho.csv')
    if not os.path.exists(csv_wire): csv_wire = os.path.join(pasta_script, 'metricas_via_wireshark.csv')
    
    if not os.path.exists(csv_app) or not os.path.exists(csv_wire):
        raise FileNotFoundError("Certifique-se de que 'metricas_desempenho.csv' e 'metricas_via_wireshark.csv' existem.")
        
    # Carrega e rotula cenários da Aplicação
    df_ap = pd.read_csv(csv_app)
    cenarios = ['Cenário A\n(0% Perda)', 'Cenário B\n(5% Perda)', 'Cenário C\n(10% Perda)']
    
    for proto in ['TCP', 'R-UDP']:
        idx = df_ap[df_ap['Protocolo'] == proto].index
        fatias = np.array_split(idx, 3)
        for idx_f, nome in enumerate(cenarios):
            if idx_f < len(fatias):
                df_ap.loc[fatias[idx_f], 'Cenário'] = nome
    df_ap['Origem'] = 'Aplicação (Python)'
    
    # Carrega e ajusta quebras de linha para os cenários do Wireshark
    df_wi = pd.read_csv(csv_wire)
    df_wi['Cenário'] = df_wi['Cenário'].str.replace(' (0% perda)', '\n(0% Perda)', regex=False)
    df_wi['Cenário'] = df_wi['Cenário'].str.replace(' (5% perda)', '\n(5% Perda)', regex=False)
    df_wi['Cenário'] = df_wi['Cenário'].str.replace(' (10% perda)', '\n(10% Perda)', regex=False)
    df_wi['Origem'] = 'Rede (Wireshark)'
    
    # Criação da pasta "graficos-gerados" no diretório do script
    pasta_graficos = os.path.join(pasta_script, 'graficos-gerados')
    os.makedirs(pasta_graficos, exist_ok=True)
    
    return df_ap, df_wi, pasta_graficos

# =========================================================================
# FUNÇÕES AUXILIARES DE PLOTAGEM DE BARRAS
# =========================================================================
def adicionar_rotulos(ax, formato='{:.3f}s'):
    for p in ax.patches:
        h = p.get_height()
        if h > 0:
            ax.annotate(formato.format(h), (p.get_x() + p.get_width() / 2., h),
                        ha='center', va='center', xytext=(0, 8), textcoords='offset points', 
                        fontsize=9, fontweight='bold')

def gerar_grafico_simples(df, x, y, hue, titulo, y_label, paleta, salvar_em, log_scale=False, fmt='{:.3f}s'):
    plt.figure(figsize=(8.5, 5.5))
    ax = sns.barplot(data=df, x=x, y=y, hue=hue, palette=paleta, errorbar='sd', capsize=0.06, edgecolor='0.2')
    if log_scale: 
        plt.yscale('log')
    plt.title(titulo, fontweight='bold')
    plt.xlabel('Cenários Controlados')
    plt.ylabel(y_label)
    plt.legend(title=hue)
    adicionar_rotulos(ax, fmt)
    plt.tight_layout()
    plt.savefig(salvar_em, dpi=300)
    plt.close()

# =========================================================================
# EXECUÇÃO DO PIPELINE DE ANÁLISES
# =========================================================================
def main():
    try:
        df_app, df_wire, pasta_graficos = carregar_e_preparar_dados()
        df_total = pd.concat([df_app, df_wire], ignore_index=True)
        
        print("\n" + "="*50 + "\n   INICIANDO GERAÇÃO DOS GRÁFICOS DO RELATÓRIO\n" + "="*50)
        print(f"Diretório de destino: {pasta_graficos}\n")
        
        # -----------------------------------------------------------------
        # BLOCO 1: COMPARATIVOS DA APLICAÇÃO (Métricas Puras do Python)
        # -----------------------------------------------------------------
        # Gráfico 1: Comparativo de Duração
        gerar_grafico_simples(
            df=df_app, x='Cenário', y='Duração(s)', hue='Protocolo',
            titulo='Comparativo de Tempo de Duração Total (Métricas da Aplicação)',
            y_label='Tempo Total de Transferência (segundos)', paleta=['#4c72b0', '#c44e52'],
            salvar_em=os.path.join(pasta_graficos, 'comparativo_tempo_aplicacao.png')
        )
        print("[✓] Gráfico 1 Gerado: 'comparativo_tempo_aplicacao.png'")
        
        # Gráfico 2: Comparativo de Vazão (Escala Log)
        gerar_grafico_simples(
            df=df_app, x='Cenário', y='Throughput(KB/s)', hue='Protocolo',
            titulo='Comparativo de Vazão Real / Throughput (Métricas da Aplicação)',
            y_label='Vazão Média (KB/s) - Escala Logarítmica', paleta=['#4c72b0', '#c44e52'],
            salvar_em=os.path.join(pasta_graficos, 'comparativo_vazao_aplicacao.png'),
            log_scale=True, fmt='{:.1f}\nKB/s'
        )
        print("[✓] Gráfico 2 Gerado: 'comparativo_vazao_aplicacao.png'")
        
        # -----------------------------------------------------------------
        # BLOCO 2: VALIDAÇÃO CRUZADA DE TEMPO (Aplicação vs Rede)
        # -----------------------------------------------------------------
        # Gráfico 3: Validação de Tempo - TCP
        gerar_grafico_simples(
            df=df_total[df_total['Protocolo'] == 'TCP'], x='Cenário', y='Duração(s)', hue='Origem',
            titulo='Validação Cruzada de Tempo de Execução: Protocolo TCP (Nativo)',
            y_label='Tempo Total de Transferência (segundos)', paleta=['#5b84c4', '#2c4a75'],
            salvar_em=os.path.join(pasta_graficos, 'validacao_duracao_tcp.png')
        )
        print("[✓] Gráfico 3 Gerado: 'validacao_duracao_tcp.png'")
        
        # Gráfico 4: Validação de Tempo - R-UDP
        gerar_grafico_simples(
            df=df_total[df_total['Protocolo'] == 'R-UDP'], x='Cenário', y='Duração(s)', hue='Origem',
            titulo='Validação Cruzada de Tempo de Execução: Protocolo R-UDP (Customizado)',
            y_label='Tempo Total de Transferência (segundos)', paleta=['#e07a5f', '#bc3908'],
            salvar_em=os.path.join(pasta_graficos, 'validacao_duracao_rudp.png')
        )
        print("[✓] Gráfico 4 Gerado: 'validacao_duracao_rudp.png'")
        
        # -----------------------------------------------------------------
        # BLOCO 3: VALIDAÇÃO CRUZADA DE VAZÃO (Aplicação vs Rede)
        # -----------------------------------------------------------------
        # Gráfico 5: Validação de Vazão - TCP
        gerar_grafico_simples(
            df=df_total[df_total['Protocolo'] == 'TCP'], x='Cenário', y='Throughput(KB/s)', hue='Origem',
            titulo='Validação Cruzada de Vazão: Protocolo TCP (Nativo)',
            y_label='Vazão Medida / Throughput (KB/s)', paleta=['#5b84c4', '#2c4a75'],
            salvar_em=os.path.join(pasta_graficos, 'validacao_vazao_tcp.png'),
            fmt='{:.1f}'
        )
        print("[✓] Gráfico 5 Gerado: 'validacao_vazao_tcp.png'")
        
        # Gráfico 6: Validação de Vazão - R-UDP
        gerar_grafico_simples(
            df=df_total[df_total['Protocolo'] == 'R-UDP'], x='Cenário', y='Throughput(KB/s)', hue='Origem',
            titulo='Validação Cruzada de Vazão: Protocolo R-UDP (Customizado)',
            y_label='Vazão Medida / Throughput (KB/s)', paleta=['#e07a5f', '#bc3908'],
            salvar_em=os.path.join(pasta_graficos, 'validacao_vazao_rudp.png'),
            fmt='{:.2f}'
        )
        print("[✓] Gráfico 6 Gerado: 'validacao_vazao_rudp.png'")
        
        print("\n" + "="*50 + f"\n[✓] SUCESSO! TODOS OS 6 GRÁFICOS FORAM SALVOS EM:\n    {pasta_graficos}\n" + "="*50)
        
    except Exception as e:
        print(f"\n[⚠️] Erro no pipeline de análise: {e}")

if __name__ == "__main__":
    main()