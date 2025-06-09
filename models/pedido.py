from models.enums import StatusPedido
from models.cliente import Cliente  

class Pedido:
    def __init__(self, id: int, cliente: Cliente, volume: float, prioridade: int, status: StatusPedido = StatusPedido.PENDENTE):
        if volume < 0:
            raise ValueError(f"Volume não pode ser negativo, recebeu {volume}")
        if not isinstance(status, StatusPedido):
            raise ValueError(f"Status inválido: esperado StatusPedido, recebeu {type(status)}")

        self.id = id
        self.cliente = cliente
        self.volume = volume
        self.prioridade = prioridade
        self.status = status

    def __repr__(self) -> str:
        return f"Pedido({self.id}, prioridade={self.prioridade}, status={self.status.name})"

    def __str__(self) -> str:
        return (f"Pedido {self.id} para {self.cliente.nome}: Volume {self.volume}, "
                f"Prioridade {self.prioridade}, Status {self.status.name}")
