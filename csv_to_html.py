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
        
        # HTMLコンテンツ生成 - 共有テンプレートジェネレーターを使用
        from lib.html_generator import HTMLTemplateGenerator
        html_generator = HTMLTemplateGenerator()
        
        # データソース情報を生成
        source_info = f"CSVデータを正常に読み込みました - {len(self.tables)} テーブル, {len(self.relationships)} 関係"
        
        html_content = html_generator.create_html_template(
            nodes_data=nodes_data,
            edges_data=edges_data,
            title="SQL Table Relationships - CSV Import",
            subtitle="CSVファイルからインポートされた関係データの可視化",
            source_info=source_info
        )
        
        # ファイル出力
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(html_content)
            print(f"✓ HTMLファイルを生成しました: {output_file}")
            print(f"  ファイルサイズ: {os.path.getsize(output_file):,} bytes")
        except Exception as e:
            print(f"❌ HTMLファイルの生成エラー: {e}")



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