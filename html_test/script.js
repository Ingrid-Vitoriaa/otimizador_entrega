// =======================================================
// 1. CONFIGURAÇÕES E ESTADO GLOBAL
// =======================================================

// URL base da sua API. Altere se o Dev 5 rodar em uma porta diferente.
const API_BASE_URL = "http://127.0.0.1:3000";

// Variável para guardar os dados que vêm da API
let appData = {
    clientes: [],
    pedidos: [],
    veiculos: []
};

// Guarda as camadas do mapa para poder limpá-las depois
let mapLayers = [];

// =======================================================
// 2. INICIALIZAÇÃO DO MAPA
// =======================================================
const map = L.map('mapa').setView([-9.56, -35.7], 12); // Foco ajustado para Maceió

L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
}).addTo(map);

// =======================================================
// 3. FUNÇÕES DE INTERAÇÃO COM A API
// =======================================================

// Função principal que é chamada quando a página carrega
async function inicializarAplicacao() {
    try {
        // Busca os dados iniciais em paralelo para ser mais rápido
        const [clientes, pedidos, veiculos] = await Promise.all([
            fetch(`${API_BASE_URL}/clientes`).then(res => res.json()),
            fetch(`${API_BASE_URL}/pedidos`).then(res => res.json()),
            fetch(`${API_BASE_URL}/veiculos`).then(res => res.json())
        ]);

        // Guarda os dados no estado global
        appData = { clientes, pedidos, veiculos };

        console.log("Dados iniciais carregados:", appData);
        alert("Dados de clientes, pedidos e veículos carregados da API!");

        // Desenha apenas os clientes no mapa inicialmente
        desenharClientesIniciais(clientes);

    } catch (error) {
        console.error("Erro ao inicializar a aplicação:", error);
        alert("Falha ao carregar dados da API. Verifique se o servidor backend está rodando.");
    }
}

// Função chamada quando o botão "Otimizar Rotas" é clicado
async function otimizarRotas() {
    alert("Enviando dados para otimização... Isso pode levar um momento.");
    try {
        // Envia os dados carregados para o endpoint de otimização
        const response = await fetch(`${API_BASE_URL}/optimize-routes`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            // O corpo da requisição é o nosso objeto appData convertido para JSON
            body: JSON.stringify(appData)
        });

        if (!response.ok) {
            // Se a resposta não for OK, lê o erro e mostra
            const errorData = await response.json();
            throw new Error(errorData.detail || "Erro na otimização");
        }

        const optimizationResult = await response.json();
        console.log("Resultado da otimização:", optimizationResult);
        alert("Otimização concluída! Desenhando rotas no mapa.");

        // Desenha o resultado no mapa
        desenharRotasOtimizadas(optimizationResult);

    } catch (error) {
        console.error("Erro ao otimizar rotas:", error);
        alert(`Falha na otimização: ${error.message}`);
    }
}

// =======================================================
// 4. FUNÇÕES DE DESENHO NO MAPA
// =======================================================

// Limpa todas as camadas (marcadores, linhas) do mapa
function limparMapa() {
    mapLayers.forEach(layer => map.removeLayer(layer));
    mapLayers = [];
}

// Desenha apenas os marcadores dos clientes no início
function desenharClientesIniciais(clientes) {
    limparMapa();
    clientes.forEach(cliente => {
        if (cliente.latitude && cliente.longitude) {
            const marker = L.marker([cliente.latitude, cliente.longitude])
                .addTo(map)
                .bindPopup(`<b>${cliente.nome}</b><br>Zona: ${cliente.zona}`);
            mapLayers.push(marker);
        }
    });
}


// >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
// FUNÇÃO MODIFICADA ABAIXO
// >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

// Desenha o resultado completo da otimização
function desenharRotasOtimizadas(result) {
    limparMapa();

    result.routes.forEach((vehicleRoute) => {
        const latlngs = [];

        // --- LÓGICA DE COR BASEADA NA LOTAÇÃO DO VEÍCULO ---
        // 1. Encontrar o veículo original na nossa lista de dados para pegar sua capacidade
        const veiculoOriginal = appData.veiculos.find(v => v.id === vehicleRoute.vehicle_id);
        let corDaRota = '#3388ff'; // Cor padrão azul

        if (veiculoOriginal && veiculoOriginal.capacidade > 0) {
            // 2. Calcular a utilização da capacidade
            const utilizacao = vehicleRoute.total_volume / veiculoOriginal.capacidade;

            // 3. Definir a cor com base na utilização
            if (utilizacao > 0.9) {
                corDaRota = 'red'; // Acima de 90% -> Vermelho (Gargalo)
            } else if (utilizacao > 0.7) {
                corDaRota = 'orange'; // De 70% a 90% -> Laranja (Atenção)
            } else if (utilizacao > 0) {
                corDaRota = '#008000'; // Abaixo de 70% e com carga -> Verde (Saudável)
            } else {
                corDaRota = '#888'; // Rota vazia -> Cinza
            }
        }
        // --- FIM DA LÓGICA DE COR ---

        vehicleRoute.route.forEach(segmento => {
            if (segmento.pedido_id !== 0) {
                const marker = L.marker([segmento.latitude, segmento.longitude], {
                    icon: L.divIcon({
                        className: 'custom-div-icon',
                        html: `<div style="background-color:${corDaRota};" class="marker-pin"></div><i>${segmento.pedido_id}</i>`,
                        iconSize: [30, 42],
                        iconAnchor: [15, 42]
                    })
                })
                    .addTo(map)
                    .bindPopup(`<b>Cliente: ${segmento.cliente_nome}</b><br>Pedido ID: ${segmento.pedido_id}<br>Volume: ${segmento.volume}`);
                mapLayers.push(marker);
            }
            latlngs.push([segmento.latitude, segmento.longitude]);
        });

        if (latlngs.length > 1 && veiculoOriginal) {
            const polyline = L.polyline(latlngs, { color: corDaRota, weight: 5, opacity: 0.8 })
                .addTo(map)
                .bindPopup(`<b>Rota do Veículo ${vehicleRoute.vehicle_id} (${veiculoOriginal.tipo})</b><br>
                            Lotação: ${vehicleRoute.total_volume} / ${veiculoOriginal.capacidade}<br>
                            Distância Total: ${(vehicleRoute.total_distance / 1000).toFixed(2)} km`);

            mapLayers.push(polyline);
        }
    });
}


// =======================================================
// 5. INÍCIO DA EXECUÇÃO E EVENTOS
// =======================================================

// Adiciona um listener para o botão de otimização
document.getElementById('optimize-button').addEventListener('click', otimizarRotas);

// Chama a função para carregar os dados iniciais assim que a página carrega
inicializarAplicacao();

// Adiciona um pouco de CSS para os marcadores personalizados (opcional)
const style = document.createElement('style');
style.innerHTML = `
.marker-pin {
    width: 30px;
    height: 30px;
    border-radius: 50% 50% 50% 0;
    position: absolute;
    transform: rotate(-45deg);
    left: 50%;
    top: 50%;
    margin: -15px 0 0 -15px;
}
.marker-pin::after {
    content: '';
    width: 24px;
    height: 24px;
    margin: 3px 0 0 3px;
    background: #fff;
    position: absolute;
    border-radius: 50%;
}
.custom-div-icon i {
    position: absolute;
    width: 100%;
    text-align: center;
    top: 6px;
    color: black;
    font-weight: bold;
    font-family: sans-serif;
    font-size: 12px;
}
`;
document.head.appendChild(style);
