# 🚀 ShadowFlow

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-2.3+-green.svg)](https://flask.palletsprojects.com)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![GitHub stars](https://img.shields.io/github/stars/dant1k/shadowflow.svg)](https://github.com/dant1k/shadowflow/stargazers)

**Advanced system for detecting coordinated trading activities on prediction markets using AI analysis, real-time monitoring, and interactive visualizations.**

## 🎯 Overview

ShadowFlow is a comprehensive system designed to identify coordinated trading activities on prediction markets like Polymarket. It combines AI-powered anomaly detection, machine learning algorithms, and real-time monitoring to uncover suspicious trading patterns and potential market manipulation.

## ✨ Key Features

### 🤖 AI-Powered Analysis
- **Anomaly Detection**: Isolation Forest algorithm to identify unusual trading patterns
- **Wallet Clustering**: DBSCAN clustering to detect connected trading accounts
- **Risk Scoring**: Comprehensive 0-100 risk assessment system
- **Pattern Recognition**: Temporal and price manipulation analysis

### 📊 Real-Time Monitoring
- **WebSocket Integration**: Live updates and notifications
- **Configurable Alerts**: Customizable risk thresholds
- **Live Dashboards**: Real-time risk score visualization
- **Alert System**: Automatic notifications for suspicious activities

### 🎨 Interactive Visualizations
- **Network Analysis**: D3.js-powered wallet relationship graphs
- **Chart.js Integration**: Dynamic charts and graphs
- **Responsive Design**: Modern Bootstrap 5 interface
- **Real-Time Updates**: Live data streaming

### 🔗 Data Integration
- **Polymarket API**: Real-time data from prediction markets
- **25,000+ Trades**: Comprehensive trade analysis
- **Multiple Markets**: Support for various prediction markets
- **Historical Analysis**: Trend analysis and pattern detection

## 📈 Current Results

- **Risk Score**: 4.3/100 (Low Risk)
- **Coordinated Clusters**: 100 detected
- **Anomalous Trades**: 2,500 (10% of total)
- **Wallet Clusters**: 3 major clusters (234 accounts)
- **Manipulated Markets**: 50 markets with suspicious activity

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- pip package manager

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/dant1k/shadowflow.git
   cd shadowflow
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Start the system**
   ```bash
   python start_system.py
   ```

4. **Access the web interface**
   - Open http://localhost:5001 in your browser
   - WebSocket monitoring: ws://localhost:8765

## 🌐 Web Interface

### 📊 Dashboard (`/`)
- Overview statistics and key metrics
- Top suspicious clusters
- Quick access to all features

### 🔍 Cluster Analysis (`/clusters`)
- Detailed coordinated action analysis
- Filtering by sync score and volume
- Wallet and trade information

### 🤖 AI Analysis (`/ai-analysis`)
- Interactive anomaly charts
- Risk factor breakdown
- Temporal pattern analysis
- Top anomalous trades

### 🌐 Network Analysis (`/network-analysis`)
- Interactive wallet relationship visualization
- D3.js-powered network graphs
- Cluster details and statistics
- Network activity metrics

### 📡 Real-Time Monitoring (`/monitoring`)
- Live metric updates
- Configurable alert thresholds
- Real-time risk score charts
- Notification center

## 🔗 API Endpoints

### Core Data
- `GET /api/summary` - General statistics
- `GET /api/clusters` - All detected clusters
- `GET /api/trades` - Trade data

### AI Analysis
- `GET /api/ai-analysis` - Comprehensive AI analysis
- `GET /api/anomalies` - Anomalous trades
- `GET /api/wallet-clusters` - Wallet clusters

### Management
- `POST /api/update-data` - Update data
- `GET /api/markets` - Market list

## ⚙️ Configuration

### Alert Thresholds
```json
{
  "risk_score": 50.0,        // Risk score threshold
  "anomaly_percentage": 15.0, // Anomaly percentage
  "cluster_count": 20,        // Cluster count threshold
  "volume_spike": 2.0         // Volume growth multiplier
}
```

### Analysis Parameters
- **Sync Threshold**: 180 seconds (configurable)
- **Minimum Trades**: 5 for cluster detection
- **Anomaly Rate**: 10% of total volume
- **Update Interval**: 60 seconds

## 📊 Risk Assessment

### Risk Score (0-100)
- **0-30**: Low Risk 🟢
- **30-60**: Medium Risk 🟡
- **60-80**: High Risk 🟠
- **80-100**: Critical Risk 🔴

### Risk Factors
1. **Anomalies** (30%) - Unusual trading patterns
2. **Wallet Clusters** (25%) - Connected accounts
3. **Price Manipulation** (25%) - Suspicious correlations
4. **Temporal Patterns** (20%) - Trading regularity

## 🏗️ Architecture

```
ShadowFlow/
├── api/                    # API clients
│   ├── polymarket.py      # Polymarket API integration
│   └── polymarket_scraper.py
├── analyzer/              # Data analysis
│   └── cluster.py         # Clustering algorithms
├── ai/                    # AI/ML components
│   └── anomaly_detector.py # Anomaly detection
├── monitoring/            # Real-time monitoring
│   └── realtime_monitor.py
├── templates/             # HTML templates
├── static/               # CSS/JS resources
└── data/                 # Data cache
```

## 🛠️ Technology Stack

- **Backend**: Python 3.11, Flask, WebSocket
- **AI/ML**: scikit-learn, pandas, numpy
- **Frontend**: Bootstrap 5, Chart.js, D3.js
- **APIs**: Polymarket Gamma API, Data API
- **Monitoring**: Real-time WebSocket

## 📚 Documentation

- **[System Guide](SYSTEM_GUIDE.md)** - Complete user manual
- **[Quick Start](QUICKSTART.md)** - Quick setup guide
- **API Documentation** - Available in code comments

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Polymarket for providing the prediction market data
- The open-source community for the amazing libraries used
- Contributors and users who help improve the system

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/dant1k/shadowflow/issues)
- **Discussions**: [GitHub Discussions](https://github.com/dant1k/shadowflow/discussions)
- **Documentation**: [System Guide](SYSTEM_GUIDE.md)

---

**ShadowFlow - Uncovering coordinated trading activities with AI-powered analysis** 🎯