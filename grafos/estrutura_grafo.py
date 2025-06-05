import networkx as nx

def construir_grafo_integrado(nodos, rotas, grafo_osm):
    G = nx.DiGraph()
    
    # Adiciona nodos logísticos com id_nodo_osm
    for nodo in nodos:
        G.add_node(nodo.id,
                   tipo=getattr(nodo, 'tipo', None),
                   nome=nodo.nome,
                   latitude=nodo.latitude,
                   longitude=nodo.longitude,
                   id_nodo_osm=getattr(nodo, 'id_nodo_osm', None))
    
    # Adiciona rotas logísticas
    for rota in rotas:
        G.add_edge(rota.origem, rota.destino, capacidade=rota.capacidade)
    
    # Adiciona nós e arestas do grafo OSM com prefixo 'osm_'
    for node_id, data in grafo_osm.nodes(data=True):
        G.add_node(f"osm_{node_id}", **data)
    
    for u, v, data in grafo_osm.edges(data=True):
        G.add_edge(f"osm_{u}", f"osm_{v}", **data)
    
    # Conecta nodos logísticos ao grafo OSM
    for nodo in nodos:
        if hasattr(nodo, 'id_nodo_osm') and nodo.id_nodo_osm is not None:
            osm_node = f"osm_{nodo.id_nodo_osm}"
            G.add_edge(nodo.id, osm_node, capacidade=float('inf'))
            G.add_edge(osm_node, nodo.id, capacidade=float('inf'))
    
    return G
