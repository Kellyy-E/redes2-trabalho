import socket
import os
from src.common.utils import Packet, FLAG_ACK, FLAG_DATA, FLAG_FIN, calcular_checksum

def iniciar_servidor_rudp(ip="0.0.0.0", porta=5001):
    servidor = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    servidor.bind((ip, porta))
    
    print(f"-------Servidor R-UDP iniciado e escutando em {ip}:{porta}-------")
    
    while True:
        print("\n--------Aguardando nova transmissão de arquivo--------")
        arquivo_aberto = False
        f = None
        esperado_seq = 0  
        
        os.makedirs("data", exist_ok=True)
        caminho_saida = "data/recebido_rudp.bin"

        while True:
            try:
                dados_brutos, addr = servidor.recvfrom(8192) 
                if not dados_brutos:
                    continue
                
                pacote, checksum_recebido = Packet.unpack(dados_brutos)
                
                # Validação de Checksum
                dados_para_checksum = dados_brutos[:4] + b'\x00\x00' + dados_brutos[6:]
                if checksum_recebido != calcular_checksum(dados_para_checksum):
                    print(f"Checksum incorreto no pacote {pacote.seq}. Descartando...")
                    continue
                
                # Tratamento do FIM (FLAG_FIN)
                if pacote.flags == FLAG_FIN:
                    print(f"Flag FIN recebida de {addr}. Respondendo com ACK e fechando arquivo.")
                    ack_fin = Packet(seq=pacote.seq, flags=FLAG_ACK, auth_hash=pacote.auth_hash.decode())
                    
                    for _ in range(3): 
                        servidor.sendto(ack_fin.pack(), addr)
                    
                    if f and not f.closed:
                        f.close()
                    break # Quebra o loop interno para limpar as variáveis de sequência e abrir espaço para o próximo teste

                # Tratamento de Dados 
                elif pacote.flags == FLAG_DATA:
                    if pacote.seq == esperado_seq:
                        if not arquivo_aberto:
                            f = open(caminho_saida, "wb")
                            arquivo_aberto = True
                        
                        f.write(pacote.data)
                        
                        ack = Packet(seq=pacote.seq, flags=FLAG_ACK, auth_hash=pacote.auth_hash.decode())
                        servidor.sendto(ack.pack(), addr)
                        
                        # Alterna entre 0 e 1 de forma correta
                        esperado_seq = 1 - esperado_seq
                    else:
                        # Se o cliente retransmitiu o pacote anterior, o ACK se perdeu na rede.
                        # Reenvia o ACK do pacote antigo para fazer o cliente avançar
                        ack_duplicado = Packet(seq=pacote.seq, flags=FLAG_ACK, auth_hash=pacote.auth_hash.decode())
                        servidor.sendto(ack_duplicado.pack(), addr)
                        
            except Exception as e:
                print(f"[ERRO] Falha no processamento: {e}")
                if f and not f.closed:
                    f.close()
                break

if __name__ == "__main__":
    iniciar_servidor_rudp()