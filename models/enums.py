from enum import Enum

class StatusPedido(Enum):
    PENDENTE = 1
    ENTREGUE = 2
    CANCELADO = 3
    EM_TRANSPORTE = 4

class TipoVeiculo(Enum):
    MOTO = 1
    VAN = 2
    CARRO = 3

class Cliente:
    def __init__(self, id, nome, zona, endereco=None):
        self.id = id
        self.nome = nome
        self.zona = zona
        self.endereco = endereco  # adiciona endereço completo

class Pedido:
    def __init__(self, id, cliente, volume, prioridade, status=StatusPedido.PENDENTE):
        self.id = id
        self.cliente = cliente
        self.volume = volume
        self.prioridade = prioridade
        if isinstance(status, str):
            self.status = StatusPedido[status]  # converte string para enum
        else:
            self.status = status

class Veiculo:
    def __init__(self, id, tipo, capacidade, disponivel):
        self.id = id
        if isinstance(tipo, str):
            self.tipo = TipoVeiculo[tipo]
        else:
            self.tipo = tipo
        self.capacidade = capacidade
        self.disponivel = disponivel
