#!/usr/bin/env python3
"""
フォルダ内のSQLファイルを一括解析するツール
"""

import os
import glob
import xml.etree.ElementTree as ET
import re
from .sql_join_analyzer import SQLJoinAnalyzer

class FolderSQLAnalyzer:
    def __init__(self):
        self.analyzer = SQLJoinAnalyzer()
        self.sql_files = []
        self.all_relationships = []
    
    def analyze_folder(self, folder_path: str, pattern: str = "*.sql"):
        """
        フォルダ内のSQLファイルまたはMyBatis XMLファイルを一括解析
        
        Args:
            folder_path: SQLファイルが格納されているフォルダパス
            pattern: ファイルパターン（デフォルト: *.sql、MyBatisの場合は *.xml）
        
        Returns:
            解析結果のリスト
        """
        print(f"=== フォルダ解析開始: {folder_path} ===")
        
        # フォルダの存在確認
        if not os.path.exists(folder_path):
            print(f"エラー: フォルダが見つかりません: {folder_path}")
            return []
        
        # SQLファイルとXMLファイルを検索
        if pattern == "*.sql":
            # デフォルトの場合は両方の拡張子をサポート
            sql_pattern = os.path.join(folder_path, "*.sql")
            xml_pattern = os.path.join(folder_path, "*.xml")
            self.sql_files = glob.glob(sql_pattern) + glob.glob(xml_pattern)
        else:
            # 特定のパターンが指定された場合はそれを使用
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
                file_extension = os.path.splitext(sql_file)[1].lower()
                
                if file_extension == '.xml':
                    # MyBatis XMLファイルの処理
                    sql_statements = self._extract_sql_from_mybatis_xml(sql_file)
                    
                    if not sql_statements:
                        print(f"スキップ: SQL文が見つかりません {sql_file}")
                        continue
                    
                    print(f"抽出されたSQL文数: {len(sql_statements)}")
                    
                    file_relationships = []
                    for stmt in sql_statements:
                        print(f"  SQL ID: {stmt['id']} ({stmt['type']})")
                        print(f"  SQL内容: {stmt['sql'][:200] + ('...' if len(stmt['sql']) > 200 else '')}")
                        
                        # クエリ解析
                        relationships = self.analyzer.analyze_sql(stmt['sql'])
                        file_relationships.extend(relationships)
                        all_queries.append(stmt['sql'])
                        
                        print(f"  関係数: {len(relationships)}")
                        for rel in relationships:
                            if rel['table1'] and rel['table2']:
                                print(f"    {rel['table1']}.{rel['column1']} -> {rel['table2']}.{rel['column2']}")
                    
                    file_results[sql_file] = {
                        'sql_statements': sql_statements,
                        'relationships': file_relationships
                    }
                
                else:
                    # 通常のSQLファイルの処理
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
    
    def _extract_sql_from_mybatis_xml(self, xml_file_path: str):
        """
        MyBatisのXMLファイルからSQL文を抽出（動的SQL対応強化版）
        
        Args:
            xml_file_path: MyBatis XMLファイルのパス
        
        Returns:
            抽出されたSQL文のリスト
        """
        sql_statements = []
        
        try:
            # XMLファイルを解析
            tree = ET.parse(xml_file_path)
            root = tree.getroot()
            
            # SQL文を含む可能性のあるタグを検索
            sql_tags = ['select', 'insert', 'update', 'delete']
            
            for tag_name in sql_tags:
                # 各タグからSQL文を抽出
                for element in root.iter(tag_name):
                    # 要素全体のテキストを取得（子要素も含む）
                    full_sql = self._extract_full_element_text(element)
                    
                    if full_sql and full_sql.strip():
                        # MyBatis特有の記法を除去
                        cleaned_sql = self._clean_mybatis_sql(full_sql)
                        if cleaned_sql:
                            sql_statements.append({
                                'id': element.get('id', 'unknown'),
                                'type': tag_name,
                                'sql': cleaned_sql,
                                'original_sql': full_sql  # デバッグ用に元のSQLも保持
                            })
        
        except ET.ParseError as e:
            print(f"XML解析エラー {xml_file_path}: {e}")
        except Exception as e:
            print(f"ファイル読み込みエラー {xml_file_path}: {e}")
        
        return sql_statements
    
    def _extract_full_element_text(self, element):
        """
        XML要素から子要素も含めた全テキストを抽出
        """
        parts = []
        
        # 要素のテキスト
        if element.text:
            parts.append(element.text)
        
        # 子要素の処理
        for child in element:
            child_text = self._process_dynamic_element(child)
            if child_text:
                parts.append(child_text)
            
            # 子要素の後のテキスト
            if child.tail:
                parts.append(child.tail)
        
        return ' '.join(parts)
    
    def _process_dynamic_element(self, element):
        """
        動的SQL要素を処理
        """
        tag = element.tag
        
        if tag == 'if':
            # if要素の内容を返す（条件は無視）
            return self._extract_full_element_text(element)
        elif tag == 'choose':
            # choose要素の最初のwhen要素を処理
            for child in element:
                if child.tag == 'when':
                    return self._extract_full_element_text(child)
                elif child.tag == 'otherwise':
                    return self._extract_full_element_text(child)
        elif tag == 'where':
            content = self._extract_full_element_text(element)
            return f"WHERE {content}" if content.strip() else ""
        elif tag == 'set':
            content = self._extract_full_element_text(element)
            return f"SET {content}" if content.strip() else ""
        elif tag == 'trim':
            # trim要素の内容をそのまま返す
            return self._extract_full_element_text(element)
        elif tag == 'foreach':
            # foreach要素の内容を簡略化して返す
            content = self._extract_full_element_text(element)
            collection = element.get('collection', 'items')
            return f"({content}) /* foreach {collection} */"
        elif tag == 'include':
            # include要素は参照先が不明なのでコメントとして残す
            refid = element.get('refid', 'unknown')
            return f"/* include {refid} */"
        else:
            # その他の要素はテキストをそのまま返す
            return self._extract_full_element_text(element)
    
    def _clean_mybatis_sql(self, sql_text: str) -> str:
        """
        MyBatis特有の記法を除去してクリーンなSQL文にする（動的SQL対応強化版）
        
        Args:
            sql_text: 元のSQL文
        
        Returns:
            クリーンなSQL文
        """
        if not sql_text:
            return ""
        
        cleaned = sql_text
        
        # MyBatis特有の記法を除去
        # #{parameter} や ${parameter} を適当な値に置換
        cleaned = re.sub(r'#\{[^}]+\}', "'placeholder'", cleaned)
        cleaned = re.sub(r'\$\{[^}]+\}', "placeholder", cleaned)
        
        # 動的SQL要素を処理（ネストしたタグにも対応）
        # choose/when/otherwise
        cleaned = re.sub(r'<choose[^>]*>.*?<when[^>]*>(.*?)</when>.*?</choose>', r'\1', cleaned, flags=re.DOTALL)
        cleaned = re.sub(r'<choose[^>]*>.*?<otherwise[^>]*>(.*?)</otherwise>.*?</choose>', r'\1', cleaned, flags=re.DOTALL)
        
        # bind要素
        cleaned = re.sub(r'<bind[^>]*name="([^"]*)"[^>]*value="([^"]*)"[^>]*/?>', r'/* bind \1 = \2 */', cleaned)
        
        # selectKey要素
        cleaned = re.sub(r'<selectKey[^>]*>.*?</selectKey>', '', cleaned, flags=re.DOTALL)
        
        # sql要素（共通SQL断片）
        cleaned = re.sub(r'<sql[^>]*id="([^"]*)"[^>]*>(.*?)</sql>', r'/* sql fragment \1: \2 */', cleaned, flags=re.DOTALL)
        
        # 残りの動的タグを除去（ネストにも対応）
        # if, where, set, trim, foreach, include
        cleaned = re.sub(r'<if[^>]*>(.*?)</if>', r'\1', cleaned, flags=re.DOTALL)
        cleaned = re.sub(r'<where[^>]*>(.*?)</where>', r'WHERE \1', cleaned, flags=re.DOTALL)
        cleaned = re.sub(r'<set[^>]*>(.*?)</set>', r'SET \1', cleaned, flags=re.DOTALL)
        cleaned = re.sub(r'<trim[^>]*>(.*?)</trim>', r'\1', cleaned, flags=re.DOTALL)
        cleaned = re.sub(r'<foreach[^>]*>(.*?)</foreach>', r'\1', cleaned, flags=re.DOTALL)
        cleaned = re.sub(r'<include[^>]*refid="([^"]*)"[^>]*/?>', r'/* include \1 */', cleaned)
        
        # 残りの全XMLタグを除去
        cleaned = re.sub(r'<[^>]+>', '', cleaned)
        
        # CDATA セクションを処理
        cleaned = re.sub(r'<!\[CDATA\[(.*?)\]\]>', r'\1', cleaned, flags=re.DOTALL)
        
        # コメントを除去
        cleaned = re.sub(r'<!--.*?-->', '', cleaned, flags=re.DOTALL)
        
        # 余分な空白を整理
        cleaned = re.sub(r'\s+', ' ', cleaned)
        cleaned = re.sub(r'\s*;\s*$', '', cleaned)  # 末尾のセミコロンを除去
        cleaned = cleaned.strip()
        
        # 空のWHERE/SETを除去
        cleaned = re.sub(r'\bWHERE\s*$', '', cleaned)
        cleaned = re.sub(r'\bSET\s*$', '', cleaned)
        cleaned = re.sub(r'\bWHERE\s+AND\b', 'WHERE', cleaned)
        cleaned = re.sub(r'\bSET\s*,', 'SET', cleaned)
        
        return cleaned


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