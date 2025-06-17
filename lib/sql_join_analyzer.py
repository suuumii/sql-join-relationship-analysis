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
        
        from .html_generator import HTMLTemplateGenerator
        
        # Prepare data for Vis.js
        nodes_data = []
        edges_data = []
        
        # Create nodes with enhanced information
        for node in self.graph.nodes():
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
        
        # Generate HTML content using shared template
        html_generator = HTMLTemplateGenerator()
        html_content = html_generator.create_html_template(
            nodes_data=nodes_data,
            edges_data=edges_data,
            title="SQL Table Relationships - Interactive Graph",
            subtitle="SQL解析によるテーブル間の関係可視化"
        )
        
        # Write to file
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"Interactive HTML visualization saved: {filename}")
    
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