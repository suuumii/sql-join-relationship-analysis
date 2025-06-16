#!/usr/bin/env python3
"""
フォルダ内SQLファイル一括解析の非対話型デモ
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from folder_analyzer import FolderSQLAnalyzer

def create_sample_files():
    """サンプルSQLファイルを作成"""
    
    # サンプルフォルダとファイル定義
    sample_data = {
        "demo_queries/ecommerce": [
            ("users_orders.sql", """
                SELECT u.username, u.email, COUNT(o.order_id) as order_count
                FROM users u
                LEFT JOIN orders o ON u.user_id = o.user_id
                WHERE u.created_at >= '2023-01-01'
                GROUP BY u.user_id
            """),
            
            ("products_categories.sql", """
                SELECT p.product_name, p.price, c.category_name
                FROM products p
                JOIN categories c ON p.category_id = c.category_id
                WHERE p.active = 1
                ORDER BY c.category_name, p.product_name
            """),
            
            ("order_details.sql", """
                SELECT o.order_id, c.customer_name, p.product_name, oi.quantity
                FROM orders o, customers c, order_items oi, products p
                WHERE o.customer_id = c.customer_id
                AND o.order_id = oi.order_id  
                AND oi.product_id = p.product_id
                AND o.status = 'completed'
            """)
        ],
        
        "demo_queries/hr": [
            ("employee_dept.sql", """
                SELECT e.employee_name, d.department_name, e.salary
                FROM employees e
                JOIN departments d USING (department_id)
                WHERE e.status = 'active'
            """),
            
            ("manager_hierarchy.sql", """
                SELECT emp.employee_name, mgr.employee_name as manager_name
                FROM employees emp
                LEFT JOIN employees mgr ON emp.manager_id = mgr.employee_id
                ORDER BY mgr.employee_name, emp.employee_name
            """)
        ],
        
        "demo_queries/analytics": [
            ("user_engagement.sql", """
                SELECT u.username, 
                       COUNT(p.post_id) as posts,
                       COUNT(c.comment_id) as comments,
                       COUNT(l.like_id) as likes
                FROM users u
                LEFT JOIN posts p ON u.user_id = p.author_id
                LEFT JOIN comments c ON u.user_id = c.user_id
                LEFT JOIN likes l ON u.user_id = l.user_id
                GROUP BY u.user_id
            """)
        ]
    }
    
    print("=== サンプルSQLファイル作成 ===")
    total_files = 0
    
    for folder_path, files in sample_data.items():
        os.makedirs(folder_path, exist_ok=True)
        print(f"\nフォルダ: {folder_path}")
        
        for filename, sql_content in files:
            file_path = os.path.join(folder_path, filename)
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(sql_content.strip())
            print(f"  ✓ {filename}")
            total_files += 1
    
    print(f"\n合計 {total_files} ファイルを作成しました")
    return list(sample_data.keys())

def demo_single_folder():
    """単一フォルダ解析デモ"""
    print(f"\n{'='*60}")
    print("🗂️  単一フォルダ解析デモ")
    print("="*60)
    
    analyzer = FolderSQLAnalyzer()
    
    folder_path = "demo_queries/ecommerce"
    print(f"解析対象: {folder_path}")
    
    results = analyzer.analyze_folder(folder_path)
    
    if results:
        analyzer.export_results(prefix="ecommerce_demo")
        
        print(f"\n📊 解析結果:")
        print(f"  ファイル数: {results['stats']['total_files']}")
        print(f"  関係数: {results['stats']['total_relationships']}")
        print(f"  テーブル数: {results['stats']['total_tables']}")
        print(f"  テーブル: {', '.join(results['tables'])}")

def demo_recursive_analysis():
    """再帰的解析デモ"""
    print(f"\n{'='*60}")
    print("🔍 再帰的フォルダ解析デモ")
    print("="*60)
    
    analyzer = FolderSQLAnalyzer()
    
    root_path = "demo_queries"
    print(f"解析対象: {root_path}/ (全サブフォルダ)")
    
    results = analyzer.analyze_with_subdirectories(root_path)
    
    if results:
        analyzer.export_results(prefix="recursive_demo")
        
        print(f"\n📈 統合解析結果:")
        print(f"  総ファイル数: {results['total_files']}")
        print(f"  統合関係数: {len(results['all_relationships'])}")
        
        # 関係の詳細表示
        print(f"\n🔗 発見された関係:")
        for i, rel in enumerate(results['all_relationships'][:10], 1):  # 最初の10件のみ
            if rel['table1'] and rel['table2']:
                print(f"  {i:2d}. {rel['table1']}.{rel['column1']} -> {rel['table2']}.{rel['column2']}")
        
        if len(results['all_relationships']) > 10:
            print(f"  ... 他 {len(results['all_relationships']) - 10} 件")

def demo_file_analysis():
    """ファイル別解析詳細"""
    print(f"\n{'='*60}")
    print("📄 ファイル別解析詳細")
    print("="*60)
    
    analyzer = FolderSQLAnalyzer()
    
    # 個別ファイル解析
    hr_folder = "demo_queries/hr"
    results = analyzer.analyze_folder(hr_folder)
    
    if results and 'file_results' in results:
        print(f"\n{hr_folder} フォルダの詳細:")
        
        for file_path, file_data in results['file_results'].items():
            filename = os.path.basename(file_path)
            relationships = file_data['relationships']
            
            print(f"\n📝 {filename}:")
            print(f"   SQL: {file_data['sql'][:80]}...")
            print(f"   関係数: {len(relationships)}")
            
            for rel in relationships:
                if rel['table1'] and rel['table2']:
                    print(f"     • {rel['table1']}.{rel['column1']} -> {rel['table2']}.{rel['column2']}")

def demo_output_files():
    """出力ファイル確認"""
    print(f"\n{'='*60}")
    print("📂 生成された出力ファイル")
    print("="*60)
    
    output_patterns = [
        "ecommerce_demo_*.csv",
        "ecommerce_demo_*.png", 
        "ecommerce_demo_*.txt",
        "recursive_demo_*.csv",
        "recursive_demo_*.png",
        "recursive_demo_*.txt"
    ]
    
    import glob
    
    found_files = []
    for pattern in output_patterns:
        files = glob.glob(os.path.join("output", pattern))
        found_files.extend(files)
    
    if found_files:
        print("✅ 以下のファイルが生成されました:")
        for file_path in sorted(found_files):
            file_size = os.path.getsize(file_path)
            print(f"   {file_path} ({file_size:,} bytes)")
    else:
        print("❌ 出力ファイルが見つかりませんでした")

def cleanup():
    """サンプルファイルの削除"""
    print(f"\n{'='*60}")
    print("🧹 クリーンアップ")
    print("="*60)
    
    try:
        import shutil
        if os.path.exists("demo_queries"):
            shutil.rmtree("demo_queries")
            print("✅ サンプルフォルダを削除しました")
        else:
            print("ℹ️  削除するサンプルフォルダがありません")
    except Exception as e:
        print(f"❌ 削除エラー: {e}")

def main():
    """メイン実行"""
    print("🎯 フォルダ内SQLファイル一括解析デモ")
    print("="*60)
    
    try:
        # サンプルファイル作成
        create_sample_files()
        
        # 各種デモ実行
        demo_single_folder()
        demo_recursive_analysis()
        demo_file_analysis()
        demo_output_files()
        
        print(f"\n{'='*60}")
        print("🎉 デモ完了!")
        print("="*60)
        print("📋 主な機能:")
        print("  ✓ 単一フォルダ内の全SQLファイル解析")
        print("  ✓ サブフォルダを含む再帰的解析")
        print("  ✓ ファイル別詳細解析")
        print("  ✓ 統合関係の抽出")
        print("  ✓ CSV/グラフ/サマリー出力")
        
    finally:
        # クリーンアップ
        cleanup()

if __name__ == "__main__":
    main()