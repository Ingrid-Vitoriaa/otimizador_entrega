class Cliente:
    def __init__(self, id, nome, zona, latitude=None, longitude=None):
        self.id = id
        self.nome = nome
        self.zona = zona
        self.latitude = latitude
        self.longitude = longitude

    def __repr__(self) -> str:
        return f"Cliente({self.nome}, Zona: {self.zona})"

    def __str__(self) -> str:
        endereco_str = self.endereco if self.endereco else "Endereço não informado"
        return f"Cliente {self.nome}, Zona: {self.zona}, Endereço: {endereco_str}"
