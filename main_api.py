# main_api.py

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Dict, Any
from enum import Enum as PyEnum

# Importando suas dependências existentes
from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp
import networkx as nx
import osmnx as ox

# Importar o módulo json para ler arquivos JSON
import json

#  Importando suas classes originais e enums da pasta 'models'
from models.enums import (
    StatusPedido as OriginalStatusPedido,
    TipoVeiculo as OriginalTipoVeiculo,
)
from models.cliente import Cliente as OriginalCliente
from models.pedido import Pedido as OriginalPedido
from models.veiculo import Veiculo as OriginalVeiculo


#  Placeholder para módulos 'fluxo'
class FlowNetwork:
    def __init__(self, pedidos, veiculos):
        self.pedidos = pedidos
        self.veiculos = veiculos
        self._max_flow = 0
        self._allocations = {}

    def multi_max_flow(self):
        total_demand = sum(p.volume for p in self.pedidos)
        total_capacity = sum(v.capacidade for v in self.veiculos)
        self._max_flow = min(total_demand, total_capacity) if total_demand > 0 else 0
        return self._max_flow


def build_flow_network(pedidos: List[OriginalPedido], veiculos: List[OriginalVeiculo]):
    return FlowNetwork(pedidos, veiculos)


def get_allocations(
    flow_network: FlowNetwork, num_pedidos: int, num_veiculos: int
) -> Dict[int, int]:
    allocations = {}
    remaining_demand = sum(p.volume for p in flow_network.pedidos)

    for v in flow_network.veiculos:
        if remaining_demand > 0:
            allocated_for_vehicle = min(v.capacidade, remaining_demand)
            allocations[v.id] = allocated_for_vehicle
            remaining_demand -= allocated_for_vehicle
        else:
            allocations[v.id] = 0
    return allocations


#  Fim dos placeholders


#  Pydantic Models para API (refletindo suas classes atualizadas)
class StatusPedidoAPI(PyEnum):
    PENDENTE = "PENDENTE"
    ENTREGUE = "ENTREGUE"
    CANCELADO = "CANCELADO"
    EM_TRANSPORTE = "EM_TRANSPORTE"


class TipoVeiculoAPI(PyEnum):
    MOTO = "MOTO"
    VAN = "VAN"
    CARRO = "CARRO"
    CARRO_MEDIO = "CARRO_MEDIO"
    CAMINHAO = "CAMINHAO"


class ClienteModel(BaseModel):
    id: int
    nome: str
    zona: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    endereco: Optional[str] = None

    @field_validator("zona")
    @classmethod
    def validate_zona(cls, v: str) -> str:
        if not v.startswith("Zona ") or not v.split()[-1].isdigit():
            raise ValueError("Zona inválida")
        return v


class PedidoModel(BaseModel):
    id: int
    cliente_id: int
    volume: float
    prioridade: int
    status: StatusPedidoAPI = StatusPedidoAPI.PENDENTE

    @field_validator("volume")
    @classmethod
    def validate_volume(cls, v: float) -> float:
        if v < 0:
            raise ValueError("Volume não pode ser negativo")
        return v


class VeiculoModel(BaseModel):
    id: int
    tipo: TipoVeiculoAPI
    capacidade: int
    disponivel: bool
    zonas_permitidas: Optional[List[str]] = None

    @field_validator("capacidade")
    @classmethod
    def validate_capacidade(cls, v: int) -> int:
        if v < 0:
            raise ValueError("Capacidade não pode ser negativa")
        return v


class OptimizationRequest(BaseModel):
    clientes: List[ClienteModel]
    pedidos: List[PedidoModel]
    veiculos: List[VeiculoModel]


class RouteSegment(BaseModel):
    pedido_id: int
    cliente_id: int
    cliente_nome: str
    latitude: float
    longitude: float
    volume: float
    endereco: Optional[str] = None


class VehicleRoute(BaseModel):
    vehicle_id: int
    vehicle_type: str
    route: List[RouteSegment]
    total_volume: float
    total_distance: Optional[int] = None


class OptimizationResponse(BaseModel):
    message: str
    routes: Optional[List[VehicleRoute]] = None
    allocations: Optional[Dict[int, float]] = None
    max_flow: Optional[float] = None
    total_demand: Optional[float] = None
    total_capacity: Optional[float] = None


#  Funções do seu código original (adaptadas para API)


def gerar_matriz_distancias_osm(
    pedidos_originais: List[OriginalPedido],
    clientes_map_pydantic: Dict[int, ClienteModel],
):
    print(
        "📍 Baixando rede de ruas de Maceió via OSMnx para cálculo de distâncias reais..."
    )
    try:
        G = ox.graph_from_place("Maceió, Brazil", network_type="drive")
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Falha ao baixar rede de ruas com OSMnx para Maceió: {e}",
        )

    nodos_osm = []
    for p_orig in pedidos_originais:
        cliente_model = clientes_map_pydantic.get(p_orig.cliente.id)
        if (
            not cliente_model
            or cliente_model.latitude is None
            or cliente_model.longitude is None
        ):
            raise HTTPException(
                status_code=400,
                detail=f"Cliente com ID {p_orig.cliente.id} (Nome: {p_orig.cliente.nome}) sem coordenadas válidas. Lat/Lon: {cliente_model.latitude}, {cliente_model.longitude}",
            )
        try:
            node = ox.distance.nearest_nodes(
                G, cliente_model.longitude, cliente_model.latitude
            )
            nodos_osm.append(node)
        except Exception as node_error:
            raise HTTPException(
                status_code=400,
                detail=f"Não foi possível encontrar um nó OSM próximo para o cliente {cliente_model.nome} (ID: {cliente_model.id}) nas coordenadas ({cliente_model.latitude}, {cliente_model.longitude}). Erro: {node_error}",
            )

    n = len(pedidos_originais)
    matriz = [[0] * n for _ in range(n)]
    for i in range(n):
        for j in range(n):
            if i != j:
                try:
                    dist = nx.shortest_path_length(
                        G, nodos_osm[i], nodos_osm[j], weight="length"
                    )
                    matriz[i][j] = int(dist)
                except nx.NetworkXNoPath:
                    matriz[i][j] = 999999999
                except Exception as path_error:
                    raise HTTPException(
                        status_code=500,
                        detail=f"Erro ao calcular caminho entre cliente {pedidos_originais[i].cliente.nome} e {pedidos_originais[j].cliente.nome}: {path_error}",
                    )
    print("✅ Matriz de distâncias reais gerada.")
    return matriz, G, nodos_osm


def criar_modelo_vrp(
    matriz_distancias, demandas, capacidades, num_veiculos, deposito=0
):
    data = {
        "distance_matrix": matriz_distancias,
        "demands": [int(d) for d in demandas],
        "vehicle_capacities": capacidades,
        "num_vehicles": num_veiculos,
        "depot": deposito,
    }
    manager = pywrapcp.RoutingIndexManager(
        len(data["distance_matrix"]), num_veiculos, data["depot"]
    )
    routing = pywrapcp.RoutingModel(manager)
    def distance_callback(from_index, to_index):
        from_node = manager.IndexToNode(from_index)
        to_node = manager.IndexToNode(to_index)
        return data["distance_matrix"][from_node][to_node]
    transit_callback_index = routing.RegisterTransitCallback(distance_callback)
    routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)
    def demand_callback(from_index):
        from_node = manager.IndexToNode(from_index)
        return data["demands"][from_node]
    demand_callback_index = routing.RegisterUnaryTransitCallback(demand_callback)
    routing.AddDimensionWithVehicleCapacity(
        demand_callback_index, 0, data["vehicle_capacities"], True, "Capacity"
    )
    search_parameters = pywrapcp.DefaultRoutingSearchParameters()
    search_parameters.time_limit.seconds = 30
    search_parameters.first_solution_strategy = (
        routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
    )
    search_parameters.local_search_metaheuristic = (
        routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH
    )
    solution = routing.SolveWithParameters(search_parameters)
    if solution:
        routes_data = []
        for vehicle_id in range(num_veiculos):
            index = routing.Start(vehicle_id)
            route_indices_for_vehicle = []
            total_distance_for_vehicle = 0
            while not routing.IsEnd(index):
                node_index = manager.IndexToNode(index)
                route_indices_for_vehicle.append(node_index)
                previous_index = index
                index = solution.Value(routing.NextVar(index))
                total_distance_for_vehicle += routing.GetArcCostForVehicle(
                    previous_index, index, vehicle_id
                )
            final_node_index = manager.IndexToNode(index)
            route_indices_for_vehicle.append(final_node_index)
            routes_data.append(
                {
                    "vehicle_id": vehicle_id,
                    "route_indices": route_indices_for_vehicle,
                    "total_distance": total_distance_for_vehicle,
                }
            )
        return routes_data, solution
    else:
        return None, None


#  Inicialização da Aplicação FastAPI
app = FastAPI(
    title="Otimizador de Rotas de Entrega",
    description="API para otimizar rotas de entrega usando OR-Tools VRP e OSMnx para distâncias reais em Maceió.",
    version="1.0.0",
)

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from fastapi.responses import RedirectResponse

## Endpoints de Leitura de Dados JSON

@app.get("/", include_in_schema=False)
async def redirect_to_docs():
    return RedirectResponse(url="/docs")

@app.get("/clientes", response_model=List[ClienteModel], summary="Lista todos os clientes existentes no arquivo ./db_json/clientes.json.")
async def get_clientes_from_json():
    try:
        with open("./db_json/clientes.json", "r", encoding="utf-8") as f:
            clientes_data = json.load(f)
        validated_clientes = [ClienteModel(**cliente) for cliente in clientes_data]
        return validated_clientes
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Arquivo ./db_json/clientes.json não encontrado.")
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="Erro ao decodificar ./db_json/clientes.json. Verifique se o arquivo está no formato JSON válido.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ocorreu um erro ao ler clientes: {str(e)}")

@app.get("/pedidos", response_model=List[PedidoModel], summary="Lista todos os pedidos existentes no arquivo ./db_json/pedidos.json.")
async def get_pedidos_from_json():
    try:
        with open("./db_json/pedidos.json", "r", encoding="utf-8") as f:
            pedidos_data_raw = json.load(f)
        validated_pedidos = []
        for pedido_item in pedidos_data_raw:
            cliente_id_from_json = pedido_item.get("cliente", {}).get("id")
            if cliente_id_from_json is None:
                raise ValueError(f"Pedido com ID {pedido_item.get('id')} não possui um 'cliente.id' válido.")
            pedido_clean_data = {k: v for k, v in pedido_item.items() if k != "cliente"}
            pedido_clean_data["cliente_id"] = cliente_id_from_json
            validated_pedidos.append(PedidoModel(**pedido_clean_data))
        return validated_pedidos
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Arquivo ./db_json/pedidos.json não encontrado.")
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="Erro ao decodificar ./db_json/pedidos.json. Verifique se o arquivo está no formato JSON válido.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ocorreu um erro ao ler pedidos: {str(e)}")

@app.get("/veiculos", response_model=List[VeiculoModel], summary="Lista todos os veículos existentes no arquivo ./db_json/veiculos.json.")
async def get_veiculos_from_json():
    try:
        with open("./db_json/veiculos.json", "r", encoding="utf-8") as f:
            veiculos_data = json.load(f)
        validated_veiculos = [VeiculoModel(**veiculo) for veiculo in veiculos_data]
        return validated_veiculos
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Arquivo ./db_json/veiculos.json não encontrado.")
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="Erro ao decodificar ./db_json/veiculos.json. Verifique se o arquivo está no formato JSON válido.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ocorreu um erro ao ler veículos: {str(e)}")


## Endpoint Principal de Otimização

@app.post("/optimize-routes", response_model=OptimizationResponse, summary="Otimiza rotas de entrega e aloca pedidos aos veículos.")
async def optimize_routes(request: OptimizationRequest):
    """
    Recebe listas de clientes, pedidos e veículos para otimizar as rotas de entrega e alocar pedidos.
    Retorna as rotas planejadas para cada veículo, o fluxo máximo de pedidos que pode ser atendido
    e a alocação de volume por veículo.
    """
    try:
        # ======================= INÍCIO DA CORREÇÃO =======================
        # 1. Filtra a lista de veículos para usar APENAS os que estão disponíveis.
        veiculos_disponiveis_model = [v for v in request.veiculos if v.disponivel]

        # 2. Verifica se existe pelo menos um veículo disponível.
        if not veiculos_disponiveis_model:
            raise HTTPException(status_code=400, detail="Nenhum veículo disponível para realizar as entregas.")
        # ======================= FIM DA CORREÇÃO =======================
        
        clientes_map_pydantic: Dict[int, ClienteModel] = {c.id: c for c in request.clientes}

        original_clientes: List[OriginalCliente] = []
        for c_model in request.clientes:
            original_clientes.append(
                OriginalCliente(
                    id=c_model.id,
                    nome=c_model.nome,
                    zona=c_model.zona,
                    latitude=c_model.latitude,
                    longitude=c_model.longitude,
                    endereco=c_model.endereco,
                )
            )

        original_pedidos: List[OriginalPedido] = []
        for p_model in request.pedidos:
            client_data = clientes_map_pydantic.get(p_model.cliente_id)
            if not client_data:
                raise HTTPException(
                    status_code=400,
                    detail=f"Cliente com ID {p_model.cliente_id} para Pedido {p_model.id} não encontrado.",
                )
            cliente_para_pedido = OriginalCliente(
                id=client_data.id,
                nome=client_data.nome,
                zona=client_data.zona,
                latitude=client_data.latitude,
                longitude=client_data.longitude,
                endereco=client_data.endereco,
            )
            original_pedidos.append(
                OriginalPedido(
                    id=p_model.id,
                    cliente=cliente_para_pedido,
                    volume=p_model.volume,
                    prioridade=p_model.prioridade,
                    status=OriginalStatusPedido[p_model.status.name],
                )
            )

        # <<< MUDANÇA 1: Usar a lista filtrada para criar os objetos originais
        original_veiculos: List[OriginalVeiculo] = []
        for v_model in veiculos_disponiveis_model: 
            original_veiculos.append(
                OriginalVeiculo(
                    id=v_model.id,
                    tipo=OriginalTipoVeiculo[v_model.tipo.name],
                    capacidade=v_model.capacidade,
                    disponivel=v_model.disponivel,
                    zonas_permitidas=v_model.zonas_permitidas,
                )
            )

        # Cálculo de Fluxo
        flow_network = build_flow_network(original_pedidos, original_veiculos)
        max_flow = flow_network.multi_max_flow()

        # Geração da Matriz de Distâncias
        matriz_distancias, G, nodos_osm = gerar_matriz_distancias_osm(
            original_pedidos, clientes_map_pydantic
        )

        # Preparar entradas para o VRP
        demandas = [p.volume for p in original_pedidos]
        capacidades = [v.capacidade for v in original_veiculos]
        # <<< MUDANÇA 2: Usar o tamanho da lista filtrada
        num_veiculos = len(veiculos_disponiveis_model) 

        # Resolver o Problema de Roteirização (VRP)
        vrp_solution_data, solution_obj = criar_modelo_vrp(
            matriz_distancias, demandas, capacidades, num_veiculos, deposito=0
        )

        routes_response: List[VehicleRoute] = []
        if vrp_solution_data:
            for route_info in vrp_solution_data:
                vehicle_id = route_info["vehicle_id"]
                # <<< MUDANÇA 3: Procurar o veículo na lista filtrada
                vehicle_obj_pydantic = next(
                    (v for v in veiculos_disponiveis_model if v.id == vehicle_id), None
                )
                if not vehicle_obj_pydantic:
                    continue

                route_segments: List[RouteSegment] = []
                current_total_volume = 0.0

                for idx in route_info["route_indices"]:
                    if idx < len(original_pedidos):
                        pedido_obj = original_pedidos[idx]
                        client_obj_pydantic = clientes_map_pydantic.get(
                            pedido_obj.cliente.id
                        )
                        if client_obj_pydantic:
                            segment_volume_for_display = (
                                pedido_obj.volume if idx != 0 else 0.0
                            )
                            route_segments.append(
                                RouteSegment(
                                    pedido_id=pedido_obj.id,
                                    cliente_id=client_obj_pydantic.id,
                                    cliente_nome=client_obj_pydantic.nome,
                                    latitude=client_obj_pydantic.latitude,
                                    longitude=client_obj_pydantic.longitude,
                                    volume=segment_volume_for_display,
                                    endereco=client_obj_pydantic.endereco,
                                )
                            )
                            if idx != 0:
                                current_total_volume += pedido_obj.volume
                    else:
                        print(f"Aviso: Índice de rota {idx} fora do limite da lista de pedidos.")

                # Apenas adicionar a rota se ela tiver paradas além do depósito
                if len(route_segments) > 2:
                    routes_response.append(
                        VehicleRoute(
                            vehicle_id=vehicle_obj_pydantic.id,
                            vehicle_type=vehicle_obj_pydantic.tipo.name,
                            route=route_segments,
                            total_volume=current_total_volume,
                            total_distance=route_info["total_distance"],
                        )
                    )

        # Alocações de Fluxo
        allocations = get_allocations(
            flow_network, len(original_pedidos), len(original_veiculos)
        )

        return OptimizationResponse(
            message="Otimização concluída com sucesso!",
            routes=routes_response,
            allocations=allocations,
            max_flow=float(max_flow),
            total_demand=float(sum(demandas)),
            total_capacity=float(sum(capacidades)),
        )

    except HTTPException as e:
        raise e
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Erro de validação de dados: {str(e)}")
    except Exception as e:
        print(f"Erro interno do servidor: {e}")
        raise HTTPException(status_code=500, detail=f"Ocorreu um erro interno no servidor: {str(e)}")
