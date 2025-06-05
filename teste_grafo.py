import osmnx as ox
from grafos.carregador import carregar_rede
from grafos.validador import validar_rede
from grafos.estrutura_grafo import construir_grafo_integrado

print("📦 Carregando dados da rede...")
nodos, rotas = carregar_rede("exemplo_rede.json")

print("🔍 Validando integridade da rede...")
erros = validar_rede(nodos, rotas)
if erros:
    print("🚫 Erros encontrados:")
    for erro in erros:
        print(" -", erro)
    exit(1)
else:
    print("✅ Rede válida!")

print("📍 Buscando rede OSM de ruas de Maceió...")
G_osm = ox.graph_from_place('Maceió, Brazil', network_type='drive')

print("🧠 Construindo grafo integrado...")
G = construir_grafo_integrado(nodos, rotas, G_osm)

print(f"📊 Grafo com {len(G.nodes)} nós e {len(G.edges)} arestas criado.")

print("\n🚚 Arestas conectadas ao nodo logístico D1:")
for u, v, data in G.edges(data=True):
    if u == "D1" or v == "D1":
        print(f"  {u} -> {v}, capacidade={data.get('capacidade', 'N/A')}")
