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
    CARRO_MEDIO = 4
    CAMINHAO = 5
