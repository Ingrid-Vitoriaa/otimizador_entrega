class Nodo:
    def __init__(self, id, tipo, nome=None, latitude=None, longitude=None):
        self.id = id
        self.tipo = tipo
        self.nome = nome
        self.latitude = latitude
        self.longitude = longitude

    def __repr__(self):
        return (f"<{self.tipo.upper()} {self.id}: {self.nome}, "
                f"lat={self.latitude}, lon={self.longitude}>")

class Deposito(Nodo):
    def __init__(self, id, nome=None, latitude=None, longitude=None):
        super().__init__(id, "deposito", nome, latitude, longitude)

class Hub(Nodo):
    def __init__(self, id, nome=None, latitude=None, longitude=None):
        super().__init__(id, "hub", nome, latitude, longitude)

class ZonaEntrega(Nodo):
    def __init__(self, id, nome=None, latitude=None, longitude=None):
        super().__init__(id, "zona", nome, latitude, longitude)

class Rota:
    def __init__(self, origem, destino, capacidade):
        self.origem = origem
        self.destino = destino
        self.capacidade = capacidade

    def __repr__(self):
        return f"Rota({self.origem} -> {self.destino}, cap={self.capacidade})"
 

