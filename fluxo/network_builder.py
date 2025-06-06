import datetime
from .ford_fulkerson import ExtendedMaxFlow

def build_flow_network(pedidos, veiculos):
    # Nós: 0 a n-1 são pedidos, n a n+m-1 são veículos
    n = len(pedidos)
    m = len(veiculos)
    flow = ExtendedMaxFlow(n + m)
    
    # Conexões pedidos-veículos
    for i, pedido in enumerate(pedidos):
        for j, veiculo in enumerate(veiculos):
            if (not veiculo.zonas_permitidas or 
                pedido.cliente.zona in veiculo.zonas_permitidas):
                flow.add_edge(i, n + j, pedido.volume)
    
    # Múltiplas fontes (pedidos)
    flow.add_multi_sources(
        sources=range(n),
        caps=[p.volume for p in pedidos]
    )
    
    # Múltiplos destinos (veículos)
    flow.add_multi_sinks(
        sinks=[n + j for j in range(m)],
        caps=[v.capacidade for v in veiculos]
    )
    
    return flow

def get_allocations(flow_network, num_pedidos, num_veiculos):
    allocations = {}
    for j in range(num_veiculos):
        veic_node = num_pedidos + j
        for edge in flow_network.graph[veic_node]:
            if edge.to != flow_network.super_sink:
                continue
            if edge.capacity < edge.original_capacity:
                allocations[j] = edge.original_capacity - edge.capacity
    return allocations

def get_network_visualization_data(flow_network, pedidos, veiculos):
    """Retorna dados estruturados para visualização"""
    nodes = []
    edges = []
    
    # Nós dos pedidos
    for i, pedido in enumerate(pedidos):
        nodes.append({
            'id': f'pedido_{i}',
            'type': 'pedido',
            'volume': pedido.volume,
            'zona': pedido.cliente.zona,
            'label': f'Pedido {i}'
        })
    
    # Nós dos veículos
    for j, veiculo in enumerate(veiculos):
        nodes.append({
            'id': f'veiculo_{j}',
            'type': 'veiculo',
            'capacidade': veiculo.capacidade,
            'tipo': veiculo.tipo,
            'label': f'Veículo {j}'
        })
    
    # Arestas (conexões)
    for i in range(len(pedidos)):
        for edge in flow_network.graph[i]:
            if edge.to >= len(pedidos):  # Conexões para veículos
                edges.append({
                    'from': f'pedido_{i}',
                    'to': f'veiculo_{edge.to - len(pedidos)}',
                    'flow': edge.original_capacity - edge.capacity,
                    'capacity': edge.original_capacity
                })
    
    return {
        'nodes': nodes,
        'edges': edges,
        'metadata': {
            'total_flow': flow_network.multi_max_flow(),
            'timestamp': datetime.now().isoformat()
        }
    }