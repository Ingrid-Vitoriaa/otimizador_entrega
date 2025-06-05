class Cliente:
    def __init__(self, id, nome, endereco, zona):
        self.id = id
        self.nome = nome
        self.endereco = endereco
        self.zona = zona

    def __repr__(self):
        return f"Cliente({self.nome}, {self.zona})"
