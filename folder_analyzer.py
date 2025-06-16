#!/usr/bin/env python3
"""
フォルダ内のSQLファイルを一括解析するツール
"""

import os
import glob
from sql_join_analyzer import SQLJoinAnalyzer

class FolderSQLAnalyzer:
    def __init__(self):
        self.analyzer = SQLJoinAnalyzer()
        self.sql_files = []
        self.all_relationships = []
    
    def analyze_folder(self, folder_path: str, pattern: str = "*.sql"):
        """
        フォルダ内のSQLファイルを一括解析
        
        Args:
            folder_path: SQLファイルが格納されているフォルダパス
            pattern: ファイルパターン（デフォルト: *.sql）
        
        Returns:
            解析結果のリスト
        """
        print(f"=== フォルダ解析開始: {folder_path} ===")
        
        # フォルダの存在確認
        if not os.path.exists(folder_path):
            print(f"エラー: フォルダが見つかりません: {folder_path}")
            return []
        
        # SQLファイルを検索
        search_pattern = os.path.join(folder_path, pattern)
        self.sql_files = glob.glob(search_pattern)
        
        if not self.sql_files:
            print(f"警告: {pattern} ファイルが見つかりません: {folder_path}")
            return []
        
        print(f"発見したSQLファイル数: {len(self.sql_files)}")
        
        # 各ファイルを解析
        file_results = {}
        all_queries = []
        
        for sql_file in sorted(self.sql_files):
            print(f"\n--- 解析中: {os.path.basename(sql_file)} ---")
            
            try:
                # ファイル読み込み
                with open(sql_file, 'r', encoding='utf-8') as f:
                    sql_content = f.read().strip()
                
                if not sql_content:
                    print(f"スキップ: 空ファイル {sql_file}")
                    continue
                
                print(f"SQL内容:")
                print(sql_content[:200] + ("..." if len(sql_content) > 200 else ""))
                
                # クエリ解析
                relationships = self.analyzer.analyze_sql(sql_content)
                file_results[sql_file] = {
                    'sql': sql_content,
                    'relationships': relationships
                }
                all_queries.append(sql_content)
                
                print(f"関係数: {len(relationships)}")
                for rel in relationships:
                    if rel['table1'] and rel['table2']:
                        print(f"  {rel['table1']}.{rel['column1']} -> {rel['table2']}.{rel['column2']}")
                
            except Exception as e:
                print(f"エラー: ファイル読み込み失敗 {sql_file}: {e}")
                continue
        
        # 統合解析
        print(f"\n=== 統合解析 ===")
        self.all_relationships = self.analyzer.analyze_multiple_queries(all_queries)
        
        print(f"総ファイル数: {len(file_results)}")
        print(f"統合関係数: {len(self.all_relationships)}")
        
        # テーブル統計
        tables = set()
        for rel in self.all_relationships:
            if rel['table1']:
                tables.add(rel['table1'])
            if rel['table2']:
                tables.add(rel['table2'])
        
        print(f"検出テーブル数: {len(tables)}")
        print(f"テーブル一覧: {', '.join(sorted(tables))}")
        
        return {
            'file_results': file_results,
            'combined_relationships': self.all_relationships,
            'tables': sorted(tables),
            'stats': {
                'total_files': len(file_results),
                'total_relationships': len(self.all_relationships),
                'total_tables': len(tables)
            }
        }
    
    def export_results(self, output_dir: str = "output", prefix: str = "folder_analysis"):
        """
        解析結果をエクスポート
        
        Args:
            output_dir: 出力ディレクトリ
            prefix: ファイル名プリフィックス
        """
        os.makedirs(output_dir, exist_ok=True)
        
        # CSV出力
        csv_file = os.path.join(output_dir, f"{prefix}_relationships.csv")
        self.analyzer.export_to_csv(csv_file)
        print(f"CSV出力: {csv_file}")
        
        # グラフ出力
        try:
            graph_file = os.path.join(output_dir, f"{prefix}_graph.png")
            self.analyzer.generate_graph_visualization(graph_file)
            print(f"グラフ出力: {graph_file}")
        except Exception as e:
            print(f"グラフ生成エラー: {e}")
        
        # サマリー出力
        summary_file = os.path.join(output_dir, f"{prefix}_summary.txt")
        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write("=== SQL フォルダ解析サマリー ===\n\n")
            
            f.write(f"解析ファイル数: {len(self.sql_files)}\n")
            f.write(f"総関係数: {len(self.all_relationships)}\n\n")
            
            f.write("=== 検出された関係 ===\n")
            for i, rel in enumerate(self.all_relationships, 1):
                if rel['table1'] and rel['table2']:
                    f.write(f"{i:3d}. {rel['table1']}.{rel['column1']} ({rel['column_definition1']}) -> "
                           f"{rel['table2']}.{rel['column2']} ({rel['column_definition2']})\n")
            
            f.write(f"\n=== 解析ファイル一覧 ===\n")
            for sql_file in sorted(self.sql_files):
                f.write(f"- {os.path.basename(sql_file)}\n")
        
        print(f"サマリー出力: {summary_file}")
    
    def analyze_with_subdirectories(self, root_path: str):
        """
        サブディレクトリも含めて再帰的に解析
        
        Args:
            root_path: ルートディレクトリパス
        """
        print(f"=== 再帰的フォルダ解析: {root_path} ===")
        
        all_sql_files = []
        
        # 再帰的にSQLファイルを検索
        for root, _, files in os.walk(root_path):
            for file in files:
                if file.endswith('.sql'):
                    full_path = os.path.join(root, file)
                    all_sql_files.append(full_path)
        
        if not all_sql_files:
            print(f"SQLファイルが見つかりません: {root_path}")
            return {}
        
        print(f"発見したSQLファイル数: {len(all_sql_files)}")
        
        # ディレクトリ別に整理
        dir_files = {}
        for sql_file in all_sql_files:
            dir_name = os.path.dirname(sql_file)
            if dir_name not in dir_files:
                dir_files[dir_name] = []
            dir_files[dir_name].append(sql_file)
        
        print(f"ディレクトリ数: {len(dir_files)}")
        
        # 各ディレクトリを解析
        all_queries = []
        results_by_dir = {}
        
        for dir_path, files in dir_files.items():
            print(f"\n--- ディレクトリ: {dir_path} ({len(files)} ファイル) ---")
            
            dir_queries = []
            for sql_file in sorted(files):
                try:
                    with open(sql_file, 'r', encoding='utf-8') as f:
                        sql_content = f.read().strip()
                    
                    if sql_content:
                        relationships = self.analyzer.analyze_sql(sql_content)
                        dir_queries.append(sql_content)
                        all_queries.append(sql_content)
                        print(f"  {os.path.basename(sql_file)}: {len(relationships)} 関係")
                
                except Exception as e:
                    print(f"  エラー {os.path.basename(sql_file)}: {e}")
            
            results_by_dir[dir_path] = dir_queries
        
        # 統合解析
        print(f"\n=== 全体統合解析 ===")
        self.all_relationships = self.analyzer.analyze_multiple_queries(all_queries)
        
        print(f"総クエリ数: {len(all_queries)}")
        print(f"統合関係数: {len(self.all_relationships)}")
        
        return {
            'results_by_dir': results_by_dir,
            'all_relationships': self.all_relationships,
            'total_files': len(all_sql_files)
        }


def main():
    """メイン処理 - 使用例"""
    analyzer = FolderSQLAnalyzer()
    
    # 使用例1: 単一フォルダ解析
    print("使用例を実行するには、SQLファイルが格納されたフォルダパスを指定してください\n")
    
    # サンプルフォルダ作成（デモ用）
    sample_dir = "sample_sql_queries"
    os.makedirs(sample_dir, exist_ok=True)
    
    # サンプルSQLファイル作成
    sample_queries = {
        "users_posts.sql": """
            SELECT u.username, p.title, p.content
            FROM users u
            INNER JOIN posts p ON u.user_id = p.user_id
            WHERE u.status = 'active'
        """,
        
        "orders_customers.sql": """
            SELECT o.order_id, c.customer_name, o.total_amount
            FROM orders o, customers c
            WHERE o.customer_id = c.customer_id
            AND o.order_date >= '2023-01-01'
        """,
        
        "employees_departments.sql": """
            SELECT e.employee_name, d.department_name, e.salary
            FROM employees e
            JOIN departments d USING (department_id)
            ORDER BY e.salary DESC
        """
    }
    
    # サンプルファイル作成
    for filename, sql_content in sample_queries.items():
        file_path = os.path.join(sample_dir, filename)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(sql_content.strip())
    
    print(f"サンプルSQLファイルを作成しました: {sample_dir}/")
    print("解析を開始します...\n")
    
    # フォルダ解析実行
    analyzer.analyze_folder(sample_dir)
    
    # 結果エクスポート
    analyzer.export_results(prefix="sample_folder")
    
    print(f"\n=== 解析完了 ===")
    print(f"結果ファイル:")
    print(f"- output/sample_folder_relationships.csv")
    print(f"- output/sample_folder_graph.png") 
    print(f"- output/sample_folder_summary.txt")


if __name__ == "__main__":
    main()