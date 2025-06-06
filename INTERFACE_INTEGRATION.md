# Integração com a Interface Gráfica

## Formatos de Dados

### 1. Dados da Rede (JSON)
Endpoint: `GET /network-data`

Exemplo de resposta:
```json
{
    "nodes": [
        {
            "id": "pedido_0",
            "type": "pedido",
            "volume": 10,
            "zona": "Zona 1",
            "label": "Pedido 0",
            "latitude": -23.55,
            "longitude": -46.63
        }
    ],
    "edges": [
        {
            "from": "pedido_0",
            "to": "veiculo_0",
            "flow": 10,
            "capacity": 10
        }
    ]
}