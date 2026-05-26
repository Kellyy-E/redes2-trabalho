import pandas as pd
import numpy as np

def converter_pcap(arquivo_pcap):
    print(f"Convertendo {arquivo_pcap}")
    
    df = pd.read_csv(arquivo_pcap, low_memory=False)
    df['Time'] = pd.to_numeric(df['Time'], errors='coerce')
    df['Length'] = pd.to_numeric(df['Length'], errors='coerce')
    df['Info'] = df['Info'].astype(str)
    df = df.dropna(subset=['Time', 'Length']).sort_values('Time').reset_index(drop=True)
    
    rodadas = []

    for porta, proto in [('5000', 'TCP'), ('5001', 'R-UDP')]:
        df_p = df[df['Info'].str.contains(porta, na=False)].copy()
        
        portas_cli = {i.split('>')[0].strip() for i in df_p['Info'] if '>' in i}
        portas_cli = {p for p in portas_cli if p != porta and p.isdigit()}
        
        for p in sorted(list(portas_cli)):
            df_s = df_p[df_p['Info'].str.contains(p, na=False)].copy()
            
            # Identifica quebras de sessão (silêncio > 5s indica nova rodada)
            df_s['id'] = (df_s['Time'].diff() > 5.0).cumsum()
            
            for _, df_sub in df_s.groupby('id'):
                t_ini, t_fim = df_sub['Time'].min(), df_sub['Time'].max()
                tempo = t_fim - t_ini
                bytes_t = df_sub['Length'].sum()
                
                # Filtros por protocolo 
                limite_b = 500000 if proto == 'TCP' else 10000
                limite_t = 60.0 if proto == 'TCP' else 150.0
                
                if bytes_t < limite_b or tempo <= 0.001 or tempo > limite_t:
                    continue
                
                vazao = (bytes_t / 1024) / tempo
                
                rodadas.append({
                    'Protocolo': proto,
                    'Duração(s)': round(tempo, 4),
                    'Throughput(KB/s)': round(vazao, 2),
                    'Ordem': t_ini
                })

    df_res = pd.DataFrame(rodadas)
    if df_res.empty:
        print("Nenhum tráfego encontrado")
        return df_res
        
    df_res = df_res.sort_values('Ordem').reset_index(drop=True)
    
    # 3. Rotula os cenários dividindo as rodadas de cada protocolo em 3 blocos iguais
    lista_finais = []
    nomes_cenarios = ['Cenário A (0% perda)', 'Cenário B (5% perda)', 'Cenário C (10% perda)']
    
    for proto in ['TCP', 'R-UDP']:
        df_sub = df_res[df_res['Protocolo'] == proto].copy().reset_index(drop=True)
        if df_sub.empty: 
            continue
            
        fatias = np.array_split(df_sub.index, 3)
        df_sub['Cenário'] = nomes_cenarios[0]
        
        for idx, nome in enumerate(nomes_cenarios):
            if idx < len(fatias):
                df_sub.loc[fatias[idx], 'Cenário'] = nome
                
        lista_finais.append(df_sub)
        
    df_final = pd.concat(lista_finais, ignore_index=True)
    return df_final[['Cenário', 'Protocolo', 'Duração(s)', 'Throughput(KB/s)']]

# --- Execução Direta ---
df_wireshark = converter_pcap('auditoria.csv')
df_wireshark.to_csv('metricas_via_wireshark.csv', index=False)

print(f"Metricas salvas em: 'metricas_via_wireshark.csv\nTotal de registros gerados: {len(df_wireshark)}")
print(df_wireshark.groupby(['Cenário', 'Protocolo']).size().to_string())