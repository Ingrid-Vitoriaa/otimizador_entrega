from models.enums import StatusPedido

class Pedido:
    def __init__(self, id, cliente, volume, prioridade):
        self.id = id
        self.cliente = cliente
        self.volume = volume
        self.prioridade = prioridade
        self.status = StatusPedido.PENDENTE

    def __repr__(self):
        return f"Pedido({self.id}, prioridade={self.prioridade}, status={self.status})"
