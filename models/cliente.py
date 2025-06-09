import random  # Lembre-se de importar no topo do seu arquivo

class Cliente:
    def __init__(self, id, nome, zona, latitude=None, longitude=None, endereco=None):
        if not zona.startswith("Zona ") or not zona.split()[-1].isdigit():
            raise ValueError("Zona inválida")
        self.id = id
        self.nome = nome
        self.zona = zona
        self.latitude = latitude or random.uniform(-23.63, -23.53)  # Exemplo: valores em São Paulo
        self.longitude = longitude or random.uniform(-46.70, -46.60)
        self.endereco = endereco  # Campo opcional para endereço

    def __repr__(self) -> str:
        return f"Cliente({self.nome}, Zona: {self.zona})"

    def __str__(self) -> str:
        endereco_str = self.endereco if self.endereco else "Endereço não informado"
        return f"Cliente {self.nome}, Zona: {self.zona}, Endereço: {endereco_str}"
