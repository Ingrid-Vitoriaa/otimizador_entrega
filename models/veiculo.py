# models/veiculo.py
from typing import Optional, List
from models.enums import TipoVeiculo

class Veiculo:
    # Adicione 'disponivel' e 'zonas_permitidas' ao construtor
    def __init__(self, id: int, tipo: TipoVeiculo, capacidade: int, disponivel: bool = True, zonas_permitidas: Optional[List[str]] = None):
        self.id = id
        self.tipo = tipo
        self.capacidade = capacidade
        self.disponivel = disponivel 
        self.zonas_permitidas = zonas_permitidas

    def __repr__(self):
        return f"Veiculo(id={self.id}, tipo={self.tipo.name}, capacidade={self.capacidade}, disponivel={self.disponivel})"