import json
from typing import List, Dict

def generate_route_geojson(pedidos: List[Dict], veiculos: List[Dict], rotas: List[List[int]]) -> Dict:
    """Gera GeoJSON para visualização em mapa"""
    features = []
    
    # Pontos de entrega
    for i, pedido in enumerate(pedidos):
        features.append({
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [pedido['longitude'], pedido['latitude']]  # Adicione coords reais
            },
            "properties": {
                "type": "pedido",
                "id": pedido['id'],
                "volume": pedido['volume'],
                "zona": pedido['zona']
            }
        })
    
    # Rotas dos veículos
    for j, rota in enumerate(rotas):
        if rota:
            coordinates = []
            for node_id in rota:
                # Adicione lógica para obter coordenadas reais
                coordinates.append([pedidos[node_id]['longitude'], pedidos[node_id]['latitude']])
            
            features.append({
                "type": "Feature",
                "geometry": {
                    "type": "LineString",
                    "coordinates": coordinates
                },
                "properties": {
                    "veiculo_id": veiculos[j]['id'],
                    "veiculo_tipo": veiculos[j]['tipo'],
                    "carga_total": sum(pedidos[node_id]['volume'] for node_id in rota)
                }
            })
    
    return {
        "type": "FeatureCollection",
        "features": features
    }