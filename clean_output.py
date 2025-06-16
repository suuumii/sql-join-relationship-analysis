#!/usr/bin/env python3
"""
outputフォルダ内のファイルを削除するクリーンアップスクリプト
"""

import os
import glob
import shutil
from datetime import datetime

def clean_output_folder(output_folder="output", confirm=True):
    """
    outputフォルダ内のファイルを削除
    
    Args:
        output_folder: 削除対象フォルダ（デフォルト: "output"）
        confirm: 削除前に確認を求めるか（デフォルト: True）
    
    Returns:
        削除したファイル数
    """
    
    if not os.path.exists(output_folder):
        print(f"📁 {output_folder} フォルダが存在しません")
        return 0
    
    # フォルダ内のファイル一覧取得
    files = []
    for pattern in ["*.csv", "*.png", "*.txt", "*.json", "*.html"]:
        files.extend(glob.glob(os.path.join(output_folder, pattern)))
    
    # .gitkeepは除外
    files = [f for f in files if not f.endswith('.gitkeep')]
    
    if not files:
        print(f"✨ {output_folder} フォルダは既に空です")
        return 0
    
    print(f"📂 {output_folder} フォルダ内のファイル:")
    total_size = 0
    for i, file_path in enumerate(sorted(files), 1):
        try:
            file_size = os.path.getsize(file_path)
            total_size += file_size
            filename = os.path.basename(file_path)
            print(f"  {i:2d}. {filename} ({file_size:,} bytes)")
        except OSError:
            print(f"  {i:2d}. {os.path.basename(file_path)} (サイズ不明)")
    
    print(f"\n📊 合計: {len(files)} ファイル ({total_size:,} bytes)")
    
    # 確認
    if confirm:
        print(f"\n❓ {len(files)} ファイルを削除しますか？")
        response = input("削除する場合は 'yes' または 'y' を入力: ").lower().strip()
        
        if response not in ['yes', 'y', 'はい']:
            print("❌ 削除をキャンセルしました")
            return 0
    
    # 削除実行
    deleted_count = 0
    failed_files = []
    
    print(f"\n🗑️  ファイルを削除中...")
    
    for file_path in files:
        try:
            os.remove(file_path)
            deleted_count += 1
            print(f"  ✓ {os.path.basename(file_path)}")
        except OSError as e:
            failed_files.append((file_path, str(e)))
            print(f"  ❌ {os.path.basename(file_path)}: {e}")
    
    # 結果表示
    print(f"\n📈 削除結果:")
    print(f"  ✅ 削除成功: {deleted_count} ファイル")
    
    if failed_files:
        print(f"  ❌ 削除失敗: {len(failed_files)} ファイル")
        for file_path, error in failed_files:
            print(f"    - {os.path.basename(file_path)}: {error}")
    
    if deleted_count > 0:
        print(f"  💾 容量節約: {total_size:,} bytes")
    
    return deleted_count

def backup_output_folder(output_folder="output", backup_folder="output_backup"):
    """
    outputフォルダをバックアップしてから削除
    
    Args:
        output_folder: バックアップ元フォルダ
        backup_folder: バックアップ先フォルダ
    """
    
    if not os.path.exists(output_folder):
        print(f"📁 {output_folder} フォルダが存在しません")
        return False
    
    # バックアップフォルダ名にタイムスタンプを付与
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f"{backup_folder}_{timestamp}"
    
    try:
        # バックアップ作成
        shutil.copytree(output_folder, backup_path)
        print(f"📦 バックアップ作成: {backup_path}")
        
        # 元フォルダを削除
        deleted_count = clean_output_folder(output_folder, confirm=False)
        
        if deleted_count > 0:
            print(f"✨ バックアップ完了 ({deleted_count} ファイル)")
        
        return True
        
    except Exception as e:
        print(f"❌ バックアップエラー: {e}")
        return False

def show_output_status(output_folder="output"):
    """
    outputフォルダの現在の状態を表示
    
    Args:
        output_folder: 確認対象フォルダ
    """
    
    if not os.path.exists(output_folder):
        print(f"📁 {output_folder} フォルダが存在しません")
        return
    
    files = []
    for pattern in ["*.csv", "*.png", "*.txt", "*.json"]:
        files.extend(glob.glob(os.path.join(output_folder, pattern)))
    
    files = [f for f in files if not f.endswith('.gitkeep')]
    
    if not files:
        print(f"✨ {output_folder} フォルダは空です")
        return
    
    print(f"📂 {output_folder} フォルダの状態:")
    
    # ファイル種別ごとに集計
    file_types = {}
    total_size = 0
    
    for file_path in files:
        try:
            ext = os.path.splitext(file_path)[1].lower()
            size = os.path.getsize(file_path)
            
            if ext not in file_types:
                file_types[ext] = {'count': 0, 'size': 0}
            
            file_types[ext]['count'] += 1
            file_types[ext]['size'] += size
            total_size += size
            
        except OSError:
            pass
    
    for ext, data in sorted(file_types.items()):
        print(f"  {ext:>5s}: {data['count']:3d} ファイル ({data['size']:,} bytes)")
    
    print(f"  {'合計':>5s}: {len(files):3d} ファイル ({total_size:,} bytes)")

def main():
    """メイン実行関数"""
    
    import argparse
    
    parser = argparse.ArgumentParser(
        description="outputフォルダクリーンアップツール",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用例:
  python clean_output.py                 # 通常の削除（確認あり）
  python clean_output.py --yes           # 確認なしで削除
  python clean_output.py --backup        # バックアップしてから削除
  python clean_output.py --status        # 現在の状態確認のみ
  python clean_output.py --folder custom # カスタムフォルダを削除
        """
    )
    
    parser.add_argument('--folder', '-f', default='output',
                       help='削除対象フォルダ（デフォルト: output）')
    parser.add_argument('--yes', '-y', action='store_true',
                       help='確認なしで削除実行')
    parser.add_argument('--backup', '-b', action='store_true',
                       help='削除前にバックアップを作成')
    parser.add_argument('--status', '-s', action='store_true',
                       help='フォルダの状態確認のみ（削除しない）')
    
    args = parser.parse_args()
    
    print("🧹 Output フォルダクリーンアップツール")
    print("=" * 50)
    
    # 状態確認モード
    if args.status:
        show_output_status(args.folder)
        return
    
    # バックアップモード
    if args.backup:
        backup_output_folder(args.folder)
        return
    
    # 通常削除モード
    deleted_count = clean_output_folder(args.folder, confirm=not args.yes)
    
    if deleted_count > 0:
        print(f"\n🎉 クリーンアップ完了!")
    else:
        print(f"\n💡 削除対象ファイルがありませんでした")

if __name__ == "__main__":
    main()