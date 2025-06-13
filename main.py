from enum import Enum
from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp
import networkx as nx

from simulador.simulador import simular_bloqueio_rotas, simular_aumento_demanda, criar_modelo_vrp
from simulador.relatorio import gerar_relatorio
from fluxo.network_builder import build_flow_network, get_allocations

class StatusPedido(Enum):
    PENDENTE = 1
    ENTREGUE = 2

class Cliente:
    def __init__(self, id, nome, zona):
        if not zona.startswith("Zona ") or not zona.split()[-1].isdigit():
            raise ValueError("Zona inválida")
        self.id = id
        self.nome = nome
        self.zona = zona

class Pedido:
    def __init__(self, id, cliente, volume, prioridade, status=StatusPedido.PENDENTE):
        if volume < 0:
            raise ValueError("Volume não pode ser negativo")
        self.id = id
        self.cliente = cliente
        self.volume = volume
        self.prioridade = prioridade
        self.status = status

class Veiculo:
    def __init__(self, id, tipo, capacidade, disponivel, zonas_permitidas=None):
        if capacidade < 0:
            raise ValueError("Capacidade não pode ser negativa")
        self.id = id
        self.tipo = tipo
        self.capacidade = capacidade
        self.disponivel = disponivel
        self.zonas_permitidas = zonas_permitidas if zonas_permitidas else []

def gerar_matriz_distancias(pedidos, penalidade_zona=10):
    G = nx.Graph()
    n = len(pedidos)
    for i in range(n):
        for j in range(n):
            if i != j:
                zona_i = int(pedidos[i].cliente.zona.split()[-1])
                zona_j = int(pedidos[j].cliente.zona.split()[-1])
                base_distancia = abs(zona_i - zona_j) + 1
                penalidade = penalidade_zona * abs(zona_i - zona_j) if zona_i != zona_j else 0
                distancia = base_distancia + penalidade
                G.add_edge(i, j, weight=distancia)

    matriz = []
    for i in range(n):
        linha = []
        for j in range(n):
            if i == j:
                linha.append(0)
            else:
                linha.append(nx.shortest_path_length(G, i, j, weight='weight'))
        matriz.append(linha)
    return matriz

def main():
    clientes = [
        Cliente(0, "Brian Evans", "Zona 4"),
        Cliente(1, "Christine Adams", "Zona 2"),
        Cliente(2, "Billy Bryan", "Zona 2"),
        Cliente(3, "Harold Harper", "Zona 2"),
        Cliente(4, "William Johnson", "Zona 2"),
        Cliente(5, "Jennifer Robinson", "Zona 5"),
        Cliente(6, "Daniel Barnes", "Zona 5"),
        Cliente(7, "Vicki Arias", "Zona 4"),
        Cliente(8, "Jason Garcia", "Zona 2"),
        Cliente(9, "Mrs. Angela Spears", "Zona 3")
    ]

    pedidos = [
        Pedido(0, clientes[3], 85, 5),
        Pedido(1, clientes[6], 84, 3),
        Pedido(2, clientes[7], 95, 5),
        Pedido(3, clientes[7], 79, 1),
        Pedido(4, clientes[2], 58, 4),
        Pedido(5, clientes[0], 20, 5),
        Pedido(6, clientes[8], 72, 5),
        Pedido(7, clientes[0], 74, 1),
        Pedido(8, clientes[0], 39, 1),
        Pedido(9, clientes[3], 31, 3),
        Pedido(10, clientes[6], 22, 1),
        Pedido(11, clientes[2], 45, 5),
        Pedido(12, clientes[7], 48, 3),
        Pedido(13, clientes[3], 11, 4),
        Pedido(14, clientes[5], 27, 5)
    ]

    veiculos = [
        Veiculo(0, "MOTO", 122, True, zonas_permitidas=["Zona 2", "Zona 3"]),
        Veiculo(1, "MOTO", 115, True, zonas_permitidas=["Zona 4", "Zona 5"]),
        Veiculo(2, "VAN", 90, True),
        Veiculo(3, "VAN", 73, True, zonas_permitidas=["Zona 2"]),
        Veiculo(4, "MOTO", 142, True)
    ]

    matriz = gerar_matriz_distancias(pedidos)

    # Simulação de bloqueio de rotas
    rotas_bloqueadas = [(1, 3), (3, 1)]
    matriz_simulada = simular_bloqueio_rotas(matriz, rotas_bloqueadas)

    # Simulação de aumento de demanda (ex: Zona 2 aumento 20%)
    aumento_por_zona = {"Zona 2": 1.2}
    demandas_simuladas = simular_aumento_demanda(pedidos, aumento_por_zona)

    capacidades = [v.capacidade for v in veiculos]
    num_veiculos = len(veiculos)
    zonas_pedidos = [p.cliente.zona for p in pedidos]

    total_demanda = sum(demandas_simuladas)
    total_capacidade = sum(capacidades)
    print(f"\n🔍 Total de demanda simulada: {total_demanda}")
    print(f"🚚 Capacidade total dos veículos: {total_capacidade}\n")

    print("📦 Zonas dos pedidos:")
    for i, p in enumerate(pedidos):
        print(f"Pedido {p.id}: Zona {p.cliente.zona}, Demanda = {demandas_simuladas[i]}, Prioridade = {p.prioridade}")

    print("\n🚗 Zonas permitidas por veículo:")
    for v in veiculos:
        zonas = v.zonas_permitidas if v.zonas_permitidas else "Todas"
        print(f"Veículo {v.id} ({v.tipo}) → Zonas: {zonas}, Capacidade: {v.capacidade}")

    # Chama VRP com prioridade no filtro de zonas (não altera prioridade no modelo, mas já temos a informação)
    rotas = criar_modelo_vrp(matriz_simulada, demandas_simuladas, capacidades, num_veiculos, zonas_pedidos, veiculos)

    if rotas is None:
        print("\n❌ Não foi possível encontrar uma solução para o VRP.")
        # Quando não há rotas, passamos None nas alocações
        gerar_relatorio(pedidos, veiculos, [], demandas_simuladas)
        return
    else:
        print("\n--- Rotas Otimizadas ---")
        for vid, rota in enumerate(rotas):
            print(f"Veículo {vid} fará pedidos: {rota}")

        # Simula fluxo de rede para gerar alocação
        flow = build_flow_network(pedidos, veiculos)
        max_flow = flow.multi_max_flow()
        allocations = get_allocations(flow, len(pedidos), len(veiculos))

        gerar_relatorio(pedidos, veiculos, allocations, demandas_simuladas)

if __name__ == "__main__":
    main()