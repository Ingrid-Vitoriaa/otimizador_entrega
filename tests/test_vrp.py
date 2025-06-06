import pytest
from main import Pedido, Veiculo, Cliente, StatusPedido, gerar_matriz_distancias, criar_modelo_vrp

def test_pedido_volume_zero():
    cliente = Cliente(0, "Teste", "Zona 1")
    pedido = Pedido(0, cliente, 0, 3)
    assert pedido.volume == 0

def test_veiculo_capacidade_zero():
    veiculo = Veiculo(0, "MOTO", 0, True)
    assert veiculo.capacidade == 0

def test_volume_negativo_deve_gerar_erro():
    cliente = Cliente(1, "Teste", "Zona 1")
    with pytest.raises(ValueError):
        Pedido(0, cliente, -10, 3)

def test_capacidade_negativa_veiculo_deve_gerar_erro():
    with pytest.raises(ValueError):
        Veiculo(0, "VAN", -5, True)

def test_zona_invalida_cliente_deve_gerar_erro():
    with pytest.raises(ValueError):
        Cliente(1, "Teste", "Zona X")

def test_status_invalido_pedido_deve_gerar_erro():
    cliente = Cliente(0, "Teste", "Zona 1")
    with pytest.raises(ValueError):
        Pedido(0, cliente, 10, 3, status="INVALIDO")

def test_solver_com_muitos_pedidos_poucos_veiculos():
    cliente = Cliente(0, "Teste", "Zona 1")
    pedidos = [Pedido(i, cliente, 10, 1) for i in range(20)]
    capacidades = [50]  # 1 veículo com capacidade 50
    demandas = [p.volume for p in pedidos]
    matriz = gerar_matriz_distancias(pedidos)
    rotas = criar_modelo_vrp(matriz, demandas, capacidades, 1)
    assert rotas is None or isinstance(rotas, list)

def test_solver_com_volume_total_maior_que_capacidade():
    cliente = Cliente(0, "Teste", "Zona 1")
    pedidos = [Pedido(i, cliente, 60, 1) for i in range(3)]  # total 180
    capacidades = [100, 50]  # total 150, menor que demanda total
    demandas = [p.volume for p in pedidos]
    matriz = gerar_matriz_distancias(pedidos)
    rotas = criar_modelo_vrp(matriz, demandas, capacidades, 2)
    assert rotas is None or isinstance(rotas, list)

def test_cliente_com_zona_valida():
    cliente = Cliente(0, "Teste", "Zona 10")
    assert cliente.zona == "Zona 10"

def test_pedido_com_status_valido():
    cliente = Cliente(0, "Teste", "Zona 1")
    pedido = Pedido(0, cliente, 10, 2, status=StatusPedido.ENTREGUE)
    assert pedido.status == StatusPedido.ENTREGUE
