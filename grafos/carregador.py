# grafos/carregador.py

import json
from grafos.entidades import Deposito, Hub, ZonaEntrega, Rota

def carregar_rede(caminho_arquivo):
    with open(caminho_arquivo, 'r', encoding='utf-8') as f:
        dados = json.load(f)

    nodos = []
    for n in dados.get('nodos', []):
        tipo = n.get('tipo')
        kwargs = {
            'id': n.get('id'),
            'nome': n.get('nome'),
            'latitude': n.get('latitude'),
            'longitude': n.get('longitude')
        }
        if tipo == 'deposito':
            nodos.append(Deposito(**kwargs))
        elif tipo == 'hub':
            nodos.append(Hub(**kwargs))
        elif tipo == 'zona':
            nodos.append(ZonaEntrega(**kwargs))

    rotas = [Rota(**r) for r in dados.get('rotas', [])]
    return nodos, rotas
