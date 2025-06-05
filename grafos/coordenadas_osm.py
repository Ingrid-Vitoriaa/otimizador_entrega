# grafos/coordenadas_osm.py

import osmnx as ox
import json
from grafos.carregador import carregar_rede

def atualizar_coordenadas_no_json(caminho_json):
    nodos, rotas = carregar_rede(caminho_json)

    print("📍 Buscando rede de ruas de Maceió, Brazil via OSMnx...")
    G = ox.graph_from_place('Maceió, Brazil', network_type='drive')

    # Associar cada nodo logístico ao nó OSM mais próximo e atualizar coords e id_nodo_osm
    for nodo in nodos:
        if nodo.latitude is None or nodo.longitude is None:
            print(f"⚠️ Nodo {nodo.id} não possui coordenadas, pulando associação.")
            continue
        
        # Encontrar o nó mais próximo na rede OSM
        nodo_nearest = ox.distance.nearest_nodes(G, nodo.longitude, nodo.latitude)
        
        # Salvar o ID do nó OSM no nodo
        nodo.id_nodo_osm = nodo_nearest
        
        # Atualizar latitude e longitude do nodo para as coordenadas reais do nó OSM (precisão)
        nodo.latitude = G.nodes[nodo_nearest]['y']
        nodo.longitude = G.nodes[nodo_nearest]['x']

        print(f"🔗 Nodo {nodo.id} associado ao nó OSM {nodo_nearest} "
              f"({nodo.latitude}, {nodo.longitude})")

    # Atualizar JSON incluindo id_nodo_osm
    dados_atualizados = {
        "nodos": [
            {
                "id": nodo.id,
                "tipo": getattr(nodo, 'tipo', None),  # Em caso de instâncias sem 'tipo'
                "nome": nodo.nome,
                "latitude": nodo.latitude,
                "longitude": nodo.longitude,
                "id_nodo_osm": getattr(nodo, 'id_nodo_osm', None)  # Campo novo
            }
            for nodo in nodos
        ],
        "rotas": [
            {
                "origem": rota.origem,
                "destino": rota.destino,
                "capacidade": rota.capacidade
            }
            for rota in rotas
        ]
    }

   
