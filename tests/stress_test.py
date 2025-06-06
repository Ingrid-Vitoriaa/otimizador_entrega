import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))


import time
import random
from fluxo.network_builder import build_flow_network
from models.pedido import Pedido
from models.veiculo import Veiculo

def stress_test():
    print("Iniciando testes de stress...\n")
    
    for test_num in range(3):  # 3 testes de exemplo
        n = random.randint(10, 20)  # Comece com valores pequenos para teste
        m = random.randint(3, 5)
        
        print(f"\n=== TESTE {test_num+1} ===")
        print(f"Configuração: {n} pedidos, {m} veículos")
        
        # Gerar dados de teste
        pedidos = [Pedido(i, None, random.randint(1, 20), 1) for i in range(n)]
        veiculos = [Veiculo(j, "VAN", random.randint(30, 50), True, None) for j in range(m)]
        
        # Construir rede
        start_time = time.time()
        flow_network = build_flow_network(pedidos, veiculos)
        max_flow = flow_network.multi_max_flow()
        elapsed = time.time() - start_time
        
        # Resultados
        print(f"\nResultados:")
        print(f"Tempo de execução: {elapsed:.4f} segundos")
        print(f"Fluxo máximo calculado: {max_flow}")
        print(f"Demanda total: {sum(p.volume for p in pedidos)}")
        print(f"Capacidade total: {sum(v.capacidade for v in veiculos)}")
        print("="*30)

if __name__ == "__main__":
    stress_test()  # Esta linha é crucial para executar o teste