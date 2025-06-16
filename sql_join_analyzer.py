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
    
    def analyze_sql(self, sql_query: str) -> List[Dict]:
        """Analyze SQL query for JOIN relationships"""
        try:
            # Parse SQL using sqlglot with MySQL dialect
            parsed = sqlglot.parse_one(sql_query, dialect=sqlglot.dialects.MySQL)
            
            # Reset for new query
            self.relationships = []
            self.tables = set()
            
            # Extract relationships from parsed query
            self._extract_joins(parsed)
            self._extract_from_where_relationships(parsed)
            
            return self.relationships
            
        except Exception as e:
            print(f"Error parsing SQL: {e}")
            return []
    
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
            
        # Handle different types of conditions
        if hasattr(condition, 'find_all'):
            # Find all column references in the condition
            columns = list(condition.find_all(sqlglot.expressions.Column))
            
            # Group columns by table
            table_columns = defaultdict(list)
            for col in columns:
                table_name = self._get_column_table(col)
                column_name = col.name
                if table_name:
                    table_columns[table_name].append(column_name)
            
            # Create relationships between tables
            tables = list(table_columns.keys())
            if len(tables) >= 2:
                for i in range(len(tables)):
                    for j in range(i + 1, len(tables)):
                        table1, table2 = tables[i], tables[j]
                        cols1, cols2 = table_columns[table1], table_columns[table2]
                        
                        # Try to match columns
                        for col1 in cols1:
                            for col2 in cols2:
                                # In JOIN conditions, assume all column pairs are related
                                # since they appear in the same condition
                                self._add_relationship(table1, col1, table2, col2)
    
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
        """Extract table name from AST node"""
        if hasattr(node, 'name'):
            return node.name
        elif hasattr(node, 'this') and hasattr(node.this, 'name'):
            return node.this.name
        elif hasattr(node, 'this') and hasattr(node.this, 'this') and hasattr(node.this.this, 'name'):
            return node.this.this.name
        return None
    
    def _get_column_table(self, column_node):
        """Get table name for a column"""
        if hasattr(column_node, 'table') and column_node.table:
            # テーブルエイリアスの場合は名前を取得
            if hasattr(column_node.table, 'name'):
                return column_node.table.name
            return str(column_node.table)
        return None
    
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
            
        # Add to graph
        if table1 and table2:
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
            fieldnames = ['table1', 'column1', 'column_definition1', 
                         'table2', 'column2', 'column_definition2']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            for relationship in self.relationships:
                writer.writerow(relationship)
    
    def generate_graph_visualization(self, filename: str = 'table_relationships.png'):
        """Generate NetworkX graph visualization"""
        if not self.graph.nodes():
            print("No relationships found to visualize")
            return
        
        plt.figure(figsize=(12, 8))
        
        # Create layout
        pos = nx.spring_layout(self.graph, k=2, iterations=50)
        
        # Draw nodes
        nx.draw_networkx_nodes(self.graph, pos, 
                              node_color='lightblue',
                              node_size=3000,
                              alpha=0.7)
        
        # Draw edges
        nx.draw_networkx_edges(self.graph, pos,
                              edge_color='gray',
                              arrows=True,
                              arrowsize=20,
                              alpha=0.6)
        
        # Draw labels
        nx.draw_networkx_labels(self.graph, pos,
                               font_size=10,
                               font_weight='bold')
        
        # Draw edge labels
        edge_labels = nx.get_edge_attributes(self.graph, 'columns')
        nx.draw_networkx_edge_labels(self.graph, pos, edge_labels,
                                    font_size=8)
        
        plt.title('Table Relationships Graph')
        plt.axis('off')
        plt.tight_layout()
        plt.savefig(filename, dpi=300, bbox_inches='tight')
        plt.show()
    
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