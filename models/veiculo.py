from models.enums import TipoVeiculo

class Veiculo:
    def __init__(self, id: int, tipo: TipoVeiculo, capacidade: float, disponivel: bool = True):
        if capacidade < 0:
            raise ValueError(f"Capacidade não pode ser negativa, recebeu {capacidade}")
        if not isinstance(tipo, TipoVeiculo):
            raise ValueError(f"Tipo de veículo inválido: esperado TipoVeiculo, recebeu {type(tipo)}")

        self.id = id
        self.tipo = tipo
        self.capacidade = capacidade
        self.disponivel = disponivel

    def __repr__(self) -> str:
        return f"Veiculo({self.tipo.name}, capacidade={self.capacidade}, disponível={self.disponivel})"

    def __str__(self) -> str:
        return f"Veículo {self.id}: Tipo {self.tipo.name}, Capacidade {self.capacidade}, Disponível: {self.disponivel}"
