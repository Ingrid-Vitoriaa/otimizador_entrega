import osmnx as ox
import json
import matplotlib.pyplot as plt
from grafos.carregador import carregar_rede

def atualizar_coordenadas_no_json(caminho_json):
    """
    Atualiza os nodos de um JSON com coordenadas reais da rede OSM de Maceió,
    associando cada ponto ao nó OSM mais próximo.
    """
    nodos, rotas = carregar_rede(caminho_json)

    print("📍 Buscando rede de ruas de Maceió, Brazil via OSMnx...")
    G = ox.graph_from_place('Maceió, Brazil', network_type='drive')

    for nodo in nodos:
        if nodo.latitude is None or nodo.longitude is None:
            print(f"⚠️ Nodo {nodo.id} não possui coordenadas, pulando associação.")
            continue

        nodo_nearest = ox.distance.nearest_nodes(G, nodo.longitude, nodo.latitude)
        nodo.id_nodo_osm = nodo_nearest
        nodo.latitude = G.nodes[nodo_nearest]['y']
        nodo.longitude = G.nodes[nodo_nearest]['x']
        print(f"🔗 Nodo {nodo.id} associado ao nó OSM {nodo_nearest} "
              f"({nodo.latitude}, {nodo.longitude})")

    dados_atualizados = {
        "nodos": [
            {
                "id": nodo.id,
                "tipo": getattr(nodo, 'tipo', None),
                "nome": nodo.nome,
                "latitude": nodo.latitude,
                "longitude": nodo.longitude,
                "id_nodo_osm": getattr(nodo, 'id_nodo_osm', None)
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

    with open(caminho_json, 'w', encoding='utf-8') as f:
        json.dump(dados_atualizados, f, indent=4, ensure_ascii=False)

    print("✅ Coordenadas atualizadas e salvas no JSON com sucesso!")

def visualizar_nodos_com_osm(caminho_json):
    """
    Plota os nodos presentes no JSON em cima da rede de ruas de Maceió via OSMnx.
    Útil para validar se os nodos foram corretamente associados a pontos reais.
    """
    print("🗺️ Carregando rede de Maceió e nodos do JSON para visualização...")
    G = ox.graph_from_place('Maceió, Brazil', network_type='drive')
    
    with open(caminho_json, encoding='utf-8') as f:
        dados = json.load(f)

    nodos_osm_ids = [n['id_nodo_osm'] for n in dados['nodos'] if n.get('id_nodo_osm')]

    fig, ax = ox.plot_graph(G, show=False, close=False, bgcolor='white')
    xs = [G.nodes[n]['x'] for n in nodos_osm_ids if n in G.nodes]
    ys = [G.nodes[n]['y'] for n in nodos_osm_ids if n in G.nodes]
    ax.scatter(xs, ys, c='red', s=40, zorder=5, label='Nodos do JSON')
    ax.legend()
    plt.title("📌 Validação visual dos nodos no mapa de Maceió")
    plt.show()
