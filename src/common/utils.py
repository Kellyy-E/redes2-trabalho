import hashlib
import struct

def gerar_x_custom_auth(matricula, nome):
    """
    Gera o Hash SHA-256 obrigatório (Matrícula + Nome).
    """
    # Remove espaços para garantir que o hash seja consistente
    string_base = f"{matricula}{nome.strip()}"
    return hashlib.sha256(string_base.encode()).hexdigest()

def calcular_checksum(dados):
    """
    Implementa uma validação simples de integridade por bloco.
    Soma os valores dos bytes (limitado a 16 bits).
    """
    if len(dados) % 2 == 1:
        dados += b'\0'
    s = sum(struct.unpack("!%dH" % (len(dados) // 2), dados))
    s = (s >> 16) + (s & 0xffff)
    s += s >> 16
    return ~s & 0xffff

class Packet:
    # Estrutura: !I (Seq: 4b) + H (Checksum: 2b) + B (Flags: 1b) + 64s (Auth: 64b)
    HEADER_FORMAT = "!IHB64s"

    def __init__(self, seq, flags, auth_hash, data=b''):
        self.seq = seq
        self.flags = flags
        self.auth_hash = auth_hash.encode()
        self.data = data
        self.checksum = 0

    def pack(self):
        """Transforma o objeto em bytes para enviar pela rede."""
        # Primeiro calcula o checksum com campo zerado
        header_temp = struct.pack(self.HEADER_FORMAT, self.seq, 0, self.flags, self.auth_hash)
        self.checksum = calcular_checksum(header_temp + self.data)
        
        # Agora empacota com o checksum real
        header = struct.pack(self.HEADER_FORMAT, self.seq, self.checksum, self.flags, self.auth_hash)
        return header + self.data

    @staticmethod
    def unpack(packet_bytes):
        """Transforma bytes recebidos em um objeto Packet."""
        header_size = struct.calcsize(Packet.HEADER_FORMAT)
        header_bytes = packet_bytes[:header_size]
        data = packet_bytes[header_size:]
        
        seq, checksum, flags, auth_hash = struct.unpack(Packet.HEADER_FORMAT, header_bytes)
        
        # Validação de integridade 
        # (Opcional: implementar verificação de checksum aqui)
        
        return Packet(seq, flags, auth_hash.decode(), data), checksum