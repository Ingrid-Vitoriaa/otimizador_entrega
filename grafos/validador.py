def validar_rede(nodos, rotas):
    erros = []

    ids_nodos = set()
    for nodo in nodos:
        if nodo.id in ids_nodos:
            erros.append(f"ID duplicado de nodo: {nodo.id}")
        else:
            ids_nodos.add(nodo.id)
        
        if not nodo.tipo or nodo.tipo not in ['deposito', 'hub', 'zona']:
            erros.append(f"Tipo inválido no nodo {nodo.id}: {nodo.tipo}")
    
    for rota in rotas:
        if rota.origem not in ids_nodos:
            erros.append(f"Rota com origem inexistente: {rota.origem}")
        if rota.destino not in ids_nodos:
            erros.append(f"Rota com destino inexistente: {rota.destino}")
        if rota.capacidade <= 0:
            erros.append(f"Rota com capacidade inválida: {rota}")

    return erros
