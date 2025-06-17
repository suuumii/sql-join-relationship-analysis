#!/usr/bin/env python3
"""
CSVファイルからインタラクティブHTMLを生成するスクリプト
"""

import pandas as pd
import networkx as nx
import argparse
import sys
import os
from datetime import datetime


class CSVToHTMLConverter:
    def __init__(self):
        self.graph = nx.DiGraph()
        self.relationships = []
        self.tables = set()

    def load_csv(self, csv_file_path: str):
        """CSVファイルを読み込んでデータを準備"""
        try:
            # CSVファイルを読み込み
            df = pd.read_csv(csv_file_path)
            
            # 必要なカラムが存在するかチェック
            required_columns = ['table1', 'column1', 'table2', 'column2']
            if not all(col in df.columns for col in required_columns):
                raise ValueError(f"CSV must contain columns: {required_columns}")
            
            print(f"✓ CSVファイルを読み込みました: {csv_file_path}")
            print(f"  関係数: {len(df)}行")
            
            # データを処理
            for _, row in df.iterrows():
                self._add_relationship(
                    str(row['table1']), str(row['column1']),
                    str(row['table2']), str(row['column2'])
                )
            
            print(f"  テーブル数: {len(self.tables)}")
            print(f"  ユニークな関係数: {len(self.relationships)}")
            
        except Exception as e:
            print(f"❌ CSVファイルの読み込みエラー: {e}")
            sys.exit(1)

    def _add_relationship(self, table1: str, col1: str, table2: str, col2: str):
        """関係をグラフに追加"""
        relationship = {
            'table1': table1,
            'column1': col1,
            'table2': table2,
            'column2': col2
        }
        
        # 重複チェック
        if relationship not in self.relationships:
            self.relationships.append(relationship)
        
        # グラフに追加 - 複数関係の累積サポート
        if table1 and table2:
            if self.graph.has_edge(table1, table2):
                # 既存の関係に追加
                existing_columns = self.graph.edges[table1, table2].get('columns', '')
                new_relationship = f"{col1} -> {col2}"
                if existing_columns and new_relationship not in existing_columns:
                    updated_columns = f"{existing_columns}; {new_relationship}"
                else:
                    updated_columns = new_relationship
                self.graph.edges[table1, table2]['columns'] = updated_columns
            else:
                # 新しいエッジを作成
                self.graph.add_edge(table1, table2, columns=f"{col1} -> {col2}")
            
            self.tables.add(table1)
            self.tables.add(table2)

    def generate_html(self, output_file: str):
        """インタラクティブHTMLを生成"""
        if not self.graph.nodes():
            print("❌ 関係データが見つかりません")
            return
        
        # ノードデータ準備
        nodes_data = []
        for node in self.graph.nodes():
            connections = len(list(self.graph.neighbors(node)))
            nodes_data.append({
                'id': node,
                'label': node,
                'title': f"Table: {node}\\nConnections: {connections}",
                'value': max(15, connections * 4),
                'shape': 'dot',
                'font': {'size': 16, 'color': '#343434', 'bold': True},
                'borderWidth': 3,
                'color': {'background': '#97c2fc', 'border': '#2b7ce9'}
            })
        
        # エッジデータ準備
        edges_data = []
        for source, target in self.graph.edges():
            edge_attrs = self.graph.edges[source, target]
            columns_info = edge_attrs.get('columns', f"{source} -> {target}")
            
            edges_data.append({
                'from': source,
                'to': target,
                'label': columns_info,
                'title': f"Relationship: {columns_info}",
                'arrows': 'to',
                'width': 3,
                'color': {'color': '#848484', 'highlight': '#ff0000'},
                'font': {'size': 12, 'align': 'middle', 'bold': True, 'background': 'rgba(255,255,255,0.8)'},
                'smooth': {'type': 'continuous', 'roundness': 0.1}
            })
        
        # HTMLコンテンツ生成
        html_content = self._create_html_template(nodes_data, edges_data)
        
        # ファイル出力
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(html_content)
            print(f"✓ HTMLファイルを生成しました: {output_file}")
            print(f"  ファイルサイズ: {os.path.getsize(output_file):,} bytes")
        except Exception as e:
            print(f"❌ HTMLファイルの生成エラー: {e}")

    def _create_html_template(self, nodes_data, edges_data) -> str:
        """HTMLテンプレートを生成"""
        import json
        
        return f'''<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SQL Table Relationships - CSV Import</title>
    <script src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script>
    <!-- Material Icons -->
    <link href="https://fonts.googleapis.com/icon?family=Material+Icons" rel="stylesheet">
    <!-- Roboto Font -->
    <link href="https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;500;700&display=swap" rel="stylesheet">
    <style>
        * {{
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Roboto', sans-serif;
            margin: 0;
            padding: 0;
            background: #fafafa;
            min-height: 100vh;
        }}
        
        .app-bar {{
            background: #1976d2;
            color: white;
            padding: 16px 24px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.2);
            position: sticky;
            top: 0;
            z-index: 100;
        }}
        
        .app-bar h1 {{
            margin: 0;
            font-size: 20px;
            font-weight: 500;
            display: flex;
            align-items: center;
        }}
        
        .app-bar h1 .material-icons {{
            margin-right: 8px;
            font-size: 24px;
        }}
        
        .app-bar p {{
            margin: 4px 0 0 0;
            opacity: 0.9;
            font-size: 14px;
            font-weight: 300;
        }}
        
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            padding: 24px;
        }}
        
        .card {{
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            margin-bottom: 16px;
            overflow: hidden;
        }}
        
        .controls-card {{
            padding: 16px;
            position: relative;
            z-index: 1000;
        }}
        
        .controls {{
            display: flex;
            gap: 8px;
            align-items: center;
            flex-wrap: wrap;
        }}
        
        .mdc-button {{
            background: none;
            border: none;
            border-radius: 4px;
            padding: 8px 16px;
            font-family: 'Roboto', sans-serif;
            font-size: 14px;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.2s;
            display: flex;
            align-items: center;
            gap: 4px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        
        .mdc-button--raised {{
            background: #1976d2;
            color: white;
            box-shadow: 0 2px 4px rgba(0,0,0,0.2);
        }}
        
        .mdc-button--raised:hover {{
            background: #1565c0;
            box-shadow: 0 4px 8px rgba(0,0,0,0.2);
        }}
        
        .mdc-button--outlined {{
            border: 1px solid #1976d2;
            color: #1976d2;
        }}
        
        .mdc-button--outlined:hover {{
            background: rgba(25, 118, 210, 0.04);
        }}
        
        .search-container {{
            display: flex;
            align-items: center;
            margin-left: auto;
            position: relative;
        }}
        
        .search-wrapper {{
            position: relative;
            margin-left: 8px;
        }}
        
        .search-input {{
            padding: 12px 16px;
            border: 1px solid #ddd;
            border-radius: 4px;
            font-size: 14px;
            font-family: 'Roboto', sans-serif;
            width: 250px;
            outline: none;
            transition: border-color 0.2s;
        }}
        
        .search-input:focus {{
            border-color: #1976d2;
            box-shadow: 0 0 0 2px rgba(25, 118, 210, 0.2);
        }}
        
        .search-results {{
            position: fixed;
            background: white;
            border: 1px solid #ddd;
            border-radius: 4px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            max-height: 300px;
            overflow-y: auto;
            display: none;
            z-index: 10000;
            min-width: 250px;
        }}
        
        .search-result-item {{
            padding: 12px 16px;
            cursor: pointer;
            display: flex;
            align-items: center;
            border-bottom: 1px solid #f0f0f0;
            transition: background-color 0.2s;
        }}
        
        .search-result-item:hover, .search-result-item.highlighted {{
            background: #e3f2fd;
        }}
        
        .search-result-item .material-icons {{
            margin-right: 8px;
            font-size: 18px;
            color: #666;
        }}
        
        .search-no-results {{
            padding: 16px;
            text-align: center;
            color: #666;
            font-style: italic;
        }}
        
        .network-card {{
            height: 600px;
            position: relative;
        }}
        
        #network-container {{
            width: 100%;
            height: 100%;
        }}
        
        .stats-card {{
            padding: 24px;
        }}
        
        .stats {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 24px;
            text-align: center;
        }}
        
        .stat-item {{
            padding: 16px;
            background: #f8f9fa;
            border-radius: 8px;
            border-left: 4px solid #1976d2;
        }}
        
        .stat-number {{
            font-size: 32px;
            font-weight: 300;
            color: #1976d2;
            margin-bottom: 4px;
        }}
        
        .stat-label {{
            font-size: 14px;
            color: #666;
            font-weight: 500;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        
        .details-panel {{
            margin-top: 16px;
        }}
        
        .details-header {{
            background: #1976d2;
            color: white;
            padding: 16px 24px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        
        .details-header h3 {{
            margin: 0;
            font-size: 18px;
            font-weight: 500;
            display: flex;
            align-items: center;
        }}
        
        .details-header h3 .material-icons {{
            margin-right: 8px;
        }}
        
        .close-btn {{
            background: none;
            border: none;
            color: white;
            cursor: pointer;
            padding: 8px;
            border-radius: 50%;
            transition: background-color 0.2s;
        }}
        
        .close-btn:hover {{
            background: rgba(255,255,255,0.1);
        }}
        
        .close-btn .material-icons {{
            font-size: 20px;
        }}
        
        .details-content {{
            padding: 24px;
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 24px;
        }}
        
        .details-section {{
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            overflow: hidden;
        }}
        
        .section-header {{
            background: #f5f5f5;
            padding: 16px;
            border-bottom: 1px solid #e0e0e0;
        }}
        
        .section-header h4 {{
            margin: 0;
            font-size: 16px;
            font-weight: 500;
            color: #333;
            display: flex;
            align-items: center;
        }}
        
        .section-header h4 .material-icons {{
            margin-right: 8px;
            color: #1976d2;
        }}
        
        .section-content {{
            padding: 16px;
        }}
        
        .table-connection {{
            display: flex;
            align-items: center;
            padding: 12px 16px;
            margin: 8px 0;
            background: #f8f9fa;
            border-radius: 8px;
            border-left: 4px solid #1976d2;
            transition: background-color 0.2s;
        }}
        
        .table-connection:hover {{
            background: #e3f2fd;
        }}
        
        .connection-arrow {{
            margin: 0 12px;
            color: #666;
            font-weight: 500;
        }}
        
        .join-condition {{
            background: #fff3e0;
            border: 1px solid #ffcc02;
            border-radius: 8px;
            padding: 16px;
            margin: 12px 0;
            font-family: 'Roboto Mono', monospace;
            font-size: 13px;
            transition: box-shadow 0.2s;
        }}
        
        .join-condition:hover {{
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }}
        
        .condition-type {{
            font-weight: 500;
            color: #f57c00;
            margin-bottom: 8px;
            display: flex;
            align-items: center;
        }}
        
        .condition-type .material-icons {{
            margin-right: 4px;
            font-size: 16px;
        }}
        
        .info-item {{
            display: flex;
            align-items: center;
            padding: 8px 0;
            border-bottom: 1px solid #f0f0f0;
        }}
        
        .info-item:last-child {{
            border-bottom: none;
        }}
        
        .info-item .material-icons {{
            margin-right: 12px;
            color: #666;
            font-size: 18px;
        }}
        
        .info-label {{
            font-weight: 500;
            margin-right: 8px;
            color: #333;
        }}
        
        .info-value {{
            color: #666;
        }}
        
        .csv-info {{
            background: #e8f5e8;
            border: 1px solid #4caf50;
            border-radius: 8px;
            padding: 16px;
            margin-bottom: 16px;
            font-size: 14px;
        }}
        
        .csv-info .material-icons {{
            vertical-align: middle;
            margin-right: 8px;
            color: #4caf50;
        }}
    </style>
</head>
<body>
    <div class="app-bar">
        <h1>
            <span class="material-icons">table_chart</span>
            SQL Table Relationships
        </h1>
        <p>CSVファイルからインポートされた関係データの可視化</p>
    </div>

    <div class="container">
        <!-- CSV Import Info -->
        <div class="card">
            <div class="csv-info">
                <span class="material-icons">file_upload</span>
                CSVデータを正常に読み込みました - {len(self.tables)} テーブル, {len(self.relationships)} 関係
            </div>
        </div>
        
        <!-- Controls Card -->
        <div class="card controls-card">
            <div class="controls">
                <button class="mdc-button mdc-button--raised" onclick="resetView()">
                    <span class="material-icons">refresh</span>
                    Reset View
                </button>
                <button class="mdc-button mdc-button--outlined" onclick="fitNetwork()">
                    <span class="material-icons">fullscreen</span>
                    Fit All
                </button>
                <button class="mdc-button mdc-button--outlined" onclick="clearSelection()">
                    <span class="material-icons">clear</span>
                    Clear Selection
                </button>
                
                <!-- Search Container -->
                <div class="search-container">
                    <span class="material-icons" style="color: #666;">search</span>
                    <div class="search-wrapper">
                        <input type="text" 
                               id="table-search" 
                               class="search-input" 
                               placeholder="テーブル名を検索..." 
                               oninput="searchTables()"
                               onkeyup="handleSearchKeyup(event)"
                               onfocus="showSearchResults()"
                               onblur="hideSearchResults()"
                               autocomplete="off">
                        <div id="search-results" class="search-results"></div>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- Network Graph Card -->
        <div class="card network-card">
            <div id="network-container"></div>
        </div>
        
        <!-- Statistics Card -->
        <div class="card stats-card">
            <div class="stats">
                <div class="stat-item">
                    <div class="stat-number">{len(nodes_data)}</div>
                    <div class="stat-label">Tables</div>
                </div>
                <div class="stat-item">
                    <div class="stat-number">{len(edges_data)}</div>
                    <div class="stat-label">Relationships</div>
                </div>
                <div class="stat-item">
                    <div class="stat-number" id="selected-count">0</div>
                    <div class="stat-label">Selected</div>
                </div>
            </div>
        </div>
        
        <!-- Selection Details Panel -->
        <div id="selection-details" class="card details-panel" style="display: none;">
            <div class="details-header">
                <h3 id="selected-table-name">
                    <span class="material-icons">table_chart</span>
                    Selected Table
                </h3>
                <button onclick="clearSelection()" class="close-btn">
                    <span class="material-icons">close</span>
                </button>
            </div>
            <div class="details-content">
                <div class="details-section">
                    <div class="section-header">
                        <h4>
                            <span class="material-icons">info</span>
                            Basic Information
                        </h4>
                    </div>
                    <div class="section-content" id="table-info"></div>
                </div>
                <div class="details-section">
                    <div class="section-header">
                        <h4>
                            <span class="material-icons">device_hub</span>
                            Related Tables
                        </h4>
                    </div>
                    <div class="section-content" id="related-tables"></div>
                </div>
                <div class="details-section">
                    <div class="section-header">
                        <h4>
                            <span class="material-icons">link</span>
                            Join Conditions
                        </h4>
                    </div>
                    <div class="section-content" id="join-conditions"></div>
                </div>
            </div>
        </div>
    </div>

    <script>
        // Data
        const nodes = new vis.DataSet({json.dumps(nodes_data, ensure_ascii=False, indent=2)});
        const edges = new vis.DataSet({json.dumps(edges_data, ensure_ascii=False, indent=2)});
        
        // Configuration
        const options = {{
            layout: {{
                hierarchical: {{
                    enabled: true,
                    direction: 'UD',
                    sortMethod: 'directed',
                    levelSeparation: 150,
                    nodeSpacing: 200
                }}
            }},
            physics: {{
                enabled: false
            }},
            interaction: {{
                hover: true,
                selectConnectedEdges: true,
                tooltipDelay: 200
            }},
            nodes: {{
                borderWidth: 3,
                shadow: true,
                font: {{ size: 16, color: '#343434', bold: true }}
            }},
            edges: {{
                shadow: true,
                width: 3,
                font: {{ size: 12, bold: true, background: 'rgba(255,255,255,0.8)' }},
                smooth: {{
                    type: 'continuous',
                    roundness: 0.1
                }}
            }}
        }};
        
        // Network
        const container = document.getElementById('network-container');
        const data = {{ nodes: nodes, edges: edges }};
        const network = new vis.Network(container, data, options);
        
        // Global variables for search
        let allTables = [];
        let currentSearchResults = [];
        
        // Initialize search functionality
        function initializeSearch() {{
            try {{
                allTables = nodes.get().map(node => node.id).sort();
                console.log('Search initialized with tables:', allTables.length);
            }} catch (error) {{
                console.error('Error initializing search:', error);
                allTables = [];
            }}
        }}
        
        // Wait for network to be fully loaded before initializing search
        network.once('afterDrawing', function() {{
            console.log('Network drawing completed, initializing search...');
            initializeSearch();
        }});
        
        // Event listeners for node selection
        network.on('select', function(params) {{
            const selectedNodes = params.nodes;
            const selectedEdges = params.edges;
            
            document.getElementById('selected-count').textContent = selectedNodes.length + selectedEdges.length;
            
            if (selectedNodes.length === 1) {{
                showNodeDetails(selectedNodes[0]);
            }} else {{
                hideNodeDetails();
            }}
        }});
        
        network.on('deselectNode', function(params) {{
            hideNodeDetails();
        }});
        
        // Control functions
        function resetView() {{
            network.unselectAll();
            hideNodeDetails();
            document.getElementById('selected-count').textContent = '0';
            network.setOptions({{
                layout: {{
                    hierarchical: {{
                        enabled: true,
                        direction: 'UD',
                        sortMethod: 'directed',
                        levelSeparation: 150,
                        nodeSpacing: 200,
                        treeSpacing: 200
                    }}
                }},
                physics: {{
                    enabled: false
                }}
            }});
            network.fit();
        }}
        
        function fitNetwork() {{
            network.fit();
        }}
        
        function clearSelection() {{
            network.unselectAll();
            hideNodeDetails();
            document.getElementById('selected-count').textContent = '0';
        }}
        
        // Search functionality
        function handleSearchKeyup(event) {{
            if (['ArrowDown', 'ArrowUp', 'Enter', 'Escape'].includes(event.key)) {{
                return;
            }}
            searchTables();
        }}
        
        function positionSearchResults() {{
            const searchInput = document.getElementById('table-search');
            const searchResults = document.getElementById('search-results');
            const rect = searchInput.getBoundingClientRect();
            
            searchResults.style.top = (rect.bottom + window.scrollY) + 'px';
            searchResults.style.left = rect.left + 'px';
            searchResults.style.width = rect.width + 'px';
        }}
        
        function searchTables() {{
            const searchInput = document.getElementById('table-search');
            const searchResults = document.getElementById('search-results');
            const query = searchInput.value.toLowerCase().trim();
            
            if (!allTables || allTables.length === 0) {{
                initializeSearch();
                if (!allTables || allTables.length === 0) {{
                    return;
                }}
            }}
            
            if (query === '') {{
                searchResults.style.display = 'none';
                currentSearchResults = [];
                return;
            }}
            
            currentSearchResults = allTables.filter(table => 
                table.toLowerCase().includes(query)
            ).sort();
            
            if (currentSearchResults.length > 0) {{
                const maxResults = Math.min(currentSearchResults.length, 15);
                searchResults.innerHTML = currentSearchResults
                    .slice(0, maxResults)
                    .map((table, index) => {{
                        const highlightedText = table.replace(
                            new RegExp(`(${{query}})`, 'gi'), 
                            '<span style="background-color: #fff3cd; font-weight: bold;">$1</span>'
                        );
                        return `
                            <div class="search-result-item" 
                                 onclick="selectTable('${{table}}')" 
                                 onmousedown="event.preventDefault()">
                                <span class="material-icons">table_chart</span>
                                <span>${{highlightedText}}</span>
                            </div>
                        `;
                    }}).join('');
                
                if (currentSearchResults.length > maxResults) {{
                    searchResults.innerHTML += `
                        <div class="search-no-results">
                            他 ${{currentSearchResults.length - maxResults}} 件のテーブルが見つかりました
                        </div>
                    `;
                }}
                
                positionSearchResults();
                searchResults.style.display = 'block';
            }} else {{
                searchResults.innerHTML = `
                    <div class="search-no-results">
                        <span class="material-icons">search_off</span>
                        "${{query}}" に一致するテーブルが見つかりませんでした
                    </div>
                `;
                positionSearchResults();
                searchResults.style.display = 'block';
            }}
        }}
        
        function selectTable(tableName) {{
            network.unselectAll();
            
            if (!allTables || !allTables.includes(tableName)) {{
                return;
            }}
            
            network.selectNodes([tableName]);
            network.focus(tableName, {{
                scale: 2.0,
                offset: {{x: 0, y: 0}},
                animation: {{
                    duration: 1500,
                    easingFunction: 'easeInOutCubic'
                }}
            }});
            
            showNodeDetails(tableName);
            document.getElementById('selected-count').textContent = '1';
            
            const searchInput = document.getElementById('table-search');
            searchInput.value = '';
            searchInput.blur();
            document.getElementById('search-results').style.display = 'none';
        }}
        
        function showSearchResults() {{
            const searchInput = document.getElementById('table-search');
            if (searchInput.value.trim() !== '') {{
                positionSearchResults();
                searchTables();
            }}
        }}
        
        function hideSearchResults() {{
            setTimeout(() => {{
                const searchResults = document.getElementById('search-results');
                if (searchResults && document.activeElement.id !== 'table-search') {{
                    searchResults.style.display = 'none';
                }}
            }}, 200);
        }}
        
        function showNodeDetails(nodeId) {{
            const detailsPanel = document.getElementById('selection-details');
            const tableName = document.getElementById('selected-table-name');
            const tableInfo = document.getElementById('table-info');
            const relatedTables = document.getElementById('related-tables');
            const joinConditions = document.getElementById('join-conditions');
            
            tableName.innerHTML = `
                <span class="material-icons">table_chart</span>
                ${{nodeId}} Table
            `;
            
            const nodeData = nodes.get(nodeId);
            const connections = network.getConnectedNodes(nodeId);
            tableInfo.innerHTML = `
                <div class="info-item">
                    <span class="material-icons">storage</span>
                    <span class="info-label">Table Name:</span>
                    <span class="info-value">${{nodeId}}</span>
                </div>
                <div class="info-item">
                    <span class="material-icons">hub</span>
                    <span class="info-label">Connections:</span>
                    <span class="info-value">${{connections.length}} tables</span>
                </div>
            `;
            
            let relatedHtml = '';
            if (connections.length > 0) {{
                connections.forEach(connectedNodeId => {{
                    relatedHtml += `
                        <div class="table-connection">
                            <span>${{nodeId}}</span>
                            <span class="connection-arrow">⟷</span>
                            <span>${{connectedNodeId}}</span>
                        </div>
                    `;
                }});
            }} else {{
                relatedHtml = '<div class="table-connection">No related tables found</div>';
            }}
            relatedTables.innerHTML = relatedHtml;
            
            // Join conditions with grouping
            let conditionsHtml = '';
            const connectedEdgeIds = network.getConnectedEdges(nodeId);
            if (connectedEdgeIds.length > 0) {{
                const tableRelationships = {{}};
                
                connectedEdgeIds.forEach(edgeId => {{
                    const edge = edges.get(edgeId);
                    const isFromNode = edge.from === nodeId;
                    const otherTable = isFromNode ? edge.to : edge.from;
                    
                    if (!tableRelationships[otherTable]) {{
                        tableRelationships[otherTable] = [];
                    }}
                    
                    const relationshipsList = edge.label.split(';').map(rel => rel.trim());
                    relationshipsList.forEach(relationship => {{
                        if (relationship && !tableRelationships[otherTable].includes(relationship)) {{
                            tableRelationships[otherTable].push(relationship);
                        }}
                    }});
                }});
                
                Object.keys(tableRelationships).forEach(otherTable => {{
                    const conditions = tableRelationships[otherTable];
                    const isMultiColumn = conditions.length > 1;
                    
                    const columnCountText = isMultiColumn ? `<span style="color: #ff9800; font-size: 12px; margin-left: 8px;">(` + conditions.length + ` columns)</span>` : '';
                    const joinConditionsText = conditions.join('<br>');
                    
                    conditionsHtml += `
                        <div class="join-condition">
                            <div class="condition-type">
                                <span class="material-icons">link</span>
                                ${{nodeId}} ⟷ ${{otherTable}}
                                ${{columnCountText}}
                            </div>
                            <div style="font-family: 'Roboto Mono', monospace; font-size: 13px; color: #424242;">
                                ${{joinConditionsText}}
                            </div>
                        </div>
                    `;
                }});
            }} else {{
                conditionsHtml = '<div class="join-condition">No join conditions found</div>';
            }}
            joinConditions.innerHTML = conditionsHtml;
            
            detailsPanel.style.display = 'block';
            detailsPanel.scrollIntoView({{ behavior: 'smooth', block: 'start' }});
        }}
        
        function hideNodeDetails() {{
            document.getElementById('selection-details').style.display = 'none';
        }}
        
        // Initial fit
        network.once('stabilizationIterationsDone', function() {{
            network.fit();
        }});
        
        // Handle window resize
        window.addEventListener('resize', function() {{
            const searchResults = document.getElementById('search-results');
            if (searchResults && searchResults.style.display === 'block') {{
                positionSearchResults();
            }}
        }});
    </script>
</body>
</html>'''


def main():
    """メイン関数"""
    parser = argparse.ArgumentParser(
        description='CSVファイルからインタラクティブHTMLを生成',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
使用例:
  python csv_to_html.py input.csv output.html
  python csv_to_html.py output/relationships.csv result.html
  python csv_to_html.py data.csv --output interactive_graph.html
        '''
    )
    
    parser.add_argument('csv_file', help='入力CSVファイルパス')
    parser.add_argument('output_file', nargs='?', help='出力HTMLファイルパス')
    parser.add_argument('-o', '--output', help='出力HTMLファイルパス（オプション形式）')
    
    args = parser.parse_args()
    
    # 出力ファイル名の決定
    if args.output_file:
        output_file = args.output_file
    elif args.output:
        output_file = args.output
    else:
        # デフォルト出力ファイル名を生成
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"csv_visualization_{timestamp}.html"
    
    # CSVファイルの存在チェック
    if not os.path.exists(args.csv_file):
        print(f"❌ CSVファイルが見つかりません: {args.csv_file}")
        sys.exit(1)
    
    print("🚀 CSV to HTML Converter")
    print("=" * 50)
    print(f"📁 入力ファイル: {args.csv_file}")
    print(f"📄 出力ファイル: {output_file}")
    print()
    
    # 変換実行
    converter = CSVToHTMLConverter()
    converter.load_csv(args.csv_file)
    converter.generate_html(output_file)
    
    print()
    print("🎉 変換完了!")
    print(f"📂 ブラウザで {output_file} を開いて確認してください")


if __name__ == "__main__":
    main()