import sqlite3
import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Any

class DatabaseManager:
    """Manages SQLite database operations for RankRight application"""
    
    def __init__(self, db_path: str = "rankright.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize database with required tables"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Create analyses table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS analyses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    content TEXT NOT NULL,
                    source_info TEXT NOT NULL,
                    summary TEXT NOT NULL,
                    evaluation_results TEXT NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create criteria_results table for detailed storage
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS criteria_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    analysis_id INTEGER,
                    criterion_name TEXT NOT NULL,
                    ranking TEXT NOT NULL,
                    score REAL NOT NULL,
                    explanation TEXT NOT NULL,
                    key_findings TEXT,
                    recommendations TEXT,
                    FOREIGN KEY (analysis_id) REFERENCES analyses (id)
                )
            ''')
            
            conn.commit()
    
    def store_analysis(self, content: str, source_info: str, summary: str, 
                      evaluation_results: Dict[str, Any]) -> int:
        """Store analysis results in database"""
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Insert main analysis record
            cursor.execute('''
                INSERT INTO analyses (content, source_info, summary, evaluation_results)
                VALUES (?, ?, ?, ?)
            ''', (content, source_info, summary, json.dumps(evaluation_results)))
            
            analysis_id = cursor.lastrowid
            
            # Insert detailed criteria results
            for criterion_name, result in evaluation_results.items():
                key_findings = json.dumps(result.get('key_findings', []))
                recommendations = json.dumps(result.get('recommendations', []))
                
                cursor.execute('''
                    INSERT INTO criteria_results 
                    (analysis_id, criterion_name, ranking, score, explanation, key_findings, recommendations)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    analysis_id,
                    criterion_name,
                    result['ranking'],
                    result['score'],
                    result['explanation'],
                    key_findings,
                    recommendations
                ))
            
            conn.commit()
            return analysis_id
    
    def get_analysis(self, analysis_id: int) -> Optional[Dict[str, Any]]:
        """Retrieve specific analysis by ID"""
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, content, source_info, summary, evaluation_results, timestamp
                FROM analyses WHERE id = ?
            ''', (analysis_id,))
            
            row = cursor.fetchone()
            if not row:
                return None
            
            return {
                'id': row[0],
                'content': row[1],
                'source_info': row[2],
                'summary': row[3],
                'evaluation_results': json.loads(row[4]),
                'timestamp': row[5]
            }
    
    def get_all_analyses(self) -> List[Dict[str, Any]]:
        """Retrieve all analyses"""
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, content, source_info, summary, evaluation_results, timestamp
                FROM analyses ORDER BY timestamp DESC
            ''')
            
            rows = cursor.fetchall()
            analyses = []
            
            for row in rows:
                analyses.append({
                    'id': row[0],
                    'content': row[1],
                    'source_info': row[2],
                    'summary': row[3],
                    'evaluation_results': json.loads(row[4]),
                    'timestamp': row[5]
                })
            
            return analyses
    
    def get_criteria_results(self, analysis_id: int) -> List[Dict[str, Any]]:
        """Get detailed criteria results for an analysis"""
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT criterion_name, ranking, score, explanation, key_findings, recommendations
                FROM criteria_results WHERE analysis_id = ?
                ORDER BY criterion_name
            ''', (analysis_id,))
            
            rows = cursor.fetchall()
            results = []
            
            for row in rows:
                results.append({
                    'criterion_name': row[0],
                    'ranking': row[1],
                    'score': row[2],
                    'explanation': row[3],
                    'key_findings': json.loads(row[4]) if row[4] else [],
                    'recommendations': json.loads(row[5]) if row[5] else []
                })
            
            return results
    
    def get_analysis_summary_stats(self) -> Dict[str, Any]:
        """Get summary statistics for all analyses"""
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Total analyses
            cursor.execute('SELECT COUNT(*) FROM analyses')
            total_analyses = cursor.fetchone()[0]
            
            # Ranking distribution
            cursor.execute('''
                SELECT ranking, COUNT(*) 
                FROM criteria_results 
                GROUP BY ranking
            ''')
            ranking_dist = dict(cursor.fetchall())
            
            # Average scores by criterion
            cursor.execute('''
                SELECT criterion_name, AVG(score) as avg_score
                FROM criteria_results 
                GROUP BY criterion_name
                ORDER BY avg_score DESC
            ''')
            avg_scores = dict(cursor.fetchall())
            
            return {
                'total_analyses': total_analyses,
                'ranking_distribution': ranking_dist,
                'average_scores': avg_scores
            }
    
    def clear_all_data(self):
        """Clear all data from database"""
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute('DELETE FROM criteria_results')
            cursor.execute('DELETE FROM analyses')
            
            conn.commit()
    
    def close(self):
        """Close database connection (cleanup)"""
        # SQLite connections are automatically closed when context exits
        pass
