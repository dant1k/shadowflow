/**
 * Интерактивная визуализация сетей кошельков с помощью D3.js
 * Показывает связи между кошельками и их торговую активность
 */

class NetworkVisualization {
    constructor(containerId, width = 800, height = 600) {
        this.containerId = containerId;
        this.width = width;
        this.height = height;
        this.svg = null;
        this.simulation = null;
        this.nodes = [];
        this.links = [];
        this.nodeElements = null;
        this.linkElements = null;
        this.labels = null;
        
        this.init();
    }
    
    init() {
        // Создаем SVG контейнер
        this.svg = d3.select(`#${this.containerId}`)
            .append('svg')
            .attr('width', this.width)
            .attr('height', this.height)
            .style('background-color', '#f8f9fa')
            .style('border-radius', '8px');
        
        // Создаем группы для элементов
        this.linkElements = this.svg.append('g').attr('class', 'links');
        this.nodeElements = this.svg.append('g').attr('class', 'nodes');
        this.labels = this.svg.append('g').attr('class', 'labels');
        
        // Добавляем зум
        this.addZoom();
    }
    
    addZoom() {
        const zoom = d3.zoom()
            .scaleExtent([0.1, 4])
            .on('zoom', (event) => {
                this.nodeElements.attr('transform', event.transform);
                this.linkElements.attr('transform', event.transform);
                this.labels.attr('transform', event.transform);
            });
        
        this.svg.call(zoom);
    }
    
    updateData(walletClusters, trades) {
        this.processData(walletClusters, trades);
        this.render();
    }
    
    processData(walletClusters, trades) {
        this.nodes = [];
        this.links = [];
        
        // Создаем узлы для каждого кошелька
        const walletStats = {};
        trades.forEach(trade => {
            const wallet = trade.wallet;
            if (!walletStats[wallet]) {
                walletStats[wallet] = {
                    wallet: wallet,
                    trades: 0,
                    volume: 0,
                    markets: new Set(),
                    cluster: null
                };
            }
            
            walletStats[wallet].trades++;
            walletStats[wallet].volume += trade.amount;
            walletStats[wallet].markets.add(trade.market_id);
        });
        
        // Определяем кластеры
        Object.entries(walletClusters).forEach(([clusterId, wallets]) => {
            wallets.forEach(wallet => {
                if (walletStats[wallet]) {
                    walletStats[wallet].cluster = clusterId;
                }
            });
        });
        
        // Создаем узлы
        Object.values(walletStats).forEach(stats => {
            this.nodes.push({
                id: stats.wallet,
                trades: stats.trades,
                volume: stats.volume,
                markets: stats.markets.size,
                cluster: stats.cluster,
                radius: Math.max(5, Math.min(20, Math.sqrt(stats.volume) / 100))
            });
        });
        
        // Создаем связи между кошельками в одном кластере
        Object.entries(walletClusters).forEach(([clusterId, wallets]) => {
            for (let i = 0; i < wallets.length; i++) {
                for (let j = i + 1; j < wallets.length; j++) {
                    this.links.push({
                        source: wallets[i],
                        target: wallets[j],
                        cluster: clusterId
                    });
                }
            }
        });
    }
    
    render() {
        // Создаем симуляцию
        this.simulation = d3.forceSimulation(this.nodes)
            .force('link', d3.forceLink(this.links).id(d => d.id).distance(100))
            .force('charge', d3.forceManyBody().strength(-300))
            .force('center', d3.forceCenter(this.width / 2, this.height / 2))
            .force('collision', d3.forceCollide().radius(d => d.radius + 5));
        
        // Рендерим связи
        this.linkElements.selectAll('line')
            .data(this.links)
            .join('line')
            .attr('stroke', '#999')
            .attr('stroke-opacity', 0.6)
            .attr('stroke-width', 2);
        
        // Рендерим узлы
        this.nodeElements.selectAll('circle')
            .data(this.nodes)
            .join('circle')
            .attr('r', d => d.radius)
            .attr('fill', d => this.getNodeColor(d))
            .attr('stroke', '#fff')
            .attr('stroke-width', 2)
            .style('cursor', 'pointer')
            .call(this.drag())
            .on('mouseover', this.showTooltip.bind(this))
            .on('mouseout', this.hideTooltip.bind(this))
            .on('click', this.selectNode.bind(this));
        
        // Рендерим подписи
        this.labels.selectAll('text')
            .data(this.nodes.filter(d => d.radius > 10))
            .join('text')
            .text(d => d.id.substring(0, 8) + '...')
            .attr('font-size', '10px')
            .attr('text-anchor', 'middle')
            .attr('dy', '0.35em')
            .style('pointer-events', 'none');
        
        // Обновляем позиции при симуляции
        this.simulation.on('tick', () => {
            this.linkElements.selectAll('line')
                .attr('x1', d => d.source.x)
                .attr('y1', d => d.source.y)
                .attr('x2', d => d.target.x)
                .attr('y2', d => d.target.y);
            
            this.nodeElements.selectAll('circle')
                .attr('cx', d => d.x)
                .attr('cy', d => d.y);
            
            this.labels.selectAll('text')
                .attr('x', d => d.x)
                .attr('y', d => d.y);
        });
    }
    
    getNodeColor(node) {
        if (node.cluster) {
            const colors = ['#e74c3c', '#3498db', '#2ecc71', '#f39c12', '#9b59b6'];
            const clusterIndex = parseInt(node.cluster.split('_')[1]) || 0;
            return colors[clusterIndex % colors.length];
        }
        return '#95a5a6';
    }
    
    drag() {
        return d3.drag()
            .on('start', (event, d) => {
                if (!event.active) this.simulation.alphaTarget(0.3).restart();
                d.fx = d.x;
                d.fy = d.y;
            })
            .on('drag', (event, d) => {
                d.fx = event.x;
                d.fy = event.y;
            })
            .on('end', (event, d) => {
                if (!event.active) this.simulation.alphaTarget(0);
                d.fx = null;
                d.fy = null;
            });
    }
    
    showTooltip(event, d) {
        const tooltip = d3.select('body').append('div')
            .attr('class', 'network-tooltip')
            .style('position', 'absolute')
            .style('background', 'rgba(0, 0, 0, 0.8)')
            .style('color', 'white')
            .style('padding', '10px')
            .style('border-radius', '5px')
            .style('font-size', '12px')
            .style('pointer-events', 'none')
            .style('z-index', '1000');
        
        tooltip.html(`
            <strong>Кошелек:</strong> ${d.id}<br>
            <strong>Сделок:</strong> ${d.trades}<br>
            <strong>Объем:</strong> $${d.volume.toFixed(2)}<br>
            <strong>Рынков:</strong> ${d.markets}<br>
            <strong>Кластер:</strong> ${d.cluster || 'Неизвестен'}
        `);
        
        tooltip.style('left', (event.pageX + 10) + 'px')
               .style('top', (event.pageY - 10) + 'px');
    }
    
    hideTooltip() {
        d3.selectAll('.network-tooltip').remove();
    }
    
    selectNode(event, d) {
        // Подсвечиваем связанные узлы
        this.nodeElements.selectAll('circle')
            .style('opacity', node => {
                return this.isConnected(d, node) ? 1 : 0.3;
            });
        
        this.linkElements.selectAll('line')
            .style('opacity', link => {
                return (link.source.id === d.id || link.target.id === d.id) ? 1 : 0.1;
            });
        
        // Показываем информацию о выбранном узле
        this.showNodeInfo(d);
    }
    
    isConnected(node1, node2) {
        if (node1.id === node2.id) return true;
        return this.links.some(link => 
            (link.source.id === node1.id && link.target.id === node2.id) ||
            (link.source.id === node2.id && link.target.id === node1.id)
        );
    }
    
    showNodeInfo(node) {
        const infoDiv = document.getElementById('node-info');
        if (infoDiv) {
            infoDiv.innerHTML = `
                <h6>Информация о кошельке</h6>
                <p><strong>Адрес:</strong> ${node.id}</p>
                <p><strong>Сделок:</strong> ${node.trades}</p>
                <p><strong>Объем:</strong> $${node.volume.toFixed(2)}</p>
                <p><strong>Рынков:</strong> ${node.markets}</p>
                <p><strong>Кластер:</strong> ${node.cluster || 'Неизвестен'}</p>
            `;
        }
    }
    
    resetView() {
        this.nodeElements.selectAll('circle').style('opacity', 1);
        this.linkElements.selectAll('line').style('opacity', 0.6);
        
        const infoDiv = document.getElementById('node-info');
        if (infoDiv) {
            infoDiv.innerHTML = '<p class="text-muted">Выберите узел для просмотра информации</p>';
        }
    }
}

// Экспортируем класс для использования
window.NetworkVisualization = NetworkVisualization;
