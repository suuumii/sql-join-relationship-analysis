#!/usr/bin/env python3
"""
CSV to HTML変換のデモスクリプト
"""

import os
import sys
import glob

# プロジェクトルートをPythonパスに追加
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from csv_to_html import CSVToHTMLConverter


def main():
    """デモ実行"""
    print("🎯 CSV to HTML Converter Demo")
    print("=" * 50)
    
    # 利用可能なCSVファイルを検索
    csv_pattern = os.path.join('..', 'output', '*relationships.csv')
    csv_files = glob.glob(csv_pattern)
    
    if not csv_files:
        print("❌ CSVファイルが見つかりません")
        print("   まず analyze_input.py を実行してCSVファイルを生成してください")
        return
    
    # 最新のCSVファイルを選択
    latest_csv = max(csv_files, key=os.path.getmtime)
    print(f"📁 使用するCSVファイル: {latest_csv}")
    
    # 出力ファイル名を生成
    output_file = "demo_csv_visualization.html"
    
    # 変換実行
    converter = CSVToHTMLConverter()
    
    try:
        converter.load_csv(latest_csv)
        converter.generate_html(output_file)
        
        print()
        print("🎉 デモ完了!")
        print(f"📂 生成されたHTMLファイル: {output_file}")
        print("   ブラウザで開いて確認してください")
        
        # ファイル情報表示
        if os.path.exists(output_file):
            file_size = os.path.getsize(output_file)
            print(f"   ファイルサイズ: {file_size:,} bytes")
            
    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")


if __name__ == "__main__":
    main()