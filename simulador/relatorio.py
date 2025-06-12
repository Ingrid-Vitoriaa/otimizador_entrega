def gerar_relatorio(pedidos, veiculos, alocacoes, demandas_simuladas):
    print("\n=== Relatório de Alocação de Pedidos ===\n")
    
    # Se alocacoes for None ou vazio, tratamos como sem alocações
    if not alocacoes:
        for v_id, veiculo in enumerate(veiculos):
            print(f"Veículo {v_id} ({veiculo.tipo}):")
            print("  - Nenhum pedido alocado\n")
    else:
        for v_id, pedidos_ids in enumerate(alocacoes):
            print(f"Veículo {v_id} ({veiculos[v_id].tipo}):")
            if pedidos_ids:
                for p_id in pedidos_ids:
                    pedido = pedidos[p_id]
                    demanda = demandas_simuladas[p_id]
                    print(f"  - Pedido {pedido.id} (Zona {pedido.cliente.zona}, Demanda {demanda}, Prioridade {pedido.prioridade})")
            else:
                print("  - Nenhum pedido alocado")
            print()

    total_demandas = sum(demandas_simuladas)
    total_capacidades = sum([v.capacidade for v in veiculos])

    # Calcula total de demandas alocadas
    total_demandas_alocadas = 0
    if alocacoes:
        for pedidos_ids in alocacoes:
            for p_id in pedidos_ids:
                total_demandas_alocadas += demandas_simuladas[p_id]

    capacidade_ociosa = total_capacidades - total_demandas_alocadas

    print(f"Demanda total simulada: {total_demandas}")
    print(f"Capacidade total dos veículos: {total_capacidades}")
    print(f"Demanda alocada total: {total_demandas_alocadas}")
    print(f"Capacidade ociosa total: {capacidade_ociosa}")
    print("=== Fim do Relatório ===\n")
