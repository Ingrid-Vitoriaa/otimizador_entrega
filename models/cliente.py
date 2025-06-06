import random

class Cliente:
    def __init__(self, id, nome, zona, latitude=None, longitude=None):
        self.id = id
        self.nome = nome
        self.zona = zona
        self.latitude = latitude or random.uniform(-23.63, -23.53)  # Ex: SP
        self.longitude = longitude or random.uniform(-46.70, -46.60)
