import os
import json
import sqlite3
from datetime import datetime
from dotenv import load_dotenv

class JobTracker:
    def __init__(self, db_path="data/tracker.db", database_url=None):
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        load_dotenv(os.path.join(base_dir, ".env"))
        
        self.db_path = db_path
        self.database_url = database_url or os.getenv("DATABASE_URL")
        self.is_postgres = False
        
        if self.database_url and (self.database_url.startswith("postgresql://") or self.database_url.startswith("postgres://")):
            self.is_postgres = True
            
        self._ensure_db_exists()
        
    def _get_connection(self):
        if self.is_postgres:
            try:
                import psycopg2
                import psycopg2.extras
                conn = psycopg2.connect(self.database_url)
                return conn
            except Exception as e:
                print(f"⚠️ Warning: Failed to connect to PostgreSQL ({e}). Falling back to local SQLite.")
                self.is_postgres = False
                
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        return sqlite3.connect(self.db_path)

    def _ensure_db_exists(self):
        conn = self._get_connection()
        cursor = conn.cursor()
        
        if self.is_postgres:
            # 1. Master Job Applications Table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS job_applications (
                    id SERIAL PRIMARY KEY,
                    company VARCHAR(255) NOT NULL,
                    title VARCHAR(255) NOT NULL,
                    platform VARCHAR(100) NOT NULL,
                    job_url TEXT UNIQUE NOT NULL,
                    location VARCHAR(255),
                    salary_range VARCHAR(255),
                    raw_job_description TEXT,
                    match_score INTEGER,
                    match_rationale TEXT,
                    custom_pitch TEXT,
                    tailored_resume_path TEXT,
                    submission_status VARCHAR(50) DEFAULT 'APPLIED',
                    error_message TEXT,
                    form_payload JSONB,
                    applied_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                );
            ''')
            
            # 2. Form Q&A Memory Bank Table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS form_qa_bank (
                    id SERIAL PRIMARY KEY,
                    job_url TEXT,
                    company VARCHAR(255),
                    platform VARCHAR(100),
                    question_raw TEXT NOT NULL,
                    field_type VARCHAR(50),
                    answer_text TEXT NOT NULL,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                );
            ''')
            
            # 3. Resume Tailoring Audit History
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS resume_tailoring_history (
                    id SERIAL PRIMARY KEY,
                    job_url TEXT,
                    company VARCHAR(255),
                    role VARCHAR(255),
                    extracted_keywords JSONB,
                    tailored_summary TEXT,
                    tailored_skills JSONB,
                    bullet_replacements JSONB,
                    pdf_path TEXT,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                );
            ''')
            
            # 4. Failed Jobs Table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS failed_jobs (
                    id SERIAL PRIMARY KEY,
                    date_failed TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    company VARCHAR(255),
                    title VARCHAR(255),
                    platform VARCHAR(100),
                    job_url TEXT UNIQUE,
                    error_message TEXT,
                    notified INTEGER DEFAULT 0
                );
            ''')
            
            # 5. Indexes
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_jobs_company ON job_applications(company);')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_jobs_status ON job_applications(submission_status);')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_qa_job ON form_qa_bank(job_url);')
        else:
            # SQLite Tables with backward compatibility
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS applied_jobs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date_applied TEXT,
                    company TEXT,
                    title TEXT,
                    platform TEXT,
                    url TEXT UNIQUE,
                    match_score INTEGER,
                    status TEXT,
                    notes TEXT
                )
            ''')
            
            # Migrate applied_jobs to add new telemetry columns if they do not exist
            cursor.execute("PRAGMA table_info(applied_jobs)")
            cols = [row[1] for row in cursor.fetchall()]
            new_cols = {
                "raw_job_description": "TEXT",
                "match_rationale": "TEXT",
                "custom_pitch": "TEXT",
                "tailored_resume_path": "TEXT",
                "form_payload": "TEXT",
                "location": "TEXT",
                "salary_range": "TEXT"
            }
            for col_name, col_type in new_cols.items():
                if col_name not in cols:
                    try:
                        cursor.execute(f"ALTER TABLE applied_jobs ADD COLUMN {col_name} {col_type}")
                    except Exception:
                        pass

            # Form Q&A Memory Bank
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS form_qa_bank (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    job_url TEXT,
                    company TEXT,
                    platform TEXT,
                    question_raw TEXT NOT NULL,
                    field_type TEXT,
                    answer_text TEXT NOT NULL,
                    created_at TEXT
                )
            ''')

            # Resume Tailoring History
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS resume_tailoring_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    job_url TEXT,
                    company TEXT,
                    role TEXT,
                    extracted_keywords TEXT,
                    tailored_summary TEXT,
                    tailored_skills TEXT,
                    bullet_replacements TEXT,
                    pdf_path TEXT,
                    created_at TEXT
                )
            ''')

            # Failed Jobs Table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS failed_jobs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date_failed TEXT,
                    company TEXT,
                    title TEXT,
                    platform TEXT,
                    url TEXT UNIQUE,
                    error_message TEXT,
                    notified INTEGER DEFAULT 0
                )
            ''')
            
        conn.commit()
        conn.close()

    def log_application(self, company, title, platform, url, score=0, 
                        job_description="", match_rationale="", custom_pitch="", 
                        tailored_resume_path="", form_payload=None, location="", 
                        salary_range="", status="Applied"):
        """Logs an application with full telemetry into PostgreSQL or SQLite."""
        conn = self._get_connection()
        cursor = conn.cursor()
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        try:
            if self.is_postgres:
                payload_json = json.dumps(form_payload) if form_payload else None
                cursor.execute('''
                    INSERT INTO job_applications (
                        company, title, platform, job_url, location, salary_range,
                        raw_job_description, match_score, match_rationale, custom_pitch,
                        tailored_resume_path, submission_status, form_payload, applied_at, updated_at
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
                    ON CONFLICT (job_url) DO UPDATE SET
                        submission_status = EXCLUDED.submission_status,
                        tailored_resume_path = EXCLUDED.tailored_resume_path,
                        updated_at = NOW();
                ''', (company, title, platform, url, location, salary_range,
                      job_description, score, match_rationale, custom_pitch,
                      tailored_resume_path, status, payload_json))
            else:
                payload_str = json.dumps(form_payload) if form_payload else ""
                cursor.execute('''
                    INSERT INTO applied_jobs (
                        date_applied, company, title, platform, url, match_score, status, notes,
                        raw_job_description, match_rationale, custom_pitch, tailored_resume_path,
                        form_payload, location, salary_range
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(url) DO UPDATE SET
                        status = excluded.status,
                        tailored_resume_path = excluded.tailored_resume_path;
                ''', (now_str, company, title, platform, url, score, status, "",
                      job_description, match_rationale, custom_pitch, tailored_resume_path,
                      payload_str, location, salary_range))
            conn.commit()
        except Exception as e:
            print(f"⚠️ Warning: Could not log application for {url}: {e}")
        finally:
            conn.close()

    def log_qa_answer(self, job_url, company, platform, question_raw, field_type, answer_text):
        """Records a screening form question and the exact answer submitted."""
        conn = self._get_connection()
        cursor = conn.cursor()
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            if self.is_postgres:
                cursor.execute('''
                    INSERT INTO form_qa_bank (job_url, company, platform, question_raw, field_type, answer_text, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s, NOW());
                ''', (job_url, company, platform, question_raw, field_type, str(answer_text)))
            else:
                cursor.execute('''
                    INSERT INTO form_qa_bank (job_url, company, platform, question_raw, field_type, answer_text, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?);
                ''', (job_url, company, platform, question_raw, field_type, str(answer_text), now_str))
            conn.commit()
        except Exception as e:
            print(f"⚠️ Warning: Could not log QA item: {e}")
        finally:
            conn.close()

    def log_tailoring(self, job_url, company, role, extracted_keywords, tailored_summary, 
                      tailored_skills, bullet_replacements, pdf_path):
        """Logs exact resume tailoring artifacts generated for this job."""
        conn = self._get_connection()
        cursor = conn.cursor()
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            if self.is_postgres:
                cursor.execute('''
                    INSERT INTO resume_tailoring_history (
                        job_url, company, role, extracted_keywords, tailored_summary,
                        tailored_skills, bullet_replacements, pdf_path, created_at
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW());
                ''', (job_url, company, role, json.dumps(extracted_keywords), tailored_summary,
                      json.dumps(tailored_skills), json.dumps(bullet_replacements), pdf_path))
            else:
                cursor.execute('''
                    INSERT INTO resume_tailoring_history (
                        job_url, company, role, extracted_keywords, tailored_summary,
                        tailored_skills, bullet_replacements, pdf_path, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
                ''', (job_url, company, role, json.dumps(extracted_keywords), tailored_summary,
                      json.dumps(tailored_skills), json.dumps(bullet_replacements), pdf_path, now_str))
            conn.commit()
        except Exception as e:
            print(f"⚠️ Warning: Could not log resume tailoring: {e}")
        finally:
            conn.close()

    def log_failure(self, company, title, platform, url, error_message):
        """Logs a failed application so we do not retry and can alert the user."""
        conn = self._get_connection()
        cursor = conn.cursor()
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            if self.is_postgres:
                cursor.execute('''
                    INSERT INTO failed_jobs (date_failed, company, title, platform, job_url, error_message, notified)
                    VALUES (NOW(), %s, %s, %s, %s, %s, 1)
                    ON CONFLICT (job_url) DO UPDATE SET
                        error_message = EXCLUDED.error_message,
                        date_failed = NOW();
                ''', (company, title, platform, url, str(error_message)[:500]))
            else:
                cursor.execute('''
                    INSERT OR REPLACE INTO failed_jobs (date_failed, company, title, platform, url, error_message, notified)
                    VALUES (?, ?, ?, ?, ?, ?, 1);
                ''', (now_str, company, title, platform, url, str(error_message)[:500]))
            conn.commit()
        except Exception as e:
            print(f"⚠️ Warning: Could not log failure: {e}")
        finally:
            conn.close()

    def has_applied_to(self, url: str) -> bool:
        """Checks if we have already successfully applied to or staged this specific job URL."""
        conn = self._get_connection()
        cursor = conn.cursor()
        applied = False
        try:
            if self.is_postgres:
                cursor.execute("SELECT 1 FROM job_applications WHERE job_url = %s AND submission_status IN ('APPLIED', 'Staged', 'Applied')", (url,))
                applied = cursor.fetchone() is not None
            else:
                cursor.execute("SELECT 1 FROM applied_jobs WHERE url = ? AND status IN ('Applied', 'Staged')", (url,))
                applied = cursor.fetchone() is not None
        except Exception as e:
            print(f"⚠️ DB lookup warning: {e}")
        finally:
            conn.close()
        return applied

    def get_todays_application_count(self) -> int:
        """Counts how many jobs were applied to today."""
        today = datetime.now().strftime("%Y-%m-%d")
        conn = self._get_connection()
        cursor = conn.cursor()
        count = 0
        try:
            if self.is_postgres:
                cursor.execute("SELECT COUNT(*) FROM job_applications WHERE applied_at >= CURRENT_DATE;")
                count = cursor.fetchone()[0]
            else:
                cursor.execute("SELECT COUNT(*) FROM applied_jobs WHERE date_applied LIKE ?", (f"{today}%",))
                count = cursor.fetchone()[0]
        except Exception as e:
            print(f"⚠️ DB count warning: {e}")
        finally:
            conn.close()
        return count

    def get_todays_stats(self) -> dict:
        """Returns a summary of today's and all-time activity."""
        today = datetime.now().strftime("%Y-%m-%d")
        conn = self._get_connection()
        cursor = conn.cursor()
        applied, failed, total = 0, 0, 0
        try:
            if self.is_postgres:
                cursor.execute("SELECT COUNT(*) FROM job_applications WHERE applied_at >= CURRENT_DATE;")
                applied = cursor.fetchone()[0]
                cursor.execute("SELECT COUNT(*) FROM failed_jobs WHERE date_failed >= CURRENT_DATE;")
                failed = cursor.fetchone()[0]
                cursor.execute("SELECT COUNT(*) FROM job_applications;")
                total = cursor.fetchone()[0]
            else:
                cursor.execute("SELECT COUNT(*) FROM applied_jobs WHERE date_applied LIKE ?", (f"{today}%",))
                applied = cursor.fetchone()[0]
                cursor.execute("SELECT COUNT(*) FROM failed_jobs WHERE date_failed LIKE ?", (f"{today}%",))
                failed = cursor.fetchone()[0]
                cursor.execute("SELECT COUNT(*) FROM applied_jobs")
                total = cursor.fetchone()[0]
        except Exception as e:
            print(f"⚠️ DB stats warning: {e}")
        finally:
            conn.close()
        return {"applied_today": applied, "failed_today": failed, "total_all_time": total}

if __name__ == "__main__":
    tracker = JobTracker()
    stats = tracker.get_todays_stats()
    print(f"Database backend: {'PostgreSQL' if tracker.is_postgres else 'SQLite (Local)'}")
    print(f"Applied today: {stats['applied_today']}")
    print(f"Failed today: {stats['failed_today']}")
    print(f"Total all time: {stats['total_all_time']}")
