import sqlite3
import os
from datetime import datetime, date
from typing import List, Dict, Optional

class DatabaseManager:
    def __init__(self, db_path: str = "al_azhar_school.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize database with required tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Students table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS students (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                father_name TEXT NOT NULL,
                class_name TEXT NOT NULL,
                phone TEXT,
                monthly_fee REAL NOT NULL,
                registration_date DATE NOT NULL,
                is_active BOOLEAN DEFAULT 1
            )
        ''')
        
        # Fee payments table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS fee_payments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id TEXT NOT NULL,
                payment_date DATE NOT NULL,
                amount REAL NOT NULL,
                month_year TEXT NOT NULL,
                payment_method TEXT DEFAULT 'نقدی',
                notes TEXT,
                FOREIGN KEY (student_id) REFERENCES students (student_id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def add_student(self, student_data: Dict) -> bool:
        """Add a new student"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO students (student_id, name, father_name, class_name, 
                                    phone, monthly_fee, registration_date)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                student_data['student_id'],
                student_data['name'],
                student_data['father_name'],
                student_data['class_name'],
                student_data.get('phone', ''),
                student_data['monthly_fee'],
                student_data.get('registration_date', date.today().isoformat())
            ))
            
            conn.commit()
            conn.close()
            return True
        except:
            return False
    
    def get_all_students(self) -> List[Dict]:
        """Get all active students"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT student_id, name, father_name, class_name, phone, monthly_fee
            FROM students WHERE is_active = 1 ORDER BY name
        ''')
        
        columns = [desc[0] for desc in cursor.description]
        students = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        conn.close()
        return students
    
    def add_payment(self, payment_data: Dict) -> bool:
        """Add a fee payment"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO fee_payments (student_id, payment_date, amount, 
                                        month_year, payment_method, notes)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                payment_data['student_id'],
                payment_data['payment_date'],
                payment_data['amount'],
                payment_data['month_year'],
                payment_data.get('payment_method', 'نقدی'),
                payment_data.get('notes', '')
            ))
            
            conn.commit()
            conn.close()
            return True
        except:
            return False
    
    def get_student_payments(self, student_id: str) -> List[Dict]:
        """Get payments for a student"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT payment_date, amount, month_year, payment_method
            FROM fee_payments WHERE student_id = ?
            ORDER BY payment_date DESC
        ''', (student_id,))
        
        columns = [desc[0] for desc in cursor.description]
        payments = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        conn.close()
        return payments
    
    def get_monthly_summary(self, year: int, month: int) -> Dict:
        """Get monthly collection summary"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        month_year = f"{year}-{month:02d}"
        
        cursor.execute('''
            SELECT COALESCE(SUM(amount), 0) as total,
                   COUNT(DISTINCT student_id) as paid_count
            FROM fee_payments WHERE month_year = ?
        ''', (month_year,))
        
        result = cursor.fetchone()
        
        cursor.execute('SELECT COUNT(*) FROM students WHERE is_active = 1')
        total_students = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            'total_collected': result[0],
            'students_paid': result[1],
            'total_students': total_students,
            'students_unpaid': total_students - result[1]
        }
