import sqlite3
import pandas as pd
import json
import os
from config import DB_PATH
from datetime import datetime  # 添加这行

def init_database():
    os.makedirs("data", exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS evaluation_templates (
            template_id INTEGER PRIMARY KEY AUTOINCREMENT,
            template_name TEXT NOT NULL,
            subject TEXT NOT NULL,
            dimensions TEXT NOT NULL,
            description TEXT,
            created_by TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS students (
            student_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            class_name TEXT,
            subject TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS evaluations (
            eval_id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id TEXT,
            lesson_id TEXT,
            lesson_name TEXT,
            subject TEXT,
            template_id INTEGER,
            eval_date TIMESTAMP,
            evaluator TEXT,
            scores_json TEXT NOT NULL,
            total_score REAL,
            comments TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (student_id) REFERENCES students(student_id),
            FOREIGN KEY (template_id) REFERENCES evaluation_templates(template_id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS learning_status (
            status_id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id TEXT,
            lesson_id TEXT,
            subject TEXT,
            pre_lesson_status TEXT,
            risk_level TEXT,
            suggested_focus TEXT,
            generated_at TIMESTAMP,
            FOREIGN KEY (student_id) REFERENCES students(student_id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS phase_evaluations (
            phase_id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id TEXT,
            subject TEXT,
            phase_name TEXT,
            start_date TIMESTAMP,
            end_date TIMESTAMP,
            overall_score REAL,
            overall_level TEXT,
            strength_areas TEXT,
            weakness_areas TEXT,
            development_suggestions TEXT,
            ai_report TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (student_id) REFERENCES students(student_id)
        )
    ''')
    
    conn.commit()
    conn.close()

def import_students(df, subject):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    for _, row in df.iterrows():
        cursor.execute('''
            INSERT OR REPLACE INTO students (student_id, name, class_name, subject)
            VALUES (?, ?, ?, ?)
        ''', (str(row['学号']), row['姓名'], row.get('班级', ''), subject))
    conn.commit()
    conn.close()

def save_template(template_name, subject, dimensions, description="", created_by=""):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO evaluation_templates (template_name, subject, dimensions, description, created_by)
        VALUES (?, ?, ?, ?, ?)
    ''', (template_name, subject, json.dumps(dimensions, ensure_ascii=False), description, created_by))
    conn.commit()
    template_id = cursor.lastrowid
    conn.close()
    return template_id

def get_templates(subject=None):
    conn = sqlite3.connect(DB_PATH)
    query = "SELECT * FROM evaluation_templates"
    params = []
    if subject:
        query += " WHERE subject = ?"
        params.append(subject)
    query += " ORDER BY created_at DESC"
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    if not df.empty:
        df['dimensions'] = df['dimensions'].apply(json.loads)
    return df

def get_template(template_id):
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT * FROM evaluation_templates WHERE template_id = ?", 
                           conn, params=[template_id])
    conn.close()
    if not df.empty:
        result = df.iloc[0].to_dict()
        result['dimensions'] = json.loads(result['dimensions'])
        return result
    return None

def save_evaluation(eval_data):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO evaluations 
        (student_id, lesson_id, lesson_name, subject, template_id, eval_date, evaluator, scores_json, total_score, comments)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        eval_data['student_id'],
        eval_data['lesson_id'],
        eval_data['lesson_name'],
        eval_data['subject'],
        eval_data.get('template_id'),
        eval_data['eval_date'],
        eval_data['evaluator'],
        json.dumps(eval_data['scores'], ensure_ascii=False),
        eval_data['total_score'],
        eval_data.get('comments', '')
    ))
    conn.commit()
    eval_id = cursor.lastrowid
    conn.close()
    return eval_id

def get_student_evaluations(student_id, subject=None):
    conn = sqlite3.connect(DB_PATH)
    query = "SELECT * FROM evaluations WHERE student_id = ?"
    params = [student_id]
    if subject:
        query += " AND subject = ?"
        params.append(subject)
    query += " ORDER BY eval_date"
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    if not df.empty and 'scores_json' in df.columns:
        scores_df = df['scores_json'].apply(lambda x: json.loads(x) if pd.notna(x) else {}).apply(pd.Series)
        df = pd.concat([df.drop('scores_json', axis=1), scores_df], axis=1)
    return df

def get_class_evaluations(lesson_id=None, subject=None, template_id=None):
    conn = sqlite3.connect(DB_PATH)
    query = "SELECT e.*, s.name FROM evaluations e JOIN students s ON e.student_id = s.student_id WHERE 1=1"
    params = []
    if lesson_id:
        query += " AND e.lesson_id = ?"
        params.append(lesson_id)
    if subject:
        query += " AND e.subject = ?"
        params.append(subject)
    if template_id:
        query += " AND e.template_id = ?"
        params.append(template_id)
    query += " ORDER BY e.eval_date"
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    if not df.empty and 'scores_json' in df.columns:
        scores_df = df['scores_json'].apply(lambda x: json.loads(x) if pd.notna(x) else {}).apply(pd.Series)
        df = pd.concat([df.drop('scores_json', axis=1), scores_df], axis=1)
    return df

def save_learning_status(status_data):
    """保存学情快照"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO learning_status 
        (student_id, lesson_id, subject, pre_lesson_status, risk_level, suggested_focus, generated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (
        status_data['student_id'],
        status_data['lesson_id'],
        status_data['subject'],
        status_data['pre_lesson_status'],
        status_data['risk_level'],
        status_data['suggested_focus'],
        datetime.now().strftime('%Y-%m-%d %H:%M:%S')  # 必须是这行，不是 pd.Timestamp.now()
    ))
    conn.commit()
    conn.close()

def save_phase_evaluation(phase_data):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO phase_evaluations 
        (student_id, subject, phase_name, start_date, end_date, overall_score, 
         overall_level, strength_areas, weakness_areas, development_suggestions, ai_report)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        phase_data['student_id'],
        phase_data['subject'],
        phase_data['phase_name'],
        phase_data['start_date'],
        phase_data['end_date'],
        phase_data['overall_score'],
        phase_data['overall_level'],
        phase_data['strength_areas'],
        phase_data['weakness_areas'],
        phase_data['development_suggestions'],
        phase_data['ai_report']
    ))
    conn.commit()
    conn.close()

init_database()