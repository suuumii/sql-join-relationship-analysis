#!/usr/bin/env python3
"""
SQLJoinAnalyzerの詳細テストとデバッグ
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import traceback
import json
from sql_join_analyzer import SQLJoinAnalyzer
from test_queries import ALL_TEST_QUERIES, get_all_valid_queries

def debug_single_query(analyzer, query, query_name=""):
    """単一クエリの詳細デバッグ"""
    print(f"\n{'='*60}")
    print(f"デバッグ: {query_name}")
    print(f"{'='*60}")
    print("SQL:")
    print(query.strip())
    print(f"\n{'-'*40}")
    
    try:
        relationships = analyzer.analyze_sql(query)
        
        print(f"関係数: {len(relationships)}")
        
        if relationships:
            print("\n発見された関係:")
            for i, rel in enumerate(relationships, 1):
                print(f"  {i}. {rel['table1']}.{rel['column1']} ({rel['column_definition1']})")
                print(f"     -> {rel['table2']}.{rel['column2']} ({rel['column_definition2']})")
        else:
            print("関係が見つかりませんでした")
        
        # テーブル情報
        if hasattr(analyzer, 'tables') and analyzer.tables:
            print(f"\n検出されたテーブル: {', '.join(sorted(analyzer.tables))}")
        
        return True, relationships
        
    except Exception as e:
        print(f"エラー: {e}")
        print(f"詳細: {traceback.format_exc()}")
        return False, []

def test_category(analyzer, category_name, queries):
    """カテゴリ別テスト"""
    print(f"\n{'#'*50}")
    print(f"# カテゴリテスト: {category_name}")
    print(f"{'#'*50}")
    
    success_count = 0
    total_relationships = 0
    
    for i, query in enumerate(queries, 1):
        success, relationships = debug_single_query(
            analyzer, query, f"{category_name} #{i}"
        )
        
        if success:
            success_count += 1
            total_relationships += len(relationships)
    
    print(f"\n=== {category_name} 結果 ===")
    print(f"成功: {success_count}/{len(queries)}")
    print(f"総関係数: {total_relationships}")
    
    return success_count, total_relationships

def comprehensive_test():
    """包括的テスト"""
    print("SQLJoinAnalyzer 包括テスト開始")
    
    analyzer = SQLJoinAnalyzer()
    
    total_success = 0
    total_queries = 0
    all_relationships = 0
    
    # カテゴリ別テスト
    for category, queries in ALL_TEST_QUERIES.items():
        if not queries:  # 空のカテゴリをスキップ
            continue
            
        success, relationships = test_category(analyzer, category, queries)
        total_success += success
        total_queries += len(queries)
        all_relationships += relationships
    
    # 統合テスト
    print(f"\n{'#'*50}")
    print("# 統合テスト")
    print(f"{'#'*50}")
    
    try:
        # 全有効クエリを統合解析
        valid_queries = get_all_valid_queries()
        print(f"統合解析: {len(valid_queries)} クエリ")
        
        combined_relationships = analyzer.analyze_multiple_queries(valid_queries)
        
        print(f"統合関係数: {len(combined_relationships)}")
        
        # CSV出力テスト
        csv_file = "debug_test_output.csv"
        analyzer.export_to_csv(csv_file)
        print(f"CSV出力: {csv_file}")
        
        # グラフ生成テスト（エラーハンドリング付き）
        try:
            graph_file = "debug_test_graph.png"
            analyzer.generate_graph_visualization(graph_file)
            print(f"グラフ生成: {graph_file}")
        except Exception as e:
            print(f"グラフ生成エラー: {e}")
        
    except Exception as e:
        print(f"統合テストエラー: {e}")
        print(traceback.format_exc())
    
    # 最終結果
    print(f"\n{'='*60}")
    print("最終テスト結果")
    print(f"{'='*60}")
    print(f"成功率: {total_success}/{total_queries} ({total_success/total_queries*100:.1f}%)")
    print(f"総関係数: {all_relationships}")

def test_specific_cases():
    """特定ケースの詳細テスト"""
    print("\n特定ケースのテスト")
    
    analyzer = SQLJoinAnalyzer()
    
    # 外部キー推測のテスト
    test_cases = [
        {
            'name': '基本的な外部キー',
            'sql': """
            SELECT u.name, p.title
            FROM users u
            JOIN posts p ON u.id = p.user_id
            """
        },
        {
            'name': 'USING句',
            'sql': """
            SELECT e.name, d.name
            FROM employees e
            JOIN departments d USING (department_id)
            """
        },
        {
            'name': 'FROM複数テーブル',
            'sql': """
            SELECT o.id, c.name
            FROM orders o, customers c
            WHERE o.customer_id = c.id
            """
        },
        {
            'name': 'NATURAL JOIN',
            'sql': """
            SELECT *
            FROM employees
            NATURAL JOIN departments
            """
        },
        {
            'name': 'サブクエリJOIN',
            'sql': """
            SELECT u.name, stats.count
            FROM users u
            JOIN (
                SELECT user_id, COUNT(*) as count
                FROM posts p
                JOIN categories c ON p.category_id = c.id
                GROUP BY user_id
            ) stats ON u.id = stats.user_id
            """
        }
    ]
    
    for case in test_cases:
        debug_single_query(analyzer, case['sql'], case['name'])

def validate_output_format():
    """出力形式の検証"""
    print(f"\n{'#'*50}")
    print("# 出力形式検証")
    print(f"{'#'*50}")
    
    analyzer = SQLJoinAnalyzer()
    
    # サンプルクエリで関係を生成
    sample_sql = """
    SELECT u.name, p.title, c.name
    FROM users u
    JOIN posts p ON u.id = p.user_id
    JOIN categories c ON p.category_id = c.id
    """
    
    relationships = analyzer.analyze_sql(sample_sql)
    
    print("サンプル関係データ:")
    for rel in relationships:
        print(json.dumps(rel, indent=2, ensure_ascii=False))
    
    # CSV出力検証
    csv_file = "format_test.csv"
    analyzer.export_to_csv(csv_file)
    
    # CSV内容を読み込んで表示
    try:
        with open(csv_file, 'r', encoding='utf-8') as f:
            content = f.read()
        print(f"\nCSV出力内容 ({csv_file}):")
        print(content)
    except Exception as e:
        print(f"CSV読み込みエラー: {e}")

if __name__ == "__main__":
    print("デバッグテスト開始")
    
    # 特定ケースのテスト
    test_specific_cases()
    
    # 出力形式検証
    validate_output_format()
    
    # 包括的テスト
    comprehensive_test()
    
    print("\nデバッグテスト完了")