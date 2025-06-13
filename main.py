from enum import Enum
from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp
import networkx as nx
import osmnx as ox
from grafos.coordenadas_osm import atualizar_coordenadas_no_json

from simulador.simulador import simular_bloqueio_rotas, simular_aumento_demanda, criar_modelo_vrp
from simulador.relatorio import gerar_relatorio
from fluxo.network_builder import build_flow_network, get_allocations

class StatusPedido(Enum):
    PENDENTE = 1
    ENTREGUE = 2

class Cliente:
    def __init__(self, id, nome, zona, latitude=None, longitude=None):
        if not zona.startswith("Zona ") or not zona.split()[-1].isdigit():
            raise ValueError("Zona inválida")
        self.id = id
        self.nome = nome
        self.zona = zona
        self.latitude = latitude
        self.longitude = longitude

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

# --- Funções ---

def gerar_matriz_distancias(pedidos, penalidade_zona=10):
    """
    Gera matriz de distâncias com penalidade para atravessar zonas distantes.
    Penalidade é adicionada à distância base (diferença entre zonas + 1)
    multiplicada pela distância entre as zonas.
    """
    G = nx.Graph()
    n = len(pedidos)
    matriz = [[0]*n for _ in range(n)]
    for i in range(n):
        for j in range(n):
            if i != j:
                zona_i = int(pedidos[i].cliente.zona.split()[-1])
                zona_j = int(pedidos[j].cliente.zona.split()[-1])
                # Distância base entre zonas
                base_distancia = abs(zona_i - zona_j) + 1
                # Penalidade extra para atravessar zonas diferentes
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

def criar_modelo_vrp(matriz_distancias, demandas, capacidades, num_veiculos, zonas_pedidos, veiculos, deposito=0, max_zonas_por_veiculo=2):
    data = {
        'distance_matrix': matriz_distancias,
        'demands': demandas,
        'vehicle_capacities': capacidades,
        'num_vehicles': num_veiculos,
        'depot': deposito
    }

    manager = pywrapcp.RoutingIndexManager(len(data['distance_matrix']),
                                           data['num_vehicles'], data['depot'])

    routing = pywrapcp.RoutingModel(manager)

    # Distância
    def distancia_callback(from_index, to_index):
        from_node = manager.IndexToNode(from_index)
        to_node = manager.IndexToNode(to_index)
        return data['distance_matrix'][from_node][to_node]

    transit_callback_index = routing.RegisterTransitCallback(distancia_callback)
    routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

    # Demandas
    def demanda_callback(from_index):
        from_node = manager.IndexToNode(from_index)
        return data['demands'][from_node]

    demanda_callback_index = routing.RegisterUnaryTransitCallback(demanda_callback)
    routing.AddDimensionWithVehicleCapacity(
        demanda_callback_index,
        0,
        data['vehicle_capacities'],
        True,
        'Capacity')

    # Limitar número máximo de entregas para 10 pedidos por veículo
    def entrega_callback(from_index):
        return 1

    entrega_callback_index = routing.RegisterUnaryTransitCallback(entrega_callback)
    routing.AddDimension(
        entrega_callback_index,
        0,
        10,
        True,
        'NumDeliveries')

    # Dimensão para contar zonas distintas visitadas
    # Atribuir para cada nó o índice da zona como "custo"
    zonas_indices = {zona: idx for idx, zona in enumerate(sorted(set(zonas_pedidos)))}

    def zona_callback(from_index):
        from_node = manager.IndexToNode(from_index)
        zona = zonas_pedidos[from_node]
        return zonas_indices[zona]

    zona_callback_index = routing.RegisterUnaryTransitCallback(zona_callback)

    routing.AddDimension(
        zona_callback_index,
        0,  # sem tolerância
        max(zonas_indices.values()),  # máximo índice de zona
        True,
        'ZonaDimension')

    zona_dimension = routing.GetDimensionOrDie('ZonaDimension')

    # Limitar zonas visitadas por veículo (simplificação: não permite mudar mais que max_zonas_por_veiculo vezes)
    for vehicle_id in range(num_veiculos):
        # Para restringir zonas visitadas, uma abordagem é limitar o valor da dimensão,
        # mas como a dimensão soma indices, precisamos controlar essa lógica com callbacks
        # Alternativa: penalizar trocar de zona várias vezes (mais complexo)
        # Aqui, vamos implementar apenas a penalização ao cruzar zonas fora do permitido
        if veiculos[vehicle_id].zonas_permitidas:
            allowed_zonas_indices = [zonas_indices[z] for z in veiculos[vehicle_id].zonas_permitidas if z in zonas_indices]

            # Criar uma callback para verificar se o nó está em zona permitida
            def zona_veiculo_callback(from_index, v_id=vehicle_id):
                from_node = manager.IndexToNode(from_index)
                zona = zonas_pedidos[from_node]
                if zonas_indices[zona] in allowed_zonas_indices:
                    return 0  # custo zero para zonas permitidas
                else:
                    return 1000000  # penalidade alta para zona proibida

            callback_index = routing.RegisterUnaryTransitCallback(zona_veiculo_callback)
            routing.SetFixedCostOfVehicle(0, vehicle_id)
            routing.AddDisjunction([manager.NodeToIndex(i) for i in range(len(zonas_pedidos))], 0)
            routing.SetArcCostEvaluatorOfVehicle(callback_index, vehicle_id)

    search_parameters = pywrapcp.DefaultRoutingSearchParameters()
    search_parameters.time_limit.seconds = 60
    search_parameters.first_solution_strategy = routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC

    solution = routing.SolveWithParameters(search_parameters)

    if solution:
        rotas = []
        for vehicle_id in range(num_veiculos):
            index = routing.Start(vehicle_id)
            rota = []
            while not routing.IsEnd(index):
                node_index = manager.IndexToNode(index)
                rota.append(node_index)
                index = solution.Value(routing.NextVar(index))
            rotas.append(rota)
        return rotas
    else:
        return None

def main():
    clientes = [
        Cliente(0, "Brian Evans", "Zona 4", -9.665, -35.735),
        Cliente(1, "Christine Adams", "Zona 2", -9.660, -35.730),
        Cliente(2, "Billy Bryan", "Zona 2", -9.658, -35.732),
        Cliente(3, "Harold Harper", "Zona 2", -9.659, -35.734),
        Cliente(4, "William Johnson", "Zona 2", -9.661, -35.733),
        Cliente(5, "Jennifer Robinson", "Zona 5", -9.670, -35.740),
        Cliente(6, "Daniel Barnes", "Zona 5", -9.672, -35.738),
        Cliente(7, "Vicki Arias", "Zona 4", -9.668, -35.737),
        Cliente(8, "Jason Garcia", "Zona 2", -9.664, -35.731),
        Cliente(9, "Mrs. Angela Spears", "Zona 3", -9.663, -35.729),
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
    ]

    veiculos = [
        Veiculo(0, "Carro pequeno", 200, True, zonas_permitidas=["Zona 4", "Zona 5"]),
        Veiculo(1, "Carro médio", 300, True, zonas_permitidas=["Zona 2", "Zona 3"]),
        Veiculo(2, "Carro grande", 400, True, zonas_permitidas=["Zona 2", "Zona 3", "Zona 4"]),
    ]

    # Resolução com fluxo
    flow_network = build_flow_network(pedidos, veiculos)
    max_flow = flow_network.multi_max_flow()

    # --- Prints para debug ---
    print("--- Clientes ---")
    for c in clientes:
        print(f"ID: {c.id}, Nome: {c.nome}, Zona: {c.zona}")
    print("\n--- Veículos ---")
    for v in veiculos:
        print(f"ID: {v.id}, Tipo: {v.tipo}, Capacidade: {v.capacidade}, Disponível: {v.disponivel}, Zonas: {v.zonas_permitidas}")
    print("\n--- Pedidos ---")
    for p in pedidos:
        print(f"ID: {p.id}, Cliente: {p.cliente.nome}, Volume: {p.volume}, Prioridade: {p.prioridade}, Status: {p.status.name}")

    # --- Gerar matriz de distâncias ---
    matriz = gerar_matriz_distancias(pedidos)
    print("\n--- Matriz de Distâncias (entre pedidos) ---")
    for linha in matriz:
        print(linha)

    # --- Demandas por pedido ---
    demandas = [p.volume for p in pedidos]
    print("\n--- Demandas por Pedido ---")
    for p in pedidos:
        print(f"Pedido {p.id} para {p.cliente.nome}: Volume {p.volume}")

    # --- Dados para o VRP ---
    capacidades = [v.capacidade for v in veiculos]
    num_veiculos = len(veiculos)
    zonas_pedidos = [p.cliente.zona for p in pedidos]

    print("\n--- Dados do VRP ---")
    print(f"Número de pedidos (nós): {len(pedidos)}")
    print(f"Demandas: {demandas}")
    print(f"Capacidades dos veículos: {capacidades}")
    print(f"Número de veículos: {num_veiculos}")
    print(f"Capacidade total dos veículos: {sum(capacidades)}")
    print(f"Soma das demandas dos pedidos: {sum(demandas)}")
    print(f"Zonas dos pedidos: {zonas_pedidos}")

    flow = build_flow_network(pedidos, veiculos)
    max_flow = flow.multi_max_flow()
    print(f"Pode atender {max_flow} unidades de volume")
    print(f"Demanda total: {sum(p.volume for p in pedidos)}")
    print(f"Capacidade total: {sum(v.capacidade for v in veiculos)}")

    # Mostrar alocações
    allocations = get_allocations(flow, len(pedidos), len(veiculos))
    for veic_id, vol in allocations.items():
        print(f"Veículo {veic_id} transportará {vol} unidades")
if __name__ == "__main__":
    # atualizar_coordenadas_no_json("./db_json/clientes.json")  # opcional
    main()