import socket
import os

def rodar_servidor_tcp(porta=5000):
    servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    servidor.bind(('0.0.0.0', porta)) # Ouve em todas as interfaces
    servidor.listen(1)
    
    print(f"[*] Servidor TCP aguardando conexão na porta {porta}...")
    
    while True:
        conn, addr = servidor.accept()
        print(f"-> Conexão estabelecida com {addr}")
        
        # Nome do arquivo de saída
        nome_arquivo = "arquivo_recebido_tcp.bin"
        
        with open(nome_arquivo, "wb") as f:
            while True:
                dados = conn.recv(4096) # Recebe em blocos de 4KB
                if not dados:
                    break # Fim da transmissão
                f.write(dados)
        
        print(f"-> Arquivo '{nome_arquivo}' recebido com sucesso.")
        conn.close()
        print("-> Conexão encerrada. Aguardando nova conexão...")

if __name__ == "__main__":
    rodar_servidor_tcp()