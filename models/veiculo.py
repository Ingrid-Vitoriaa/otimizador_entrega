from models.enums import TipoVeiculo

class Veiculo:
    def __init__(self, id, tipo: TipoVeiculo, capacidade):
        self.id = id
        self.tipo = tipo
        self.capacidade = capacidade
        self.disponivel = True

    def __repr__(self):
        return f"Veiculo({self.tipo}, capacidade={self.capacidade})"
