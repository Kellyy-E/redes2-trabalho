import socket
import time
import os

def enviar_arquivo_tcp(caminho_arquivo, ip_destino, porta=5000):
    if not os.path.exists(caminho_arquivo):
        print("Erro: Arquivo não encontrado.")
        return

    tamanho_arquivo = os.path.getsize(caminho_arquivo)
    
    # Início da medição de desempenho
    inicio = time.time()
    
    # Criação do socket TCP
    cliente = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    try:
        cliente.connect((ip_destino, porta))
        
        with open(caminho_arquivo, "rb") as f:
            while True:
                chunk = f.read(4096)
                if not chunk:
                    break
                cliente.sendall(chunk) # Envia garantindo que todos os bytes saiam
                
        cliente.close()
        fim = time.time()
        
        # Cálculos exigidos (Item 18 e 42 do PDF)
        duracao = fim - inicio
        throughput_kbs = (tamanho_arquivo / 1024) / duracao if duracao > 0 else 0
        
        print(f"\n--- Estatísticas de Envio TCP ---")
        print(f"Arquivo: {caminho_arquivo}")
        print(f"Tempo total: {duracao:.4f} segundos")
        print(f"Vazão (Throughput): {throughput_kbs:.2f} KB/s")
        
    except ConnectionRefusedError:
        print("Erro: O servidor não está ligado ou a porta está fechada.")

if __name__ == "__main__":
    # Teste local (IP 127.0.0.1)
    # Você precisará criar um arquivo chamado 'teste.bin' para testar
    enviar_arquivo_tcp("teste.bin", "127.0.0.1")