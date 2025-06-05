import networkx as nx
from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp

def gerar_matriz_distancias(grafo, nodos):
    matriz = []
    for origem in nodos:
        linha = []
        for destino in nodos:
            if origem == destino:
                linha.append(0)
            else:
                distancia = nx.shortest_path_length(grafo, origem, destino, weight='weight')
                linha.append(distancia)
        matriz.append(linha)
    return matriz

def criar_modelo_vrp(matriz_distancias, demandas, capacidades, num_veiculos, deposito):
    data = {}
    data['distance_matrix'] = matriz_distancias
    data['demands'] = demandas
    data['vehicle_capacities'] = capacidades
    data['num_vehicles'] = num_veiculos
    data['depot'] = deposito

    manager = pywrapcp.RoutingIndexManager(len(data['distance_matrix']),
                                           data['num_vehicles'], data['depot'])
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
    routing.AddDimensionWithVehicleCapacity(
        demanda_callback_index,
        0,
        data['vehicle_capacities'],
        True,
        'Capacity')

    search_parameters = pywrapcp.DefaultRoutingSearchParameters()
    search_parameters.first_solution_strategy = (
        routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC)

    solution = routing.SolveWithParameters(search_parameters)

    if solution:
        rotas = []
        for vehicle_id in range(data['num_vehicles']):
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

if __name__ == "__main__":
    # Crie seu grafo aqui ou importe de onde você tem ele
    G = nx.Graph()
    # Exemplo básico de grafo (substitua pelo seu grafo real)
    nodos = ['deposito', 'cliente1', 'cliente2', 'cliente3']
    G.add_edge('deposito', 'cliente1', weight=10)
    G.add_edge('deposito', 'cliente2', weight=20)
    G.add_edge('cliente1', 'cliente3', weight=15)
    G.add_edge('cliente2', 'cliente3', weight=30)

    matriz = gerar_matriz_distancias(G, nodos)
    print("Matriz de distâncias:")
    for linha in matriz:
        print(linha)

    demandas = [0, 10, 15, 10]  # 0 para depósito, demandas fictícias dos clientes
    capacidades = [25, 25]  # Capacidades dos veículos
    num_veiculos = len(capacidades)
    deposito = 0  # índice do depósito na matriz

    rotas = criar_modelo_vrp(matriz, demandas, capacidades, num_veiculos, deposito)

    if rotas:
        for i, rota in enumerate(rotas):
            print(f"Rota do veículo {i+1}: {[nodos[i] for i in rota]}")
    else:
        print("Nenhuma solução encontrada")
