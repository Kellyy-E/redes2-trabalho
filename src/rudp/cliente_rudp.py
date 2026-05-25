import socket
import time
import os
import sys
from src.common.utils import Packet, gerar_x_custom_auth, FLAG_DATA, FLAG_ACK, FLAG_FIN, salvar_log_csv

def enviar_arquivo_rudp(caminho_arquivo, ip_destino, porta=5001):
    MATRICULA = "20249016916" 
    NOME = "Eurikelly Luiza"
    auth_hash = gerar_x_custom_auth(MATRICULA, NOME)
    
    TIMEOUT_VALUE = 0.5  # 500ms de espera antes de retransmitir
    
    # Criação do objeto socket UDP 
    cliente = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    cliente.settimeout(TIMEOUT_VALUE)

    if not os.path.exists(caminho_arquivo):
        print(f"[ERRO] Ficheiro não encontrado: {caminho_arquivo}")
        return

    tamanho_arquivo = os.path.getsize(caminho_arquivo)
    
    inicio_tempo = time.time()
    
    seq_atual = 0  

    with open(caminho_arquivo, "rb") as f:
        while True:
            dados = f.read(4096)  # Lê blocos de 4KB 
            if not dados:
                break  
            
            pacote = Packet(seq=seq_atual, flags=FLAG_DATA, auth_hash=auth_hash, data=dados)
            pacote_binario = pacote.pack()
            
            # Stop-and-Wait Puro 
            confirmado = False
            while not confirmado:
                try:
                    # Envia o bloco binário para o destino
                    cliente.sendto(pacote_binario, (ip_destino, porta))
                    
                    # Aguarda pelo ACK do servidor
                    ack_bytes, _ = cliente.recvfrom(8192) 
                    ack_obj, _ = Packet.unpack(ack_bytes)
                    
                    # Valida o ACK 
                    if ack_obj.flags == FLAG_ACK and ack_obj.seq == seq_atual:
                        confirmado = True
                        # Alterna o número de sequência entre 0 e 1 
                        seq_atual = 1 - seq_atual
                        
                except socket.timeout:
                    # Se houver perda ou latência excessiva, gera a exceção e retransmite
                    print(f"[!] Timeout no pacote de dados {seq_atual}. Reenviando...")

    print("Enviando sinalização de fim (FIN)...")
    pacote_fin = Packet(seq=seq_atual, flags=FLAG_FIN, auth_hash=auth_hash, data=b'')
    fin_binario = pacote_fin.pack()
    
    fin_confirmado = False
    while not fin_confirmado:
        try:
            cliente.sendto(fin_binario, (ip_destino, porta))
            
            ack_bytes, _ = cliente.recvfrom(8192)
            ack_obj, _ = Packet.unpack(ack_bytes)
            
            if ack_obj.flags == FLAG_ACK and ack_obj.seq == seq_atual:
                fin_confirmado = True
                print("Servidor confirmou o encerramento da transmissão.")
                
        except socket.timeout:
            print(f"Timeout no pacote FIN {seq_atual}. Reenviando sinal de fim...")

    cliente.close()
    fim_tempo = time.time()
    
    print("Transferência R-UDP concluída com sucesso.")
    
    #REGISTRO NO CSV
    salvar_log_csv("R-UDP", caminho_arquivo, inicio_tempo, fim_tempo, tamanho_arquivo)

if __name__ == "__main__":
    caminho = sys.argv[1] if len(sys.argv) > 1 else "data/arquivo_teste.bin"
    enviar_arquivo_rudp(caminho, "servidor")