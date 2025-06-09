import json
from models.cliente import Cliente
from models.veiculo import Veiculo
from models.pedido import Pedido
from models.enums import TipoVeiculo, StatusPedido

def carregar_clientes_de_json(caminho="clientes.json"):
    with open(caminho, "r") as f:
        dados = json.load(f)
        clientes = []
        for c in dados:
            cliente = Cliente(
                id=c["id"],
                nome=c["nome"],
                zona=c["zona"],
                latitude=c.get("latitude"),
                longitude=c.get("longitude")
            )
            clientes.append(cliente)
        return clientes


def salvar_clientes(clientes, caminho="clientes.json"):
    with open(caminho, "w") as f:
        json.dump([cliente.__dict__ for cliente in clientes], f, indent=4)

def carregar_clientes(caminho="clientes.json"):
    with open(caminho, "r") as f:
        dados = json.load(f)
        return [Cliente(**cliente) for cliente in dados]

def salvar_veiculos(veiculos, caminho="veiculos.json"):
    with open(caminho, "w") as f:
        json.dump([
            {
                "id": veiculo.id,
                "tipo": veiculo.tipo.value,  # salva o Enum como string
                "capacidade": veiculo.capacidade,
                "disponivel": veiculo.disponivel
            }
            for veiculo in veiculos
        ], f, indent=4)

def carregar_veiculos(caminho="veiculos.json"):
    with open(caminho, "r") as f:
        dados = json.load(f)
        return [
            Veiculo(
                v["id"],
                TipoVeiculo[v["tipo"]],  # Corrige para usar a chave do enum (string) no acesso
                v["capacidade"],
                v.get("disponivel", True)  # Usa True como padrão se não existir a chave
            )
            for v in dados
        ]


def salvar_pedidos(pedidos, caminho="pedidos.json"):
    with open(caminho, "w") as f:
        json.dump([{
            "id": pedido.id,
            "cliente": pedido.cliente.__dict__,
            "volume": pedido.volume,
            "prioridade": pedido.prioridade,
            "status": pedido.status.name
        } for pedido in pedidos], f, indent=4)

def carregar_pedidos(caminho="pedidos.json"):
    with open(caminho, "r") as f:
        dados = json.load(f)
        pedidos = []
        for p in dados:
            cliente = Cliente(**p["cliente"])
            status = StatusPedido[p["status"]]
            pedido = Pedido(p["id"], cliente, p["volume"], p["prioridade"])
            pedido.status = status
            pedidos.append(pedido)
        return pedidos
