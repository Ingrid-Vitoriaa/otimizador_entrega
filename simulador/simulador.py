from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp

def simular_bloqueio_rotas(matriz_distancias, rotas_bloqueadas):
    """
    Recebe matriz de distâncias e uma lista de pares (i,j) de rotas bloqueadas.
    Para rotas bloqueadas, coloca um custo muito alto para simular bloqueio.
    """
    penalidade = 1000000  # Valor muito alto para simular o bloqueio
    n = len(matriz_distancias)
    nova_matriz = [row[:] for row in matriz_distancias]  # Cria uma cópia da matriz original

    for i, j in rotas_bloqueadas:
        if 0 <= i < n and 0 <= j < n:
            nova_matriz[i][j] = penalidade
            nova_matriz[j][i] = penalidade  # Matriz simétrica
    return nova_matriz

def simular_aumento_demanda(pedidos, aumento_por_zona):
    """
    Retorna uma nova lista de volumes de pedidos, ajustando os volumes
    de acordo com o aumento percentual por zona.

    - pedidos: lista de objetos Pedido
    - aumento_por_zona: dict {zona: fator_de_aumento}
    """
    novas_demandas = []
    for pedido in pedidos:
        zona = pedido.cliente.zona
        fator = aumento_por_zona.get(zona, 1.0)  # Se a zona não tiver aumento, usa 1.0
        nova_demanda = int(round(pedido.volume * fator))
        novas_demandas.append(nova_demanda)
    return novas_demandas

from ortools.constraint_solver import pywrapcp, routing_enums_pb2

def criar_modelo_vrp(matriz, demandas, capacidades, num_veiculos, zonas_pedidos, veiculos):
    num_pedidos = len(demandas)
    depot = 0  # Ponto de partida fictício

    # Adiciona o depósito como primeiro nó
    nova_matriz = [[0] + row for row in matriz]
    nova_matriz.insert(0, [0] * (num_pedidos + 1))

    nova_demanda = [0] + demandas  # 0 para o depósito

    # Cria o gerenciador de index
    manager = pywrapcp.RoutingIndexManager(len(nova_matriz), num_veiculos, depot)

    # Cria o modelo de roteamento
    routing = pywrapcp.RoutingModel(manager)

    # Função de distância
    def distance_callback(from_index, to_index):
        from_node = manager.IndexToNode(from_index)
        to_node = manager.IndexToNode(to_index)
        return nova_matriz[from_node][to_node]

    transit_callback_index = routing.RegisterTransitCallback(distance_callback)
    routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

    # Adiciona a restrição de capacidade
    def demand_callback(from_index):
        from_node = manager.IndexToNode(from_index)
        return nova_demanda[from_node]

    demand_callback_index = routing.RegisterUnaryTransitCallback(demand_callback)
    routing.AddDimensionWithVehicleCapacity(
        demand_callback_index,
        0,  # sem capacidade extra
        capacidades,
        True,
        'Capacity'
    )

    # Restrição: zonas permitidas por veículo
    for pedido_index in range(1, num_pedidos + 1):
        zona_pedido = zonas_pedidos[pedido_index - 1]
        for veiculo_id, veiculo in enumerate(veiculos):
            if veiculo.zonas_permitidas and zona_pedido not in veiculo.zonas_permitidas:
                index = manager.NodeToIndex(pedido_index)
                routing.VehicleVar(index).RemoveValue(veiculo_id)

    # Configura parâmetros do solver
    search_parameters = pywrapcp.DefaultRoutingSearchParameters()
    search_parameters.first_solution_strategy = routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
    search_parameters.local_search_metaheuristic = routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH
    search_parameters.time_limit.seconds = 10

    # Resolve o problema
    solution = routing.SolveWithParameters(search_parameters)

    if solution:
        rotas = []
        for veiculo_id in range(num_veiculos):
            index = routing.Start(veiculo_id)
            rota = []
            while not routing.IsEnd(index):
                node = manager.IndexToNode(index)
                if node != depot:
                    rota.append(node - 1)  # remove o deslocamento do depósito
                index = solution.Value(routing.NextVar(index))
            rotas.append(rota)
        return rotas
    else:
        return None
