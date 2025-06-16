#!/usr/bin/env python3
"""
inputフォルダ内のSQLファイルを解析してoutputフォルダに結果を出力する
"""

import os
import sys
from datetime import datetime
from lib.folder_analyzer import FolderSQLAnalyzer

def main():
    """メイン実行関数"""
    print("🎯 Input フォルダSQL解析ツール")
    print("=" * 50)
    
    # フォルダパス設定
    input_folder = "input"
    output_folder = "output"
    
    # フォルダの存在確認
    if not os.path.exists(input_folder):
        print(f"❌ エラー: {input_folder} フォルダが見つかりません")
        print(f"💡 {input_folder} フォルダを作成し、SQLファイルを配置してください")
        return False
    
    # outputフォルダ作成
    os.makedirs(output_folder, exist_ok=True)
    print(f"📁 出力フォルダ: {output_folder}")
    
    # 解析器初期化
    analyzer = FolderSQLAnalyzer()
    
    # 解析実行
    print(f"\n🔍 {input_folder} フォルダの解析を開始...")
    results = analyzer.analyze_folder(input_folder)
    
    if not results:
        print(f"❌ {input_folder} フォルダにSQLファイルが見つかりませんでした")
        return False
    
    # 結果表示
    stats = results['stats']
    print(f"\n📊 解析結果:")
    print(f"  ✓ SQLファイル数: {stats['total_files']}")
    print(f"  ✓ 検出関係数: {stats['total_relationships']}")
    print(f"  ✓ 関連テーブル数: {stats['total_tables']}")
    
    # テーブル一覧表示（最初の10個）
    tables = results['tables']
    if tables:
        print(f"\n📋 検出されたテーブル:")
        display_tables = tables[:10]
        for i, table in enumerate(display_tables, 1):
            print(f"  {i:2d}. {table}")
        
        if len(tables) > 10:
            print(f"  ... 他 {len(tables) - 10} テーブル")
    
    # 関係の詳細表示（最初の10個）
    relationships = results['combined_relationships']
    if relationships:
        print(f"\n🔗 発見された関係（上位10件）:")
        display_rels = relationships[:10]
        for i, rel in enumerate(display_rels, 1):
            if rel['table1'] and rel['table2']:
                print(f"  {i:2d}. {rel['table1']}.{rel['column1']} -> {rel['table2']}.{rel['column2']}")
        
        if len(relationships) > 10:
            print(f"  ... 他 {len(relationships) - 10} 関係")
    
    # 結果エクスポート
    print(f"\n💾 結果をエクスポート中...")
    
    # タイムスタンプ付きプリフィックス
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    prefix = f"input_analysis_{timestamp}"
    
    # エクスポート実行（出力先をoutputに変更）
    
    def custom_export_results(prefix_name):
        """カスタムエクスポート関数（出力先変更）"""
        os.makedirs(output_folder, exist_ok=True)
        
        # CSV出力
        csv_file = os.path.join(output_folder, f"{prefix_name}_relationships.csv")
        analyzer.analyzer.export_to_csv(csv_file)
        print(f"  ✓ CSV: {csv_file}")
        
        # PNG グラフ出力
        try:
            graph_file = os.path.join(output_folder, f"{prefix_name}_graph.png")
            analyzer.analyzer.generate_graph_visualization(graph_file)
            print(f"  ✓ PNG グラフ: {graph_file}")
        except Exception as e:
            print(f"  ❌ PNG グラフ生成エラー: {e}")
        
        # HTML インタラクティブグラフ出力
        try:
            html_file = os.path.join(output_folder, f"{prefix_name}_interactive.html")
            analyzer.analyzer.generate_interactive_html(html_file)
            print(f"  ✓ HTML グラフ: {html_file}")
        except Exception as e:
            print(f"  ❌ HTML グラフ生成エラー: {e}")
        
        # サマリー出力
        summary_file = os.path.join(output_folder, f"{prefix_name}_summary.txt")
        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write("=== Input フォルダSQL解析サマリー ===\\n\\n")
            f.write(f"解析日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\\n")
            f.write(f"解析フォルダ: {input_folder}/\\n")
            f.write(f"出力フォルダ: {output_folder}/\\n\\n")
            
            f.write(f"解析ファイル数: {stats['total_files']}\\n")
            f.write(f"総関係数: {stats['total_relationships']}\\n")
            f.write(f"総テーブル数: {stats['total_tables']}\\n\\n")
            
            f.write("=== 検出されたテーブル ===\\n")
            for i, table in enumerate(tables, 1):
                f.write(f"{i:3d}. {table}\\n")
            
            f.write(f"\\n=== 検出された関係 ===\\n")
            for i, rel in enumerate(relationships, 1):
                if rel['table1'] and rel['table2']:
                    f.write(f"{i:3d}. {rel['table1']}.{rel['column1']} ({rel['column_definition1']}) -> "
                           f"{rel['table2']}.{rel['column2']} ({rel['column_definition2']})\\n")
            
            # 解析ファイル一覧
            f.write(f"\\n=== 解析ファイル一覧 ===\\n")
            if 'file_results' in results:
                for file_path in sorted(results['file_results'].keys()):
                    filename = os.path.basename(file_path)
                    file_rels = len(results['file_results'][file_path]['relationships'])
                    f.write(f"- {filename} ({file_rels} 関係)\\n")
        
        print(f"  ✓ サマリー: {summary_file}")
    
    # カスタムエクスポート実行
    custom_export_results(prefix)
    
    # 完了メッセージ
    print(f"\\n🎉 解析完了!")
    print(f"📂 結果は {output_folder}/ フォルダに保存されました")
    
    # 生成されたファイル一覧
    print(f"\\n📄 生成されたファイル:")
    try:
        output_files = [f for f in os.listdir(output_folder) if f.startswith(prefix)]
        for file in sorted(output_files):
            file_path = os.path.join(output_folder, file)
            file_size = os.path.getsize(file_path)
            print(f"  • {file} ({file_size:,} bytes)")
    except Exception as e:
        print(f"  ❌ ファイル一覧取得エラー: {e}")
    
    return True

def show_input_folder_info():
    """inputフォルダの情報を表示"""
    input_folder = "input"
    
    if not os.path.exists(input_folder):
        print(f"📁 {input_folder} フォルダが存在しません")
        return
    
    sql_files = [f for f in os.listdir(input_folder) if f.endswith('.sql')]
    
    print(f"\\n📁 {input_folder} フォルダ情報:")
    print(f"  SQLファイル数: {len(sql_files)}")
    
    if sql_files:
        print(f"  ファイル一覧:")
        for i, file in enumerate(sorted(sql_files), 1):
            file_path = os.path.join(input_folder, file)
            try:
                file_size = os.path.getsize(file_path)
                print(f"    {i:2d}. {file} ({file_size:,} bytes)")
            except:
                print(f"    {i:2d}. {file}")

if __name__ == "__main__":
    print("🚀 Input フォルダSQL解析ツール")
    
    # inputフォルダ情報表示
    show_input_folder_info()
    
    # 解析実行
    success = main()
    
    if success:
        print(f"\\n✨ 正常に完了しました!")
    else:
        print(f"\\n❌ エラーが発生しました")
        sys.exit(1)