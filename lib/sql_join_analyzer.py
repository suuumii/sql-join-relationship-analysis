import sqlglot
import csv
import networkx as nx
import matplotlib.pyplot as plt
from collections import defaultdict
from typing import List, Dict, Tuple, Set
import re


class SQLJoinAnalyzer:
    def __init__(self):
        self.relationships = []
        self.tables = set()
        self.graph = nx.DiGraph()
        self.alias_to_table = {}  # エイリアスから実際のテーブル名へのマッピング
    
    def analyze_sql(self, sql_query: str) -> List[Dict]:
        """Analyze SQL query for JOIN relationships"""
        try:
            # Parse SQL using sqlglot with MySQL dialect
            parsed = sqlglot.parse_one(sql_query, dialect=sqlglot.dialects.MySQL)
            
            # Reset for new query
            self.relationships = []
            self.tables = set()
            self.alias_to_table = {}
            
            # Extract table aliases first
            self._extract_table_aliases(parsed)
            
            # Extract relationships from parsed query
            self._extract_joins(parsed)
            self._extract_from_where_relationships(parsed)
            
            return self.relationships
            
        except Exception as e:
            print(f"Error parsing SQL: {e}")
            return []
    
    def _extract_table_aliases(self, node, visited=None):
        """Extract table aliases from the SQL query"""
        if visited is None:
            visited = set()
        
        node_id = id(node)
        if node_id in visited:
            return
        visited.add(node_id)
        
        try:
            # Extract FROM clause aliases
            from_clause = node.find(sqlglot.expressions.From)
            if from_clause and hasattr(from_clause, 'this'):
                self._extract_alias_from_table_node(from_clause.this)
            
            # Extract JOIN clause aliases
            joins = list(node.find_all(sqlglot.expressions.Join))
            for join in joins:
                if hasattr(join, 'this'):
                    self._extract_alias_from_table_node(join.this)
            
            # Process subqueries recursively
            subqueries = list(node.find_all(sqlglot.expressions.Subquery))
            for subquery in subqueries:
                if hasattr(subquery, 'this') and subquery.this:
                    sub_id = id(subquery.this)
                    if sub_id not in visited:
                        self._extract_table_aliases(subquery.this, visited)
                        
        except Exception as e:
            print(f"Error extracting table aliases: {e}")
    
    def _extract_alias_from_table_node(self, table_node):
        """Extract alias from a table node"""
        try:
            # Check if this is a Table node with alias
            if isinstance(table_node, sqlglot.expressions.Table):
                table_name = table_node.name if hasattr(table_node, 'name') else None
                alias = table_node.alias if hasattr(table_node, 'alias') else None
                
                if table_name and alias:
                    self.alias_to_table[alias] = table_name
                elif table_name:
                    # No alias, map table name to itself
                    self.alias_to_table[table_name] = table_name
            
            # Check if this is an Alias node
            elif isinstance(table_node, sqlglot.expressions.Alias):
                alias_name = table_node.alias if hasattr(table_node, 'alias') else None
                if hasattr(table_node, 'this') and isinstance(table_node.this, sqlglot.expressions.Table):
                    table_name = table_node.this.name
                    if alias_name and table_name:
                        self.alias_to_table[alias_name] = table_name
                        
        except Exception as e:
            print(f"Error extracting alias from table node: {e}")
    
    def _extract_joins(self, node, visited=None):
        """Extract JOIN relationships from AST"""
        if visited is None:
            visited = set()
        
        # Prevent infinite recursion
        node_id = id(node)
        if node_id in visited:
            return
        visited.add(node_id)
        
        try:
            # Get left table from FROM clause for context
            left_table = None
            from_clause = node.find(sqlglot.expressions.From)
            if from_clause and hasattr(from_clause, 'this'):
                left_table = self._get_table_name(from_clause.this)
            
            # For SELECT statements, check joins property directly
            if hasattr(node, 'joins') and node.joins:
                for join in node.joins:
                    self._process_join(join, left_table)
            
            # Also find all JOIN nodes recursively for subqueries
            joins = list(node.find_all(sqlglot.expressions.Join))
            for join in joins:
                self._process_join(join, left_table)
            
            # Find and process subqueries
            subqueries = list(node.find_all(sqlglot.expressions.Subquery))
            for subquery in subqueries:
                if hasattr(subquery, 'this') and subquery.this:
                    sub_id = id(subquery.this)
                    if sub_id not in visited:
                        self._extract_joins(subquery.this, visited)
                        
        except Exception as e:
            print(f"Error in _extract_joins: {e}")
    
    def _process_join(self, join_node, left_table=None):
        """Process a single JOIN node"""
        try:
            # Get the table being joined
            if hasattr(join_node, 'this') and join_node.this:
                right_table = self._get_table_name(join_node.this)
                
                # Get ON condition
                if hasattr(join_node, 'args') and 'on' in join_node.args and join_node.args['on']:
                    self._process_join_condition(join_node.args['on'], right_table)
                # Get USING clause
                elif hasattr(join_node, 'args') and 'using' in join_node.args and join_node.args['using']:
                    self._process_using_clause(join_node.args['using'], right_table, left_table)
                # Check for NATURAL JOIN
                elif hasattr(join_node, 'args') and join_node.args.get('kind') == "NATURAL":
                    self._process_natural_join(right_table)
                # For comma-separated tables (converted to JOINs), check WHERE clause
                elif not hasattr(join_node, 'args') or 'on' not in join_node.args:
                    # This is likely a comma-separated table, relationships will be in WHERE
                    pass
                    
        except Exception as e:
            print(f"Error processing join: {e}")
    
    def _process_join_condition(self, condition, right_table=None):
        """Process JOIN ON condition"""
        if not condition:
            return
            
        try:
            # Process equality conditions specifically
            self._extract_equality_conditions(condition)
            
        except Exception as e:
            print(f"Error processing join condition: {e}")
    
    def _extract_equality_conditions(self, node):
        """Extract only equality conditions from JOIN ON clause"""
        if not node:
            return
            
        # Handle EQ (equality) expressions directly
        if isinstance(node, sqlglot.expressions.EQ):
            left = node.left
            right = node.right
            
            # Check if both sides are columns
            if (isinstance(left, sqlglot.expressions.Column) and 
                isinstance(right, sqlglot.expressions.Column)):
                
                left_table = self._get_column_table(left)
                left_column = left.name
                right_table = self._get_column_table(right)
                right_column = right.name
                
                if left_table and right_table and left_table != right_table:
                    self._add_relationship(left_table, left_column, right_table, right_column)
        
        # Handle AND expressions - process each condition separately
        elif isinstance(node, sqlglot.expressions.And):
            self._extract_equality_conditions(node.left)
            self._extract_equality_conditions(node.right)
        
        # Handle other logical operators
        elif isinstance(node, (sqlglot.expressions.Or, sqlglot.expressions.Not)):
            # For OR conditions, we don't create relationships as they're not definitive
            # For NOT conditions, we also skip as they represent negative relationships
            pass
        
        # Recursively process nested expressions
        elif hasattr(node, 'args') and node.args:
            for arg_name, arg_value in node.args.items():
                if isinstance(arg_value, list):
                    for item in arg_value:
                        if hasattr(item, 'find_all'):
                            self._extract_equality_conditions(item)
                elif hasattr(arg_value, 'find_all'):
                    self._extract_equality_conditions(arg_value)
    
    def _process_using_clause(self, using_clause, right_table, left_table=None):
        """Process USING clause"""
        try:
            # USING clause can be a list of columns
            if isinstance(using_clause, list):
                columns = using_clause
            elif hasattr(using_clause, 'expressions'):
                columns = using_clause.expressions
            else:
                return
            
            for column in columns:
                column_name = None
                if hasattr(column, 'name'):
                    column_name = column.name
                elif hasattr(column, 'this') and hasattr(column.this, 'name'):
                    column_name = column.this.name
                elif hasattr(column, 'this'):
                    column_name = str(column.this)
                else:
                    column_name = str(column)
                
                if column_name:
                    # In USING clause, the same column name exists in both tables
                    # Left table will be inferred from context
                    self._add_relationship(left_table or "LEFT_TABLE", column_name, right_table, column_name)
        except Exception as e:
            print(f"Error processing USING clause: {e}")
    
    def _process_natural_join(self, right_table):
        """Process NATURAL JOIN"""
        # NATURAL JOIN automatically joins on columns with the same name
        # We can't determine the exact columns without schema information
        # So we'll add a placeholder relationship
        self._add_relationship(None, "NATURAL", right_table, "NATURAL")
    
    def _extract_from_where_relationships(self, node):
        """Extract relationships from FROM clause with WHERE conditions"""
        try:
            # Check if there are any comma-separated tables that were converted to joins
            if hasattr(node, 'args') and 'joins' in node.args and node.args['joins']:
                from_clause = node.find(sqlglot.expressions.From)
                joins = node.args['joins']
                
                # Get all table names
                from_tables = []
                
                # Add main FROM table
                if from_clause and hasattr(from_clause, 'this'):
                    main_table = self._get_table_name(from_clause.this)
                    if main_table:
                        from_tables.append(main_table)
                
                # Add joined tables (for comma-separated FROM)
                for join in joins:
                    if hasattr(join, 'this'):
                        table_name = self._get_table_name(join.this)
                        if table_name:
                            from_tables.append(table_name)
                
                # If we have multiple tables and no ON conditions, check WHERE
                comma_separated_joins = [j for j in joins if not (hasattr(j, 'args') and 'on' in j.args)]
                
                if len(from_tables) > 1 and comma_separated_joins:
                    where_clause = node.find(sqlglot.expressions.Where)
                    if where_clause:
                        self._process_where_conditions(where_clause, from_tables)
                    
        except Exception as e:
            print(f"Error extracting FROM-WHERE relationships: {e}")
    
    def _process_where_conditions(self, where_clause, from_tables):
        """Process WHERE clause conditions for table relationships"""
        if not where_clause:
            return
        
        try:
            # Look for equality conditions between tables
            equalities = list(where_clause.find_all(sqlglot.expressions.EQ))
            for eq in equalities:
                # Get left and right sides of the equality
                left_col = eq.args.get('this') if 'this' in eq.args else eq.left
                right_col = eq.args.get('expression') if 'expression' in eq.args else eq.right
                
                # Check if both sides are columns
                if (isinstance(left_col, sqlglot.expressions.Column) and 
                    isinstance(right_col, sqlglot.expressions.Column)):
                    
                    left_table = self._get_column_table(left_col)
                    right_table = self._get_column_table(right_col)
                    left_column = left_col.name if hasattr(left_col, 'name') else str(left_col.this)
                    right_column = right_col.name if hasattr(right_col, 'name') else str(right_col.this)
                    
                    if (left_table and right_table and 
                        left_table != right_table):
                        
                        self._add_relationship(left_table, left_column, 
                                             right_table, right_column)
                        
        except Exception as e:
            print(f"Error processing WHERE conditions: {e}")
    
    def _get_table_name(self, node):
        """Extract table name from AST node and resolve alias to actual table name"""
        table_name = None
        
        if hasattr(node, 'name'):
            table_name = node.name
        elif hasattr(node, 'this') and hasattr(node.this, 'name'):
            table_name = node.this.name
        elif hasattr(node, 'this') and hasattr(node.this, 'this') and hasattr(node.this.this, 'name'):
            table_name = node.this.this.name
        
        # Resolve alias to actual table name
        if table_name and table_name in self.alias_to_table:
            return self.alias_to_table[table_name]
        return table_name
    
    def _get_column_table(self, column_node):
        """Get table name for a column and resolve alias to actual table name"""
        table_name = None
        
        if hasattr(column_node, 'table') and column_node.table:
            # テーブルエイリアスの場合は名前を取得
            if hasattr(column_node.table, 'name'):
                table_name = column_node.table.name
            else:
                table_name = str(column_node.table)
        
        # Resolve alias to actual table name
        if table_name and table_name in self.alias_to_table:
            return self.alias_to_table[table_name]
        return table_name
    
    def _are_related_columns(self, col1: str, col2: str) -> bool:
        """Check if two columns are likely related based on naming conventions"""
        # Direct match
        if col1 == col2:
            return True
        
        # Foreign key patterns
        if col1.endswith('_id') and col2 == 'id':
            return True
        if col2.endswith('_id') and col1 == 'id':
            return True
        
        # Extract base name from foreign key
        if col1.endswith('_id') and col2.endswith('_id'):
            base1 = col1[:-3]
            base2 = col2[:-3]
            return base1 == base2
        
        return False
    
    def _add_relationship(self, table1: str, col1: str, table2: str, col2: str):
        """Add a relationship between tables"""
        relationship = {
            'table1': table1,
            'column1': col1,
            'column_definition1': self._infer_column_type(col1),
            'table2': table2,
            'column2': col2,
            'column_definition2': self._infer_column_type(col2)
        }
        
        # Avoid duplicates
        if relationship not in self.relationships:
            self.relationships.append(relationship)
            
        # Add to graph - handle multiple relationships between same tables
        if table1 and table2:
            if self.graph.has_edge(table1, table2):
                # Append to existing relationship
                existing_columns = self.graph.edges[table1, table2].get('columns', '')
                new_relationship = f"{col1} -> {col2}"
                if existing_columns and new_relationship not in existing_columns:
                    updated_columns = f"{existing_columns}; {new_relationship}"
                else:
                    updated_columns = new_relationship
                self.graph.edges[table1, table2]['columns'] = updated_columns
            else:
                # Create new edge
                self.graph.add_edge(table1, table2, 
                                  columns=f"{col1} -> {col2}")
            self.tables.add(table1)
            self.tables.add(table2)
    
    def _infer_column_type(self, column_name: str) -> str:
        """Infer column type based on naming conventions"""
        if not column_name or column_name in ['NATURAL']:
            return 'UNKNOWN'
        
        if column_name.endswith('_id') or column_name == 'id':
            return 'INT PRIMARY KEY' if column_name == 'id' else 'INT FOREIGN KEY'
        elif column_name.endswith('_at') or column_name.endswith('_time'):
            return 'DATETIME'
        elif column_name.endswith('_date'):
            return 'DATE'
        elif column_name.endswith('_count') or column_name.endswith('_num'):
            return 'INT'
        elif column_name.endswith('_flag') or column_name.startswith('is_'):
            return 'BOOLEAN'
        else:
            return 'VARCHAR(255)'
    
    def export_to_csv(self, filename: str):
        """Export relationships to CSV file"""
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['table1', 'column1', 'table2', 'column2']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            for relationship in self.relationships:
                # Only write the columns we need for CSV
                csv_row = {
                    'table1': relationship['table1'],
                    'column1': relationship['column1'],
                    'table2': relationship['table2'],
                    'column2': relationship['column2']
                }
                writer.writerow(csv_row)
    
    def generate_graph_visualization(self, filename: str = 'table_relationships.png'):
        """Generate improved NetworkX graph visualization with reduced line overlap"""
        if not self.graph.nodes():
            print("No relationships found to visualize")
            return
        
        # Create larger figure for better spacing
        plt.figure(figsize=(16, 12))
        
        # Try multiple layout algorithms for better node positioning
        node_count = len(self.graph.nodes())
        
        if node_count < 10:
            # For small graphs, use circular layout
            pos = nx.circular_layout(self.graph, scale=3)
        elif node_count < 20:
            # For medium graphs, use spring layout with better parameters
            pos = nx.spring_layout(self.graph, k=3, iterations=100, seed=42)
        else:
            # For large graphs, use hierarchical layout
            try:
                # Use graphviz layout if available (better for complex graphs)
                pos = nx.nx_agraph.graphviz_layout(self.graph, prog='neato')
            except:
                # Fallback to spring layout with increased spacing
                pos = nx.spring_layout(self.graph, k=4, iterations=150, seed=42)
        
        # Create multiple edge collections to avoid overlap
        edges = list(self.graph.edges())
        edge_colors = ['#4a90e2', '#7b68ee', '#50c878', '#ff6b6b', '#ffa500'] * (len(edges) // 5 + 1)
        
        # Draw nodes with better styling
        nx.draw_networkx_nodes(self.graph, pos, 
                              node_color='lightblue',
                              node_size=4000,
                              alpha=0.8,
                              linewidths=2,
                              edgecolors='darkblue')
        
        # Draw edges with curve to reduce overlap
        for i, edge in enumerate(edges):
            # Use different connection styles for different edges
            connection_style = f"arc3,rad={0.1 * (i % 3 - 1)}"  # Curve edges differently
            nx.draw_networkx_edges(self.graph, pos,
                                  edgelist=[edge],
                                  edge_color=edge_colors[i],
                                  arrows=True,
                                  arrowsize=25,
                                  alpha=0.7,
                                  width=2,
                                  connectionstyle=connection_style)
        
        # Draw labels with better positioning
        nx.draw_networkx_labels(self.graph, pos,
                               font_size=11,
                               font_weight='bold',
                               font_color='darkblue')
        
        # Draw edge labels with offset to avoid overlap
        edge_labels = nx.get_edge_attributes(self.graph, 'columns')
        
        # Create offset positions for edge labels
        edge_label_pos = {}
        for edge in edge_labels:
            x1, y1 = pos[edge[0]]
            x2, y2 = pos[edge[1]]
            # Position label slightly offset from edge center
            edge_label_pos[edge] = ((x1 + x2) / 2 + 0.1, (y1 + y2) / 2 + 0.1)
        
        # Draw edge labels with smaller font and offset
        for edge, label in edge_labels.items():
            if edge in edge_label_pos:
                plt.text(edge_label_pos[edge][0], edge_label_pos[edge][1], 
                        label, fontsize=7, ha='center', va='center',
                        bbox=dict(boxstyle='round,pad=0.2', facecolor='white', alpha=0.8))
        
        plt.title('Table Relationships Graph', fontsize=16, fontweight='bold', pad=20)
        plt.axis('off')
        
        # Adjust margins to prevent clipping
        plt.subplots_adjust(left=0.05, right=0.95, top=0.95, bottom=0.05)
        
        # Save with high resolution
        plt.savefig(filename, dpi=300, bbox_inches='tight', facecolor='white')
        plt.close()  # Close instead of show to avoid display issues
    
    def generate_interactive_html(self, filename: str = 'table_relationships.html'):
        """Generate interactive HTML visualization using Vis.js"""
        if not self.graph.nodes():
            print("No relationships found to visualize")
            return
        
        # Prepare data for Vis.js
        nodes_data = []
        edges_data = []
        
        # Create nodes with enhanced information
        for i, node in enumerate(self.graph.nodes()):
            # Count connections for node sizing
            connections = len(list(self.graph.neighbors(node)))
            
            nodes_data.append({
                'id': node,
                'label': node,
                'title': f"Table: {node}\\nConnections: {connections}",
                'value': max(15, connections * 4),  # Larger size for better readability
                'shape': 'dot',
                'font': {'size': 16, 'color': '#343434', 'bold': True},  # Larger, bold font
                'borderWidth': 3,
                'color': {'background': '#97c2fc', 'border': '#2b7ce9'}
            })
        
        # Create edges with relationship information
        for i, (source, target) in enumerate(self.graph.edges()):
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
        
        # Generate HTML content
        html_content = self._create_html_template(nodes_data, edges_data)
        
        # Write to file
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"Interactive HTML visualization saved: {filename}")
    
    def _create_html_template(self, nodes_data, edges_data) -> str:
        """Create complete HTML template with Vis.js"""
        import json
        
        return f'''<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SQL Table Relationships - Interactive Graph</title>
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
            gap: 8px;
            margin-left: auto;
            position: relative;
            z-index: 10000;
        }}
        
        .search-input {{
            background: white;
            border: 1px solid #ddd;
            border-radius: 20px;
            padding: 8px 16px;
            font-family: 'Roboto', sans-serif;
            font-size: 14px;
            width: 200px;
            transition: all 0.2s;
        }}
        
        .search-input:focus {{
            outline: none;
            border-color: #1976d2;
            box-shadow: 0 0 0 2px rgba(25, 118, 210, 0.2);
        }}
        
        .search-results {{
            position: fixed;
            background: white;
            border: 1px solid #ddd;
            border-radius: 0 0 4px 4px;
            border-top: none;
            max-height: 250px;
            overflow-y: auto;
            z-index: 999999;
            display: none;
            box-shadow: 0 8px 16px rgba(0,0,0,0.2);
            min-width: 200px;
        }}
        
        .search-result-item {{
            padding: 12px 16px;
            cursor: pointer;
            border-bottom: 1px solid #f0f0f0;
            font-size: 14px;
            color: #333;
            transition: all 0.2s;
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        
        .search-result-item:last-child {{
            border-bottom: none;
        }}
        
        .search-result-item:hover {{
            background: #f5f5f5;
            color: #1976d2;
        }}
        
        .search-result-item.highlighted {{
            background: #e3f2fd;
            color: #1976d2;
            font-weight: 500;
        }}
        
        .search-result-item .material-icons {{
            font-size: 16px;
            color: #666;
        }}
        
        .search-no-results {{
            padding: 16px;
            text-align: center;
            color: #666;
            font-style: italic;
        }}
        
        .search-wrapper {{
            position: relative;
            z-index: 10000;
        }}
        
        .network-card {{
            height: 600px;
            position: relative;
            z-index: 1;
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
            grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
            gap: 24px;
            text-align: center;
        }}
        
        .stat-item {{
            padding: 16px;
            border-radius: 8px;
            background: #f5f5f5;
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
            color: #1976d2;
            font-size: 20px;
        }}
        
        .info-label {{
            font-weight: 500;
            color: #666;
            margin-right: 8px;
        }}
        
        .info-value {{
            color: #333;
            font-weight: 400;
        }}
        
        @media (max-width: 768px) {{
            .details-content {{
                grid-template-columns: 1fr;
            }}
            
            .container {{
                padding: 16px;
            }}
        }}
    </style>
</head>
<body>
    <!-- App Bar -->
    <div class="app-bar">
        <h1>
            <span class="material-icons">storage</span>
            SQL Table Relationships
        </h1>
        <p>Interactive Database Schema Visualization</p>
    </div>
    
    <!-- Main Container -->
    <div class="container">
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
        
        // Wait for network to be fully loaded before initializing search
        network.once('afterDrawing', function() {{
            console.log('Network drawing completed, initializing search...');
            initializeSearch();
            
            // Test search functionality
            setTimeout(() => {{
                console.log('Testing search functionality...');
                const searchInput = document.getElementById('table-search');
                const searchResults = document.getElementById('search-results');
                console.log('Search input element:', searchInput);
                console.log('Search results element:', searchResults);
                console.log('Total tables available:', allTables);
            }}, 500);
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
            // 選択を全てクリア
            network.unselectAll();
            
            // 詳細パネルを隠す
            hideNodeDetails();
            
            // 選択カウンターをリセット
            document.getElementById('selected-count').textContent = '0';
            
            // ノードの位置を初期状態に戻すため、レイアウトを再適用
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
            
            // レイアウト完了後にビューをフィット
            setTimeout(() => {{
                network.fit({{
                    animation: {{
                        duration: 1000,
                        easingFunction: 'easeInOutQuad'
                    }}
                }});
            }}, 100);
        }}
        
        function fitNetwork() {{
            network.fit({{ 
                animation: {{ 
                    duration: 1000, 
                    easingFunction: 'easeInOutQuad' 
                }} 
            }});
        }}
        
        function clearSelection() {{
            network.unselectAll();
            hideNodeDetails();
            document.getElementById('selected-count').textContent = '0';
        }}
        
        // Search functionality
        let allTables = [];
        let currentSearchResults = [];
        
        function initializeSearch() {{
            try {{
                // Get all table names from the network
                if (typeof nodes !== 'undefined' && nodes && typeof nodes.getIds === 'function') {{
                    allTables = nodes.getIds().sort();
                    console.log('Search initialized with tables:', allTables);
                }} else {{
                    console.error('Nodes object not available for search initialization');
                    allTables = [];
                }}
            }} catch (error) {{
                console.error('Error initializing search:', error);
                allTables = [];
            }}
        }}
        
        function handleSearchKeyup(event) {{
            // Handle special keys that don't trigger searchTables
            if (['ArrowDown', 'ArrowUp', 'Enter', 'Escape'].includes(event.key)) {{
                return; // These are handled in the main keydown listener
            }}
            // For other keys, ensure searchTables is called
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
            
            console.log('Searching for:', query);
            
            // Check if allTables is initialized
            if (!allTables || allTables.length === 0) {{
                console.warn('allTables not initialized yet, reinitializing...');
                initializeSearch();
                if (!allTables || allTables.length === 0) {{
                    console.error('Failed to initialize tables');
                    return;
                }}
            }}
            
            console.log('Available tables:', allTables.length);
            
            if (query === '') {{
                searchResults.style.display = 'none';
                currentSearchResults = [];
                return;
            }}
            
            // Filter tables that match the search query
            currentSearchResults = allTables.filter(table => 
                table.toLowerCase().includes(query)
            ).sort(); // Sort alphabetically
            
            console.log('Found results:', currentSearchResults);
            
            // Display search results
            if (currentSearchResults.length > 0) {{
                const maxResults = Math.min(currentSearchResults.length, 15); // Limit to 15 results
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
                
                // Add "more results" indicator if needed
                if (currentSearchResults.length > maxResults) {{
                    searchResults.innerHTML += `
                        <div class="search-no-results">
                            他 ${{currentSearchResults.length - maxResults}} 件のテーブルが見つかりました
                        </div>
                    `;
                }}
                
                // Position and display search results
                positionSearchResults();
                searchResults.style.display = 'block';
                console.log('Search results displayed with z-index:', getComputedStyle(searchResults).zIndex);
                console.log('Search wrapper z-index:', getComputedStyle(searchResults.parentElement).zIndex);
                console.log('Search results position:', searchResults.style.top, searchResults.style.left);
            }} else {{
                searchResults.innerHTML = `
                    <div class="search-no-results">
                        <span class="material-icons">search_off</span>
                        "${{query}}" に一致するテーブルが見つかりませんでした
                    </div>
                `;
                positionSearchResults();
                searchResults.style.display = 'block';
                console.log('No results found for:', query);
            }}
        }}
        
        function selectTable(tableName) {{
            console.log('Selecting table:', tableName);
            
            // Clear previous selection
            network.unselectAll();
            
            // Check if allTables is initialized
            if (!allTables || allTables.length === 0) {{
                console.warn('allTables not initialized, reinitializing...');
                initializeSearch();
            }}
            
            // Check if the table exists in the network
            if (!allTables || !allTables.includes(tableName)) {{
                console.error('Table not found:', tableName, 'Available tables:', allTables);
                return;
            }}
            
            // Select the table node
            network.selectNodes([tableName]);
            
            // Focus on the selected node with animation
            network.focus(tableName, {{
                scale: 2.0,
                offset: {{x: 0, y: 0}},
                animation: {{
                    duration: 1500,
                    easingFunction: 'easeInOutCubic'
                }}
            }});
            
            // Show node details
            showNodeDetails(tableName);
            
            // Update selected count
            document.getElementById('selected-count').textContent = '1';
            
            // Clear search input and hide results
            const searchInput = document.getElementById('table-search');
            searchInput.value = '';
            searchInput.blur(); // Remove focus from input
            document.getElementById('search-results').style.display = 'none';
            
            // Visual feedback - briefly highlight the selected node
            setTimeout(() => {{
                // Get the node position for visual feedback
                const nodePosition = network.getPositions([tableName]);
                if (nodePosition[tableName]) {{
                    console.log('Table selected successfully:', tableName);
                }}
            }}, 100);
        }}
        
        function showSearchResults() {{
            const searchInput = document.getElementById('table-search');
            if (searchInput.value.trim() !== '') {{
                positionSearchResults();
                searchTables();
            }}
        }}
        
        function hideSearchResults() {{
            // Delay hiding to allow click events on search results
            setTimeout(() => {{
                const searchResults = document.getElementById('search-results');
                if (searchResults && document.activeElement.id !== 'table-search') {{
                    searchResults.style.display = 'none';
                }}
            }}, 200);
        }}
        
        // Keyboard navigation variables
        let selectedResultIndex = -1;
        
        // Handle keyboard navigation in search
        document.addEventListener('keydown', function(e) {{
            const searchInput = document.getElementById('table-search');
            const searchResults = document.getElementById('search-results');
            const resultItems = searchResults.querySelectorAll('.search-result-item');
            
            // Ctrl+F to focus search
            if (e.ctrlKey && e.key === 'f') {{
                e.preventDefault();
                searchInput.focus();
                searchInput.select();
                return;
            }}
            
            // Only handle keys when search input is focused
            if (document.activeElement === searchInput) {{
                if (e.key === 'Enter') {{
                    e.preventDefault();
                    if (selectedResultIndex >= 0 && selectedResultIndex < currentSearchResults.length) {{
                        selectTable(currentSearchResults[selectedResultIndex]);
                    }} else if (currentSearchResults.length > 0) {{
                        selectTable(currentSearchResults[0]);
                    }}
                }} else if (e.key === 'Escape') {{
                    searchInput.value = '';
                    searchInput.blur();
                    searchResults.style.display = 'none';
                    selectedResultIndex = -1;
                }} else if (e.key === 'ArrowDown') {{
                    e.preventDefault();
                    if (currentSearchResults.length > 0) {{
                        selectedResultIndex = Math.min(selectedResultIndex + 1, Math.min(currentSearchResults.length - 1, 14));
                        updateResultHighlight();
                    }}
                }} else if (e.key === 'ArrowUp') {{
                    e.preventDefault();
                    if (currentSearchResults.length > 0) {{
                        selectedResultIndex = Math.max(selectedResultIndex - 1, -1);
                        updateResultHighlight();
                    }}
                }}
            }}
        }});
        
        function updateResultHighlight() {{
            const resultItems = document.querySelectorAll('.search-result-item');
            resultItems.forEach((item, index) => {{
                if (index === selectedResultIndex) {{
                    item.classList.add('highlighted');
                }} else {{
                    item.classList.remove('highlighted');
                }}
            }});
        }}
        
        // Reset selection index when search changes
        document.getElementById('table-search').addEventListener('input', function() {{
            selectedResultIndex = -1;
        }});
        
        // Reposition search results on window resize
        window.addEventListener('resize', function() {{
            const searchResults = document.getElementById('search-results');
            if (searchResults && searchResults.style.display === 'block') {{
                positionSearchResults();
            }}
        }});
        
        function showNodeDetails(nodeId) {{
            const detailsPanel = document.getElementById('selection-details');
            const tableName = document.getElementById('selected-table-name');
            const tableInfo = document.getElementById('table-info');
            const relatedTables = document.getElementById('related-tables');
            const joinConditions = document.getElementById('join-conditions');
            
            // テーブル名設定
            tableName.innerHTML = `
                <span class="material-icons">table_chart</span>
                ${{nodeId}} Table
            `;
            
            // 基本情報
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
            
            // 関連テーブル
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
            
            // 結合条件 - 複数カラムJOINをグループ化
            let conditionsHtml = '';
            const connectedEdgeIds = network.getConnectedEdges(nodeId);
            if (connectedEdgeIds.length > 0) {{
                // テーブル間の関係をグループ化
                const tableRelationships = {{}};
                
                connectedEdgeIds.forEach(edgeId => {{
                    const edge = edges.get(edgeId);
                    const isFromNode = edge.from === nodeId;
                    const otherTable = isFromNode ? edge.to : edge.from;
                    
                    if (!tableRelationships[otherTable]) {{
                        tableRelationships[otherTable] = [];
                    }}
                    
                    // Handle multiple relationships separated by semicolon
                    const relationshipsList = edge.label.split(';').map(rel => rel.trim());
                    relationshipsList.forEach(relationship => {{
                        if (relationship && !tableRelationships[otherTable].includes(relationship)) {{
                            tableRelationships[otherTable].push(relationship);
                        }}
                    }});
                }});
                
                // グループ化された関係を表示
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
            
            // パネル表示
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
    </script>
</body>
</html>'''
    
    def analyze_multiple_queries(self, queries: List[str]) -> List[Dict]:
        """Analyze multiple SQL queries and combine results"""
        all_relationships = []
        
        for i, query in enumerate(queries):
            print(f"Analyzing query {i+1}...")
            relationships = self.analyze_sql(query)
            all_relationships.extend(relationships)
        
        # Remove duplicates
        unique_relationships = []
        seen = set()
        for rel in all_relationships:
            key = (rel['table1'], rel['column1'], rel['table2'], rel['column2'])
            if key not in seen:
                seen.add(key)
                unique_relationships.append(rel)
        
        self.relationships = unique_relationships
        return unique_relationships


def main():
    """Example usage"""
    analyzer = SQLJoinAnalyzer()
    
    # Example SQL queries
    sample_queries = [
        """
        SELECT u.name, p.title, c.name as category
        FROM users u
        JOIN posts p ON u.id = p.user_id
        JOIN categories c ON p.category_id = c.id
        WHERE u.active = 1
        """,
        
        """
        SELECT o.id, o.total, c.name, p.name
        FROM orders o, customers c, products p
        WHERE o.customer_id = c.id AND o.product_id = p.id
        """,
        
        """
        SELECT *
        FROM employees e
        NATURAL JOIN departments d
        """,
        
        """
        SELECT u.name, 
               (SELECT COUNT(*) FROM posts WHERE user_id = u.id) as post_count
        FROM users u
        LEFT JOIN profiles p USING (user_id)
        """
    ]
    
    # Analyze queries
    print("Analyzing SQL queries...")
    results = analyzer.analyze_multiple_queries(sample_queries)
    
    # Export to CSV
    csv_filename = 'table_relationships.csv'
    analyzer.export_to_csv(csv_filename)
    print(f"Results exported to {csv_filename}")
    
    # Generate visualization
    analyzer.generate_graph_visualization()
    print("Graph visualization generated")
    
    # Print results
    print(f"\nFound {len(results)} relationships:")
    for rel in results:
        print(f"{rel['table1']}.{rel['column1']} -> {rel['table2']}.{rel['column2']}")


if __name__ == "__main__":
    main()