from utils import gerar_x_custom_auth, calcular_checksum, Packet

def testar_protocolo():
    # 1. Teste de Identidade
    matricula = "202612345" # Substitua pela sua
    nome = "Eurikelly Luiza" # Substitua pelo seu
    hash_auth = gerar_x_custom_auth(matricula, nome)
    print(f"--- TESTE DE IDENTIDADE ---")
    print(f"Matrícula + Nome: {matricula}{nome}")
    print(f"Hash SHA-256 (64 chars): {hash_auth}\n")

    # 2. Teste de Pacote e Checksum
    print(f"--- TESTE DE INTEGRIDADE ---")
    dados_originais = b"Ola, este e um teste de Redes II!"
    
    # Criamos um pacote com Sequência 1 e Flag 0 (Dados)
    pacote = Packet(seq=1, flags=0, auth_hash=hash_auth, data=dados_originais)
    
    # Transformamos em bytes para "enviar"
    pacote_binario = pacote.pack()
    print(f"Pacote empacotado (bytes): {pacote_binario}") # Mostra só o início

# Simulamos o recebimento e desempacotamos
    # Aqui, desempacotamos o objeto E o valor do checksum que veio no cabeçalho
    pacote_recebido, checksum = Packet.unpack(pacote_binario)
    
    print(f"Dados recebidos: {pacote_recebido.data.decode()}")
    
    print(f"Checksum extraído do cabeçalho: {checksum}")
    
    # Teste de validação (Opcional, mas recomendado)
    if checksum != 0:
        print("✅ SUCESSO: O Checksum foi calculado e transmitido!")
    else:
        print("⚠️ ALERTA: O Checksum resultou em 0 (pode ser coincidência ou erro).")

    if pacote_recebido.data == dados_originais:
        print("✅ SUCESSO: Os dados chegaram íntegros!")

if __name__ == "__main__":
    testar_protocolo()