import os
import pandas as pd
import numpy as np

def carregar_e_rotular(caminho_csv, origem_nome):
    if not os.path.exists(caminho_csv):
        return None
        
    df = pd.read_csv(caminho_csv)
    
    # Se for o CSV da aplicação, precisamos rotular os cenários sequenciais
    if 'Cenário' not in df.columns:
        df['Cenário'] = ''
        cenarios_nomes = ['Cenário A (0% perda)', 'Cenário B (5% perda)', 'Cenário C (10% perda)']
        for proto in ['TCP', 'R-UDP']:
            idx = df[df['Protocolo'] == proto].index
            fatias = np.array_split(idx, 3)
            for i, nome in enumerate(cenarios_nomes):
                if i < len(fatias):
                    df.loc[fatias[i], 'Cenário'] = nome
                    
    df['Origem'] = origem_nome
    return df[['Cenário', 'Protocolo', 'Throughput(KB/s)', 'Origem']]

def main():
    pasta_script = os.path.dirname(os.path.abspath(__file__))
    raiz = os.path.abspath(os.path.join(pasta_script, ".."))
    
    # Localiza os arquivos
    csv_app = os.path.join(raiz, 'metricas_desempenho.csv')
    csv_wire = os.path.join(raiz, 'metricas_via_wireshark.csv')
    
    if not os.path.exists(csv_app): csv_app = os.path.join(pasta_script, 'metricas_desempenho.csv')
    if not os.path.exists(csv_wire): csv_wire = os.path.join(pasta_script, 'metricas_via_wireshark.csv')
    
    df_ap = carregar_e_rotular(csv_app, 'Aplicação (Python)')
    df_wi = carregar_e_rotular(csv_wire, 'Rede (Wireshark/tcpdump)')
    
    if df_ap is None and df_wi is None:
        print("Nenhum arquivo CSV foi encontrado.")
        return

    # Junta os dados se ambos existirem para comparar lado a lado
    lista_dfs = [df for df in [df_ap, df_wi] if df is not None]
    df_total = pd.concat(lista_dfs, ignore_index=True)
    
    # Agrupa por Origem, Cenário e Protocolo e calcula o resumo estatístico solicitado
    resumo_estatistico = df_total.groupby(['Origem', 'Cenário', 'Protocolo'])['Throughput(KB/s)'].agg(
        Mínima='min',
        Média='mean',
        Máxima='max',
        Desvio_Padrão='std'
    ).round(2)
    
    print(" RESUMO ESTATÍSTICO DE VAZÃO")
    
    # Exibe a tabela formatada na tela
    pd.set_option('display.max_columns', None)
    pd.set_option('display.width', 1000)
    print(resumo_estatistico)
    print("="*85)
    
    # Opcional: Salva uma planilha com os dados consolidados para conferência posterior
    caminho_saida = os.path.join(pasta_script, 'tabela_estatisticas_vazao.csv')
    resumo_estatistico.to_csv(caminho_saida)
    print(f"Tabela exportada com sucesso para: 'analysis/tabela_estatisticas_vazao.csv'\n")

if __name__ == "__main__":
    main()