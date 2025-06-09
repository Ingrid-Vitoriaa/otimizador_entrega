from enum import Enum
from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp
import networkx as nx
import osmnx as ox
from grafos.coordenadas_osm import atualizar_coordenadas_no_json

# --- Enums ---
class StatusPedido(Enum):
    PENDENTE = 1
    ENTREGUE = 2

# --- Classes ---
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
        if not isinstance(status, StatusPedido):
            raise ValueError("Status inválido")
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
def gerar_matriz_distancias_osm(pedidos):
    print("📍 Baixando rede de ruas de Maceió via OSMnx para cálculo de distâncias reais...")
    G = ox.graph_from_place('Maceió, Brazil', network_type='drive')

    # Mapear pedidos aos nós OSM
    nodos_osm = []
    for p in pedidos:
        if p.cliente.latitude is None or p.cliente.longitude is None:
            raise ValueError(f"Cliente {p.cliente.nome} sem coordenadas definidas.")
        node = ox.distance.nearest_nodes(G, p.cliente.longitude, p.cliente.latitude)
        nodos_osm.append(node)

    n = len(pedidos)
    matriz = [[0]*n for _ in range(n)]
    for i in range(n):
        for j in range(n):
            if i != j:
                try:
                    dist = nx.shortest_path_length(G, nodos_osm[i], nodos_osm[j], weight='length')
                    matriz[i][j] = int(dist)
                except nx.NetworkXNoPath:
                    matriz[i][j] = 999999
    print("✅ Matriz de distâncias reais gerada.")
    return matriz

def criar_modelo_vrp(matriz_distancias, demandas, capacidades, num_veiculos, zonas_pedidos, veiculos, deposito=0):
    data = {
        'distance_matrix': matriz_distancias,
        'demands': demandas,
        'vehicle_capacities': capacidades,
        'num_vehicles': num_veiculos,
        'depot': deposito
    }

    manager = pywrapcp.RoutingIndexManager(len(data['distance_matrix']), num_veiculos, data['depot'])
    routing = pywrapcp.RoutingModel(manager)

    def distancia_callback(from_index, to_index):
        from_node = manager.IndexToNode(from_index)
        to_node = manager.IndexToNode(to_index)
        return data['distance_matrix'][from_node][to_node]

    transit_callback_index = routing.RegisterTransitCallback(distancia_callback)
    routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

    def demanda_callback(from_index):
        from_node = manager.IndexToNode(from_index)
        return data['demands'][from_node]

    demanda_callback_index = routing.RegisterUnaryTransitCallback(demanda_callback)
    routing.AddDimensionWithVehicleCapacity(demanda_callback_index, 0, data['vehicle_capacities'], True, 'Capacity')

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
    # --- Clientes ---
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

    # --- Pedidos ---
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

    # --- Veículos ---
    veiculos = [
        Veiculo(0, "Carro pequeno", 200, True, zonas_permitidas=["Zona 4", "Zona 5"]),
        Veiculo(1, "Carro médio", 300, True, zonas_permitidas=["Zona 2", "Zona 3"]),
        Veiculo(2, "Carro grande", 400, True, zonas_permitidas=["Zona 2", "Zona 3", "Zona 4"]),
    ]

    # --- Dados para o VRP ---
    demandas = [p.volume for p in pedidos]
    capacidades = [v.capacidade for v in veiculos]
    zonas_pedidos = [p.cliente.zona for p in pedidos]

    # --- Matriz de distâncias ---
    matriz_distancias = gerar_matriz_distancias_osm(pedidos)

    # --- Resolver o problema ---
    rotas = criar_modelo_vrp(matriz_distancias, demandas, capacidades, len(veiculos), zonas_pedidos, veiculos)

    # --- Exibir solução ---
    if rotas:
        for v, rota in enumerate(rotas):
            print(f"Veículo {v} ({veiculos[v].tipo}): Rota = {rota}")
    else:
        print("Não foi possível encontrar uma solução.")

if __name__ == "__main__":
    # atualizar_coordenadas_no_json("clientes.json")  # opcional
    main()
