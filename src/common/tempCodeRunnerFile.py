    pacote_recebido, checksum_recebido = Packet.unpack(pacote_binario)
    
    print(f"Dados recebidos: {pacote_recebido.data.decode()}")
    print(f"Checksum calculado: {pacote_recebido.checksum}")
    
    if pacote_recebido.data == dados_originais:
        print("✅ SUCESSO: Os dados chegaram íntegros!")
    else:
        print("❌ ERRO: Os dados foram corrompidos.")