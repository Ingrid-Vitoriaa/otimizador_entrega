from models.enums import TipoVeiculo

class Veiculo:
    def __init__(self, id: int, tipo: str, capacidade: int, disponivel: bool, zonas_permitidas: list[str] = None):
        if capacidade < 0:
            raise ValueError("Capacidade não pode ser negativa")
        self.id = id
        self.tipo = tipo
        self.capacidade = capacidade
        self.disponivel = disponivel
        self.zonas_permitidas = zonas_permitidas if zonas_permitidas else []