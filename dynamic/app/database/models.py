"""
Database models for Zhihu Hot Questions Scraper
"""
import os
import sqlite3
import datetime
from typing import List, Dict, Any, Optional


class Question:
    """Question model representing a Zhihu hot question"""
    def __init__(self, 
                 id: str, 
                 title: str, 
                 url: str, 
                 answer_count: int = 0, 
                 follow_count: int = 0,
                 hot_score: Optional[int] = None,
                 timestamp: Optional[datetime.datetime] = None):
        self.id = id
        self.title = title
        self.url = url
        self.answer_count = answer_count
        self.follow_count = follow_count
        self.hot_score = hot_score
        self.timestamp = timestamp or datetime.datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert object to dictionary"""
        return {
            'id': self.id,
            'title': self.title,
            'url': self.url,
            'answer_count': self.answer_count,
            'follow_count': self.follow_count,
            'hot_score': self.hot_score,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Question':
        """Create object from dictionary"""
        if 'timestamp' in data and data['timestamp']:
            if isinstance(data['timestamp'], str):
                data['timestamp'] = datetime.datetime.fromisoformat(data['timestamp'])
        return cls(**data)


class QuestionDatabase:
    """Database handler for Zhihu hot questions"""
    def __init__(self, database_path: str):
        """Initialize the database"""
        self.database_path = database_path
        self.conn = None
        self.initialize_db()
    
    def initialize_db(self):
        """Initialize the database schema"""
        # Create database directory if needed
        db_dir = os.path.dirname(self.database_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir)
        
        # Connect to database
        self.conn = sqlite3.connect(self.database_path)
        cursor = self.conn.cursor()
        
        # Create questions table if it doesn't exist
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS questions (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                url TEXT NOT NULL,
                answer_count INTEGER DEFAULT 0,
                follow_count INTEGER DEFAULT 0,
                hot_score INTEGER,
                timestamp TEXT NOT NULL
            )
        ''')
        
        self.conn.commit()
    
    def add_question(self, question: Question) -> bool:
        """Add a question to the database"""
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO questions (id, title, url, answer_count, follow_count, hot_score, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                question.id,
                question.title,
                question.url,
                question.answer_count,
                question.follow_count,
                question.hot_score,
                question.timestamp.isoformat()
            ))
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Error adding question: {e}")
            return False
    
    def add_questions(self, questions: List[Question]) -> int:
        """Add multiple questions to the database"""
        count = 0
        for question in questions:
            if self.add_question(question):
                count += 1
        return count
    
    def get_question(self, question_id: str) -> Optional[Question]:
        """Get a question by ID"""
        try:
            cursor = self.conn.cursor()
            cursor.execute('SELECT * FROM questions WHERE id = ?', (question_id,))
            row = cursor.fetchone()
            if row:
                return Question(
                    id=row[0],
                    title=row[1],
                    url=row[2],
                    answer_count=row[3],
                    follow_count=row[4],
                    hot_score=row[5],
                    timestamp=datetime.datetime.fromisoformat(row[6])
                )
            return None
        except Exception as e:
            print(f"Error getting question: {e}")
            return None
    
    def get_all_questions(self, limit: int = 100, offset: int = 0) -> List[Question]:
        """Get all questions with pagination"""
        questions = []
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                SELECT * FROM questions 
                ORDER BY timestamp DESC
                LIMIT ? OFFSET ?
            ''', (limit, offset))
            
            for row in cursor.fetchall():
                questions.append(Question(
                    id=row[0],
                    title=row[1],
                    url=row[2],
                    answer_count=row[3],
                    follow_count=row[4],
                    hot_score=row[5],
                    timestamp=datetime.datetime.fromisoformat(row[6])
                ))
            
            return questions
        except Exception as e:
            print(f"Error getting questions: {e}")
            return []
    
    def count_questions(self) -> int:
        """Count total questions in the database"""
        try:
            cursor = self.conn.cursor()
            cursor.execute('SELECT COUNT(*) FROM questions')
            return cursor.fetchone()[0]
        except Exception as e:
            print(f"Error counting questions: {e}")
            return 0
    
    def close(self):
        """Close the database connection"""
        if self.conn:
            self.conn.close()
    
    def __del__(self):
        """Destructor to ensure database connection is closed"""
        self.close() 