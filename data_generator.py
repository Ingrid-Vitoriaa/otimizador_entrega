from faker import Faker
import random
from models.cliente import Cliente
from models.pedido import Pedido
from models.veiculo import Veiculo
from models.enums import TipoVeiculo
import data_storage  # importando o módulo que criamos para salvar/carregar

fake = Faker()

ZONAS = ["Zona 1", "Zona 2", "Zona 3", "Zona 4", "Zona 5"]

def gerar_clientes(qtd):
    return [Cliente(i, fake.name(), fake.address(), random.choice(ZONAS)) for i in range(qtd)]

def gerar_veiculos(qtd):
    tipos = list(TipoVeiculo)
    return [Veiculo(i, random.choice(tipos), random.randint(50, 200)) for i in range(qtd)]

def gerar_pedidos(clientes, qtd):
    return [
        Pedido(i, random.choice(clientes), volume=random.randint(10, 100), prioridade=random.randint(1, 5))
        for i in range(qtd)
    ]

if __name__ == "__main__":
    clientes = gerar_clientes(10)
    veiculos = gerar_veiculos(5)
    pedidos = gerar_pedidos(clientes, 15)

    print("Clientes:", clientes)
    print("Veículos:", veiculos)
    print("Pedidos:", pedidos)

    # SALVAR AUTOMÁTICO APÓS GERAR
    data_storage.salvar_clientes(clientes)
    data_storage.salvar_veiculos(veiculos)
    data_storage.salvar_pedidos(pedidos)

    print("Dados salvos em JSON com sucesso!")
