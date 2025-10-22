// Clusters JavaScript - Version 2.4 - Fixed all syntax errors
console.log('Clusters script loaded - version 2.4 - Fixed all syntax errors - ' + new Date().toISOString());

let allClusters = [];
let filteredClusters = [];
let currentPage = 1;
const clustersPerPage = 10;

// Загрузка данных при загрузке страницы
document.addEventListener('DOMContentLoaded', function() {
    loadClusters();
    setupFilters();
});

async function loadClusters() {
    console.log('🔄 Загружаем кластеры...');
    try {
        const response = await fetch('/api/clusters');
        console.log('📡 Ответ получен:', response.status);
        const data = await response.json();
        console.log('📊 Данные:', data);
        
        if (data.clusters && Array.isArray(data.clusters)) {
            console.log('✅ Найдено кластеров:', data.clusters.length);
            allClusters = data.clusters;
            filteredClusters = [...allClusters];
            updateCounts();
            displayClusters();
            populateMarketFilter();
        } else {
            console.error('❌ Неверный формат данных:', data);
            showAlert('danger', 'Ошибка при загрузке кластеров: ' + (data.error || 'Неверный формат данных'));
        }
    } catch (error) {
        console.error('❌ Ошибка при загрузке кластеров:', error);
        showAlert('danger', 'Ошибка при загрузке кластеров: ' + error.message);
    }
}

function setupFilters() {
    // Слайдер синхронности
    const syncSlider = document.getElementById('syncScoreFilter');
    const syncValue = document.getElementById('syncScoreValue');
    
    syncSlider.addEventListener('input', function() {
        syncValue.textContent = this.value + '%';
    });
}

function populateMarketFilter() {
    const marketFilter = document.getElementById('marketFilter');
    const markets = [...new Set(allClusters.map(c => c.market_name))].sort();
    
    markets.forEach(market => {
        const option = document.createElement('option');
        option.value = market;
        option.textContent = market;
        marketFilter.appendChild(option);
    });
}

function applyFilters() {
    const syncScore = parseFloat(document.getElementById('syncScoreFilter').value);
    const volume = parseFloat(document.getElementById('volumeFilter').value) || 0;
    const wallets = parseInt(document.getElementById('walletsFilter').value) || 1;
    const market = document.getElementById('marketFilter').value;
    
    filteredClusters = allClusters.filter(cluster => {
        return cluster.sync_score >= syncScore &&
               cluster.total_volume >= volume &&
               cluster.wallets_count >= wallets &&
               (market === '' || cluster.market_name === market);
    });
    
    currentPage = 1;
    updateCounts();
    displayClusters();
}

function clearFilters() {
    document.getElementById('syncScoreFilter').value = 0;
    document.getElementById('syncScoreValue').textContent = '0%';
    document.getElementById('volumeFilter').value = 0;
    document.getElementById('walletsFilter').value = 1;
    document.getElementById('marketFilter').value = '';
    
    filteredClusters = [...allClusters];
    currentPage = 1;
    updateCounts();
    displayClusters();
}

function updateCounts() {
    document.getElementById('filteredCount').textContent = filteredClusters.length;
    document.getElementById('totalCount').textContent = allClusters.length;
}

function displayClusters() {
    const startIndex = (currentPage - 1) * clustersPerPage;
    const endIndex = startIndex + clustersPerPage;
    const pageClusters = filteredClusters.slice(startIndex, endIndex);
    
    const container = document.getElementById('clustersList');
    
    if (pageClusters.length === 0) {
        container.innerHTML = `
            <div class="text-center text-muted">
                <i class="fas fa-search fa-2x mb-2"></i>
                <p>Кластеры не найдены по заданным фильтрам.</p>
            </div>
        `;
        updatePagination();
        return;
    }
    
    // Загружаем информацию о рынках асинхронно
    loadMarketInfoAsync(pageClusters).then(marketInfoMap => {
        const clustersHtml = pageClusters.map((cluster, index) => {
            const marketInfo = marketInfoMap[cluster.market_id] || {
                name: cluster.market_name || `Market ${cluster.market_id}`,
                url: `https://polymarket.com/search?q=${cluster.market_id}`,
                description: cluster.market_question || 'Нет описания'
            };
            
            // Улучшаем отображение названия рынка
            let displayName = marketInfo.name;
            if (!displayName || displayName.startsWith('Market 0x') || displayName.length > 60) {
                displayName = cluster.market_question || `Market ${cluster.market_id.substring(0, 8)}...`;
            }
            
            const clusterIndex = startIndex + index;
            
            return `
                <div class="card cluster-card ${getRiskClass(cluster.sync_score)} mb-3">
                    <div class="card-body">
                        <div class="row">
                            <div class="col-md-8">
                                <h5 class="market-name">
                                    <a href="${marketInfo.url}" target="_blank" class="text-decoration-none" title="${marketInfo.name}">
                                        ${displayName}
                                        <i class="fas fa-external-link-alt ms-1"></i>
                                    </a>
                                </h5>
                                <p class="text-muted mb-2">${marketInfo.description}</p>
                        
                                <div class="d-flex flex-wrap gap-2 mb-3">
                                    <span class="badge bg-${cluster.side === 'YES' ? 'success' : 'danger'} fs-6">
                                        ${cluster.side}
                                    </span>
                                    <span class="badge bg-info">
                                        <i class="fas fa-wallet"></i> ${cluster.wallets_count} кошельков
                                    </span>
                                    <span class="badge bg-secondary">
                                        <i class="fas fa-exchange-alt"></i> ${cluster.trades_count} сделок
                                    </span>
                                    <span class="badge bg-warning text-dark">
                                        <i class="fas fa-clock"></i> ${cluster.time_window_str}
                                    </span>
                                </div>
                        
                                <div class="row">
                                    <div class="col-md-6">
                                        <strong>Кошельки:</strong>
                                        <div class="mt-1">
                                            ${cluster.wallets.slice(0, 3).map(wallet => 
                                                `<span class="wallet-address me-1">${wallet.substring(0, 8)}...</span>`
                                            ).join('')}
                                            ${cluster.wallets.length > 3 ? `<span class="text-muted">+${cluster.wallets.length - 3} еще</span>` : ''}
                                        </div>
                                    </div>
                                    <div class="col-md-6">
                                        <strong>Временное окно:</strong>
                                        <div class="text-muted small">
                                            ${formatTime(cluster.start_time)} - ${formatTime(cluster.end_time)}
                                        </div>
                                    </div>
                                </div>
                            </div>
                    
                            <div class="col-md-4 text-end">
                                <div class="sync-score ${getSyncScoreClass(cluster.sync_score)} mb-2">
                                    ${cluster.sync_score.toFixed(1)}%
                                </div>
                                <div class="text-muted small mb-2">Синхронность</div>
                        
                                <div class="fw-bold fs-5 mb-1">${formatCurrency(cluster.total_volume)}</div>
                                <div class="text-muted small mb-2">Общий объем</div>
                        
                                <div class="text-muted small mb-2">
                                    ${formatCurrency(cluster.avg_trade_size)} средняя сделка
                                </div>
                        
                                <button class="btn btn-outline-primary btn-sm" onclick="showClusterDetails(${clusterIndex})">
                                    <i class="fas fa-eye"></i> Детали
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            `;
        }).join('');
    
        container.innerHTML = clustersHtml;
        updatePagination();
    });
}

async function loadMarketInfoAsync(clusters) {
    const marketIds = [...new Set(clusters.map(c => c.market_id))];
    const marketInfoMap = {};
    
    // Загружаем информацию о рынках параллельно
    const promises = marketIds.map(async (marketId) => {
        try {
            const response = await fetch(`/api/market-info/${marketId}`);
            const data = await response.json();
            if (data.success) {
                marketInfoMap[marketId] = data.market;
            }
        } catch (error) {
            console.warn(`Не удалось загрузить информацию о рынке ${marketId}:`, error);
        }
    });
    
    await Promise.all(promises);
    return marketInfoMap;
}

function updatePagination() {
    const totalPages = Math.ceil(filteredClusters.length / clustersPerPage);
    const pagination = document.getElementById('pagination');
    
    if (totalPages <= 1) {
        pagination.innerHTML = '';
        return;
    }
    
    let paginationHtml = '';
    
    // Предыдущая страница
    if (currentPage > 1) {
        paginationHtml += `
            <li class="page-item">
                <a class="page-link" href="#" onclick="changePage(${currentPage - 1})">Предыдущая</a>
            </li>
        `;
    }
    
    // Страницы
    const startPage = Math.max(1, currentPage - 2);
    const endPage = Math.min(totalPages, currentPage + 2);
    
    for (let i = startPage; i <= endPage; i++) {
        paginationHtml += `
            <li class="page-item ${i === currentPage ? 'active' : ''}">
                <a class="page-link" href="#" onclick="changePage(${i})">${i}</a>
            </li>
        `;
    }
    
    // Следующая страница
    if (currentPage < totalPages) {
        paginationHtml += `
            <li class="page-item">
                <a class="page-link" href="#" onclick="changePage(${currentPage + 1})">Следующая</a>
            </li>
        `;
    }
    
    pagination.innerHTML = paginationHtml;
}

function changePage(page) {
    currentPage = page;
    displayClusters();
}

function showClusterDetails(clusterIndex) {
    const cluster = filteredClusters[clusterIndex];
    
    // Создаем модальное окно с деталями
    const modalHtml = `
        <div class="modal fade" id="clusterDetailsModal" tabindex="-1">
            <div class="modal-dialog modal-lg">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">Детали кластера</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <div class="row">
                            <div class="col-md-6">
                                <h6>Информация о рынке</h6>
                                <p><strong>Название:</strong> ${cluster.market_name}</p>
                                <p><strong>Вопрос:</strong> ${cluster.market_question}</p>
                                <p><strong>Направление:</strong> 
                                    <span class="badge bg-${cluster.side === 'YES' ? 'success' : 'danger'}">${cluster.side}</span>
                                </p>
                            </div>
                            <div class="col-md-6">
                                <h6>Метрики</h6>
                                <p><strong>Синхронность:</strong> ${cluster.sync_score.toFixed(1)}%</p>
                                <p><strong>Объем:</strong> ${formatCurrency(cluster.total_volume)}</p>
                                <p><strong>Сделок:</strong> ${cluster.trades_count}</p>
                                <p><strong>Кошельков:</strong> ${cluster.wallets_count}</p>
                            </div>
                        </div>
                        
                        <h6 class="mt-3">Кошельки</h6>
                        <div class="row">
                            ${cluster.wallets.map(wallet => `
                                <div class="col-md-6 mb-2">
                                    <span class="wallet-address">${wallet}</span>
                                </div>
                            `).join('')}
                        </div>
                        
                        <h6 class="mt-3">Статистика по кошелькам</h6>
                        <div class="table-responsive">
                            <table class="table table-sm">
                                <thead>
                                    <tr>
                                        <th>Кошелек</th>
                                        <th>Сделок</th>
                                        <th>Объем</th>
                                        <th>Цена</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    ${Object.entries(cluster.wallet_stats).map(([wallet, stats]) => `
                                        <tr>
                                            <td><span class="wallet-address">${wallet.substring(0, 12)}...</span></td>
                                            <td>${stats.trades_count}</td>
                                            <td>${formatCurrency(stats.total_amount)}</td>
                                            <td>${stats.avg_price.toFixed(3)}</td>
                                        </tr>
                                    `).join('')}
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    // Удаляем предыдущее модальное окно, если есть
    const existingModal = document.getElementById('clusterDetailsModal');
    if (existingModal) {
        existingModal.remove();
    }
    
    // Добавляем новое модальное окно
    document.body.insertAdjacentHTML('beforeend', modalHtml);
    
    // Показываем модальное окно
    const modal = new bootstrap.Modal(document.getElementById('clusterDetailsModal'));
    modal.show();
}

function exportClusters() {
    const dataStr = JSON.stringify(filteredClusters, null, 2);
    const dataBlob = new Blob([dataStr], {type: 'application/json'});
    
    const link = document.createElement('a');
    link.href = URL.createObjectURL(dataBlob);
    link.download = `clusters_${new Date().toISOString().split('T')[0]}.json`;
    link.click();
}

function showAlert(type, message) {
    // Создаем алерт
    const alertHtml = `
        <div class="alert alert-${type} alert-dismissible fade show" role="alert">
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>
    `;
    
    // Добавляем алерт в начало страницы
    const container = document.querySelector('.row:first-child');
    container.insertAdjacentHTML('afterbegin', alertHtml);
    
    // Автоматически скрываем через 5 секунд
    setTimeout(() => {
        const alert = document.querySelector('.alert');
        if (alert) {
            alert.remove();
        }
    }, 5000);
}

function getRiskClass(syncScore) {
    if (syncScore >= 80) return 'border-danger';
    if (syncScore >= 60) return 'border-warning';
    return 'border-info';
}

function getSyncScoreClass(syncScore) {
    if (syncScore >= 80) return 'text-danger fw-bold';
    if (syncScore >= 60) return 'text-warning fw-bold';
    return 'text-info fw-bold';
}

function formatCurrency(amount) {
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD',
        minimumFractionDigits: 0,
        maximumFractionDigits: 0
    }).format(amount);
}

function formatTime(timestamp) {
    return new Date(timestamp * 1000).toLocaleString('ru-RU');
}