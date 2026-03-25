"""
╔══════════════════════════════════════════════════════════════════════════════╗
║         AI INTERVIEW COACH — ENTERPRISE BACKEND v3.0                       ║
║   Powerful Database | Mistral AI | Multi-Dim Scoring | Full Session History ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

# ═══════════════════════════════════════════════════════════════════════════════
# INITIALIZE ENVIRONMENT & LOGGING FIRST (before any other imports)
# ═══════════════════════════════════════════════════════════════════════════════
import sys
import os

# Set encoding for Windows before anything else
if sys.platform == 'win32':
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except:
        pass

# Set HF token environment variable early
if not os.environ.get('HF_TOKEN'):
    os.environ['HF_TOKEN'] = ''

# Import environment configuration
try:
    from config_environment import app_logger, background_tasks
    logger = app_logger
except ImportError as e:
    # Fallback if config file not found
    import logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    class DummyCounter:
        def increment(self): return 0
        def decrement(self): return 0
        def value(self): return 0
    background_tasks = DummyCounter()

# ═══════════════════════════════════════════════════════════════════════════════
# CONTINUE WITH NORMAL IMPORTS
# ═══════════════════════════════════════════════════════════════════════════════

from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import (
    JWTManager, create_access_token, create_refresh_token,
    jwt_required, get_jwt_identity, get_jwt
)
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import event, text
from sqlalchemy.engine import Engine
from datetime import datetime, timedelta
from openai import OpenAI
import json, logging, traceback, re, warnings
import uuid as uuid_mod
from logging.handlers import RotatingFileHandler
import secrets as _secrets
import threading
import time
import collections

# ── Suppress non-critical warnings for clean logs ─────────────────────────────
warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", category=UserWarning, message=".*unauthenticated.*")
warnings.filterwarnings("ignore", message=".*Core Pydantic V1.*")
warnings.filterwarnings("ignore", message=".*LangChainDeprecationWarning.*")
import logging as python_logging
from urllib3.exceptions import InsecureRequestWarning
warnings.filterwarnings("ignore", category=InsecureRequestWarning)

# ── Load .env ─────────────────────────────────────────────────────────────────
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# ── App Init ──────────────────────────────────────────────────────────────────
app = Flask(__name__)
basedir = os.path.abspath(os.path.dirname(__file__))
frontend_dir = os.path.join(os.path.dirname(basedir), 'frontend')

app.config['SECRET_KEY']              = os.environ.get('SECRET_KEY') or os.urandom(32).hex()
app.config['JWT_SECRET_KEY']          = os.environ.get('JWT_SECRET_KEY') or os.urandom(32).hex()
if not os.environ.get('SECRET_KEY') or not os.environ.get('JWT_SECRET_KEY'):
    logger.warning('[Security] SECRET_KEY or JWT_SECRET_KEY not set in environment. Using random keys (sessions will not survive restarts).')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=1)  # Extended: was 15 min, now 1 hr to prevent mid-interview expiry
app.config['JWT_REFRESH_TOKEN_EXPIRES'] = timedelta(days=30)
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(basedir,"interview_coach.db")}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JSON_SORT_KEYS'] = False
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 31536000
app.config['SQLALCHEMY_ECHO']         = False   # quiet in production
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'connect_args': {'check_same_thread': False},
    'pool_pre_ping': True,
}

# ── SQLite Power-ups: WAL mode + FK enforcement ────────────────────────────────
@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")       # concurrent reads
    cursor.execute("PRAGMA foreign_keys=ON")        # enforce FK contraints
    cursor.execute("PRAGMA synchronous=NORMAL")     # safe + fast
    cursor.execute("PRAGMA cache_size=-32000")      # 32 MB page cache
    cursor.execute("PRAGMA temp_store=MEMORY")      # temp tables in RAM
    cursor.close()

# ── CORS ──────────────────────────────────────────────────────────────────────
_allowed_origins = os.environ.get('ALLOWED_ORIGINS', '*').split(',')
CORS(app, resources={r"/api/*": {
    "origins": _allowed_origins,
    "methods": ["GET","POST","PUT","DELETE","OPTIONS"],
    "allow_headers": ["Content-Type","Authorization"]
}})

# ── Frontend static serving ───────────────────────────────────────────────────
@app.route('/')
def serve_index():
    from flask import send_from_directory
    return send_from_directory(frontend_dir, 'index.html')

@app.route('/<path:filename>')
def serve_frontend(filename):
    from flask import send_from_directory
    if os.path.exists(os.path.join(frontend_dir, filename)):
        return send_from_directory(frontend_dir, filename)
    return jsonify({'error': 'Not found'}), 404

# ── Extensions ────────────────────────────────────────────────────────────────
db  = SQLAlchemy(app)
jwt = JWTManager(app)

# ── Rate Limiter ──────────────────────────────────────────────────────────────
try:
    from flask_limiter import Limiter
    from flask_limiter.util import get_remote_address
    limiter = Limiter(get_remote_address, app=app, default_limits=[],
                      storage_uri='memory://')
    _rate_limit = limiter.limit
except ImportError:
    # flask-limiter not installed — skip rate-limiting gracefully
    def _rate_limit(*a, **kw):
        def _id(fn): return fn
        return _id
    limiter = None
    logger.warning('[Auth] flask-limiter not installed — rate limiting disabled. pip install flask-limiter')

# ── JWT Error Handlers (no more 422!) ─────────────────────────────────────────
@jwt.invalid_token_loader
def invalid_token_cb(reason):
    return jsonify({'error': f'Invalid token: {reason}'}), 401

@jwt.unauthorized_loader
def missing_token_cb(reason):
    return jsonify({'error': 'Authorization token missing. Please log in.'}), 401

@jwt.expired_token_loader
def expired_token_cb(header, payload):
    return jsonify({'error': 'Session expired. Please log in again.'}), 401

@jwt.revoked_token_loader
def revoked_token_cb(header, payload):
    return jsonify({'error': 'Token revoked. Please log in again.'}), 401

# ── Security Headers ──────────────────────────────────────────────────────────
@app.after_request
def add_security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    response.headers['Permissions-Policy'] = 'camera=(), microphone=(), geolocation=()'
    if request.is_secure:
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    return response

# ── JWT Token Blocklist Check ─────────────────────────────────────────────────
@jwt.token_in_blocklist_loader
def check_if_token_revoked(jwt_header, jwt_payload):
    """Check if a JWT jti is in the blocklist (i.e. user logged out)."""
    jti = jwt_payload['jti']
    token = db.session.query(TokenBlocklist.id).filter_by(jti=jti).scalar()
    return token is not None

# ── Shared password-strength validator ────────────────────────────────────────
_PASSWORD_MIN_LEN = 8
_PASSWORD_RULES = [
    (lambda p: len(p) >= _PASSWORD_MIN_LEN,     f'Password must be at least {_PASSWORD_MIN_LEN} characters'),
    (lambda p: any(c.isupper() for c in p),      'Password must contain at least one uppercase letter'),
    (lambda p: any(c.islower() for c in p),      'Password must contain at least one lowercase letter'),
    (lambda p: any(c.isdigit() for c in p),      'Password must contain at least one number'),
]

def validate_password_strength(password):
    """Return first failing rule message, or None if strong enough."""
    for check_fn, msg in _PASSWORD_RULES:
        if not check_fn(password):
            return msg
    return None

# ── Account lockout constants ─────────────────────────────────────────────────
MAX_FAILED_LOGINS   = 5          # lock after 5 consecutive failures
LOCKOUT_DURATION    = timedelta(minutes=15)   # 15-minute lockout

# ── Logging ───────────────────────────────────────────────────────────────────
os.makedirs('logs', exist_ok=True)
fh = RotatingFileHandler('logs/ai_coach.log', maxBytes=10_000_000, backupCount=5, encoding='utf-8')
fh.setFormatter(logging.Formatter('%(asctime)s %(levelname)s: %(message)s [%(pathname)s:%(lineno)d]'))
fh.setLevel(logging.INFO)
app.logger.addHandler(fh)
app.logger.setLevel(logging.INFO)
app.logger.info('AI Interview Coach Enterprise Backend Starting...')

# ── Interview Manager (helper module for validation and business logic) ────────
try:
    from interview_manager import (
        InterviewSessionManager,
        MockQuestionInterviewHandler,
        WrittenInterviewHandler,
        interview_error_handler,
    )
    _interview_manager_loaded = True
except ImportError as _im_err:
    app.logger.warning(f'[Interview] interview_manager not loaded: {_im_err}')
    _interview_manager_loaded = False


# ══════════════════════════════════════════════════════════════════════════════
#  DATABASE MODELS — ENTERPRISE GRADE
# ══════════════════════════════════════════════════════════════════════════════

# Field name normalization mapping
FIELD_NAME_MAP = {
    'software': 'Software Engineering',
    'software-engineering': 'Software Engineering',
    'data-science': 'Data Science',
    'data': 'Data Science',
    'product': 'Product Management',
    'product-management': 'Product Management',
    'marketing': 'Marketing',
    'sales': 'Sales',
    'finance': 'Finance',
}

LEVEL_NAME_MAP = {
    'entry': 'Entry',
    'junior': 'Entry',
    'mid': 'Mid',
    'senior': 'Senior',
    'lead': 'Lead',
    'principal': 'Lead',
}

COMPANY_NAME_MAP = {
    'google': 'Google',
    'amazon': 'Amazon',
    'microsoft': 'Microsoft',
    'meta': 'Meta',
    'facebook': 'Meta',
    'apple': 'Apple',
    'netflix': 'Netflix',
    'startup': 'Startup',
}

class User(db.Model):
    """
    Core user account with full professional profile.
    Everything Mistral needs to personalise questions lives here.
    """
    __tablename__ = 'users'

    id                 = db.Column(db.Integer,     primary_key=True)
    uuid               = db.Column(db.String(36),  unique=True, nullable=False,
                                   default=lambda: str(uuid_mod.uuid4()))
    email              = db.Column(db.String(120),  unique=True, nullable=False)
    password_hash      = db.Column(db.String(255),  nullable=False)

    # Profile
    first_name         = db.Column(db.String(50))
    last_name          = db.Column(db.String(50))
    phone              = db.Column(db.String(20))
    linkedin_url       = db.Column(db.String(255))
    github_url         = db.Column(db.String(255))
    profile_picture    = db.Column(db.String(255))
    headline           = db.Column(db.String(200))          # "Senior Software Engineer at Google"
    resume_summary     = db.Column(db.Text)                 # pasted resume / bio

    # Professional context (fed to Mistral for personalised questions)
    experience_years   = db.Column(db.Integer, default=0)
    current_role       = db.Column(db.String(100))
    skills             = db.Column(db.Text)                 # JSON list ["Python","React",…]
    education          = db.Column(db.Text)                 # JSON list [{degree, school, year}]
    dream_companies    = db.Column(db.Text)                 # JSON list ["Google","Meta",…]
    target_roles       = db.Column(db.Text)                 # JSON list ["SDE II","ML Engineer"]

    # Subscription
    subscription_tier  = db.Column(db.String(20), default='free')  # free | pro | enterprise

    # Aggregate stats (maintained by triggers / endpoint logic)
    total_interviews   = db.Column(db.Integer, default=0)
    total_questions_answered = db.Column(db.Integer, default=0)
    total_practice_time= db.Column(db.Integer, default=0)   # seconds
    average_score      = db.Column(db.Float,   default=0.0)
    best_score         = db.Column(db.Float,   default=0.0)
    current_streak     = db.Column(db.Integer, default=0)
    longest_streak     = db.Column(db.Integer, default=0)
    last_activity_date = db.Column(db.Date)

    # Meta
    is_active          = db.Column(db.Boolean, default=True)
    email_verified     = db.Column(db.Boolean, default=False)
    created_at         = db.Column(db.DateTime, default=datetime.utcnow)
    last_login         = db.Column(db.DateTime)

    # Password Reset Fields (for forgot password functionality)
    password_reset_token = db.Column(db.String(255))           # Secure reset token
    password_reset_token_expiry = db.Column(db.DateTime)       # Token expiration time

    # Security — brute-force / account-lockout
    failed_login_attempts   = db.Column(db.Integer, default=0)
    account_locked_until    = db.Column(db.DateTime)            # NULL = not locked
    last_failed_login       = db.Column(db.DateTime)
    password_changed_at     = db.Column(db.DateTime)            # track password changes

    # Relationships
    interviews  = db.relationship('Interview', backref='user', lazy='dynamic',
                                  cascade='all, delete-orphan')
    feedbacks   = db.relationship('Feedback', backref='user', lazy='dynamic',
                                  cascade='all, delete-orphan')

    # ── Indexes ───────────────────────────────────────────────────────────────
    __table_args__ = (
        db.Index('ix_users_email',    'email'),
        db.Index('ix_users_uuid',     'uuid'),
        db.Index('ix_users_is_active','is_active'),
    )

    def set_password(self, pw):   self.password_hash = generate_password_hash(pw)
    def check_password(self, pw): return check_password_hash(self.password_hash, pw)

    def generate_password_reset_token(self):
        """Generate a secure password reset token valid for 1 hour"""
        import secrets
        self.password_reset_token = secrets.token_urlsafe(32)  # 32-char secure token
        self.password_reset_token_expiry = datetime.utcnow() + timedelta(hours=1)
        return self.password_reset_token
    
    def verify_password_reset_token(self, token):
        """Verify if the reset token is valid and not expired"""
        if not self.password_reset_token or not self.password_reset_token_expiry:
            return False
        if self.password_reset_token != token:
            return False
        if datetime.utcnow() > self.password_reset_token_expiry:
            return False
        return True
    
    def clear_password_reset_token(self):
        """Clear the reset token after successful password change"""
        self.password_reset_token = None
        self.password_reset_token_expiry = None

    def skills_list(self):
        try: return json.loads(self.skills or '[]')
        except: return []

    def dream_companies_list(self):
        try: return json.loads(self.dream_companies or '[]')
        except: return []

    def to_dict(self):
        return {
            'id': self.id, 'uuid': self.uuid, 'email': self.email,
            'first_name': self.first_name, 'last_name': self.last_name,
            'headline': self.headline, 'experience_years': self.experience_years,
            'current_role': self.current_role,
            'skills': self.skills_list(),
            'dream_companies': self.dream_companies_list(),
            'subscription_tier': self.subscription_tier,
            'total_interviews': self.total_interviews,
            'total_questions_answered': self.total_questions_answered,
            'average_score': round(self.average_score or 0.0, 2),
            'best_score': round(self.best_score or 0.0, 2),
            'current_streak': self.current_streak or 0,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None,
        }


class TokenBlocklist(db.Model):
    """
    Stores revoked JWT token IDs (jti) so logout actually invalidates tokens.
    """
    __tablename__ = 'token_blocklist'
    id         = db.Column(db.Integer, primary_key=True)
    jti        = db.Column(db.String(36), nullable=False, index=True, unique=True)
    token_type = db.Column(db.String(10), nullable=False)   # 'access' or 'refresh'
    user_id    = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=False)


class Interview(db.Model):
    """
    A single practice session — the top-level container for questions + answers.
    """
    __tablename__ = 'interviews'

    id               = db.Column(db.Integer, primary_key=True)
    uuid             = db.Column(db.String(36), unique=True, nullable=False,
                                 default=lambda: str(uuid_mod.uuid4()))
    user_id          = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'),
                                 nullable=False)

    # Session config
    field            = db.Column(db.String(100))    # "Software Engineering"
    level            = db.Column(db.String(50))     # "Mid" / "Senior"
    company          = db.Column(db.String(100))    # "Google"
    interview_type   = db.Column(db.String(50), default='technical')
    mode             = db.Column(db.String(20),  default='text')
    question_type    = db.Column(db.String(50), default='mock')  # mock | written
    answer_type      = db.Column(db.String(50), default='mock')  # backward-compatible alias (user requested rename)

    # AI context stored for full reproducibility
    user_profile_snapshot = db.Column(db.Text)      # JSON snapshot of user profile at session start
    question_prompt       = db.Column(db.Text)      # The exact prompt sent to Mistral
    ai_model_used         = db.Column(db.String(80))

    # Timeline
    started_at       = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at     = db.Column(db.DateTime)
    duration_seconds = db.Column(db.Integer,  default=0)
    status           = db.Column(db.String(20), default='in_progress')  # in_progress | completed | abandoned

    # Scores
    questions_total    = db.Column(db.Integer, default=5)
    questions_answered = db.Column(db.Integer, default=0)
    overall_score      = db.Column(db.Float)
    technical_score    = db.Column(db.Float)
    communication_score= db.Column(db.Float)
    clarity_score      = db.Column(db.Float)
    depth_score        = db.Column(db.Float)
    performance_grade  = db.Column(db.String(2))    # A+ A B C D F

    # Relationships
    questions = db.relationship('Question', backref='interview', lazy=True,
                                cascade='all, delete-orphan',
                                order_by='Question.question_number')
    answers   = db.relationship('Answer',   backref='interview', lazy=True,
                                cascade='all, delete-orphan')

    __table_args__ = (
        db.Index('ix_interviews_user_id',      'user_id'),
        db.Index('ix_interviews_uuid',         'uuid'),
        db.Index('ix_interviews_status',       'status'),
        db.Index('ix_interviews_started_at',   'started_at'),
        db.Index('ix_interviews_user_status',  'user_id', 'status'),
    )

    def _grade(self, score):
        if score is None: return None
        if score >= 9.0: return 'A+'
        if score >= 8.0: return 'A'
        if score >= 7.0: return 'B'
        if score >= 6.0: return 'C'
        if score >= 5.0: return 'D'
        return 'F'

    def to_dict(self):
        return {
            'id': self.id, 'uuid': self.uuid, 'user_id': self.user_id,
            'field': self.field, 'level': self.level, 'company': self.company,
            'interview_type': self.interview_type, 'mode': self.mode, 'question_type': self.question_type,
            'answer_type': self.answer_type or self.question_type,
            'status': self.status,
            'questions_total': self.questions_total,
            'questions_answered': self.questions_answered,
            'overall_score': round(self.overall_score, 2) if self.overall_score else None,
            'technical_score': round(self.technical_score, 2) if self.technical_score else None,
            'communication_score': round(self.communication_score, 2) if self.communication_score else None,
            'performance_grade': self._grade(self.overall_score),
            'ai_model_used': self.ai_model_used,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'duration_seconds': self.duration_seconds,
        }


class Question(db.Model):
    """
    A question generated by Mistral (or pulled from the bank) for a session.
    Stores the exact question, expected answer points, and Mistral's context.
    """
    __tablename__ = 'questions'

    id              = db.Column(db.Integer, primary_key=True)
    uuid            = db.Column(db.String(36), unique=True, nullable=False,
                                default=lambda: str(uuid_mod.uuid4()))
    interview_id    = db.Column(db.Integer, db.ForeignKey('interviews.id', ondelete='CASCADE'),
                                nullable=True)

    text            = db.Column(db.Text, nullable=False)
    category        = db.Column(db.String(50))       # technical | behavioral | system_design
    field           = db.Column(db.String(100))
    level           = db.Column(db.String(50))
    company         = db.Column(db.String(100))
    difficulty      = db.Column(db.String(20))       # easy | medium | hard | expert
    topic_tags      = db.Column(db.Text)             # JSON list ["arrays","recursion"]
    hint            = db.Column(db.Text)
    sample_answer   = db.Column(db.Text)
    expected_points = db.Column(db.Text)             # JSON list of key points Mistral expects
    time_limit_secs = db.Column(db.Integer, default=300)
    source          = db.Column(db.String(30), default='ai_generated')  # ai_generated | bank | user

    # Multiple-choice fields (NEW)
    is_multiple_choice = db.Column(db.Boolean, default=False)  # if true, this question has options
    options          = db.Column(db.Text)             # JSON list of 5 options
    correct_answers  = db.Column(db.Text)             # JSON list of correct indices [0,2] or [1]
    multiple_allowed = db.Column(db.Boolean, default=False)  # if true, multiple correct answers allowed

    question_number = db.Column(db.Integer, default=1)
    created_at      = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    answers = db.relationship('Answer', backref='question', lazy=True)

    __table_args__ = (
        db.Index('ix_questions_interview_id', 'interview_id'),
        db.Index('ix_questions_uuid',         'uuid'),
        db.Index('ix_questions_field_level',  'field', 'level'),
        db.Index('ix_questions_company',      'company'),
        db.Index('ix_questions_category',     'category'),
    )

    def options_list(self):
        try: return json.loads(self.options or '[]')
        except: return []
    
    def correct_answers_list(self):
        try: return json.loads(self.correct_answers or '[]')
        except: return []

    def to_dict(self):
        return {
            'id': self.id, 'uuid': self.uuid,
            'text': self.text, 'category': self.category,
            'field': self.field, 'level': self.level,
            'company': self.company, 'difficulty': self.difficulty or 'medium',
            'topic_tags': json.loads(self.topic_tags or '[]'),
            'hint': self.hint,
            'time_limit_secs': self.time_limit_secs,
            'question_number': self.question_number,
            'source': self.source,
            'is_multiple_choice': self.is_multiple_choice,
            'options': self.options_list(),
            'correct_answers': self.correct_answers_list(),
            'multiple_allowed': self.multiple_allowed,
        }


class Answer(db.Model):
    """
    User's answer to a question — stores the text plus ALL AI-scored dimensions.
    This is the core analytics record.
    """
    __tablename__ = 'answers'

    id              = db.Column(db.Integer, primary_key=True)
    uuid            = db.Column(db.String(36), unique=True, nullable=False,
                                default=lambda: str(uuid_mod.uuid4()))
    interview_id    = db.Column(db.Integer, db.ForeignKey('interviews.id', ondelete='CASCADE'),
                                nullable=False)
    question_id     = db.Column(db.Integer, db.ForeignKey('questions.id', ondelete='SET NULL'),
                                nullable=True)

    text            = db.Column(db.Text)
    word_count      = db.Column(db.Integer, default=0)
    selected_options = db.Column(db.Text)             # JSON list of selected option indices [0,2]

    # 6-dimension AI scores (each 0-10)
    score                = db.Column(db.Float)   # overall weighted
    technical_accuracy   = db.Column(db.Float)
    depth_score          = db.Column(db.Float)
    clarity_score        = db.Column(db.Float)
    relevance_score      = db.Column(db.Float)
    communication_score  = db.Column(db.Float)
    confidence_score     = db.Column(db.Float)

    time_spent_seconds   = db.Column(db.Integer, default=0)
    submitted_at         = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    feedbacks = db.relationship('Feedback', backref='answer', lazy=True,
                                cascade='all, delete-orphan')

    __table_args__ = (
        db.Index('ix_answers_interview_id', 'interview_id'),
        db.Index('ix_answers_question_id',  'question_id'),
        db.Index('ix_answers_uuid',         'uuid'),
        db.Index('ix_answers_submitted_at', 'submitted_at'),
    )

    def selected_options_list(self):
        try: return json.loads(self.selected_options or '[]')
        except: return []

    def to_dict(self):
        try:
            return {
                'id': self.id, 'uuid': self.uuid,
                'interview_id': self.interview_id, 'question_id': self.question_id,
                'text': self.text, 'word_count': self.word_count or 0,
                'selected_options': self.selected_options_list() if hasattr(self, 'selected_options') and self.selected_options else [],
                'score': round(self.score, 2) if self.score else None,
                'technical_accuracy': round(self.technical_accuracy, 2) if self.technical_accuracy else None,
                'depth_score': round(self.depth_score, 2) if self.depth_score else None,
                'clarity_score': round(self.clarity_score, 2) if self.clarity_score else None,
                'relevance_score': round(self.relevance_score, 2) if self.relevance_score else None,
                'communication_score': round(self.communication_score, 2) if self.communication_score else None,
                'confidence_score': round(self.confidence_score, 2) if self.confidence_score else None,
                'time_spent_seconds': self.time_spent_seconds or 0,
                'submitted_at': self.submitted_at.isoformat() if self.submitted_at else None,
            }
        except Exception as e:
            app.logger.debug(f"[Answer.to_dict] Serialization issue: {e}")
            return {
                'id': self.id, 'uuid': self.uuid,
                'interview_id': self.interview_id, 'question_id': self.question_id,
                'text': self.text,
            }


class Feedback(db.Model):
    """
    Mistral AI's full structured feedback for one answer.
    Includes strengths, weaknesses, improvement plan, and suggested resources.
    """
    __tablename__ = 'feedback'

    id               = db.Column(db.Integer, primary_key=True)
    uuid             = db.Column(db.String(36), unique=True, nullable=False,
                                 default=lambda: str(uuid_mod.uuid4()))
    user_id          = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'),
                                 nullable=False)
    answer_id        = db.Column(db.Integer, db.ForeignKey('answers.id', ondelete='CASCADE'),
                                 nullable=False)

    score            = db.Column(db.Float)
    strengths        = db.Column(db.Text)           # JSON list
    improvements     = db.Column(db.Text)           # JSON list
    detailed_feedback= db.Column(db.Text)
    improvement_plan = db.Column(db.Text)           # JSON list of 3 specific action items
    model_used       = db.Column(db.String(80))
    generated_at     = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        db.Index('ix_feedback_user_id',   'user_id'),
        db.Index('ix_feedback_answer_id', 'answer_id'),
        db.Index('ix_feedback_uuid',      'uuid'),
    )

    def strengths_list(self):
        try: return json.loads(self.strengths or '[]')
        except: return []

    def improvements_list(self):
        try: return json.loads(self.improvements or '[]')
        except: return []

    def improvement_plan_list(self):
        try: return json.loads(self.improvement_plan or '[]')
        except: return []

    def to_dict(self):
        try:
            return {
                'id': self.id, 'uuid': self.uuid,
                'score': round(self.score, 2) if self.score else None,
                'strengths': self.strengths_list() if hasattr(self, 'strengths') and self.strengths else [],
                'improvements': self.improvements_list() if hasattr(self, 'improvements') and self.improvements else [],
                'detailed_feedback': self.detailed_feedback or '',
                'improvement_plan': self.improvement_plan_list() if hasattr(self, 'improvement_plan') and self.improvement_plan else [],
                'model_used': self.model_used or 'unknown',
                'generated_at': self.generated_at.isoformat() if self.generated_at else None,
            }
        except Exception as e:
            app.logger.debug(f"[Feedback.to_dict] Serialization issue: {e}")
            return {
                'id': self.id, 'uuid': self.uuid,
                'score': self.score,
                'detailed_feedback': self.detailed_feedback or '',
            }


class QuestionBank(db.Model):
    """
    Global reusable question library independent of any session.
    Mistral-generated and curated, indexed for fast lookup.
    """
    __tablename__ = 'question_bank'

    id              = db.Column(db.Integer, primary_key=True)
    uuid            = db.Column(db.String(36), unique=True, nullable=False,
                                default=lambda: str(uuid_mod.uuid4()))
    text            = db.Column(db.Text, nullable=False)
    category        = db.Column(db.String(50))
    field           = db.Column(db.String(100))
    level           = db.Column(db.String(50))
    company         = db.Column(db.String(100))
    difficulty      = db.Column(db.String(20), default='medium')
    question_type   = db.Column(db.String(50), default='mock')  # mock | written (NEW)
    answer_type     = db.Column(db.String(50), default='mock')  # For backward compatibility (NEW)
    topic_tags      = db.Column(db.Text)
    expected_points = db.Column(db.Text)
    sample_answer   = db.Column(db.Text)
    hint            = db.Column(db.Text)
    times_used      = db.Column(db.Integer, default=0)
    avg_score       = db.Column(db.Float,   default=0.0)
    is_verified     = db.Column(db.Boolean, default=False)
    created_at      = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        db.Index('ix_qbank_field_level',   'field', 'level'),
        db.Index('ix_qbank_question_type', 'question_type'),
        db.Index('ix_qbank_company',       'company'),
        db.Index('ix_qbank_category',      'category'),
        db.Index('ix_qbank_difficulty',    'difficulty'),
    )

    def to_dict(self):
        return {
            'id': self.id, 'uuid': self.uuid,
            'text': self.text, 'category': self.category,
            'field': self.field, 'level': self.level,
            'company': self.company, 'difficulty': self.difficulty,
            'topic_tags': json.loads(self.topic_tags or '[]'),
            'hint': self.hint,
            'times_used': self.times_used,
            'avg_score': round(self.avg_score or 0, 2),
            'is_verified': self.is_verified,
        }


class HybridInterviewSession(db.Model):
    """
    Tracks hybrid loading state: questions from DB are shown immediately,
    while AI loads more advanced questions in the background.
    This reduces perceived latency from 40-50 seconds to <500ms.
    """
    __tablename__ = 'hybrid_interview_sessions'

    id              = db.Column(db.Integer, primary_key=True)
    uuid            = db.Column(db.String(36), unique=True, nullable=False,
                                default=lambda: str(uuid_mod.uuid4()))
    interview_id    = db.Column(db.Integer, db.ForeignKey('interviews.id', ondelete='CASCADE'),
                                nullable=False)
    
    # Hybrid loading state
    loading_mode    = db.Column(db.String(20), default='hybrid')  # hybrid | ai_only | db_only
    db_questions_loaded = db.Column(db.Boolean, default=False)    # DB questions shown immediately
    ai_questions_loaded = db.Column(db.Boolean, default=False)    # AI questions generated in background
    ai_load_time_sec = db.Column(db.Float)                         # How long AI took to generate
    
    # Question sources by number
    question_sources = db.Column(db.Text)  # JSON: {"1": "db", "2": "ai", "3": "db", ...}
    
    # Performance metrics
    initial_load_time_ms = db.Column(db.Float)  # Time to load initial DB questions (<500ms target)
    total_load_time_sec  = db.Column(db.Float)  # Total time until AI finishes
    
    created_at      = db.Column(db.DateTime, default=datetime.utcnow)
    ai_finish_time  = db.Column(db.DateTime)    # When AI finished generating questions

    __table_args__ = (
        db.Index('ix_hybrid_interview_id', 'interview_id'),
        db.Index('ix_hybrid_loading_mode',  'loading_mode'),
    )

    def question_sources_dict(self):
        try:
            return json.loads(self.question_sources or '{}')
        except:
            return {}

    def to_dict(self):
        return {
            'id': self.id, 'uuid': self.uuid,
            'interview_id': self.interview_id,
            'loading_mode': self.loading_mode,
            'db_questions_loaded': self.db_questions_loaded,
            'ai_questions_loaded': self.ai_questions_loaded,
            'ai_load_time_sec': round(self.ai_load_time_sec, 2) if self.ai_load_time_sec else None,
            'initial_load_time_ms': round(self.initial_load_time_ms, 1) if self.initial_load_time_ms else None,
            'total_load_time_sec': round(self.total_load_time_sec, 2) if self.total_load_time_sec else None,
            'question_sources': self.question_sources_dict(),
        }


# ==============================================================================
#  USER ANALYTICS & RECOMMENDATION MODELS
# ==============================================================================

class UserAnalytics(db.Model):
    """
    Track user's performance profile for personalized question generation.
    Analyzes strengths/weaknesses by field, level, category, etc.
    """
    __tablename__ = 'user_analytics'
    
    id              = db.Column(db.Integer, primary_key=True)
    user_id         = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'),
                                nullable=False, unique=True)
    
    # Field-level performance (JSON: {field -> {level -> score}})
    field_scores    = db.Column(db.Text, default='{}')  # Aggregated scores by field
    
    # Category performance (JSON: {category -> {accuracy, count}})
    category_performance = db.Column(db.Text, default='{}')  # Technical, Behavioral, System Design
    
    # Weak topics (JSON: [topic1, topic2, ...])
    weak_topics     = db.Column(db.Text, default='[]')
    strong_topics   = db.Column(db.Text, default='[]')
    
    # Interview statistics
    total_interviews = db.Column(db.Integer, default=0)
    total_questions = db.Column(db.Integer, default=0)
    correct_answers = db.Column(db.Integer, default=0)
    
    # Average scores by dimension
    avg_technical_accuracy = db.Column(db.Float, default=0.0)
    avg_clarity = db.Column(db.Float, default=0.0)
    avg_depth = db.Column(db.Float, default=0.0)
    avg_communication = db.Column(db.Float, default=0.0)
    
    # Last updated
    updated_at      = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        db.Index('ix_analytics_user_id', 'user_id'),
    )
    
    def field_scores_dict(self):
        try: return json.loads(self.field_scores or '{}')
        except: return {}
    
    def category_perf_dict(self):
        try: return json.loads(self.category_performance or '{}')
        except: return {}
    
    def weak_topics_list(self):
        try: return json.loads(self.weak_topics or '[]')
        except: return []
    
    def strong_topics_list(self):
        try: return json.loads(self.strong_topics or '[]')
        except: return []


class QuestionRecommendation(db.Model):
    """
    Stores recommended questions for users based on their weak areas.
    System generates personalized questions targeting specific weaknesses.
    """
    __tablename__ = 'question_recommendations'
    
    id              = db.Column(db.Integer, primary_key=True)
    user_id         = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'),
                                nullable=False)
    
    # What the recommendation targets
    target_field    = db.Column(db.String(100), nullable=False)
    target_level    = db.Column(db.String(50), nullable=False)
    target_topic    = db.Column(db.String(100), nullable=False)  # Weak topic
    reason          = db.Column(db.Text)  # Why this question was recommended
    
    # The recommended question ID
    question_id     = db.Column(db.Integer, db.ForeignKey('questions.id'))
    question_bank_id = db.Column(db.Integer, db.ForeignKey('question_bank.id'))
    
    # Recommendation metadata
    difficulty_boost = db.Column(db.Float, default=0.0)  # How much harder than usual
    priority        = db.Column(db.Integer, default=0)   # Higher = more focused on weak area
    was_attempted   = db.Column(db.Boolean, default=False)
    attempt_score   = db.Column(db.Float)  # Score if user attempted
    
    created_at      = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at      = db.Column(db.DateTime)  # Recommendations expire over time
    
    __table_args__ = (
        db.Index('ix_rec_user_id', 'user_id'),
        db.Index('ix_rec_target_field', 'target_field'),
        db.Index('ix_rec_priority', 'priority'),
    )


class AnswerCache(db.Model):
    """
    Cache for answer analysis to speed up feedback generation.
    Stores pre-computed scores and feedback for similar answers.
    """
    __tablename__ = 'answer_cache'
    
    id              = db.Column(db.Integer, primary_key=True)
    
    # Question + answer hash (for quick lookup)
    question_hash   = db.Column(db.String(64), nullable=False)  # SHA256 of question
    answer_hash     = db.Column(db.String(64), nullable=False)  # SHA256 of answer
    answer_length   = db.Column(db.Integer)  # Word count bucket
    
    # Cached analysis (JSON)
    cached_analysis = db.Column(db.Text, nullable=False)  # All 6 dimensions + feedback
    
    # Stats
    hit_count       = db.Column(db.Integer, default=0)  # How many times used
    created_at      = db.Column(db.DateTime, default=datetime.utcnow)
    last_accessed   = db.Column(db.DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        db.Index('ix_cache_question_hash', 'question_hash'),
        db.Index('ix_cache_answer_hash', 'answer_hash'),
        db.Index('ix_cache_hit_count', 'hit_count'),
    )
    
    def cached_analysis_dict(self):
        try: return json.loads(self.cached_analysis or '{}')
        except: return {}


# ==============================================================================
#  MISTRAL AI AGENT - ENTERPRISE GRADE
# ==============================================================================

COMPANY_STYLES = {
    'google':    "Google favours deep algorithmic thinking, system design at scale, and STAR behavioral answers.",
    'amazon':    "Amazon uses Leadership Principles for behaviorals. Expect coding, system design, and LP stories.",
    'microsoft': "Microsoft balances coding fundamentals, design, and growth-mindset culture fit.",
    'meta':      "Meta focuses on speed + correctness in coding, product sense, and collaboration at massive scale.",
    'apple':     "Apple values quality, detail, and product thinking. Deep dives into past projects.",
    'netflix':   "Netflix values high performance, independent decision-making, and data-driven thinking.",
    'startup':   "Startups value versatility, speed, and ownership. Broad scope and product intuition.",
    'default':   "Focus on solid fundamentals, clear communication, and real-world problem-solving.",
}

DIFFICULTY_MAP = {
    'entry':   ('easy',   'warm-up and intermediate level'),
    'junior':  ('easy',   'warm-up and intermediate level'),
    'mid':     ('medium', 'intermediate and advanced level'),
    'senior':  ('hard',   'advanced and expert level'),
    'lead':    ('expert', 'expert and architecture-level'),
    'default': ('medium', 'intermediate level'),
}


class MistralPerformanceController:
    """
    Adaptive performance controller for local LLM (LM Studio).
    
    Tracks response times and parse success rates, then automatically tunes
    max_tokens, temperature, top_p, timeout, and prompt verbosity so every call
    is as fast AND as accurate as possible for the current situation.

    Situations handled:
    - Task type        : mc_questions | text_questions | analysis
    - Field complexity : simple (HTML/CSS) vs complex (ML/distributed-systems)
    - Interview level  : junior / mid / senior / lead
    - Answer length    : short (<80 words) / medium / long (>300 words)
    - Recent speed     : auto-reduces tokens when model is running slow
    - Parse failures   : auto-switches to safer format after failures
    """

    # Fields ranked by complexity (1=simple → 5=very complex)
    FIELD_COMPLEXITY = {
        'html': 1, 'css': 1, 'ui': 1,
        'javascript': 2, 'frontend': 2, 'react': 2, 'vue': 2,
        'python': 2, 'java': 2, 'sql': 2,
        'backend': 3, 'fullstack': 3, 'nodejs': 3, 'django': 3,
        'devops': 3, 'cloud': 3, 'aws': 3, 'docker': 3,
        'software': 3, 'engineering': 3,
        'system design': 4, 'architecture': 4, 'databases': 4,
        'machine learning': 5, 'ml': 5, 'ai': 5, 'data science': 5,
        'distributed': 5, 'security': 4, 'blockchain': 4,
    }

    # Level multipliers for token budget (more senior = deeper answers expected)
    LEVEL_MULTIPLIERS = {
        'junior': 0.7, 'entry': 0.7,
        'mid': 1.0, 'intermediate': 1.0,
        'senior': 1.3, 'lead': 1.5, 'staff': 1.5, 'principal': 1.5,
    }

    def __init__(self):
        self._response_times = []   # rolling last 10 response times (seconds)
        self._parse_failures  = 0   # consecutive parse failures
        self._parse_successes = 0   # consecutive parse successes
        self._call_count      = 0

    # ── Public API ────────────────────────────────────────────────────────────

    def params_for_mc_questions(self, field, level, num_questions):
        """Return (max_tokens, temperature, top_p, timeout) for MC question generation."""
        complexity = self._field_complexity(field)
        level_mult = self._level_mult(level)
        speed_mult = self._speed_multiplier()

        # Pipe format: each MC line is ~80-120 tokens (question+4 detailed options+letter)
        # Generous headroom so Mistral never truncates mid-question; cap at 1500
        base_per_q = 100 + (complexity - 1) * 15   # 100 → 160 as complexity 1→5
        base_per_q = int(base_per_q * level_mult)
        max_tokens = int(min(num_questions * base_per_q * speed_mult, 1500))
        max_tokens = max(max_tokens, num_questions * 80)  # absolute floor

        # Complex topics need slightly more creativity; simple ones stay tight
        temperature = 0.3 + (complexity - 1) * 0.06   # 0.30 → 0.54
        temperature = round(min(temperature, 0.55), 2)

        top_p = 0.85
        # Timeout: 8s per question base; shrink further when model has been fast
        timeout = max(30.0, num_questions * 8.0 * (1 / speed_mult))

        params = dict(max_tokens=max_tokens, temperature=temperature,
                      top_p=top_p, timeout=min(timeout, 90.0))
        self._log('mc_questions', field, level, params)
        return params

    def params_for_text_questions(self, field, level, num_questions):
        """Return params for plain text question generation."""
        complexity = self._field_complexity(field)
        level_mult = self._level_mult(level)
        speed_mult = self._speed_multiplier()

        base_per_q = 80 + (complexity - 1) * 15   # 80 → 140
        base_per_q = int(base_per_q * level_mult)
        max_tokens = int(min(num_questions * base_per_q * speed_mult, 1200))
        max_tokens = max(max_tokens, num_questions * 50)

        temperature = 0.5 + (complexity - 1) * 0.08  # slightly creative for variety
        temperature = round(min(temperature, 0.75), 2)

        timeout = max(25.0, num_questions * 6.0 * (1 / speed_mult))
        params = dict(max_tokens=max_tokens, temperature=temperature,
                      top_p=0.9, timeout=min(timeout, 90.0))
        self._log('text_questions', field, level, params)
        return params

    def params_for_analysis(self, field, level, answer_text):
        """Return params for answer analysis, tuned to answer length & complexity."""
        complexity   = self._field_complexity(field)
        level_mult   = self._level_mult(level)
        speed_mult   = self._speed_multiplier()
        word_count   = len(answer_text.split())

        # ── Answer/Question character limits ─────────────────────────────────
        # Use 6 chars/word average; floor at 150, cap at 1200 so model sees full answer
        a_len = min(max(word_count * 6, 150), 1200)
        # 300 chars covers ~95% of interview questions fully
        q_len = 300

        # ── Token budget for output ───────────────────────────────────────────
        # Generous budget for detailed analysis: scores + strengths/weaknesses + feedback
        base       = 400 + (complexity - 1) * 20   # 400 → 480
        base       = int(base * min(level_mult, 1.3))
        max_tokens = int(min(base * speed_mult, 600))
        max_tokens = max(max_tokens, 350)            # hard floor — never truncate output

        # ── Temperature ───────────────────────────────────────────────────────
        # 0.12: near-deterministic for scoring accuracy yet allows nuanced feedback text
        temperature = 0.12

        timeout = max(18.0, max_tokens / 14 * (1 / speed_mult))  # ~18-28s typical
        params = dict(max_tokens=max_tokens, temperature=temperature,
                      top_p=0.85, timeout=min(timeout, 40.0),
                      q_len=q_len, a_len=a_len)
        self._log('analysis', field, level, params, extra=f'words={word_count} a_len={a_len}')
        return params

    def record_response(self, elapsed_seconds):
        """Call after every successful Mistral response."""
        self._response_times.append(elapsed_seconds)
        if len(self._response_times) > 10:
            self._response_times.pop(0)
        self._call_count += 1

    def record_parse_success(self):
        self._parse_successes += 1
        self._parse_failures  = 0   # reset consecutive failures

    def record_parse_failure(self):
        self._parse_failures  += 1
        self._parse_successes = 0
        app.logger.warning(f"[PerfCtrl] Parse failure #{self._parse_failures} — switching to safer format")

    def use_safe_format(self):
        """True when recent parse failures suggest compact format is unreliable."""
        return self._parse_failures >= 2

    # ── Internal helpers ─────────────────────────────────────────────────────

    def _field_complexity(self, field):
        if not field:
            return 3
        fl = field.lower()
        for key, val in self.FIELD_COMPLEXITY.items():
            if key in fl:
                return val
        return 3  # default: medium

    def _level_mult(self, level):
        if not level:
            return 1.0
        return self.LEVEL_MULTIPLIERS.get(level.lower().split()[0], 1.0)

    def _speed_multiplier(self):
        """
        Returns a multiplier applied to max_tokens based on recent response times.
        If the model is running slow, we shrink max_tokens to keep latency acceptable.
        Fast (<10s): 1.0   Normal (10-20s): 0.9   Slow (20-30s): 0.75   Very slow (>30s): 0.6
        """
        if len(self._response_times) < 2:
            return 1.0
        avg = sum(self._response_times[-5:]) / min(5, len(self._response_times))
        if avg < 10:   return 1.0
        if avg < 20:   return 0.9
        if avg < 30:   return 0.75
        return 0.6

    def _log(self, task, field, level, params, extra=''):
        speed = self._speed_multiplier()
        app.logger.info(
            f"[PerfCtrl] {task} | field={field} level={level} "
            f"tokens={params['max_tokens']} temp={params['temperature']} "
            f"timeout={params['timeout']:.0f}s speed_mult={speed:.2f} {extra}"
        )


# Single global instance shared by MistralAIAgent
perf_ctrl = MistralPerformanceController()

# ── Async analysis result store ───────────────────────────────────────────────
# Keyed by answer_uuid → {'status': 'pending'|'done'|'error', 'analysis': dict}
# Populated by background thread; polled by /api/interview/.../analysis endpoint.
_pending_analysis: dict = {}
_pending_analysis_lock = threading.Lock()


def _build_feedback_points(main_point: str, point_type: str, ta: float, dep: float, cla: float) -> list:
    """
    Build 3 rich feedback points from one Mistral-generated sentence + dimension scores.
    Returns a list of 3 strings.
    """
    points = [main_point]
    if point_type == 'strength':
        if ta >= 7:
            points.append("Demonstrated solid technical accuracy with correct concepts and terminology.")
        elif ta >= 5:
            points.append("Shows foundational technical knowledge with room to deepen precision.")
        if cla >= 7:
            points.append("Answer was well-structured and easy to follow throughout.")
        elif dep >= 7:
            points.append("Thorough coverage of the topic with good detail and examples.")
        else:
            points.append("Attempted to address the core aspects of the question.")
    else:  # improvement
        if ta < 7:
            points.append("Strengthen technical accuracy — review core definitions and correct any factual gaps.")
        if dep < 7:
            points.append("Add concrete examples, edge cases, and trade-off analysis to deepen the answer.")
        else:
            points.append("Consider discussing alternative approaches or performance implications.")
    return [p for p in points[:3] if p]


class MistralAIAgent:
    """Enterprise Mistral AI - company-aware question generation + 6-dimension scoring with auto-reconnect."""

    def __init__(self):
        self.base_url   = os.environ.get('MISTRAL_BASE_URL',   'http://127.0.0.1:1234/v1')
        self.model_name = os.environ.get('MISTRAL_MODEL_NAME', 'mistral-7b-instruct-v0.2')
        api_key         = os.environ.get('MISTRAL_API_KEY',    'lm-studio')
        
        # Reconnection tracking with exponential backoff
        self.is_available = False
        self.last_check_time = datetime.utcnow()
        self.check_interval = 5  # 5 seconds for first check
        self.max_check_interval = 120  # 2 minutes max
        self.check_failures = 0
        self.client = None
        self.connection_error = None
        self.last_error_msg = None

        # Per-user question deduplication: {user_key → deque of last 30 question texts (lowercased)}
        self._question_history = {}   # type: dict[str, collections.deque]
        
        print(f"\n{'='*80}")
        print(f"  MISTRAL AI AGENT - INITIALIZATION")
        print(f"{'='*80}")
        print(f"  Base URL:  {self.base_url}")
        print(f"  Model:     {self.model_name}")
        print(f"  Config:    LM Studio (Local Model)")
        print(f"{'='*80}\n")
        
        # Initial connection attempt
        self._connect()
        
        if not self.is_available:
            print(f"⚠️  WARNING: Mistral AI is OFFLINE")
            print(f"   - Ensure LM Studio is running on {self.base_url}")
            print(f"   - Load model: {self.model_name} and start the server")
            print(f"   - Application WILL USE FALLBACK: Static questions & basic evaluation")
            print(f"{'='*80}\n")

    # ── Question deduplication helpers ────────────────────────────────────────

    def _history_key(self, user_id, field, level):
        return f"{user_id}:{(field or '').lower()}:{(level or '').lower()}"

    def _get_recent_questions(self, user_id, field, level):
        """Return list of recent question texts (lowercased) for this user+field+level."""
        key = self._history_key(user_id, field, level)
        return list(self._question_history.get(key, []))

    def _record_questions(self, user_id, field, level, questions):
        """Append generated question texts into per-user history (capped at 30)."""
        key = self._history_key(user_id, field, level)
        if key not in self._question_history:
            self._question_history[key] = collections.deque(maxlen=30)
        dq = self._question_history[key]
        for q in questions:
            text = (q.get('text') or '').strip()
            if text:
                dq.append(text.lower()[:120])  # store first 120 chars lowercased

    def _connect(self):
        """Establish connection to Mistral. Returns True if successful."""
        try:
            api_key = os.environ.get('MISTRAL_API_KEY', 'lm-studio')
            # Create OpenAI client with proper timeout configuration
            self.client = OpenAI(
                base_url=self.base_url, 
                api_key=api_key,
                timeout=120.0  # 2-minute timeout for initial setup
            )
            
            # Test connection with proper timeout for LLM inference (30+ seconds)
            # LLMs need sufficient time to generate responses
            timeout_duration = 30.0 if self.check_failures == 0 else 20.0
            
            self.client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": "ping"}],
                max_tokens=5,
                timeout=timeout_duration)
            
            self.is_available = True
            self.check_failures = 0
            self.check_interval = 5
            self.last_error_msg = None
            self.connection_error = None
            
            print("[OK] Mistral AI ONLINE and READY!")
            app.logger.info("[Mistral] [OK] Connection established - AI questions enabled")
            return True
            
        except Exception as e:
            self.is_available = False
            self.check_failures += 1
            error_str = str(e).lower()
            
            # Categorize error type
            if "timeout" in error_str or "timed out" in error_str:
                self.last_error_msg = f"Connection timeout (server not responding in time)"
            elif "connection refused" in error_str or "refused" in error_str:
                self.last_error_msg = f"Connection refused (LM Studio not running on {self.base_url})"
            elif "name or service not known" in error_str or "nodename nor servname" in error_str:
                self.last_error_msg = f"DNS resolution failed (invalid URL: {self.base_url})"
            elif "cannot connect" in error_str:
                self.last_error_msg = f"Network error (check network connectivity)"
            else:
                self.last_error_msg = str(e)[:100]
            
            # Exponential backoff for retry attempts
            self.check_interval = min(
                5 * (2 ** self.check_failures),  # exponential: 5, 10, 20, 40, 80, 120
                self.max_check_interval
            )
            
            self.connection_error = {
                'error': self.last_error_msg,
                'attempt': self.check_failures,
                'next_retry_in_seconds': self.check_interval,
                'base_url': self.base_url,
                'model_name': self.model_name,
            }
            
            print(f"[OFFLINE] Mistral OFFLINE (Attempt #{self.check_failures})")
            print(f"  Error: {self.last_error_msg}")
            print(f"  Next retry in {self.check_interval}s")
            print(f"  Fallback mode ACTIVE: Using pre-loaded questions & heuristic scoring\n")
            
            app.logger.warning(f"[Mistral] [FAILED] Connection failed: {self.last_error_msg}")
            app.logger.info(f"[Mistral] Next reconnection attempt in {self.check_interval}s")
            app.logger.info("[Mistral] FALLBACK active - using static questions and basic evaluation")
            
            self.last_check_time = datetime.utcnow()
            return False
    
    def _ensure_available(self):
        """Auto-reconnect if offline and enough time has passed (best-effort)."""
        if self.is_available:
            return True  # Already online
        
        # Check if we should retry
        time_since_check = (datetime.utcnow() - self.last_check_time).total_seconds()
        if time_since_check >= self.check_interval:
            app.logger.info(f"[Mistral] Attempting reconnection (after {time_since_check:.1f}s)...")
            return self._connect()
        
        return False  # Still offline

    def generate_questions(self, field, level, company, num=5, user_profile=None, question_type='mock', interview_mode='text', interview_type='technical'):
        # Try to reconnect if offline
        self._ensure_available()
        
        if not self.is_available:
            return self._fallback_questions(field, level, company, num, question_type, interview_type=interview_type)

        import random as _rnd

        company_lower = (company or 'default').lower()
        style = COMPANY_STYLES.get(company_lower, COMPANY_STYLES['default'])
        diff_key = (level or 'mid').lower()
        difficulty, diff_desc = DIFFICULTY_MAP.get(diff_key, DIFFICULTY_MAP['default'])

        # Build rich user profile context from ALL selected options
        profile_ctx = ""
        skills_ctx = ""
        experience_ctx = ""
        role_ctx = ""
        resume_ctx = ""
        dream_ctx = ""
        if user_profile:
            skills  = user_profile.get('skills', [])
            exp     = user_profile.get('experience_years', 0)
            role    = user_profile.get('current_role', '')
            resume  = user_profile.get('resume_summary', '')
            dreams  = user_profile.get('dream_companies', [])
            if skills:
                skills_ctx = f"Candidate Skills: {', '.join(skills[:10])}"
                profile_ctx += skills_ctx
            if exp:
                experience_ctx = f"Years of Experience: {exp}"
                profile_ctx += f" | {experience_ctx}"
            if role:
                role_ctx = f"Current Role: {role}"
                profile_ctx += f" | {role_ctx}"
            if resume:
                resume_ctx = f"Background: {resume[:200]}"
                profile_ctx += f" | {resume_ctx}"
            if dreams:
                dream_ctx = f"Target Companies: {', '.join(dreams[:3])}"
                profile_ctx += f" | {dream_ctx}"

        # Determine question type context for prompt
        question_type_desc = "real-time mock interview with live Q&A" if question_type == 'mock' else "written interview assessment"
        question_type_guidance = (
            "For MOCK questions: Focus on conversational technical & behavioral questions suitable for live verbal discussion. "
            "Keep questions concise and answerable in 1-3 minutes."
        ) if question_type == 'mock' else (
            "For WRITTEN questions: Create detailed problem-solving questions requiring structured written responses, "
            "code snippets, or in-depth explanations. Questions should demand 200-500 word answers."
        )

        # Use random seed per call so AI generates unique questions each time
        session_seed = _rnd.randint(1000, 9999)

        # Interview-type-aware question mix
        LEGACY_TYPE_MIX = {
            'technical':     "80% technical (coding, algorithms, debugging), 10% behavioral, 10% scenario",
            'behavioral':    "70% behavioral/STAR (teamwork, leadership, conflict), 20% situational, 10% technical",
            'system-design': "80% system design (architecture, scalability, trade-offs), 10% technical, 10% behavioral",
            'hr':            "60% HR/culture-fit (motivation, goals, values), 30% behavioral, 10% scenario",
        }
        type_mix = LEGACY_TYPE_MIX.get(interview_type, LEGACY_TYPE_MIX['technical'])

        # Fully personalized but COMPACT prompt — halved token count for faster inference
        prompt = f"""Generate exactly {num} unique {level} {field} {interview_type} interview questions for {company or 'Top Tech Company'}.
Format: {question_type} ({question_type_desc}). Mode: {interview_mode or 'text'}. Interview type: {interview_type}.
{profile_ctx.strip() if profile_ctx.strip() else ''}
Rules:
1. Match {level} seniority: entry=fundamentals, mid=design+architecture, senior=leadership+system-design
2. Use real {field} terminology and tools
3. Mirror {company or 'top tech company'} interview style
4. {question_type_guidance}
5. Question mix: {type_mix}
6. Seed {session_seed} — generate FRESH unique questions

Output ONLY a numbered list (1. 2. 3. ...). No explanations.
"""

        try:
            resp = self.client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=2000,
                temperature=0.85,  # Higher temperature for more variety per interview
                top_p=0.95,
                timeout=90.0)
            raw = resp.choices[0].message.content
            qs  = self._parse_questions(raw, field, level, company, difficulty, question_type)
            if len(qs) < num:
                qs += self._fallback_questions(field, level, company, num - len(qs), question_type, interview_type=interview_type)
            return qs[:num]
        except Exception as e:
            app.logger.error(f"[Mistral] generate_questions: {type(e).__name__}: {str(e)[:100]}")
            # Mark as potentially offline and log failure
            error_lower = str(e).lower()
            if any(keyword in error_lower for keyword in ["timeout", "timed out", "connection", "refused", "network"]):
                self.is_available = False
                self.check_failures += 1
                self._ensure_available()  # Try reconnect
            app.logger.warning(f"[Mistral] Falling back to basic questions due to: {str(e)[:80]}")
            return self._fallback_questions(field, level, company, num, question_type, interview_type=interview_type)

    def generate_questions_fast(self, field, level, company, num=5, user_profile=None, question_type='mock', interview_mode='text', user_id=None, interview_type='technical'):
        """
        FAST question generation: single Mistral call, NO per-question MC overhead.
        Up to 6x faster than generate_questions() because it skips the 5 MC option API calls.
        Returns plain text questions ready to display immediately.
        """
        self._ensure_available()
        if not self.is_available:
            return self._fallback_questions(field, level, company, num, question_type, interview_type=interview_type)

        import random as _rnd
        company_lower = (company or 'default').lower()
        style = COMPANY_STYLES.get(company_lower, COMPANY_STYLES['default'])
        diff_key = (level or 'mid').lower()
        difficulty, diff_desc = DIFFICULTY_MAP.get(diff_key, DIFFICULTY_MAP['default'])

        up = user_profile or {}
        skills_str = ', '.join(up.get('skills', [])[:5]) if up.get('skills') else ''
        role_str   = up.get('current_role', '')
        exp_str    = str(up.get('experience_years', ''))
        session_seed = _rnd.randint(1000, 9999)

        candidate_ctx = ''
        if role_str:   candidate_ctx += f' Current role: {role_str}.'
        if exp_str:    candidate_ctx += f' {exp_str} years experience.'
        if skills_str: candidate_ctx += f' Skills: {skills_str}.'

        # Mock interviews need MC options → use the combined single-call generator
        if question_type == 'mock':
            return self._generate_mc_questions_fast(
                field, level, company, num, difficulty, candidate_ctx,
                style, session_seed, question_type, user_id=user_id,
                interview_mode=interview_mode, interview_type=interview_type,
            )

        # ── Written/text-mode: rich system+user split prompt ─────────────────
        recent = self._get_recent_questions(user_id or 'anon', field, level) if user_id else []
        exclude_hint = ''
        if recent:
            snippets = [q[:55] for q in recent[-6:]]
            exclude_hint = f' Do NOT repeat these topics: {"; ".join(snippets)}.'

        diff_key = (level or 'mid').lower()
        _, diff_desc = DIFFICULTY_MAP.get(diff_key, DIFFICULTY_MAP['default'])

        mode_ctx = (
            "Voice/spoken — keep questions concise and verbally answerable in 2-3 minutes."
            if interview_mode == 'voice'
            else "Written text — questions should require structured 200-500 word responses."
        )

        # Question mix varies by interview_type selection
        INTERVIEW_TYPE_MIX = {
            'technical':     f"80% deep technical ({field} concepts, code, algorithms, debugging), 10% behavioral, 10% scenario",
            'behavioral':    f"70% behavioral/STAR (teamwork, leadership, conflict, growth), 20% situational, 10% light technical",
            'system-design': f"80% system design & architecture (scalability, trade-offs, data flow), 10% technical, 10% behavioral",
            'hr':            f"60% HR/culture-fit (motivation, career goals, values), 30% behavioral, 10% scenario",
        }
        question_mix = INTERVIEW_TYPE_MIX.get(interview_type, INTERVIEW_TYPE_MIX['technical'])

        system_msg = (
            f"You are a senior {interview_type} interviewer at {company or 'a top tech company'} "
            f"specializing in {field}.\n"
            f"Interview context:\n"
            f"- Field: {field}\n"
            f"- Interview type: {interview_type.upper()}\n"
            f"- Seniority: {level} ({diff_desc})\n"
            f"- Company: {company or 'top tech company'} — {style}\n"
            f"- Format: Written/text interview ({mode_ctx})\n"
            f"{('- Candidate: ' + candidate_ctx.strip()) if candidate_ctx.strip() else ''}\n\n"
            f"Question rules:\n"
            f"1. Match EXACTLY {level} level: entry=core concepts, mid=design+architecture, senior=leadership+system-scale\n"
            f"2. Use real {field} terminology, frameworks, tools\n"
            f"3. Question mix: {question_mix}\n"
            f"4. ALL questions MUST be strictly {interview_type.upper()} type — do NOT mix in other interview types\n"
            f"5. Probe {field}-specific challenges relevant to {company or 'the company'}\n"
            f"6. Each question must be self-contained and unambiguous\n"
            f"7. Analyze answers with full depth — evaluate technical accuracy, communication, clarity, and depth"
        )

        user_msg = (
            f"[seed:{session_seed}] Generate EXACTLY {num} unique {level} {field} {interview_type} interview "
            f"questions for a WRITTEN assessment.{exclude_hint}\n"
            f"Each question must require a detailed written response (200-500 words).\n"
            f"Output ONLY a numbered list ({num} questions), one question per line, no explanations:\n"
            + '\n'.join(f'{i+1}.' for i in range(num))
        )

        try:
            import time as _t
            p = perf_ctrl.params_for_text_questions(field, level, num)
            stop_seqs = [f"\n{num + 1}.", f"\n{num + 1})"]
            t0 = _t.time()
            resp = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "user", "content": system_msg + "\n\n" + user_msg},
                ],
                max_tokens=p['max_tokens'],
                temperature=p['temperature'],
                top_p=p['top_p'],
                frequency_penalty=0.12,
                stop=stop_seqs,
                timeout=p['timeout'])
            perf_ctrl.record_response(_t.time() - t0)
            raw = resp.choices[0].message.content
            qs = self._parse_questions(raw, field, level, company, difficulty, question_type)
            if len(qs) < num:
                qs += self._fallback_questions(field, level, company, num - len(qs), question_type, interview_type=interview_type)
            result = qs[:num]
            if user_id:
                self._record_questions(user_id, field, level, result)
            return result
        except Exception as e:
            app.logger.error(f"[Mistral Fast] generate_questions_fast error: {str(e)[:100]}")
            if any(k in str(e).lower() for k in ['timeout', 'connection', 'refused', 'network']):
                self.is_available = False
                self.check_failures += 1
            return self._fallback_questions(field, level, company, num, question_type, interview_type=interview_type)

    def _generate_mc_questions_fast(self, field, level, company, num, difficulty,
                                     candidate_ctx, style, session_seed, question_type,
                                     user_id=None, interview_mode='text', interview_type='technical'):
        """
        Generate mock interview questions WITH options in ONE Mistral call.
        Uses system+user split for rich context + ultra-compact pipe format for speed.
        Output: Q|question|optA|optB|optC|optD|correct_letter  (one line per question)
        """
        import random as _rnd

        # Build exclusion hint from per-user history
        recent = self._get_recent_questions(user_id or 'anon', field, level) if user_id else []
        exclude_hint = ''
        if recent:
            snippets = [q[:55] for q in recent[-6:]]
            exclude_hint = f' Do NOT repeat these topics: {"; ".join(snippets)}.'

        seed_val = session_seed if session_seed else _rnd.randint(1000, 9999)

        diff_key = (level or 'mid').lower()
        _, diff_desc = DIFFICULTY_MAP.get(diff_key, DIFFICULTY_MAP['default'])

        mode_ctx = (
            "Voice/spoken interview — keep questions concise (max 20 words)."
            if interview_mode == 'voice'
            else "Text-based interview — questions can be detailed and scenario-based."
        )

        # Interview-type-aware topic guidance for MC questions
        MC_TOPIC_MAP = {
            'technical':     f"concepts, algorithms, debugging, tools, best practices in {field}",
            'behavioral':    "teamwork, leadership, conflict resolution, STAR-based scenarios, growth mindset",
            'system-design': f"system architecture, scalability, trade-offs, data modeling in {field}",
            'hr':            "motivation, career goals, culture fit, work-life balance, company values",
        }
        topic_guidance = MC_TOPIC_MAP.get(interview_type, MC_TOPIC_MAP['technical'])

        # System message: rich context about company/field/level so format stays clean
        system_msg = (
            f"You are a senior {interview_type} interviewer at {company or 'a top tech company'}. "
            f"You specialize in {field} interviews.\n"
            f"Interview context:\n"
            f"- Field: {field}\n"
            f"- Interview type: {interview_type.upper()}\n"
            f"- Level: {level} ({diff_desc})\n"
            f"- Company: {company or 'top tech company'} — {style}\n"
            f"- Format: Multiple-choice ({mode_ctx})\n"
            f"{('- Candidate: ' + candidate_ctx.strip()) if candidate_ctx.strip() else ''}\n\n"
            f"STRICT Rules for questions:\n"
            f"1. You MUST generate EXACTLY {num} questions — no more, no less\n"
            f"2. Questions MUST test real {level}-level {interview_type} knowledge in {field}\n"
            f"3. EXACTLY ONE option must be clearly correct; the other 3 distractors must be HIGHLY PLAUSIBLE and tricky — designed to confuse candidates who lack deep understanding\n"
            f"4. The correct_letter MUST accurately identify the correct option (A, B, C, or D)\n"
            f"5. Topics to cover: {topic_guidance}\n"
            f"6. ALL questions MUST be strictly {interview_type.upper()} type — do NOT mix in other interview types\n"
            f"7. Each question must be unique — no duplicate topics or concepts\n"
            f"8. Output ONLY pipe-separated lines — no headers, no explanations, no blank lines, no numbering\n"
            f"Format: question|optionA|optionB|optionC|optionD|correct_letter"
        )

        # User message: compact generation command
        user_msg = (
            f"[seed:{seed_val}] Generate EXACTLY {num} unique {level} {field} {interview_type} interview "
            f"questions with 4 options each.{exclude_hint}\n"
            f"Output EXACTLY {num} lines in this pipe-separated format (no other text, no numbering):\n"
            f"question|optA|optB|optC|optD|correct_letter\n"
            f"IMPORTANT: correct_letter must be A, B, C, or D matching the correct option.\n"
            f"Now output exactly {num} lines:"
        )

        try:
            import time as _t
            p = perf_ctrl.params_for_mc_questions(field, level, num)
            use_safe = perf_ctrl.use_safe_format()
            # Stop the moment the model tries to write line N+1 (pipe format)
            stop_seqs = [f"\n{num + 1}|", f"\nQ{num + 1}|", f"\n{num + 1}."]
            t0 = _t.time()
            resp = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "user", "content": system_msg + "\n\n" + user_msg},
                ],
                max_tokens=p['max_tokens'],
                temperature=p['temperature'],
                top_p=p['top_p'],
                frequency_penalty=0.15,
                stop=stop_seqs,
                timeout=p['timeout'])
            perf_ctrl.record_response(_t.time() - t0)
            raw = resp.choices[0].message.content
            app.logger.info(f"[Mistral MC-Fast] {len(raw)} chars for {num} MC questions (safe_fmt={use_safe})")
            questions = self._parse_mc_pipe_format(raw, field, level, company, difficulty)
            app.logger.info(f"[Mistral MC-Fast] Parsed {len(questions)}/{num} questions")
            if len(questions) >= num * 0.6:
                perf_ctrl.record_parse_success()
            else:
                perf_ctrl.record_parse_failure()
            if len(questions) < num:
                app.logger.warning(f"[Mistral MC-Fast] Padding {num - len(questions)} with fallback")
                questions += self._fallback_questions(field, level, company, num - len(questions), question_type, interview_type=interview_type)
            result = questions[:num]
            # Record in history so next session avoids these topics
            if user_id:
                self._record_questions(user_id, field, level, result)
            return result
        except Exception as e:
            app.logger.error(f"[Mistral MC-Fast] error: {str(e)[:100]}")
            if any(k in str(e).lower() for k in ['timeout', 'connection', 'refused', 'network']):
                self.is_available = False
                self.check_failures += 1
            return self._fallback_questions(field, level, company, num, question_type, interview_type=interview_type)

    def _parse_mc_pipe_format(self, text, field, level, company, difficulty):
        """
        Parse ultra-compact pipe format:
          Q|question|optA|optB|optC|optD|correct_letter

        Also falls back to the older block format (Q1:/A)/CORRECT:) if pipe format not found.
        """
        questions = []

        for line in text.strip().splitlines():
            line = line.strip()
            if not line:
                continue

            # ── Try pipe format first ────────────────────────────────────────
            if '|' in line:
                parts = [p.strip() for p in line.split('|')]
                # Accept: Q|question|A|B|C|D|letter  (7 parts, first may be "Q" or number)
                if len(parts) >= 6:
                    # Strip leading Q or number prefix from first part
                    start = 1 if parts[0].upper() in ('Q', '') or re.match(r'^\d+$', parts[0]) else 0
                    q_text = parts[start]
                    options = parts[start+1:-1]   # everything between question and last part
                    correct_part = parts[-1].strip().upper()

                    # Accept 4 or 5 options
                    if len(options) >= 4 and len(q_text) > 10:
                        # Map letter to index
                        correct_idx = 0
                        if correct_part and correct_part[0] in 'ABCDE':
                            correct_idx = ord(correct_part[0]) - ord('A')
                            correct_idx = min(correct_idx, len(options) - 1)

                        questions.append({
                            'text':               q_text,
                            'category':           'technical',
                            'field':              field,
                            'level':              level,
                            'company':            company,
                            'difficulty':         difficulty,
                            'topic_tags':         json.dumps([field.lower()]),
                            'is_multiple_choice': True,
                            'options':            options[:5],  # cap at 5
                            'correct_answers':    [correct_idx],
                            'multiple_allowed':   False,
                        })

        # ── If pipe parsing got nothing, fall back to block format parser ───
        if not questions:
            app.logger.warning("[MC Parser] Pipe format failed, trying block format fallback")
            questions = self._parse_mc_questions_fast(text, field, level, company, difficulty)

        return questions

    def _parse_mc_questions_fast(self, text, field, level, company, difficulty):
        """
        Parse the combined Q+options format:
          Q1: question text
          A) option...
          B) option...
          C) option...
          D) option...
          E) option...
          CORRECT: B
          ---
        Returns list of question dicts with is_multiple_choice=True.
        """
        questions = []
        # Split on block separators (---, Q1:, Q2: etc.)
        # We'll walk line by line with a state machine
        current_q = None
        current_options = []
        correct_letter = None

        def flush():
            nonlocal current_q, current_options, correct_letter
            if current_q and len(current_options) >= 3:
                # Map correct letter to index
                correct_idx = 0
                if correct_letter:
                    idx = ord(correct_letter.upper()) - ord('A')
                    if 0 <= idx < len(current_options):
                        correct_idx = idx
                questions.append({
                    'text':             current_q,
                    'category':         'technical',
                    'field':            field,
                    'level':            level,
                    'company':          company,
                    'difficulty':       difficulty,
                    'topic_tags':       json.dumps([field.lower()]),
                    'is_multiple_choice': True,
                    'options':          current_options,
                    'correct_answers':  [correct_idx],
                    'multiple_allowed': False,
                })
            current_q = None
            current_options = []
            correct_letter = None

        for line in text.strip().splitlines():
            line = line.strip()
            if not line or line == '---':
                continue

            # Match "Q1: text" or "1. text" or "1) text"
            q_match = re.match(r'^Q?\s*\d+[.:)]\s*(.+)', line, re.IGNORECASE)
            # Match "A) text" or "A. text"
            opt_match = re.match(r'^([A-Ea-e])[.)]\s*(.+)', line)
            # Match "CORRECT: B" or "CORRECT ANSWER: B"
            correct_match = re.match(r'^CORRECT(?:\s+ANSWER)?\s*[:\-]\s*([A-Ea-e])', line, re.IGNORECASE)

            if q_match:
                flush()  # Save previous question
                current_q = q_match.group(1).strip()
            elif opt_match and current_q is not None:
                current_options.append(opt_match.group(2).strip())
            elif correct_match:
                correct_letter = correct_match.group(1).upper()

        flush()  # Save last question
        app.logger.info(f"[MC-Fast Parser] Parsed {len(questions)} MC questions")
        return questions

    def generate_adaptive_question(self, field, level, company, question_number, total_questions,
                                   previous_questions_answers=None, user_profile=None):
        """
        Adaptive question generation: analyzes the user's previous answers and scores
        to generate a targeted next question — probing weak areas or advancing depth.
        Returns a single question dict or None on failure.
        """
        self._ensure_available()
        if not self.is_available:
            fallback = self._fallback_questions(field, level, company, 1, 'mock')
            return fallback[0] if fallback else None

        diff_key  = (level or 'mid').lower()
        difficulty, _ = DIFFICULTY_MAP.get(diff_key, DIFFICULTY_MAP['default'])
        up = user_profile or {}
        skills_str = ', '.join(up.get('skills', [])[:5]) if up.get('skills') else ''

        # Build concise Q&A history context (last 3 pairs to keep prompt small)
        prev_ctx = ''
        if previous_questions_answers:
            for i, qa in enumerate(previous_questions_answers[-3:]):
                score = qa.get('score', 7.0)
                q_snippet = (qa.get('question') or '')[:80]
                prev_ctx += f'\nQ{i+1}: {q_snippet} → Score: {score}/10'

        prompt = (
            f"You are interviewing a {level} {field} candidate for {company}."
            + (f' Their skills: {skills_str}.' if skills_str else '')
            + (f'\nPrevious performance:{prev_ctx}' if prev_ctx else '\nThis is the opening question.')
            + f'\n\nGenerate question #{question_number} of {total_questions}.'
            + ' Rules: if previous scores <6 ask foundational; if >8 ask harder/follow-up; vary topic each time.'
            + ' Return ONLY the question text, no numbering, no explanation:'
        )

        try:
            resp = self.client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=150,
                temperature=0.85,
                top_p=0.95,
                timeout=30.0)
            q_text = resp.choices[0].message.content.strip()
            # Strip any accidental numbering
            q_text = re.sub(r'^[\d]+[.)]\s*', '', q_text).strip()
            q_text = re.sub(r'^[Qq]uestion\s*[\d]*\s*[:.-]\s*', '', q_text).strip()
            if len(q_text) > 15:
                return {
                    'text': q_text, 'category': 'adaptive',
                    'field': field, 'level': level, 'company': company,
                    'difficulty': difficulty,
                    'topic_tags': json.dumps([field.lower()]),
                    'source': 'ai_adaptive',
                }
            fallback = self._fallback_questions(field, level, company, 1, 'mock')
            return fallback[0] if fallback else None
        except Exception as e:
            app.logger.error(f"[Mistral Adaptive] generate_adaptive_question: {str(e)[:80]}")
            if any(k in str(e).lower() for k in ['timeout', 'connection', 'refused', 'network']):
                self.is_available = False
                self.check_failures += 1
            fallback = self._fallback_questions(field, level, company, 1, 'mock')
            return fallback[0] if fallback else None

    def generate_mc_feedback(self, question, correct_options, user_selected, field, level, company='',
                              answer_uuid=None, question_type='mock'):
        """
        Instant MC feedback: returns heuristic immediately, fires AI in background.
        Real AI result stored in _pending_analysis[answer_uuid] for polling.
        """
        is_correct = set(user_selected) == set(correct_options)
        fallback   = self._fallback_mc_feedback(question, correct_options, user_selected)

        # If AI is offline or no UUID to store against, just return fallback
        self._ensure_available()
        if not self.is_available or not answer_uuid:
            return fallback

        correct_letters = [chr(65 + i) for i in correct_options]
        user_letters    = [chr(65 + i) for i in user_selected]
        result_word     = 'CORRECT' if is_correct else 'WRONG'

        company_style = COMPANY_STYLES.get((company or 'default').lower(), COMPANY_STYLES['default'])
        diff_key = (level or 'mid').lower()
        _, diff_desc = DIFFICULTY_MAP.get(diff_key, DIFFICULTY_MAP['default'])
        fmt_ctx = "multiple-choice mock interview" if question_type == 'mock' else "multiple-choice written assessment"

        system_msg = (
            f"You are an expert {field} interviewer at {company or 'a top tech company'} "
            f"reviewing a {fmt_ctx} answer.\n"
            f"Level: {level} ({diff_desc}). Company style: {company_style}\n"
            "Output EXACTLY these 5 lines with no extra text:\n"
            "STATUS: Correct  OR  STATUS: Incorrect\n"
            "EXPLANATION: <why the correct answer is right — reference specific concept, max 20 words>\n"
            "FEEDBACK: <specific feedback on the candidate's selection, max 18 words>\n"
            "KEY_CONCEPT: <the core concept this question tests, max 12 words>\n"
            "TIP: <one actionable study tip for this topic, max 12 words>"
        )
        user_msg = (
            f"Question: {question[:160]}\n"
            f"User selected: {', '.join(user_letters)}  |  Correct: {', '.join(correct_letters)}  |  Result: {result_word}\n"
            f"Field: {field} | Level: {level} | Company: {company or 'general'}"
        )

        def _bg_mc():
            try:
                import time as _t
                t0 = _t.time()
                resp = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=[
                        {"role": "user", "content": system_msg + "\n\n" + user_msg},
                    ],
                    max_tokens=160,
                    temperature=0.10,
                    top_p=0.80,
                    stop=["\n\n\n"],
                    timeout=20.0)
                raw = resp.choices[0].message.content
                result = self._parse_mc_feedback(raw, is_correct)
                result['source'] = 'mistral-bg'
                # Build full analysis dict compatible with submit_answer structure
                mc_analysis = self._mc_feedback_to_analysis(result, is_correct, selected_options=user_selected, correct_answers=correct_options, options=[chr(65+i) for i in range(max(max(correct_options)+1, max(user_selected)+1) if correct_options and user_selected else 4)])
                with _pending_analysis_lock:
                    _pending_analysis[answer_uuid] = {'status': 'done', 'analysis': mc_analysis}
                app.logger.info(f"[BG MC Feedback] {answer_uuid[:8]} done in {_t.time()-t0:.1f}s")
                self._update_answer_scores_in_db(answer_uuid, mc_analysis)
            except Exception as e:
                app.logger.error(f"[BG MC Feedback] {answer_uuid[:8]} failed: {str(e)[:60]}")
                with _pending_analysis_lock:
                    _pending_analysis[answer_uuid] = {'status': 'error', 'analysis': fallback}

        with _pending_analysis_lock:
            _pending_analysis[answer_uuid] = {'status': 'pending', 'analysis': fallback}
        threading.Thread(target=_bg_mc, daemon=True,
                         name=f"BGMCFeedback-{answer_uuid[:8]}").start()
        return fallback

    @staticmethod
    def _mc_feedback_to_analysis(mc_feedback, is_correct, selected_options, correct_answers, options):
        """Convert MC feedback dict into a standard analysis dict."""
        score = mc_feedback.get('score', 9.0 if is_correct else 3.0)
        acc   = 10.0 if is_correct else 0.0
        letter_sel = [chr(65+i) for i in selected_options]
        letter_cor = [chr(65+i) for i in correct_answers]
        feedback_text = (
            f"{mc_feedback.get('status','')}\n\n"
            f"{mc_feedback.get('explanation','')}\n\n"
            f"Your Selection: {letter_sel}  Correct: {letter_cor}\n\n"
            f"Key Concept: {mc_feedback.get('key_concept','')}\n"
            f"Tip: {mc_feedback.get('tip','')}"
        )
        return {
            'score': 10.0 if is_correct else 0.0, 'technical_accuracy': acc,
            'depth_score': 10.0 if is_correct else 0.0, 'clarity_score': 10.0 if is_correct else 0.0,
            'relevance_score': acc, 'communication_score': 10.0 if is_correct else 0.0,
            'confidence_score': 10.0 if is_correct else 0.0,
            'strengths': [mc_feedback.get('explanation', 'Answered the question')],
            'weaknesses': [] if is_correct else [mc_feedback.get('feedback', 'Review concept')],
            'feedback': feedback_text,
            'improvement_plan': [mc_feedback.get('key_concept',''), mc_feedback.get('tip',''),
                                 'Complete similar practice questions'],
            'model': mc_feedback.get('model', 'ai-mc'),
        }
    
    def _parse_mc_feedback(self, text, was_correct):
        """Parse AI-generated MC feedback into structured format."""
        def extract_after(marker):
            idx = text.upper().find(marker.upper())
            if idx == -1:
                return ''
            start = idx + len(marker)
            content = text[start:].strip()
            # Find next marker or end
            for next_marker in ['EXPLANATION:', 'FEEDBACK:', 'KEY_CONCEPT:', 'TIP:', 'SCORE:']:
                next_idx = content.upper().find(next_marker.upper())
                if next_idx > 0:
                    content = content[:next_idx].strip()
                    break
            return content.rstrip(':').strip()
        
        # Extract numerical score — STRICT: 10.0 for correct, 0.0 for incorrect
        score_text = extract_after('SCORE:')
        try:
            score = float(re.search(r'(\d+[.\\d]*)', score_text).group(1) if score_text else (10.0 if was_correct else 0.0))
            score = min(10.0, max(0.0, score))
        except:
            score = 10.0 if was_correct else 0.0
        # Override: enforce strict binary scoring for MC
        score = 10.0 if was_correct else 0.0
        
        return {
            'status': extract_after('STATUS:') or ('Correct' if was_correct else 'Incorrect'),
            'explanation': extract_after('EXPLANATION:') or 'See feedback below',
            'feedback': extract_after('FEEDBACK:') or ('Excellent! Correct answer.' if was_correct else 'Incorrect. Review the concept and try again.'),
            'key_concept': extract_after('KEY_CONCEPT:') or 'Master this topic',
            'tip': extract_after('TIP:') or 'Practice similar questions',
            'score': score,
            'model': self.model_name,
        }
    
    def _fallback_mc_feedback(self, question, correct_options, user_selected):
        """Generate fallback feedback when AI is unavailable.
        STRICT: 10.0 for correct, 0.0 for incorrect."""
        is_correct = set(user_selected) == set(correct_options)
        correct_letters = [chr(65 + i) for i in correct_options]
        user_letters = [chr(65 + i) for i in user_selected]
        
        return {
            'status': 'Correct' if is_correct else 'Incorrect',
            'explanation': f"The correct answer is {', '.join(correct_letters)}. This option directly addresses the core requirement of the question.",
            'feedback': f"You selected {', '.join(user_letters)}. {'Perfect! This is the correct answer — full marks awarded.' if is_correct else 'This is incorrect. The correct answer is ' + correct_letters[0] + '. Review the concept thoroughly.'}",
            'key_concept': 'Review the fundamental principles being tested in this question',
            'tip': 'Eliminate obviously wrong answers first, then choose the most precise option',
            'score': 10.0 if is_correct else 0.0,
            'model': 'fallback',
        }

    def analyze_answer(self, question, answer, field, level, company='', question_type='mock', interview_type='technical'):
        # Try to reconnect if offline
        self._ensure_available()
        
        if not self.is_available:
            return self._fallback_analysis(question, answer)

        style = COMPANY_STYLES.get((company or 'default').lower(), COMPANY_STYLES['default'])

        # Determine evaluation context based on question type + interview type
        question_type_context = "real-time mock interview with live Q&A discussion" if question_type == 'mock' else "written interview assessment with detailed code/responses"
        evaluation_focus = "conversational clarity, real-time problem-solving, and communication" if question_type == 'mock' else "completeness of code, depth of explanation, and solution correctness"

        # Interview-type-aware scoring emphasis
        LEGACY_TYPE_FOCUS = {
            'technical':     "Prioritize TECHNICAL_ACCURACY and DEPTH scores. Code correctness is critical.",
            'behavioral':    "Prioritize COMMUNICATION and CLARITY. Evaluate STAR method, leadership examples. Be lenient on TECHNICAL_ACCURACY.",
            'system-design': "Prioritize DEPTH and TECHNICAL_ACCURACY. Evaluate architecture reasoning and trade-off analysis.",
            'hr':            "Prioritize COMMUNICATION and CONFIDENCE. Evaluate cultural fit, motivation. Be lenient on TECHNICAL_ACCURACY.",
        }
        type_emphasis = LEGACY_TYPE_FOCUS.get(interview_type, LEGACY_TYPE_FOCUS['technical'])

        # Optimized prompt: concise + directive for faster, more accurate output
        prompt = f"""You are a senior {interview_type} interviewer. Score this {level} {field} candidate answer with PRECISION.
Context: {question_type_context}
Focus: {evaluation_focus}
Interview type: {interview_type.upper()} — {type_emphasis}

STRICT SCORING RULES:
- 0 = no answer or completely wrong | 1-3 = fundamentally wrong | 4-5 = partial/shallow | 6-7 = mostly correct | 8-9 = strong | 10 = expert-level
- Factually incorrect claims = 0-3 on TECHNICAL_ACCURACY
- Short answers (<30 words) cannot score above 5 on DEPTH
- Off-topic answers = 0-2 on RELEVANCE
- Do NOT inflate scores. Be honest and strict.

Q: {question}
A: {answer}

Reply in EXACTLY this format (scores 0-10, decimals OK):
TECHNICAL_ACCURACY: [score]
DEPTH: [score]
CLARITY: [score]
RELEVANCE: [score]
COMMUNICATION: [score]
CONFIDENCE: [score]
OVERALL_SCORE: [score]
STRENGTHS:
- [point]
- [point]
- [point]
IMPROVEMENTS:
- [point]
- [point]
- [point]
DETAILED_FEEDBACK: [2 sentences max — specific to the answer content]
IMPROVEMENT_PLAN:
- [action]
- [action]
- [action]"""

        try:
            resp = self.client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=500,  # Reduced: structured output needs ~350 tokens max
                temperature=0.15,  # More deterministic for accurate scoring
                top_p=0.8,
                stop=["\n\n\n"],  # Stop on triple newline to prevent runaway
                timeout=90.0)
            result = self._parse_analysis(resp.choices[0].message.content, answer)

            # Retry once if model returned mostly default scores (garbled output)
            core = [result['technical_accuracy'], result['depth_score'],
                    result['clarity_score'], result['relevance_score']]
            _wc = len((answer or '').split())
            _exp_default = 3.0 if _wc < 15 else (5.0 if _wc < 40 else (6.0 if _wc < 80 else 7.0))
            defaults_hit = sum(1 for s in core if s == _exp_default)
            if defaults_hit >= 3:
                app.logger.warning("[Mistral] Mostly default scores — retrying with lower temperature")
                resp2 = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=500,
                    temperature=0.08,
                    top_p=0.75,
                    stop=["\n\n\n"],
                    timeout=90.0)
                result = self._parse_analysis(resp2.choices[0].message.content, answer)

            return result
        except Exception as e:
            app.logger.error(f"[Mistral] analyze_answer: {type(e).__name__}: {str(e)[:100]}")
            # Mark as potentially offline
            error_lower = str(e).lower()
            if any(keyword in error_lower for keyword in ["timeout", "timed out", "connection", "refused", "network"]):
                self.is_available = False
                self.check_failures += 1
                self._ensure_available()  # Try reconnect
            app.logger.warning(f"[Mistral] Falling back to basic analysis due to: {str(e)[:80]}")
            return self._fallback_analysis(question, answer)

    # ── Scoring rubric injected into every analysis call ─────────────────────
    _SCORING_RUBRIC = (
        "You are a senior technical interviewer evaluating a candidate's answer with PRECISION.\n"
        "Score each dimension as an integer or decimal 0-10 using these STRICT anchors:\n"
        "  0 = no answer, completely wrong, or irrelevant\n"
        "  1-3 = fundamentally wrong, missing key concepts, factual errors\n"
        "  4-5 = partially correct but shallow, missing important details\n"
        "  6-7 = mostly correct with reasonable depth, minor gaps\n"
        "  8-9 = strong answer with good examples and accurate concepts\n"
        "  10 = expert-level, comprehensive, flawless with real-world examples\n\n"
        "Scoring dimensions (evaluate each INDEPENDENTLY based on the answer content):\n"
        "TECHNICAL_ACCURACY — Are ALL facts, concepts, code logic, and technical claims CORRECT? Penalize any factual errors severely.\n"
        "DEPTH — Does the answer cover edge cases, trade-offs, examples, and implementation details? Short/vague answers = low score.\n"
        "CLARITY — Is the answer well-structured, logically organized, and easy to follow?\n"
        "RELEVANCE — Does the answer DIRECTLY address the specific question asked? Off-topic content = low score.\n"
        "COMMUNICATION — Is the language professional, precise, and appropriate for the level?\n"
        "CONFIDENCE — Does the answer express certainty and ownership of the knowledge?\n\n"
        "CRITICAL RULES:\n"
        "1. Short answers (<30 words) CANNOT score above 5 on DEPTH regardless of quality.\n"
        "2. Factually incorrect answers MUST score 0-3 on TECHNICAL_ACCURACY.\n"
        "3. Off-topic or irrelevant answers MUST score 0-2 on RELEVANCE.\n"
        "4. Do NOT inflate scores — be strict and honest.\n"
        "5. Each dimension score must be justified by the actual answer content.\n\n"
        "Your response MUST be EXACTLY these 10 lines (no other text, no extra lines):\n"
        "TECHNICAL_ACCURACY: [score]\n"
        "DEPTH: [score]\n"
        "CLARITY: [score]\n"
        "RELEVANCE: [score]\n"
        "COMMUNICATION: [score]\n"
        "CONFIDENCE: [score]\n"
        "OVERALL: [score]\n"
        "STRENGTH: [One specific strength of this answer in one sentence]\n"
        "IMPROVEMENT: [One specific improvement needed in one sentence]\n"
        "FEEDBACK: [Two sentences: what was good and what to improve, be specific to the answer content]"
    )

    def analyze_answer_fast(self, question, answer, field, level, company='',
                            answer_uuid=None, store_async=False, question_type='mock',
                            interview_mode='text', interview_type='technical'):
        """
        Fast answer analysis with scoring rubric.
        - store_async=False: blocking call, returns structured result directly.
        - store_async=True: instant heuristic returned; real AI in background thread.
        - question_type: 'mock' or 'written' — adjusts evaluation focus.
        - interview_mode: 'text' or 'voice' — adjusts communication scoring weight.
        """
        self._ensure_available()
        if not self.is_available:
            return self._fallback_analysis(question, answer)

        import time as _t
        p = perf_ctrl.params_for_analysis(field, level, answer)
        q_short = question[:p['q_len']]
        a_short = answer[:p['a_len']]

        # Context: question_type + interview_mode + interview_type form the evaluation lens
        if question_type == 'written':
            eval_context = (
                "WRITTEN interview answer — STRICT evaluation required. "
                "Weight: technical correctness (30%) > depth of explanation (25%) > solution completeness (20%) > clarity (15%) > communication (10%). "
                "Penalize vague answers that lack code/algorithms/concrete steps. "
                "Short answers (<50 words) should score LOW on depth. "
                "Factually incorrect claims should score 0-3 on technical accuracy. "
                "Evaluate ONLY what the candidate actually wrote — do not assume or infer missing content."
            )
        else:
            eval_context = (
                "MOCK (real-time verbal) interview answer. "
                "Weight: problem-solving approach > technical accuracy > clarity > communication. "
                "Be lenient on minor wording issues but STRICT on conceptual correctness. "
                "Factually wrong statements must be heavily penalized in TECHNICAL_ACCURACY."
            )

        # Interview-type-aware dimension weighting
        ANALYSIS_TYPE_FOCUS = {
            'technical':     "Focus on TECHNICAL_ACCURACY and DEPTH. Code correctness and algorithm knowledge are critical.",
            'behavioral':    "Focus on COMMUNICATION and CLARITY. Evaluate STAR method usage, leadership examples, conflict resolution quality. Be lenient on TECHNICAL_ACCURACY.",
            'system-design': "Focus on DEPTH and TECHNICAL_ACCURACY. Evaluate architecture decisions, scalability reasoning, trade-off analysis.",
            'hr':            "Focus on COMMUNICATION, CONFIDENCE, and RELEVANCE. Evaluate cultural fit, motivation, career alignment. Be lenient on TECHNICAL_ACCURACY and DEPTH.",
        }
        type_focus = ANALYSIS_TYPE_FOCUS.get(interview_type, ANALYSIS_TYPE_FOCUS['technical'])

        if interview_mode == 'voice':
            mode_note = (
                f"Mode: VOICE/spoken answer for {company or 'the company'}. "
                "Boost COMMUNICATION and CONFIDENCE scores for fluent verbal delivery. "
                "Do not penalize lack of code syntax — prioritize spoken explanation quality."
            )
        else:
            mode_note = (
                f"Mode: TEXT answer for {company or 'the company'}. "
                "Evaluate structure, completeness, and technical precision."
            )

        diff_key = (level or 'mid').lower()
        _, diff_desc = DIFFICULTY_MAP.get(diff_key, DIFFICULTY_MAP['default'])
        company_style = COMPANY_STYLES.get((company or 'default').lower(), COMPANY_STYLES['default'])

        user_msg = (
            f"Evaluate this {level}-level {field} {interview_type} interview answer for {company or 'a tech company'}.\n"
            f"Interview type: {interview_type.upper()} — {type_focus}\n"
            f"Level expectation: {diff_desc}.\n"
            f"Company style: {company_style}\n"
            f"Evaluation type: {eval_context}\n"
            f"{mode_note}\n\n"
            f"QUESTION: {q_short}\n\n"
            f"ANSWER: {a_short}"
        )

        messages = [
            {"role": "user", "content": self._SCORING_RUBRIC + "\n\n" + user_msg},
        ]

        stop_seqs = ["\n\n\n"]

        if store_async and answer_uuid:
            heuristic = self._fallback_analysis(question, answer)
            heuristic['source'] = 'heuristic_pending'

            def _bg_analyze():
                try:
                    t0 = _t.time()
                    resp = self.client.chat.completions.create(
                        model=self.model_name,
                        messages=messages,
                        max_tokens=p['max_tokens'],
                        temperature=p['temperature'],
                        top_p=p['top_p'],
                        stop=stop_seqs,
                        timeout=p['timeout'])
                    perf_ctrl.record_response(_t.time() - t0)
                    raw = resp.choices[0].message.content
                    result = self._parse_analysis_output(raw, answer)
                    result['source'] = 'mistral-bg'
                    with _pending_analysis_lock:
                        _pending_analysis[answer_uuid] = {'status': 'done', 'analysis': result}
                    app.logger.info(f"[BG Analysis] {answer_uuid[:8]} done in {_t.time()-t0:.1f}s "
                                    f"score={result['score']}")
                    self._update_answer_scores_in_db(answer_uuid, result)
                    # Write to AnswerCache so future identical Q+A pairs get instant response
                    self._write_answer_cache(question, answer, result)
                except Exception as e:
                    app.logger.error(f"[BG Analysis] {answer_uuid[:8]} failed: {str(e)[:80]}")
                    with _pending_analysis_lock:
                        _pending_analysis[answer_uuid] = {
                            'status': 'error',
                            'analysis': self._fallback_analysis(question, answer)
                        }

            with _pending_analysis_lock:
                _pending_analysis[answer_uuid] = {'status': 'pending', 'analysis': heuristic}
            threading.Thread(target=_bg_analyze, daemon=True,
                             name=f"BGAnalysis-{answer_uuid[:8]}").start()
            return heuristic

        # Blocking path
        try:
            t0 = _t.time()
            resp = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                max_tokens=p['max_tokens'],
                temperature=p['temperature'],
                top_p=p['top_p'],
                stop=stop_seqs,
                timeout=p['timeout'])
            perf_ctrl.record_response(_t.time() - t0)
            raw = resp.choices[0].message.content
            elapsed = _t.time() - t0
            app.logger.info(f"[Mistral Analyze] {len(raw)}chars in {elapsed:.1f}s")
            result = self._parse_analysis_output(raw, answer)
            if result['score'] > 0:
                perf_ctrl.record_parse_success()
                # Retry once if all dimension scores fell to median (garbled output)
                core = [result['technical_accuracy'], result.get('depth_score', 0),
                        result.get('clarity_score', 0), result.get('relevance_score', 0)]
                if len(set(round(s, 1) for s in core)) == 1 and core[0] == result['score']:
                    app.logger.warning("[Mistral Fast] All scores identical — retrying")
                    resp2 = self.client.chat.completions.create(
                        model=self.model_name, messages=messages,
                        max_tokens=p['max_tokens'],
                        temperature=max(0.05, p['temperature'] - 0.05),
                        top_p=0.78, stop=stop_seqs, timeout=p['timeout'])
                    perf_ctrl.record_response(_t.time() - t0)
                    result = self._parse_analysis_output(resp2.choices[0].message.content, answer)
            else:
                perf_ctrl.record_parse_failure()
            return result
        except Exception as e:
            app.logger.error(f"[Mistral] analyze_answer_fast: {str(e)[:80]}")
            if any(k in str(e).lower() for k in ['timeout', 'connection', 'refused', 'network']):
                self.is_available = False
                self.check_failures += 1
            return self._fallback_analysis(question, answer)

    def _update_answer_scores_in_db(self, answer_uuid, analysis):
        """Update Answer + Feedback rows with real AI scores after background analysis."""
        try:
            with app.app_context():
                ans = Answer.query.filter_by(uuid=answer_uuid).first()
                if not ans:
                    return
                ans.score              = analysis['score']
                ans.technical_accuracy = analysis['technical_accuracy']
                ans.depth_score        = analysis.get('depth_score', analysis['score'])
                ans.clarity_score      = analysis.get('clarity_score', analysis['score'])
                ans.relevance_score    = analysis.get('relevance_score', analysis['score'])
                ans.communication_score= analysis.get('communication_score', analysis['score'])
                ans.confidence_score   = analysis.get('confidence_score', analysis['score'])
                fb = Feedback.query.filter_by(answer_id=ans.id).first()
                if fb:
                    fb.score             = analysis['score']
                    fb.strengths         = json.dumps(analysis.get('strengths', []))
                    fb.improvements      = json.dumps(analysis.get('weaknesses', []))
                    fb.detailed_feedback = analysis.get('feedback', '')
                    fb.improvement_plan  = json.dumps(analysis.get('improvement_plan', []))
                    fb.model_used        = analysis.get('model', self.model_name)
                db.session.commit()
                app.logger.info(f"[BG Analysis] DB scores updated for answer {answer_uuid[:8]}")
        except Exception as e:
            app.logger.warning(f"[BG Analysis] DB update failed: {str(e)[:80]}")

    def _write_answer_cache(self, question, answer, analysis):
        """
        Persist AI analysis to AnswerCache so future identical Q+A pairs skip the AI call.
        Safe to call from background threads — uses its own app_context + session.
        """
        try:
            from hashlib import sha256
            question_hash = sha256(question.lower().encode()).hexdigest()
            answer_hash   = sha256(answer.lower().encode()).hexdigest()
            length_bucket = len(answer.split()) // 10
            with app.app_context():
                exists = AnswerCache.query.filter_by(
                    question_hash=question_hash,
                    answer_hash=answer_hash,
                    answer_length=length_bucket,
                ).first()
                if exists:
                    # Update hit-count and refresh cached analysis
                    exists.cached_analysis = json.dumps(analysis)
                    exists.hit_count       = (exists.hit_count or 0) + 1
                    exists.last_accessed   = datetime.utcnow()
                else:
                    entry = AnswerCache(
                        question_hash   = question_hash,
                        answer_hash     = answer_hash,
                        answer_length   = length_bucket,
                        cached_analysis = json.dumps(analysis),
                        hit_count       = 0,
                    )
                    db.session.add(entry)
                db.session.commit()
                app.logger.info(f"[AnswerCache] Written — q={question_hash[:8]} a={answer_hash[:8]}")
        except Exception as e:
            app.logger.warning(f"[AnswerCache] Write failed: {str(e)[:80]}")

    def _parse_analysis_output(self, text, answer):
        """
        Unified parser for structured analysis output.
        Handles Mistral output styles in priority order:
          1. Full labels:   TECHNICAL_ACCURACY: 7
          2. Short labels:  TA: 7
        Falls back to _parse_fast_analysis if fewer than 3 scores found.
        """
        def num(patterns, default=None):
            for pat in patterns:
                m = re.search(pat, text, re.IGNORECASE)
                if m:
                    try:
                        v = float(m.group(1))
                        if 0.0 <= v <= 10.0:
                            return v
                    except (ValueError, IndexError):
                        pass
            return default

        def single_line(patterns):
            """Extract a single-line value; reject literal placeholder text."""
            for pat in patterns:
                m = re.search(pat, text, re.IGNORECASE)
                if m:
                    v = m.group(1).strip()
                    if re.match(r'^<[^>]+>$', v):   # placeholder like <something>
                        continue
                    v = v.split('\n')[0].strip()
                    if len(v) > 2:
                        return v[:300]
            return None

        def multi_line(patterns, max_chars=500):
            """Extract a multi-line value (for FEEDBACK which spans 2 sentences)."""
            for pat in patterns:
                m = re.search(pat, text, re.IGNORECASE | re.DOTALL)
                if m:
                    v = m.group(1).strip()
                    if re.match(r'^<[^>]+>$', v):
                        continue
                    # Stop at next all-caps label
                    v = re.split(r'\n[A-Z_]{3,}:', v)[0].strip()
                    # Remove excess blank lines
                    v = re.sub(r'\n{3,}', '\n\n', v)
                    if len(v) > 4:
                        return v[:max_chars]
            return None

        # ── Extract all 7 scores ─────────────────────────────────────────────
        ta   = num([r'TECHNICAL_ACCURACY\s*:\s*([\d.]+)', r'\bTA\s*:\s*([\d.]+)'])
        dep  = num([r'\bDEPTH\s*:\s*([\d.]+)',             r'\bDE\s*:\s*([\d.]+)'])
        cla  = num([r'\bCLARITY\s*:\s*([\d.]+)',           r'\bCL\s*:\s*([\d.]+)'])
        rel  = num([r'\bRELEVANCE\s*:\s*([\d.]+)',         r'\bRE\s*:\s*([\d.]+)'])
        com  = num([r'\bCOMMUNICATION\s*:\s*([\d.]+)',     r'\bCOM\s*:\s*([\d.]+)',
                    r'\bCO\s*:\s*([\d.]+)'])
        conf = num([r'\bCONFIDENCE\s*:\s*([\d.]+)',        r'\bCONF\s*:\s*([\d.]+)',
                    r'\bCF\s*:\s*([\d.]+)'])
        ov   = num([r'\bOVERALL(?:_SCORE)?\s*:\s*([\d.]+)', r'\bOV\s*:\s*([\d.]+)'])

        # ── Fallback if fewer than 3 scores parsed ───────────────────────────
        found = [x for x in [ta, dep, cla, rel, com, conf] if x is not None]
        if len(found) < 3:
            app.logger.warning(f"[ParseAnalysis] Only {len(found)}/6 scores found, retrying with legacy parser")
            return self._parse_fast_analysis(text, answer)

        # Fill missing with median
        import statistics as _stats
        median_score = round(_stats.median(found), 1)
        ta   = ta   if ta   is not None else median_score
        dep  = dep  if dep  is not None else median_score
        cla  = cla  if cla  is not None else median_score
        rel  = rel  if rel  is not None else median_score
        com  = com  if com  is not None else median_score
        conf = conf if conf is not None else median_score

        # Weighted overall; blend with model's OVERALL if provided
        computed = round(ta*0.30 + dep*0.20 + cla*0.20 + rel*0.15 + com*0.10 + conf*0.05, 2)
        if ov is not None:
            overall = round(ov * 0.4 + computed * 0.6, 2)
        else:
            overall = computed

        # ── Extract text fields ──────────────────────────────────────────────
        # STRENGTH/STRENGTHS: handles both single-line and bullet-point formats
        def extract_section(markers, text_block):
            """Extract a section that may be single-line OR bullet-point format."""
            for marker in markers:
                # Try single-line: MARKER: some text on same line
                m = re.search(marker + r'\s*:\s*(.+?)(?=\n[A-Z_]{3,}:|\Z)', text_block, re.IGNORECASE)
                if m:
                    val = m.group(1).strip()
                    if re.match(r'^<[^>]+>$', val):
                        continue
                    # Check if it's bullet points (starts with newline + dash)
                    lines = val.split('\n')
                    bullets = [l.lstrip('- ').strip() for l in lines if l.strip().startswith('-') and len(l.strip()) > 2]
                    if bullets:
                        return '. '.join(bullets[:3])
                    # Single line value
                    first_line = lines[0].strip()
                    if len(first_line) > 2:
                        return first_line[:300]
                # Try bullet-point format: MARKER:\n- point\n- point
                m2 = re.search(marker + r'\s*:\s*\n((?:\s*-\s*.+\n?)+)', text_block, re.IGNORECASE)
                if m2:
                    bullet_block = m2.group(1)
                    bullets = [l.lstrip('- ').strip() for l in bullet_block.split('\n') if l.strip().startswith('-') and len(l.strip()) > 2]
                    if bullets:
                        return '. '.join(bullets[:3])
            return None

        strength_raw = extract_section(['STRENGTHS?', 'ST'], text)
        improve_raw = extract_section(['IMPROVEMENTS?', 'WEAKNESS(?:ES)?', 'IM'], text)

        # FEEDBACK: multi-line (2 sentences)
        feedback_raw = multi_line([
            r'FEEDBACK\s*:\s*(.+)',
            r'DETAILED_FEEDBACK\s*:\s*(.+)',
            r'\bFB\s*:\s*(.+)',
        ])

        # IMPROVEMENT_PLAN: also try bullet extraction
        plan_raw = extract_section(['IMPROVEMENT_PLAN'], text)

        wc = len(answer.split())
        strength_raw = (strength_raw or 'Engaged with the question and provided a relevant response.')[:250]
        improve_raw  = (improve_raw  or 'Provide more specific examples, edge cases, and trade-off discussion.')[:250]

        # Build 3 strengths and 3 improvements for richer feedback
        strengths = _build_feedback_points(strength_raw, 'strength', ta, dep, cla)
        improvements = _build_feedback_points(improve_raw, 'improvement', ta, dep, cla)

        if feedback_raw:
            feedback = feedback_raw.strip()[:500]
        else:
            quality = 'Strong technical knowledge shown' if overall >= 7 else 'More depth and examples needed'
            feedback = (
                f"Score {overall}/10 for this {wc}-word answer. {quality}. "
                f"Focus on {'expanding depth and providing concrete examples' if dep < 7 else 'maintaining strong clarity and structure'}."
            )[:500]

        app.logger.info(
            f"[ParseAnalysis] ta={ta} dep={dep} cl={cla} rel={rel} co={com} cf={conf} ov={overall:.2f}"
        )
        return {
            'score':               overall,
            'technical_accuracy':  ta,
            'depth_score':         dep,
            'clarity_score':       cla,
            'relevance_score':     rel,
            'communication_score': com,
            'confidence_score':    conf,
            'strengths':           strengths,
            'weaknesses':          improvements,
            'improvement_plan':    [plan_raw or improve_raw,
                                    'Review the core theory and reference material for this topic.',
                                    'Practice answering 2-3 similar questions under timed conditions.'],
            'feedback':            feedback,
            'model':               self.model_name,
        }

    def _parse_compact_analysis(self, text, answer):
        """Kept for backward compatibility — delegates to unified parser."""
        return self._parse_analysis_output(text, answer)

    def analyze_answer_stream(self, question, answer, field, level, company='',
                              question_type='mock', interview_mode='text', interview_type='technical'):
        """
        STREAMING analysis generator: yields SSE-formatted chunks as Mistral generates.
        Each chunk: 'data: {"t":"<token>"}\n\n'
        Final chunk: 'data: {"done":true,"analysis":{...}}\n\n'
        Uses the same rubric-anchored prompt as analyze_answer_fast.
        """
        self._ensure_available()
        if not self.is_available:
            fb = self._fallback_analysis(question, answer)
            yield f"data: {json.dumps({'done': True, 'analysis': fb, 'source': 'fallback'})}\n\n"
            return

        p = perf_ctrl.params_for_analysis(field, level, answer)
        q_short = question[:p['q_len']]
        a_short = answer[:p['a_len']]

        if question_type == 'written':
            eval_context = (
                "WRITTEN interview answer — STRICT evaluation required. "
                "Weight: technical correctness > depth of explanation > solution completeness > clarity. "
                "Penalize vague/short answers. Factually incorrect = low TECHNICAL_ACCURACY."
            )
        else:
            eval_context = (
                "MOCK (real-time verbal) interview answer. "
                "Weight: problem-solving approach > technical accuracy > clarity > communication. "
                "Strict on conceptual correctness."
            )

        # Interview-type-aware evaluation focus
        STREAM_TYPE_FOCUS = {
            'technical':     "Focus on TECHNICAL_ACCURACY and DEPTH.",
            'behavioral':    "Focus on COMMUNICATION and CLARITY. Evaluate STAR method, leadership examples.",
            'system-design': "Focus on DEPTH and TECHNICAL_ACCURACY. Evaluate architecture and trade-offs.",
            'hr':            "Focus on COMMUNICATION and CONFIDENCE. Evaluate cultural fit and motivation.",
        }
        type_focus = STREAM_TYPE_FOCUS.get(interview_type, STREAM_TYPE_FOCUS['technical'])

        mode_note = (
            f"Mode: VOICE answer — boost COMMUNICATION/CONFIDENCE for spoken delivery."
            if interview_mode == 'voice'
            else f"Mode: TEXT answer for {company or 'a tech company'} — evaluate precision."
        )

        diff_key = (level or 'mid').lower()
        _, diff_desc = DIFFICULTY_MAP.get(diff_key, DIFFICULTY_MAP['default'])
        company_style = COMPANY_STYLES.get((company or 'default').lower(), COMPANY_STYLES['default'])

        messages = [
            {"role": "user", "content": self._SCORING_RUBRIC + "\n\n" + (
                f"Evaluate this {level}-level {field} {interview_type} interview answer for {company or 'a tech company'}.\n"
                f"Interview type: {interview_type.upper()} — {type_focus}\n"
                f"Level: {diff_desc}. Company style: {company_style}\n"
                f"Evaluation type: {eval_context}\n"
                f"{mode_note}\n\n"
                f"QUESTION: {q_short}\n\nANSWER: {a_short}"
            )},
        ]

        try:
            stream = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                max_tokens=p['max_tokens'],
                temperature=p['temperature'],
                top_p=p['top_p'],
                stop=["\n\n\n"],
                stream=True,
                timeout=p['timeout'])

            full_text = ""
            for chunk in stream:
                delta = chunk.choices[0].delta.content if chunk.choices[0].delta else None
                if delta:
                    full_text += delta
                    yield f"data: {json.dumps({'t': delta})}\n\n"

            analysis = self._parse_analysis_output(full_text, answer)
            analysis['source'] = 'mistral-stream'
            yield f"data: {json.dumps({'done': True, 'analysis': analysis})}\n\n"

        except Exception as e:
            app.logger.error(f"[Mistral Stream] {str(e)[:80]}")
            if any(k in str(e).lower() for k in ['timeout', 'connection', 'refused', 'network']):
                self.is_available = False
                self.check_failures += 1
            fb = self._fallback_analysis(question, answer)
            yield f"data: {json.dumps({'done': True, 'analysis': fb, 'source': 'fallback'})}\n\n"

    def _parse_fast_analysis(self, text, answer):
        """
        Parse the labeled format:
          TECHNICAL_ACCURACY: 7
          DEPTH: 6
          ...
          STRENGTH: <sentence>
          IMPROVEMENT: <sentence>
          FEEDBACK: <sentences>

        Also accepts the old compact TA:/DE: format as fallback.
        Returns all 6 dimension scores + overall + feedback fields.
        """
        # Answer-length-aware default — prevents inflated scores for short/poor answers
        _wc = len((answer or '').split())
        if _wc < 15:
            _def_score = 3.0
        elif _wc < 40:
            _def_score = 5.0
        elif _wc < 80:
            _def_score = 5.5
        else:
            _def_score = 6.0

        def extract_num(patterns, default=_def_score):
            """Try each regex pattern in order, return first match as float."""
            for pat in patterns:
                m = re.search(pat, text, re.IGNORECASE)
                if m:
                    try:
                        val = float(m.group(1))
                        return min(10.0, max(0.0, val))
                    except (ValueError, IndexError):
                        continue
            return default

        def extract_text(patterns):
            """Return first matching text capture, stripped."""
            for pat in patterns:
                m = re.search(pat, text, re.IGNORECASE)
                if m:
                    captured = m.group(1).strip()
                    # Remove angle-bracket placeholders the model forgot to fill
                    if captured.startswith('<') and captured.endswith('>'):
                        continue
                    if captured:
                        return captured
            return None

        ta   = extract_num([r'TECHNICAL_ACCURACY\s*:\s*([\d.]+)', r'\bTA\s*:\s*([\d.]+)'])
        dep  = extract_num([r'\bDEPTH\s*:\s*([\d.]+)',            r'\bDE\s*:\s*([\d.]+)'])
        cla  = extract_num([r'\bCLARITY\s*:\s*([\d.]+)',          r'\bCL\s*:\s*([\d.]+)'])
        rel  = extract_num([r'\bRELEVANCE\s*:\s*([\d.]+)',        r'\bRE\s*:\s*([\d.]+)'])
        com  = extract_num([r'\bCOMMUNICATION\s*:\s*([\d.]+)',    r'\bCO\s*:\s*([\d.]+)'])
        conf = extract_num([r'\bCONFIDENCE\s*:\s*([\d.]+)',       r'\bCF\s*:\s*([\d.]+)'])
        ov   = extract_num([r'\bOVERALL(?:_SCORE)?\s*:\s*([\d.]+)', r'\bOV\s*:\s*([\d.]+)'],
                           default=None)

        # Weighted average as sanity-check on OVERALL
        computed = ta*0.30 + dep*0.20 + cla*0.20 + rel*0.15 + com*0.10 + conf*0.05
        # Blend with model's OVERALL only if actually parsed; avoid conflating 6.0 default
        overall = round(ov * 0.4 + computed * 0.6, 2) if ov is not None else round(computed, 2)

        feedback_raw = None
        # Multi-line FEEDBACK extraction — look from keyword to triple-newline or end
        m_fb = re.search(r'(?:FEEDBACK|DETAILED_FEEDBACK)\s*:\s*(.*?)(?=\n\n\n|\Z)', text, re.IGNORECASE | re.DOTALL)
        if m_fb:
            captured = m_fb.group(1).strip()
            if not (captured.startswith('<') and captured.endswith('>')):
                feedback_raw = captured[:500]

        # Trim at double newline
        if feedback_raw:
            feedback_raw = feedback_raw.split('\n\n')[0].strip()[:500]

        strength = extract_text([
            r'STRENGTH\s*:\s*(.+?)(?=\n[A-Z]|\Z)',
            r'STRENGTHS?\s*:\s*[-•*]?\s*(.+?)(?=\n|\Z)',
        ])
        improve = extract_text([
            r'IMPROVEMENT\s*:\s*(.+?)(?=\n[A-Z]|\Z)',
            r'IMPROVEMENTS?\s*:\s*[-•*]?\s*(.+?)(?=\n|\Z)',
            r'WEAKNESS(?:ES)?\s*:\s*[-•*]?\s*(.+?)(?=\n|\Z)',
        ])

        strength = (strength or 'Provided a relevant answer to the question.')[:250]
        improve  = (improve  or 'Add concrete examples and go deeper into edge cases.')[:250]
        feedback = (feedback_raw or f'Overall score: {overall}/10. '
                                    f'Focus on depth and examples to strengthen your answers.')[:500]

        app.logger.info(
            f"[ParseFast] ta={ta} dep={dep} cla={cla} rel={rel} com={com} cf={conf} ov={overall}"
        )

        strengths_list   = _build_feedback_points(strength, 'strength',     ta, dep, cla)
        improvement_list = _build_feedback_points(improve,  'improvement',  ta, dep, cla)

        return {
            'score':              overall,
            'technical_accuracy': ta,
            'depth_score':        dep,
            'clarity_score':      cla,
            'relevance_score':    rel,
            'communication_score':com,
            'confidence_score':   conf,
            'strengths':          strengths_list,
            'weaknesses':         improvement_list,
            'improvement_plan':   improvement_list,
            'feedback':           feedback,
            'model':              self.model_name,
        }

    def _parse_questions(self, text, field, level, company, difficulty, question_type='mock'):
        questions = []
        for line in text.strip().split('\n'):
            line = line.strip()
            m = re.match(r'^[\d]+[.)]\s*(.+)', line)
            if m:
                q_text = m.group(1).strip()
            elif line.startswith('-') and len(line) > 5:
                q_text = line.lstrip('- ').strip()
            else:
                continue
            if len(q_text) > 15:
                qdata = {
                    'text': q_text, 'category': 'technical',
                    'field': field, 'level': level, 'company': company,
                    'difficulty': difficulty,
                    'topic_tags': json.dumps([field.lower()]),
                }
                
                # For mock question type, generate multiple-choice options
                if question_type == 'mock':
                    options_data = self._generate_multiple_choice_options(q_text, difficulty)
                    if options_data:
                        qdata['is_multiple_choice'] = True
                        qdata['options'] = options_data['options']
                        qdata['correct_answers'] = options_data['correct_answers']
                        qdata['multiple_allowed'] = options_data['multiple_allowed']
                
                questions.append(qdata)
        return questions
    
    def _generate_multiple_choice_options(self, question, difficulty):
        """Generate 4 multiple-choice options with EXACTLY ONE CORRECT answer using contextual analysis.
        
        GUARANTEES:
        - Exactly 4 options (A, B, C, D)
        - All options are semantically related to the question
        - Exactly ONE option is marked as correct (100% accuracy)
        - Options vary in wrongness (obvious to subtle)
        - No duplicate options
        """
        if not self.is_available:
            return self._generate_fallback_mc_options(question, difficulty)
        
        # Build prompt requesting structured MC options with contextual distractors
        prompt = f"""CRITICAL TASK: Generate 4 multiple-choice options for this {difficulty} interview question.
GUARANTEE: Exactly ONE correct answer, ALL options semantically similar to question topic.

QUESTION: {question}
DIFFICULTY: {difficulty}

SEMANTIC ANALYSIS REQUIREMENTS (100% accuracy required):
1. Generate EXACTLY 4 options (A-D) - MUST BE EXACTLY 4
2. ALL options MUST address the SAME topic as the question
3. All options must be plausible answers that relate to the core concept
4. Options must have varying levels of correctness:
   - 1 option: COMPLETELY CORRECT - best possible answer
   - 1 option: Partially correct - related concept but with a subtle error
   - 2 options: Incorrect but plausible - reasonable-sounding but wrong
5. Semantic similarity guidance:
   - If question asks "how to optimize database", ALL answers should be about database optimization techniques
   - Options should use similar vocabulary and terminology
   - Avoid completely off-topic distractors
6. NO duplicates or near-duplicates
7. Each option: 1-2 professional sentences, clear and specific
8. EXACTLY ONE answer is correct - not ambiguous
9. Do NOT make correct answer obviously longest/shortest

RESPONSE FORMAT (STRICT - MUST FOLLOW EXACTLY):
A) [Option text - specific, professional, 1-2 sentences]
B) [Option text - specific, professional, 1-2 sentences]
C) [Option text - specific, professional, 1-2 sentences]
D) [Option text - specific, professional, 1-2 sentences]

CORRECT_ANSWER: [ONLY the letter, e.g., B]
EXPLANATION: [One sentence: Why this is the best/most correct answer]

Generate now:"""

        try:
            app.logger.info(f"[Mistral MC] Requesting options for: {question[:50]}... ({difficulty})")
            resp = self.client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=700,  # Increased for better quality
                temperature=0.5,  # More deterministic for consistency
                top_p=0.85,
                timeout=60.0)  # 60-second timeout for MC options generation (increased from 12s)
            raw_text = resp.choices[0].message.content
            app.logger.info(f"[Mistral MC] Response received ({len(raw_text)} chars)")
            app.logger.debug(f"[Mistral MC] Raw response: {raw_text[:300]}...")
            
            parsed = self._parse_multiple_choice(raw_text)
            # Validation: must have exactly 4 options and exactly 1 correct answer
            if parsed and len(parsed.get('options', [])) == 4 and len(parsed.get('correct_answers', [])) == 1:
                # SUCCESS: All validations passed
                parsed['multiple_allowed'] = False  # Mock questions: single answer only
                correct_idx = parsed['correct_answers'][0]
                app.logger.info(f"[Mistral MC] [SUCCESS] 4 options generated, correct: {chr(65+correct_idx)}")
                return parsed
            elif parsed and len(parsed.get('options', [])) >= 3:
                # Partial: Try to salvage response — trim to 4 if we have more
                app.logger.warning(f"[Mistral MC] Partial parse: {len(parsed.get('options', []))} options, {len(parsed.get('correct_answers', []))} answers")
                if len(parsed.get('options', [])) > 4:
                    # Trim to 4, keeping correct answer
                    opts = parsed['options']
                    correct_idx = parsed.get('correct_answers', [0])[0] if parsed.get('correct_answers') else 0
                    correct_opt = opts[correct_idx] if correct_idx < len(opts) else opts[0]
                    other_opts = [o for i, o in enumerate(opts) if i != correct_idx][:3]
                    import random as _rnd_mc
                    final = other_opts + [correct_opt]
                    _rnd_mc.shuffle(final)
                    parsed['options'] = final
                    parsed['correct_answers'] = [final.index(correct_opt)]
                elif len(parsed.get('options', [])) < 4:
                    # Not enough options - don't use, fall back
                    app.logger.warning(f"[Mistral MC] Insufficient options - falling back")
                    return self._generate_fallback_mc_options(question, difficulty)
                # Force to single correct answer if multiple found
                if len(parsed.get('correct_answers', [])) != 1:
                    parsed['correct_answers'] = [parsed['correct_answers'][0] if parsed['correct_answers'] else 0]
                parsed['multiple_allowed'] = False
                app.logger.info(f"[Mistral MC] Partial salvage: using {len(parsed['options'])} options")
                return parsed
            else:
                # Complete parse failure
                app.logger.warning(f"[Mistral MC] Parse failed or invalid structure - using fallback")
                return self._generate_fallback_mc_options(question, difficulty)
            
        except Exception as e:
            error_type = type(e).__name__
            error_msg = str(e)[:150]
            app.logger.error(f"[Mistral MC] [ERR] {error_type}: {error_msg}")
            
            # Mark as offline if network-related
            error_keywords = ["timeout", "timed out", "connection", "network", "refused", "unreachable"]
            if any(keyword in error_msg.lower() for keyword in error_keywords):
                self.is_available = False
                self.check_failures += 1
                app.logger.warning(f"[Mistral MC] Network issue detected - marked offline (attempt #{self.check_failures})")
            
            app.logger.info("[Mistral MC] Falling back to generated options")
            return self._generate_fallback_mc_options(question, difficulty)
    
    def _parse_multiple_choice(self, text):
        """Parse AI response into structured MC options with STRICT validation for 100% accuracy guarantee.
        
        VALIDATION CHECKLIST (ALL MUST PASS):
        - Extract exactly 4 options (A-D)
        - Extract exactly 1 correct answer (not 0, not multiple)
        - Correct answer index must be valid (0-3)
        - Each option must be non-empty and meaningful
        - No duplicate options
        """
        options = []
        correct_answers = []
        explanation = ""
        
        try:
            if not text or len(text.strip()) < 10:
                app.logger.warning(f"[MC Parse] Input too short ({len(text)} chars) - invalid response")
                return None
                
            lines = [line.strip() for line in text.strip().split('\n')]
            app.logger.debug(f"[MC Parse] Processing {len(lines)} lines")
            
            # === STEP 1: PARSE OPTIONS (A-E) ===
            # Look for patterns: "A) text", "A: text", "A - text", or "A| text"
            # Case-insensitive to handle various AI formats
            for i, line in enumerate(lines):
                if not line:
                    continue
                # Match letter A-E followed by punctuation then option text
                match = re.match(r'^\s*([a-dA-D])\s*[\)\:\-\|\.]\s*(.+)$', line)
                if match:
                    option_letter = match.group(1).upper()
                    option_text = match.group(2).strip()
                    
                    # Validation: option must be meaningful (min 3 chars)
                    if len(option_text) < 3:
                        app.logger.warning(f"[MC Parse] Option {option_letter} too short ({len(option_text)} chars): {option_text}")
                        continue
                    
                    # Check for duplicates
                    if option_text in options:
                        app.logger.warning(f"[MC Parse] Duplicate option detected: {option_text[:40]}...")
                        continue
                    
                    options.append(option_text)
                    app.logger.debug(f"[MC Parse] Parsed option {option_letter}: {option_text[:50]}...")
            
            app.logger.info(f"[MC Parse] Extracted {len(options)} options from response")
            
            # === STEP 2: PARSE CORRECT ANSWER (EXACTLY ONE) ===
            # Look for markers indicating correct answer line
            correct_answer_markers = ['CORRECT_ANSWER', 'CORRECT ANSWER', 'ANSWER:', 'CORRECT:', 'ANSWER IS', 'THE ANSWER']
            
            for line in lines:
                line_upper = line.upper()
                # Check if this line contains a correct answer marker
                if any(marker in line_upper for marker in correct_answer_markers):
                    # Extract answer after the marker
                    answer_part = line
                    if ':' in line:
                        answer_part = line.split(':', 1)[-1]
                    elif '=' in line:
                        answer_part = line.split('=', 1)[-1]
                    
                    answer_part = answer_part.strip()
                    
                    # Find ALL letters A-D in answer part
                    found_letters = re.findall(r'[A-Da-d]', answer_part)
                    if found_letters:
                        # CRITICAL: Take ONLY the first letter
                        chosen_letter = found_letters[0].upper()
                        correct_idx = ord(chosen_letter) - ord('A')
                        
                        # Validate index is in valid range
                        if 0 <= correct_idx < len(options):
                            correct_answers = [correct_idx]  # Force exactly one
                            app.logger.info(f"[MC Parse] Correct answer identified: {chosen_letter} (Index {correct_idx})")
                            break
                        else:
                            app.logger.warning(f"[MC Parse] Correct answer {chosen_letter} index {correct_idx} out of range (have {len(options)} options)")
            
            # === STEP 3: PARSE EXPLANATION (OPTIONAL) ===
            explanation_markers = ['WHY', 'BECAUSE', 'EXPLANATION', 'JUSTIFICATION']
            for line in lines:
                line_upper = line.upper()
                if any(marker in line_upper for marker in explanation_markers) and ':' in line:
                    explanation = line.split(':', 1)[-1].strip()
                    app.logger.debug(f"[MC Parse] Explanation found: {explanation[:60]}...")
                    break
            
            # === STEP 4: STRICT VALIDATION (ALL MUST PASS) ===
            validation_passed = True
            issues = []
            
            if len(options) != 4:
                validation_passed = False
                issues.append(f"Options: {len(options)}/4 (NEED EXACTLY 4)")
            
            if len(correct_answers) != 1:
                validation_passed = False
                issues.append(f"Correct answers: {len(correct_answers)}/1 (NEED EXACTLY 1)")
            
            if correct_answers and not (0 <= correct_answers[0] < len(options)):
                validation_passed = False
                issues.append(f"Answer index {correct_answers[0]} out of range [0-{len(options)-1}]")

            # === FINAL DECISION ===
            if validation_passed:
                # ALL VALIDATIONS PASSED [PASS]
                app.logger.info("[MC Parse] [PASS] VALIDATION PASSED [PASS]")
                app.logger.info(f"  - Options: {len(options)} (correct)")
                app.logger.info(f"  - Correct answer: {chr(65 + correct_answers[0])} (Index {correct_answers[0]})")
                for idx, opt in enumerate(options):
                    marker = " ← CORRECT" if idx == correct_answers[0] else ""
                    app.logger.debug(f"    {chr(65+idx)}) {opt[:45]}...{marker}")
                
                return {
                    'options': options,
                    'correct_answers': correct_answers,  # Guaranteed: exactly 1 element
                    'multiple_allowed': False,  # Mock: single answer only
                    'explanation': explanation, }
            else:
                # VALIDATION FAILED [FAIL]
                app.logger.error("[MC Parse] [FAIL] VALIDATION FAILED [FAIL]")
                for issue in issues:
                    app.logger.error(f"  [X] {issue}")
                app.logger.error(f"  Text length: {len(text)} chars")
                app.logger.error(f"  First 300 chars: {text[:300]}...")
                return None
                
        except Exception as e:
            app.logger.error(f"[MC Parse Exception] {type(e).__name__}: {str(e)[:150]}")
            import traceback
            tb_lines = traceback.format_exc().split('\n')
            for tb_line in tb_lines[:5]:
                app.logger.error(f"  {tb_line}")
            return None

    def _generate_fallback_mc_options(self, question, difficulty):
        """Generate fallback multiple-choice options when AI is unavailable.
        Creates smart distractors contextually related to the question by analyzing keywords.
        Returns exactly 4 options (A-D) with 1 correct answer."""
        import hashlib
        
        try:
            # Extract key concepts from the question
            question_lower = question.lower()
            
            # Common technical concepts and their variations
            concept_distractors = {
                'api': ['REST', 'SOAP', 'GraphQL', 'RPC', 'gRPC'],
                'database': ['SQL', 'NoSQL', 'MongoDB', 'PostgreSQL', 'MySQL'],
                'cache': ['Redis', 'Memcached', 'DynamoDB', 'Cassandra', 'Elasticsearch'],
                'scaling': ['Horizontal', 'Vertical', 'Load Balancing', 'Sharding', 'Replication'],
                'security': ['OAuth', 'JWT', 'SSL/TLS', 'CORS', 'CSRF'],
                'performance': ['Caching', 'Indexing', 'Async', 'CDN', 'Compression'],
                'design pattern': ['Singleton', 'Factory', 'Observer', 'Strategy', 'Adapter'],
                'algorithm': ['BFS', 'DFS', 'Dijkstra', 'Binary Search', 'Dynamic Programming'],
            }
            
            # Generate deterministic but diverse options
            seed_num = int(hashlib.md5(question.encode()).hexdigest(), 16) % 100000
            base_options = []
            
            # Find matching concepts and create distractors
            matched_concepts = []
            for concept, distractors in concept_distractors.items():
                if concept in question_lower:
                    matched_concepts.extend(distractors)
            
            # If concepts found, use them; otherwise create generic options
            if matched_concepts:
                # Use first 3 as distractors
                for i in range(3):
                    idx = (seed_num + i) % len(matched_concepts)
                    option = matched_concepts[idx]
                    if option not in base_options:
                        base_options.append(option)
            
            # Ensure we have 3 distractors
            generic_distractors = ['Implementation Detail', 'Architecture Pattern', 'Best Practice', 'Common Approach']
            while len(base_options) < 3:
                idx = (seed_num + len(base_options)) % len(generic_distractors)
                option = generic_distractors[idx]
                if option not in base_options:
                    base_options.append(option)
            
            # The correct answer should be extracted from question context
            correct_phrase = self._extract_correct_answer_phrase(question)
            
            # Build 4 options: 3 distractors + 1 correct
            all_options = base_options[:3] + [correct_phrase]
            import random as _rnd
            # Shuffle to randomize correct answer position
            indices = list(range(4))
            _rnd.shuffle(indices)
            shuffled = [all_options[i] for i in indices]
            correct_final_idx = indices.index(3)  # where the correct answer ended up
            
            app.logger.info(f"[Fallback MC] Generated 4 options with correct answer at index {correct_final_idx}")
            
            return {
                'options': shuffled,
                'correct_answers': [correct_final_idx],
                'multiple_allowed': False,
                'explanation': 'Generated fallback options - AI unavailable',
            }
            
        except Exception as e:
            app.logger.error(f"[Fallback MC] Error: {str(e)[:100]}")
            # Return absolute basic fallback
            return {
                'options': ['Option A', 'Option B', 'Option C', 'Option D'],
                'correct_answers': [0],
                'multiple_allowed': False,
                'explanation': 'Basic fallback - generation failed',
            }
    
    def _extract_correct_answer_phrase(self, question):
        """Extract likely correct answer phrase from question for fallback generation."""
        # Remove question marks and extra spaces
        q = question.strip().rstrip('?')
        
        # Common answer patterns based on question type
        if 'what is' in q.lower() or 'what are' in q.lower():
            # Extract after "what is/are"
            parts = q.lower().split('what is')[-1].split('what are')[-1]
            # Take first 3-4 words
            words = parts.strip().split()
            return ' '.join(words[:3]).title() if words else 'Correct Answer'
        elif 'how do you' in q.lower() or 'how do i' in q.lower():
            return 'Implement best practices'
        elif 'when should' in q.lower():
            return 'When requirements change'
        elif 'which' in q.lower():
            return 'The optimal solution'
        else:
            # Default: take last meaningful phrase
            words = [w for w in q.split() if len(w) > 3]
            return ' '.join(words[-2:]).title() if len(words) > 1 else 'Correct Answer'

    def _parse_analysis(self, text, answer):
        # Answer-length-aware default — short/empty answers shouldn't default to 7.0
        _wc = len((answer or '').split())
        if _wc < 15:
            _def_score = 3.0
        elif _wc < 40:
            _def_score = 5.0
        elif _wc < 80:
            _def_score = 6.0
        else:
            _def_score = 7.0

        def num(pattern, default=_def_score):
            m = re.search(pattern, text, re.IGNORECASE)
            if m:
                try: return min(10.0, max(0.0, float(m.group(1))))
                except: pass
            return default

        def bullets(marker):
            items, active = [], False
            for line in text.split('\n'):
                if marker.upper() in line.upper(): active = True; continue
                if active:
                    s = line.strip()
                    if s.startswith('-') and len(s) > 2: items.append(s.lstrip('- ').strip())
                    elif s and not s.startswith('-') and items: break
            return items

        def block(marker):
            idx = text.upper().find(marker.upper())
            if idx == -1: return ''
            blk = text[idx + len(marker):].strip()
            for m2 in re.finditer(r'\n[A-Z_]{5,}:', blk):
                blk = blk[:m2.start()]; break
            return blk.strip()

        ta   = num(r'TECHNICAL_ACCURACY\s*:\s*([\d.]+)')
        dep  = num(r'DEPTH\s*:\s*([\d.]+)')
        cla  = num(r'CLARITY\s*:\s*([\d.]+)')
        rel  = num(r'RELEVANCE\s*:\s*([\d.]+)')
        com  = num(r'COMMUNICATION\s*:\s*([\d.]+)')
        conf = num(r'CONFIDENCE\s*:\s*([\d.]+)')
        ov   = num(r'OVERALL_SCORE\s*:\s*([\d.]+)')
        computed = ta*0.30 + dep*0.20 + cla*0.20 + rel*0.15 + com*0.10 + conf*0.05
        overall  = round((ov + computed) / 2, 2)

        strengths    = bullets('STRENGTHS')        or ['Engaged with the question', 'Provided a relevant response']
        improvements = bullets('IMPROVEMENTS')     or ['Elaborate more on key points', 'Add concrete examples']
        plan         = bullets('IMPROVEMENT_PLAN') or [
            'Review core concepts for this topic',
            'Practice answering aloud in 150-300 words',
            'Complete 2 mock interviews this week',
        ]
        feedback = block('DETAILED_FEEDBACK:')
        if not feedback:
            wc = len(answer.split())
            feedback = f"Your {wc}-word answer scores {overall}/10. {'Good depth.' if wc > 80 else 'Try to elaborate more with examples.'}"

        return {
            'score': overall, 'technical_accuracy': ta, 'depth_score': dep,
            'clarity_score': cla, 'relevance_score': rel,
            'communication_score': com, 'confidence_score': conf,
            'strengths': strengths[:3], 'weaknesses': improvements[:3],
            'improvement_plan': plan[:3], 'feedback': feedback,
            'model': self.model_name,
        }

    def _fallback_questions(self, field, level, company, num, question_type='mock', interview_type='technical'):
        """Generate fallback questions when Mistral is unavailable.
        For mock interviews, also generates MC options.
        Guaranteed to return at least `num` questions via 3-tier fallback.
        """
        app.logger.info(f"[Mistral] Using fallback questions ({question_type}, type={interview_type}, need={num})")
        import random as _random

        itype = (interview_type or 'technical').lower()

        # ── TIER 1: Try QuestionBank DB ──────────────────────────────────────
        try:
            base_q = QuestionBank.query.filter(QuestionBank.field.ilike(f'%{field}%'))
            _itype_cat = {'behavioral': 'behavioral', 'system-design': 'system_design', 'hr': 'hr'}
            db_category = _itype_cat.get(itype, 'technical')
            if itype == 'technical':
                cat_q = base_q.filter(QuestionBank.category.in_(['technical', 'system_design']))
            else:
                cat_q = base_q.filter(QuestionBank.category == db_category)
            bank = cat_q.order_by(db.func.random()).limit(num * 3).all()
            if not bank:
                bank = base_q.order_by(db.func.random()).limit(num * 3).all()
            if bank:
                _random.shuffle(bank)
                bank = bank[:num]
                questions = []
                for q in bank:
                    qdata = {
                        'text': q.text, 'category': q.category,
                        'field': field, 'level': level, 'company': company,
                        'difficulty': q.difficulty,
                        'topic_tags': q.topic_tags or json.dumps([field.lower()])
                    }
                    if question_type == 'mock':
                        mc_data = self._generate_fallback_mc_options(q.text)
                        if mc_data:
                            qdata.update(mc_data)
                    questions.append(qdata)
                if len(questions) >= num:
                    return questions[:num]
                # Not enough from DB, fall through to static pools
        except Exception as e:
            app.logger.debug(f"[Mistral] Fallback bank query failed: {str(e)[:80]}")

        # ── TIER 2: Static question pools (10+ per category) ─────────────────
        diff_key   = (level or 'mid').lower()
        difficulty = DIFFICULTY_MAP.get(diff_key, DIFFICULTY_MAP['default'])[0]
        field_low  = (field or 'software').lower()
        co         = company or 'Tech Company'

        behavioral_pool = [
            ("Tell me about a time you faced a significant challenge at work. How did you handle it?", 'behavioral', 'medium'),
            ("Describe a situation where you had to work with a difficult team member. What did you do?", 'behavioral', 'medium'),
            ("Give an example of a goal you set and how you achieved it.", 'behavioral', 'medium'),
            ("Tell me about a time you failed. What did you learn from it?", 'behavioral', 'medium'),
            ("Describe a time you showed leadership without having a formal leadership role.", 'behavioral', 'medium'),
            ("Tell me about a time you had to adapt quickly to a major change.", 'behavioral', 'medium'),
            ("Describe your greatest professional achievement and why it matters to you.", 'behavioral', 'medium'),
            ("Tell me about a time you had to deliver bad news to a stakeholder.", 'behavioral', 'hard'),
            ("Describe a time you managed competing priorities. How did you decide what to focus on?", 'behavioral', 'medium'),
            ("What motivates you most at work and how does this role align with that?", 'behavioral', 'medium'),
        ]

        hr_pool = [
            ("Why are you interested in this position?", 'hr', 'medium'),
            ("Where do you see yourself in 5 years?", 'hr', 'medium'),
            ("What are your greatest strengths and how do they apply to this role?", 'hr', 'medium'),
            ("What is your biggest weakness and what are you doing to improve it?", 'hr', 'medium'),
            (f"Why do you want to work at {co}?", 'hr', 'medium'),
            ("What is your expected salary range for this role?", 'hr', 'medium'),
            ("How do you handle stress and pressure in the workplace?", 'hr', 'medium'),
            ("Describe your ideal work environment.", 'hr', 'medium'),
            ("Are you open to relocation or remote work?", 'hr', 'medium'),
            ("Do you have any questions for us?", 'hr', 'medium'),
        ]

        system_design_pool = [
            (f"Design a URL-shortening service like bit.ly. Walk through architecture, data model, and scaling.", 'system_design', 'hard'),
            (f"Design a real-time chat system for {co} supporting millions of concurrent users.", 'system_design', 'hard'),
            ("Design a distributed rate limiter for a public API. How do you handle edge cases?", 'system_design', 'hard'),
            ("Design a news feed system like Twitter's timeline. Focus on read performance.", 'system_design', 'hard'),
            ("Design a distributed cache system. Explain eviction policies and consistency trade-offs.", 'system_design', 'hard'),
            ("Design a search autocomplete system. How do you handle millions of queries per second?", 'system_design', 'hard'),
            (f"How would you migrate {co}'s monolith to microservices without downtime?", 'system_design', 'hard'),
            ("Design a notification system that handles push, email, and SMS at scale.", 'system_design', 'hard'),
        ]

        technical_pools = {
            'software': [
                ("Explain the difference between a process and a thread. When would you use each?", 'technical', 'medium'),
                ("How does garbage collection work? What are its performance implications?", 'technical', 'medium'),
                ("Describe the CAP theorem. How would you design a payment service given those constraints?", 'technical', 'hard'),
                ("Walk me through implementing rate-limiting for a high-traffic public API.", 'technical', 'hard'),
                (f"How would you migrate a monolith to microservices at {co} without downtime?", 'technical', 'hard'),
                ("Explain the difference between optimistic and pessimistic locking. When is each appropriate?", 'technical', 'medium'),
                ("What are SOLID principles? Give a real-world example of applying one.", 'technical', 'medium'),
                ("Explain how a hash map works internally. What is the time complexity of operations?", 'technical', 'medium'),
                ("What is the difference between REST and GraphQL? When would you choose each?", 'technical', 'medium'),
                ("Describe a complex algorithm you implemented. Why did you choose that approach?", 'technical', 'hard'),
            ],
            'data': [
                ("How do you handle class imbalance in a classification problem? Explain at least 3 techniques.", 'technical', 'medium'),
                ("Explain overfitting and how you prevent it in production ML models.", 'technical', 'medium'),
                ("Walk me through your end-to-end ML pipeline for predicting customer churn.", 'technical', 'hard'),
                ("How do you evaluate a recommendation system? What metrics matter most?", 'technical', 'medium'),
                ("Explain the bias-variance tradeoff and how it guides your model selection.", 'technical', 'medium'),
                ("How do you detect and handle data drift in a production model?", 'technical', 'hard'),
                (f"Design a real-time fraud detection pipeline for {co}. Walk through your full approach.", 'technical', 'hard'),
                ("What is regularisation and when would you choose L1 over L2?", 'technical', 'medium'),
                ("Explain the difference between precision and recall. When do you optimise for each?", 'technical', 'medium'),
                ("How would you design an A/B test for a new model feature?", 'technical', 'medium'),
            ],
            'product': [
                (f"How would you measure the success of {co}'s new onboarding feature?", 'technical', 'medium'),
                ("How do you decide what NOT to build? Walk me through your framework.", 'technical', 'hard'),
                ("Design a feature to improve day-30 retention for a mobile app.", 'technical', 'hard'),
                (f"How would you launch {co}'s new product in a market you've never entered?", 'technical', 'hard'),
                ("What metrics would you track for the first 30/60/90 days of a new product?", 'technical', 'medium'),
                ("Walk me through how you'd respond to a 20% drop in DAU.", 'technical', 'hard'),
                ("How do you prioritise a backlog when stakeholders have conflicting priorities?", 'technical', 'medium'),
                ("What is your framework for setting and tracking product OKRs?", 'technical', 'medium'),
            ],
            'marketing': [
                ("How do you build a go-to-market strategy for a new SaaS product targeting SMBs?", 'technical', 'hard'),
                ("Walk me through how you'd design and measure a content marketing campaign.", 'technical', 'medium'),
                ("How do you balance brand-awareness spending with performance marketing?", 'technical', 'medium'),
                ("How would you segment customers to personalise a retention email programme?", 'technical', 'medium'),
                ("What is your framework for setting and tracking marketing OKRs?", 'technical', 'medium'),
                ("How do you measure the ROI of a brand-awareness campaign with no direct conversion?", 'technical', 'hard'),
                (f"How would you grow {co}'s organic traffic 3x in 12 months with a flat budget?", 'technical', 'hard'),
                ("What channels would you prioritise for a B2B product launch and why?", 'technical', 'medium'),
            ],
            'sales': [
                ("Walk me through your full sales process from first contact to close.", 'technical', 'medium'),
                ("How do you handle the objection 'your price is too high'?", 'technical', 'medium'),
                ("How do you forecast your pipeline with 85%+ accuracy for the quarter?", 'technical', 'medium'),
                (f"How would you build an account-based sales strategy for a key {co} target account?", 'technical', 'hard'),
                ("How do you shorten a 6-month enterprise sales cycle?", 'technical', 'hard'),
                ("What CRM metrics do you track weekly and how do they drive your actions?", 'technical', 'medium'),
            ],
            'finance': [
                ("Walk me through the three financial statements and how they connect to each other.", 'technical', 'medium'),
                ("How would you value a pre-revenue startup using DCF? What key assumptions do you make?", 'technical', 'hard'),
                ("Explain the difference between NPV and IRR. When would you use each for capital allocation?", 'technical', 'medium'),
                ("Walk me through a leveraged buyout. What are the key value drivers?", 'technical', 'hard'),
                ("How do rising interest rates flow through the three financial statements?", 'technical', 'medium'),
                ("How do you decide whether a company should pursue M&A vs. organic growth?", 'technical', 'hard'),
                ("What is working capital and why does it matter for a high-growth business?", 'technical', 'medium'),
                ("How would you structure a sensitivity analysis for a major capital investment decision?", 'technical', 'hard'),
            ],
        }

        # Select the right pool based on interview_type
        if itype == 'behavioral':
            chosen = behavioral_pool
        elif itype == 'hr':
            chosen = hr_pool
        elif itype == 'system-design':
            chosen = system_design_pool
        else:
            pool_key = 'software'
            for k in technical_pools:
                if k in field_low:
                    pool_key = k
                    break
            chosen = technical_pools[pool_key]

        _random.shuffle(chosen)

        questions = []
        for text, cat, diff in chosen[:num]:
            qdata = {
                'text': text, 'category': cat, 'field': field, 'level': level, 'company': company,
                'difficulty': diff, 'topic_tags': json.dumps([field_low])
            }
            if question_type == 'mock':
                mc_data = self._generate_fallback_mc_options(text)
                if mc_data:
                    qdata.update(mc_data)
            questions.append(qdata)

        return questions

    # ── STATIC FALLBACK QUESTION BANK WITH REAL MC OPTIONS ───────────────────
    # Each entry: (question_text, [opt_A, opt_B, opt_C, opt_D, opt_E], correct_index)
    # Options are deliberately similar/confusing to test real knowledge.
    _FALLBACK_MC_BANK = {
        'software': [
            (
                "What does the CAP theorem state about distributed systems?",
                [
                    "A system can simultaneously guarantee Consistency, Availability, and Partition tolerance",
                    "A system can guarantee at most two of: Consistency, Availability, Partition tolerance",
                    "A system must sacrifice Availability to achieve Consistency during network partitions",
                    "A system must sacrifice Consistency to achieve Availability during network partitions",
                    "CAP only applies to databases, not distributed services",
                ], 1
            ),
            (
                "What is the difference between a process and a thread?",
                [
                    "A process is lightweight and shares memory with other processes; a thread is heavyweight and isolated",
                    "A process is an independent execution unit with its own memory space; a thread shares memory within a process",
                    "A thread and a process are interchangeable terms for the same concept in modern OSes",
                    "A process runs in user space while a thread always runs in kernel space",
                    "A thread cannot be created without spawning a new process first",
                ], 1
            ),
            (
                "Which HTTP status code means 'resource not found'?",
                [
                    "400 – Bad Request",
                    "401 – Unauthorized",
                    "403 – Forbidden",
                    "404 – Not Found",
                    "500 – Internal Server Error",
                ], 3
            ),
            (
                "What is Big O notation O(log n) typically associated with?",
                [
                    "Linear search through an unsorted array",
                    "Bubble sort on a partially sorted array",
                    "Binary search on a sorted array",
                    "Inserting into a hash table with no collisions",
                    "Depth-first traversal of a binary tree",
                ], 2
            ),
            (
                "In REST APIs, which HTTP method is idempotent AND safe?",
                [
                    "POST – creates a resource, safe to repeat",
                    "PUT – updates a resource, always idempotent",
                    "GET – retrieves data without side effects",
                    "DELETE – removes a resource, safe to repeat",
                    "PATCH – partially updates a resource",
                ], 2
            ),
        ],
        'data': [
            (
                "What is the primary difference between supervised and unsupervised learning?",
                [
                    "Supervised uses unlabeled data; unsupervised uses labeled data",
                    "Supervised learning requires labeled training data; unsupervised finds patterns without labels",
                    "Supervised learning only works for regression, unsupervised only for classification",
                    "Supervised and unsupervised refer to the number of layers in a neural network",
                    "Supervised learning is faster to train because it doesn't need labels",
                ], 1
            ),
            (
                "What does 'overfitting' mean in machine learning?",
                [
                    "The model performs poorly on both training and test data",
                    "The model is too simple to capture the underlying pattern",
                    "The model memorises training data but fails to generalise to new data",
                    "The model trains too slowly due to too many parameters",
                    "The model has a high bias and low variance",
                ], 2
            ),
            (
                "Which metric is most appropriate for an imbalanced classification dataset?",
                [
                    "Accuracy – percentage of correct predictions",
                    "Mean Squared Error – average squared difference",
                    "R-squared – proportion of variance explained",
                    "F1-score – harmonic mean of precision and recall",
                    "Log Loss – penalises confident wrong predictions equally",
                ], 3
            ),
        ],
        'frontend': [
            (
                "What is the difference between '==' and '===' in JavaScript?",
                [
                    "'==' checks value and type; '===' checks value only",
                    "'==' and '===' are identical in modern JavaScript",
                    "'==' performs type coercion before comparing; '===' checks value AND type strictly",
                    "'===' is only used for comparing objects; '==' for primitives",
                    "'==' is used in TypeScript; '===' is used in vanilla JavaScript",
                ], 2
            ),
            (
                "In CSS, what is the difference between 'display: none' and 'visibility: hidden'?",
                [
                    "Both remove the element from the document flow",
                    "'display: none' hides the element but preserves its space; 'visibility: hidden' removes it from flow",
                    "'display: none' removes the element from the document flow; 'visibility: hidden' hides it but preserves its space",
                    "They are identical in behaviour but differ in browser support",
                    "'visibility: hidden' removes the element from DOM entirely",
                ], 2
            ),
            (
                "What does 'virtual DOM' mean in React?",
                [
                    "A separate server-side copy of the DOM used for server-side rendering",
                    "A lightweight in-memory representation of the real DOM used to batch and optimise updates",
                    "A browser extension that speeds up DOM manipulation",
                    "The DOM structure stored in a database for persistence across sessions",
                    "A shadow copy of the DOM created only during event handling",
                ], 1
            ),
        ],
        'backend': [
            (
                "What is the N+1 query problem in database access?",
                [
                    "When a query returns N+1 rows instead of the expected N rows",
                    "When you execute 1 query to get N records, then N additional queries to fetch related data",
                    "When a database table has more than N+1 columns causing slow reads",
                    "When N+1 simultaneous connections exceed the database connection pool limit",
                    "When an index is missing on N+1 foreign key columns",
                ], 1
            ),
            (
                "What is the purpose of database indexing?",
                [
                    "To compress data and reduce storage space",
                    "To enforce referential integrity between tables",
                    "To speed up data retrieval at the cost of additional storage and write overhead",
                    "To replicate data across multiple database servers automatically",
                    "To encrypt sensitive columns for security compliance",
                ], 2
            ),
        ],
        'default': [
            (
                "What does SOLID stand for in software engineering?",
                [
                    "Scalable, Open, Lightweight, Integrated, Distributed",
                    "Single responsibility, Open-closed, Liskov substitution, Interface segregation, Dependency inversion",
                    "Single source, Object-oriented, Library, Interface, Design",
                    "Structured, Object, Linked, Independent, Dynamic",
                    "Simple, Open, Layered, Iterative, Documented",
                ], 1
            ),
            (
                "What is the difference between SQL and NoSQL databases?",
                [
                    "SQL databases are newer and faster; NoSQL databases are legacy systems",
                    "SQL stores data only as key-value pairs; NoSQL uses tables with rows and columns",
                    "SQL uses structured tables with a fixed schema; NoSQL is flexible and schema-less, suited for unstructured data",
                    "NoSQL databases always perform better than SQL databases for all use cases",
                    "SQL and NoSQL refer to programming languages, not database types",
                ], 2
            ),
            (
                "What is the purpose of a load balancer?",
                [
                    "To compress and cache static assets like images and CSS files",
                    "To encrypt traffic between clients and servers using SSL/TLS",
                    "To distribute incoming network traffic across multiple servers to ensure reliability and performance",
                    "To monitor server CPU and memory usage and alert on anomalies",
                    "To store session state so servers can remain stateless",
                ], 2
            ),
        ],
    }

    def _generate_fallback_mc_options(self, question, difficulty=None):
        """
        Pick a question from the fallback bank and return its options.
        Called when Mistral is offline — options are real, confusing, and
        semantically close to the correct answer (not placeholder text).
        Returns dict with is_multiple_choice, options, correct_answers, multiple_allowed.
        """
        import random as _rnd
        try:
            # Pick the bank closest to the question topic by keyword matching
            q_lower = question.lower()
            bank_key = 'default'
            for key in ('frontend', 'backend', 'data', 'software'):
                keywords = {
                    'frontend': ['html', 'css', 'javascript', 'react', 'vue', 'dom', 'ui'],
                    'backend':  ['database', 'sql', 'api', 'server', 'query', 'index', 'rest'],
                    'data':     ['machine learning', 'model', 'overfitting', 'dataset', 'training', 'feature'],
                    'software': ['thread', 'process', 'algorithm', 'o(', 'cap', 'distributed', 'big o'],
                }
                if any(kw in q_lower for kw in keywords.get(key, [])):
                    bank_key = key
                    break

            bank = self._FALLBACK_MC_BANK.get(bank_key, self._FALLBACK_MC_BANK['default'])
            q_text, options, correct_idx = _rnd.choice(bank)

            # Ensure exactly 4 options (A-D): keep correct + pick 3 distractors
            if len(options) > 4:
                correct_opt = options[correct_idx]
                distractors = [o for i, o in enumerate(options) if i != correct_idx]
                _rnd.shuffle(distractors)
                final_opts = distractors[:3] + [correct_opt]
                _rnd.shuffle(final_opts)
                new_correct = final_opts.index(correct_opt)
                options = final_opts
                correct_idx = new_correct

            # Shuffle options (keeping track of correct answer)
            indexed = list(enumerate(options))
            _rnd.shuffle(indexed)
            shuffled_options = [o for _, o in indexed]
            new_correct = next(i for i, (orig_i, _) in enumerate(indexed) if orig_i == correct_idx)

            return {
                'is_multiple_choice': True,
                'options':            shuffled_options,
                'correct_answers':    [new_correct],
                'multiple_allowed':   False,
            }
        except Exception as e:
            app.logger.debug(f"[Fallback MC] generation failed: {str(e)[:80]}")
            return None

    def _fallback_analysis(self, question, answer):
        """Heuristic analysis when Mistral is offline. Uses word count, keyword matching,
        and structural analysis for more accurate scoring."""
        wc = len((answer or '').split())
        q_lower = (question or '').lower()
        a_lower = (answer or '').lower()
        
        # Base score from word count (more nuanced tiers)
        if wc < 5:
            base_score = 1.0
        elif wc < 15:
            base_score = 2.5
        elif wc < 30:
            base_score = 3.5
        elif wc < 60:
            base_score = 5.0
        elif wc < 120:
            base_score = 6.0
        elif wc < 250:
            base_score = 6.5
        else:
            base_score = 7.0
        
        # Keyword relevance: check if answer contains words from the question
        q_words = set(w for w in q_lower.split() if len(w) > 3)
        a_words = set(w for w in a_lower.split() if len(w) > 3)
        overlap = len(q_words & a_words)
        if overlap >= 3:
            base_score += 0.5
        elif overlap >= 1:
            base_score += 0.2
        
        # Structure bonus: sentences, paragraphs
        sentences = len([s for s in (answer or '').split('.') if s.strip()])
        if sentences >= 3:
            base_score += 0.3
        
        # Check for technical indicators (code, examples)
        if any(kw in a_lower for kw in ['for example', 'such as', 'instance', 'specifically']):
            base_score += 0.3
        if any(kw in a_lower for kw in ['def ', 'function', 'class ', 'return ', 'import ']):
            base_score += 0.3
        
        score = min(10.0, max(1.0, round(base_score, 1)))
        
        # Derive dimension scores from base (not all equal)
        depth = max(1.0, round(score - 0.5 if wc < 50 else score, 1))
        clarity = max(1.0, round(score - 0.3 if sentences < 2 else score + 0.2, 1))
        relevance = max(1.0, round(score + 0.3 if overlap >= 2 else score - 0.5, 1))
        
        return {
            'score': score, 'technical_accuracy': score,
            'depth_score': min(10.0, depth),
            'clarity_score': min(10.0, clarity),
            'relevance_score': min(10.0, relevance),
            'communication_score': max(1.0, round(score - 0.2, 1)),
            'confidence_score': max(1.0, round(score - 0.5, 1)),
            'strengths': [
                'Provided a response to the question',
                f'{wc} words written' + (' with good detail' if wc > 80 else ''),
                'Answer addresses the topic' if overlap >= 1 else 'Answer submitted',
            ],
            'weaknesses': [
                'AI offline — full scoring unavailable. Start LM Studio for precise AI feedback.',
                'Consider adding more specific examples and technical details' if wc < 100 else 'Review for technical accuracy',
            ],
            'improvement_plan': [
                'Start LM Studio for live AI scoring',
                'Practice answering in 150-300 words with concrete examples',
                'Review core concepts for this topic',
            ],
            'feedback': f"[AI Offline] Heuristic score: {score}/10 ({wc} words). Start LM Studio for full AI-powered feedback with 6-dimension scoring.",
            'model': 'fallback-heuristic',
        }


# Initialise AI agent
mistral_agent = MistralAIAgent()


# ── Runtime DB compatibility fixes (adds missing columns / normalises datetimes) ──
def ensure_db_schema_compatibility():
    """At import/run time ensure the SQLite DB schema contains expected columns
    and that stored datetime strings are in ISO format. This makes the app
    tolerant of older databases that lack newly-added columns.
    
    Handles all tables: interviews, answers, questions, users, feedback.
    Adds missing columns for question_type, answer_type, selected_options, etc.
    Normalizes datetime strings to ISO format (space → 'T').
    """
    try:
        with app.app_context():
            inspector = db.inspect(db.engine)
            table_names = inspector.get_table_names()
            
            # Create all tables if DB is empty
            if 'interviews' not in table_names:
                app.logger.info('[Schema] Tables missing, creating all from models')
                db.create_all()
                return

            # Helper to add column if missing
            def _add_column_safe(table, col_name, col_type, default_val=None):
                try:
                    existing_cols = [c['name'] for c in inspector.get_columns(table)]
                    if col_name not in existing_cols:
                        if default_val:
                            sql = text(f"ALTER TABLE {table} ADD COLUMN {col_name} {col_type} DEFAULT '{default_val}'")
                        else:
                            sql = text(f"ALTER TABLE {table} ADD COLUMN {col_name} {col_type}")
                        db.session.execute(sql)
                        db.session.commit()
                        app.logger.info(f'[Schema] Added column {table}.{col_name}')
                except Exception as e:
                    app.logger.debug(f"[Schema] Could not add {table}.{col_name}: {str(e)[:80]}")

            # ── INTERVIEWS TABLE ──────────────────────────────────────────────────────
            _add_column_safe('interviews', 'question_type', 'TEXT', 'mock')
            _add_column_safe('interviews', 'answer_type', 'TEXT', 'mock')
            _add_column_safe('interviews', 'mode', 'TEXT', 'text')
            _add_column_safe('interviews', 'ai_model_used', 'TEXT')
            
            # ── ANSWERS TABLE ──────────────────────────────────────────────────────────
            _add_column_safe('answers', 'selected_options', 'TEXT')
            _add_column_safe('answers', 'word_count', 'INTEGER', '0')
            _add_column_safe('answers', 'score', 'REAL')
            _add_column_safe('answers', 'technical_accuracy', 'REAL')
            _add_column_safe('answers', 'depth_score', 'REAL')
            _add_column_safe('answers', 'clarity_score', 'REAL')
            _add_column_safe('answers', 'relevance_score', 'REAL')
            _add_column_safe('answers', 'communication_score', 'REAL')
            _add_column_safe('answers', 'confidence_score', 'REAL')
            _add_column_safe('answers', 'time_spent_seconds', 'INTEGER', '0')
            _add_column_safe('answers', 'submitted_at', 'DATETIME')
            
            # ── QUESTIONS TABLE ────────────────────────────────────────────────────────
            _add_column_safe('questions', 'is_multiple_choice', 'BOOLEAN', '0')
            _add_column_safe('questions', 'options', 'TEXT')
            _add_column_safe('questions', 'correct_answers', 'TEXT')
            _add_column_safe('questions', 'multiple_allowed', 'BOOLEAN', '0')
            _add_column_safe('questions', 'question_number', 'INTEGER', '1')
            _add_column_safe('questions', 'source', 'TEXT', 'ai_generated')
            _add_column_safe('questions', 'topic_tags', 'TEXT')
            _add_column_safe('questions', 'difficulty', 'TEXT')
            _add_column_safe('questions', 'hint', 'TEXT')
            _add_column_safe('questions', 'expected_points', 'TEXT')
            _add_column_safe('questions', 'time_limit_secs', 'INTEGER', '300')
            
            # ── QUESTION_BANK TABLE ────────────────────────────────────────────────────
            _add_column_safe('question_bank', 'question_type', 'TEXT', 'mock')  # NEW
            _add_column_safe('question_bank', 'answer_type', 'TEXT', 'mock')    # NEW
            
            # ── FEEDBACK TABLE ────────────────────────────────────────────────────────
            _add_column_safe('feedback', 'score', 'REAL')
            _add_column_safe('feedback', 'strengths', 'TEXT')
            _add_column_safe('feedback', 'improvements', 'TEXT')
            _add_column_safe('feedback', 'detailed_feedback', 'TEXT')
            _add_column_safe('feedback', 'improvement_plan', 'TEXT')
            _add_column_safe('feedback', 'model_used', 'TEXT')
            _add_column_safe('feedback', 'generated_at', 'DATETIME')
            
            # ── USERS TABLE ────────────────────────────────────────────────────────────
            _add_column_safe('users', 'created_at', 'DATETIME')
            _add_column_safe('users', 'last_login', 'DATETIME')
            _add_column_safe('users', 'failed_login_attempts', 'INTEGER', '0')
            _add_column_safe('users', 'account_locked_until', 'DATETIME')
            _add_column_safe('users', 'last_failed_login', 'DATETIME')
            _add_column_safe('users', 'password_changed_at', 'DATETIME')

            # ── TOKEN_BLOCKLIST TABLE ──────────────────────────────────────────────────
            if 'token_blocklist' not in table_names:
                try:
                    db.session.execute(text(
                        "CREATE TABLE IF NOT EXISTS token_blocklist ("
                        "id INTEGER PRIMARY KEY AUTOINCREMENT, "
                        "jti VARCHAR(36) NOT NULL UNIQUE, "
                        "token_type VARCHAR(10) NOT NULL, "
                        "user_id INTEGER, "
                        "created_at DATETIME, "
                        "expires_at DATETIME, "
                        "FOREIGN KEY(user_id) REFERENCES users(id))"
                    ))
                    db.session.execute(text(
                        "CREATE INDEX IF NOT EXISTS ix_token_blocklist_jti ON token_blocklist(jti)"
                    ))
                    db.session.commit()
                    app.logger.info('[Schema] Created token_blocklist table')
                except Exception as e:
                    app.logger.debug(f"[Schema] token_blocklist creation note: {str(e)[:80]}")

            # Normalise datetime strings (replace space with 'T') in all datetime columns
            def _normalise_table_datetime(table, cols_to_fix):
                try:
                    existing_cols = [c['name'] for c in inspector.get_columns(table)]
                    for col in cols_to_fix:
                        if col in existing_cols:
                            sql = text(f"UPDATE {table} SET {col} = replace({col}, ' ', 'T') WHERE {col} LIKE '% %' AND {col} NOT LIKE '%T%' AND {col} IS NOT NULL")
                            db.session.execute(sql)
                    db.session.commit()
                except Exception as e:
                    app.logger.debug(f"[Schema] Datetime normalisation warning for {table}: {str(e)[:80]}")

            # Normalize all datetime columns
            _normalise_table_datetime('interviews', ['started_at', 'completed_at'])
            _normalise_table_datetime('users', ['created_at', 'last_login'])
            _normalise_table_datetime('answers', ['submitted_at'])
            _normalise_table_datetime('feedback', ['generated_at'])

            app.logger.info('[Schema] Database schema compatibility check completed successfully')

    except Exception as e:
        app.logger.error(f"[Schema] ensure_db_schema_compatibility error: {str(e)[:200]}")


# Run compatibility check at import time so endpoints won't error on older DBs
ensure_db_schema_compatibility()


# ==============================================================================
#  HELPER FUNCTIONS — DATA INTEGRITY & STATS RECALCULATION
# ==============================================================================

def recalculate_user_stats(user_id):
    """
    Recalculate and sync all user aggregate statistics from actual interview data.
    Ensures database integrity and corrects any stale or missing stats.
    
    CRITICAL: Must be called after any interview status change or completion.
    """
    try:
        user = db.session.get(User, user_id)
        if not user:
            return False
        
        # Get ALL completed interviews for this user
        try:
            completed_interviews = Interview.query.filter_by(
                user_id=user_id, 
                status='completed'
            ).all()
        except Exception as e:
            app.logger.warning(f"[Stats] Could not query interviews: {str(e)[:80]}, using empty list")
            completed_interviews = []
        
        # Count completed interviews
        total_completed = len(completed_interviews)
        
        # Calculate scores from completed interviews
        scores = [i.overall_score for i in completed_interviews 
                  if i.overall_score is not None]
        best_score = round(max(scores), 2) if scores else 0.0
        avg_score = round(sum(scores) / len(scores), 2) if scores else 0.0
        
        # Calculate total practice time from all completed interviews
        total_duration = sum(i.duration_seconds or 0 for i in completed_interviews)
        
        # Count total questions answered from all completed interviews
        total_questions = 0
        for interview in completed_interviews:
            try:
                answers = Answer.query.filter_by(interview_id=interview.id).all()
                total_questions += len(answers)
            except Exception as e:
                app.logger.debug(f"[Stats] Could not query answers for interview {interview.id}: {str(e)[:80]}")
                continue
        
        # Get last activity date
        try:
            latest_interview = Interview.query.filter_by(user_id=user_id).order_by(
                Interview.completed_at.desc()
            ).first()
        except Exception as e:
            app.logger.debug(f"[Stats] Could not get latest interview: {str(e)[:80]}")
            latest_interview = None
        
        # UPDATE user stats atomically
        user.total_interviews = total_completed
        user.average_score = avg_score
        user.best_score = best_score
        user.total_practice_time = total_duration
        user.total_questions_answered = total_questions
        if latest_interview and latest_interview.completed_at:
            try:
                user.last_activity_date = latest_interview.completed_at.date()
            except:
                pass
        
        # Commit changes
        db.session.commit()
        
        app.logger.info(
            f"[Stats] User {user_id} synced: "
            f"interviews={total_completed}, avg_score={avg_score}, "
            f"best={best_score}, time={total_duration}s, questions={total_questions}"
        )
        return True
        
    except Exception as e:
        app.logger.error(f"[Stats] Error recalculating stats for user {user_id}: {str(e)[:150]}")
        db.session.rollback()
        return False


# ==============================================================================
#  API ENDPOINTS
# ==============================================================================

@app.route('/api/health', methods=['GET'])
def health_check():
    """
    Comprehensive health check endpoint.
    Returns system status including database, Mistral AI, and troubleshooting info.
    """
    mistral_status = {
        'available': mistral_agent.is_available,
        'connection_error': mistral_agent.connection_error,
        'last_error': mistral_agent.last_error_msg,
        'configured_url': mistral_agent.base_url,
        'configured_model': mistral_agent.model_name,
    }
    
    if not mistral_agent.is_available:
        mistral_status['troubleshooting'] = {
            'status': 'OFFLINE - Using fallback mode',
            'issue': mistral_agent.last_error_msg or 'Unknown connection error',
            'what_to_do': [
                '1. Verify LM Studio is installed',
                '2. Open LM Studio application',
                '3. Load a Mistral model (mistral-7b-instruct-v0.2 recommended)',
                '4. Start the local server (check the "Start Server" button)',
                '5. Verify server is running on http://127.0.0.1:1234/v1',
                '6. Application will auto-reconnect within 5-120 seconds',
            ],
            'docs': 'https://lmstudio.ai (download and setup instructions)',
            'fallback_active': True,
            'fallback_features': [
                '[OK] Mock interviews with pre-loaded questions',
                '[OK] Multiple-choice options (generated locally)',
                '[OK] Basic answer evaluation (word count + heuristics)',
                '[REQUIRES AI] AI-powered answer analysis (requires Mistral)',
            ],
        }
    
    return jsonify({
        'status': 'healthy',
        'database': 'connected',
        'mistral': mistral_status,
        'version': '3.0.0-enterprise',
        'timestamp': datetime.now().isoformat()
    }), 200


@app.route('/api/ai/ping', methods=['GET'])
def ai_ping():
    """
    Lightweight AI status endpoint — no JWT required.
    Called every 15s by the frontend health monitor.
    Returns current Mistral online/offline state instantly (no AI call made).
    """
    # If offline, try to reconnect (non-blocking check against backoff timer)
    if not mistral_agent.is_available:
        mistral_agent._ensure_available()

    return jsonify({
        'online':  mistral_agent.is_available,
        'model':   mistral_agent.model_name,
        'url':     mistral_agent.base_url,
        'error':   mistral_agent.last_error_msg if not mistral_agent.is_available else None,
    }), 200


# ── AUTH ────────────────────────────────────────────────────────────────────────

@app.route('/api/auth/register', methods=['POST'])
@_rate_limit('5 per minute')
def register():
    try:
        data = request.get_json(force=True, silent=True) or {}
        email = (data.get('email') or '').strip().lower()
        password = data.get('password', '')

        if not email or not password:
            return jsonify({'error': 'Email and password required'}), 400

        # Validate password strength (same rules everywhere)
        pw_err = validate_password_strength(password)
        if pw_err:
            return jsonify({'error': pw_err}), 400

        if User.query.filter_by(email=email).first():
            return jsonify({'error': 'Email already registered'}), 400

        user = User(
            email=email,
            first_name=data.get('first_name') or data.get('firstName', ''),
            last_name=data.get('last_name')  or data.get('lastName', ''),
            password_changed_at=datetime.utcnow(),
        )
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        app.logger.info(f"[Auth] Registered: {user.email} (ID {user.id})")
        access_token  = create_access_token(identity=str(user.id))
        refresh_token = create_refresh_token(identity=str(user.id))
        return jsonify({
            'message': 'Registration successful',
            'access_token': access_token,
            'refresh_token': refresh_token,
            'user': user.to_dict()
        }), 201
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"[Auth] Register error: {e}\n{traceback.format_exc()}")
        return jsonify({'error': str(e)}), 500


# ── PASSWORD RESET FLOW ─────────────────────────────────────────────────────────
# This implements a professional forgot password system:
# 1. User requests password reset via email
# 2. System generates secure token (valid 1 hour)
# 3. Token returned to frontend (in real production, would send via email)
# 4. User enters new password with the token
# 5. System validates token and updates password in database

@app.route('/api/auth/forgot-password', methods=['POST'])
def forgot_password():
    """
    Request a password reset token for the given email.
    Token is valid for 1 hour.
    """
    try:
        data = request.get_json(force=True, silent=True) or {}
        email = data.get('email', '').strip().lower()
        
        if not email:
            return jsonify({'error': 'Email is required'}), 400
        
        # Find user by email
        user = User.query.filter_by(email=email).first()
        
        if not user:
            # For security: don't reveal if email exists or not
            # But log it for debugging
            app.logger.warning(f"[Auth] [SECURITY] Forgot password requested for non-existent email: {email}")
            return jsonify({
                'message': 'If an account exists with this email, a reset link will be sent'
            }), 200
        
        # Generate reset token for this user
        reset_token = user.generate_password_reset_token()
        db.session.commit()
        
        app.logger.info(f"[Auth] [SECURITY] Password reset token generated for: {user.email}")
        
        # In production, send token via email only — never expose in API response
        # For local dev/testing, token is logged (check logs/ai_coach.log)
        if app.debug:
            app.logger.info(f"[Auth] [DEV-ONLY] Reset token for {user.email}: {reset_token}")
        
        return jsonify({
            'message': 'Password reset instructions sent to your email',
            'tokenExpiry': user.password_reset_token_expiry.isoformat() if user.password_reset_token_expiry else None
        }), 200
        
    except Exception as e:
        app.logger.error(f"[Auth] Forgot password error: {e}\n{traceback.format_exc()}")
        return jsonify({'error': 'An error occurred. Please try again.'}), 500


@app.route('/api/auth/verify-reset-token', methods=['POST'])
def verify_reset_token():
    """
    Verify if a password reset token is valid and not expired.
    """
    try:
        data = request.get_json(force=True, silent=True) or {}
        email = data.get('email', '').strip().lower()
        token = data.get('token', '').strip()
        
        if not email or not token:
            return jsonify({'error': 'Email and token are required'}), 400
        
        user = User.query.filter_by(email=email).first()
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Verify token validity and expiry
        if not user.verify_password_reset_token(token):
            return jsonify({'error': 'Invalid or expired password reset token'}), 401
        
        app.logger.info(f"[Auth] Password reset token verified for: {user.email}")
        return jsonify({'message': 'Token is valid', 'valid': True}), 200
        
    except Exception as e:
        app.logger.error(f"[Auth] Verify reset token error: {e}")
        return jsonify({'error': 'An error occurred'}), 500


@app.route('/api/auth/reset-password', methods=['POST'])
def reset_password():
    """
    Reset the user's password using a valid reset token.
    Updates password_hash in database with 100% accuracy.
    This is a critical operation with strong validation.
    """
    try:
        data = request.get_json(force=True, silent=True) or {}
        email = data.get('email', '').strip().lower()
        token = data.get('token', '').strip()
        new_password = data.get('new_password', '')
        confirm_password = data.get('confirm_password', '')
        
        # ── VALIDATION ──────────────────────────────────────────────────────
        if not all([email, token, new_password, confirm_password]):
            return jsonify({'error': 'All fields are required'}), 400
        
        # Find user
        user = User.query.filter_by(email=email).first()
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Verify reset token is valid and not expired
        if not user.verify_password_reset_token(token):
            return jsonify({'error': 'Invalid or expired password reset token'}), 401
        
        # Validate password requirements
        if len(new_password) < 8:
            return jsonify({'error': 'Password must be at least 8 characters'}), 400
        
        if new_password != confirm_password:
            return jsonify({'error': 'Passwords do not match'}), 400
        
        # Check password strength (at least 1 uppercase, 1 lowercase, 1 number, 1 special char)
        if not any(c.isupper() for c in new_password):
            return jsonify({'error': 'Password must contain at least one uppercase letter'}), 400
        
        if not any(c.islower() for c in new_password):
            return jsonify({'error': 'Password must contain at least one lowercase letter'}), 400
        
        if not any(c.isdigit() for c in new_password):
            return jsonify({'error': 'Password must contain at least one number'}), 400
        
        # Check that new password is different from old password
        if user.check_password(new_password):
            return jsonify({'error': 'New password must be different from current password'}), 400
        
        # ── SET NEW PASSWORD ────────────────────────────────────────────────
        # This is where the actual password update happens
        # Using werkzeug.security.generate_password_hash for secure hashing
        user.set_password(new_password)
        user.clear_password_reset_token()  # Clear the token after use
        
        # ── COMMIT TO DATABASE ──────────────────────────────────────────────
        db.session.commit()
        
        # ── VERIFICATION ────────────────────────────────────────────────────
        # Immediately verify the password was saved correctly
        db.session.refresh(user)  # Refresh from database
        if not user.check_password(new_password):
            # This should never happen, but if it does, we catch it
            db.session.rollback()
            app.logger.critical(f"[CRITICAL] Password verification failed after reset for user: {user.email}")
            return jsonify({'error': 'Password update verification failed. Please try again.'}), 500
        
        app.logger.info(f"[Auth] Password successfully reset for: {user.email}")
        
        return jsonify({
            'message': 'Password has been reset successfully',
            'success': True
        }), 200
        
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"[Auth] Reset password error: {e}\n{traceback.format_exc()}")
        return jsonify({'error': 'An error occurred while resetting password'}), 500


@app.route('/api/auth/login', methods=['POST'])
@_rate_limit('10 per minute')
def login():
    try:
        data = request.get_json(force=True, silent=True) or {}
        email = (data.get('email') or '').strip().lower()
        password = data.get('password', '')
        if not email or not password:
            return jsonify({'error': 'Email and password required'}), 400

        user = User.query.filter_by(email=email).first()

        # ── Account lockout check ───────────────────────────────────────────
        if user and user.account_locked_until and datetime.utcnow() < user.account_locked_until:
            remaining = int((user.account_locked_until - datetime.utcnow()).total_seconds() / 60) + 1
            app.logger.warning(f"[Auth] Locked-out login attempt for {email}")
            return jsonify({
                'error': f'Account temporarily locked. Try again in {remaining} minute(s).',
                'locked': True,
                'retry_after': remaining
            }), 429

        # ── Credential check ────────────────────────────────────────────────
        if not user or not user.check_password(password):
            # Record failure
            if user:
                user.failed_login_attempts = (user.failed_login_attempts or 0) + 1
                user.last_failed_login = datetime.utcnow()
                if user.failed_login_attempts >= MAX_FAILED_LOGINS:
                    user.account_locked_until = datetime.utcnow() + LOCKOUT_DURATION
                    db.session.commit()
                    app.logger.warning(f"[Auth] Account LOCKED after {MAX_FAILED_LOGINS} failures: {email}")
                    return jsonify({
                        'error': f'Too many failed attempts. Account locked for {int(LOCKOUT_DURATION.total_seconds()//60)} minutes.',
                        'locked': True
                    }), 429
                db.session.commit()
            return jsonify({'error': 'Invalid credentials'}), 401

        if not user.is_active:
            return jsonify({'error': 'Account disabled. Contact support.'}), 403

        # ── Success — reset counters ────────────────────────────────────────
        user.failed_login_attempts = 0
        user.account_locked_until  = None
        user.last_login = datetime.utcnow()
        db.session.commit()

        app.logger.info(f"[Auth] Login: {user.email} (ID {user.id})")
        access_token  = create_access_token(identity=str(user.id))
        refresh_token = create_refresh_token(identity=str(user.id))
        return jsonify({
            'message': 'Login successful',
            'access_token': access_token,
            'refresh_token': refresh_token,
            'user': user.to_dict()
        }), 200
    except Exception as e:
        app.logger.error(f"[Auth] Login error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/auth/me', methods=['GET'])
@jwt_required()
def get_me():
    try:
        user = db.session.get(User, int(get_jwt_identity()))
        if not user: return jsonify({'error': 'User not found'}), 404
        return jsonify(user.to_dict()), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/auth/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh_token():
    """Issue a new access token using a valid refresh token."""
    try:
        user_id = get_jwt_identity()
        user = db.session.get(User, int(user_id))
        if not user or not user.is_active:
            return jsonify({'error': 'User not found or disabled'}), 401
        new_access = create_access_token(identity=user_id)
        return jsonify({'access_token': new_access}), 200
    except Exception as e:
        app.logger.error(f"[Auth] Refresh error: {e}")
        return jsonify({'error': 'Token refresh failed'}), 500


@app.route('/api/auth/logout', methods=['POST'])
@jwt_required(verify_type=False)   # accepts both access and refresh tokens
def logout():
    """Revoke the current token by adding its jti to the blocklist."""
    try:
        jwt_data = get_jwt()
        jti        = jwt_data['jti']
        token_type = jwt_data['type']
        exp_ts     = jwt_data['exp']
        user_id    = get_jwt_identity()

        blocked = TokenBlocklist(
            jti=jti,
            token_type=token_type,
            user_id=int(user_id) if user_id else None,
            expires_at=datetime.utcfromtimestamp(exp_ts),
        )
        db.session.add(blocked)
        db.session.commit()
        app.logger.info(f"[Auth] Token revoked ({token_type}) for user {user_id}")
        return jsonify({'message': 'Successfully logged out'}), 200
    except Exception as e:
        app.logger.error(f"[Auth] Logout error: {e}")
        return jsonify({'error': 'Logout failed'}), 500


# ── USER PROFILE ────────────────────────────────────────────────────────────────

@app.route('/api/user/profile', methods=['GET'])
@jwt_required()
def get_profile():
    try:
        user = db.session.get(User, int(get_jwt_identity()))
        if not user: return jsonify({'error': 'User not found'}), 404
        profile = user.to_dict()
        profile['resume_summary']   = user.resume_summary
        profile['linkedin_url']     = user.linkedin_url
        profile['github_url']       = user.github_url
        profile['headline']         = user.headline
        profile['education']        = json.loads(user.education or '[]')
        profile['target_roles']     = json.loads(user.target_roles or '[]')
        profile['total_questions_answered'] = user.total_questions_answered
        return jsonify(profile), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/user/profile', methods=['PUT'])
@jwt_required()
def update_profile():
    try:
        user = db.session.get(User, int(get_jwt_identity()))
        if not user: return jsonify({'error': 'User not found'}), 404
        data = request.get_json(force=True, silent=True) or {}

        for field_name in ['first_name','last_name','phone','linkedin_url','github_url',
                           'headline','resume_summary','current_role']:
            if field_name in data:
                setattr(user, field_name, data[field_name])
        if 'experience_years' in data:
            user.experience_years = int(data['experience_years'])
        if 'skills' in data:
            user.skills = json.dumps(data['skills'] if isinstance(data['skills'], list) else [data['skills']])
        if 'dream_companies' in data:
            user.dream_companies = json.dumps(data['dream_companies'] if isinstance(data['dream_companies'], list) else [])
        if 'target_roles' in data:
            user.target_roles = json.dumps(data['target_roles'] if isinstance(data['target_roles'], list) else [])
        if 'education' in data:
            user.education = json.dumps(data['education'] if isinstance(data['education'], list) else [])

        db.session.commit()
        return jsonify({'message': 'Profile updated', 'user': user.to_dict()}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@app.route('/api/user/change-password', methods=['POST'])
@jwt_required()
def change_password():
    try:
        user = db.session.get(User, int(get_jwt_identity()))
        if not user: return jsonify({'error': 'User not found'}), 404
        
        data = request.get_json(force=True, silent=True) or {}
        current_password = data.get('current_password', '')
        new_password = data.get('new_password', '')
        confirm_password = data.get('confirm_password', '')
        
        if not current_password or not new_password:
            return jsonify({'error': 'Current password and new password are required'}), 400
        
        if new_password != confirm_password:
            return jsonify({'error': 'New passwords do not match'}), 400
        
        # Use shared password strength validator (consistent everywhere)
        pw_err = validate_password_strength(new_password)
        if pw_err:
            return jsonify({'error': pw_err}), 400
        
        if not user.check_password(current_password):
            return jsonify({'error': 'Current password is incorrect'}), 401
        
        user.set_password(new_password)
        user.password_changed_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({'message': 'Password changed successfully'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@app.route('/api/user/change-email', methods=['POST'])
@jwt_required()
def change_email():
    try:
        user = db.session.get(User, int(get_jwt_identity()))
        if not user: return jsonify({'error': 'User not found'}), 404
        
        data = request.get_json(force=True, silent=True) or {}
        new_email = data.get('email', '').strip().lower()
        password = data.get('password', '')
        
        if not new_email or '@' not in new_email:
            return jsonify({'error': 'Valid email is required'}), 400
        
        if not password or not user.check_password(password):
            return jsonify({'error': 'Password is required to change email'}), 401
        
        # Check if email already exists
        existing = User.query.filter_by(email=new_email).first()
        if existing and existing.id != user.id:
            return jsonify({'error': 'Email already in use'}), 400
        
        user.email = new_email
        db.session.commit()
        
        return jsonify({'message': 'Email changed successfully', 'email': new_email}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


# ── QUESTION BANK / LIBRARY ──────────────────────────────────────────────────

@app.route('/api/questions/library', methods=['GET'])
@jwt_required()
def get_question_library():
    try:
        category = request.args.get('category', '')
        field = request.args.get('field', '')
        difficulty = request.args.get('difficulty', '')
        search = request.args.get('search', '')
        
        query = QuestionBank.query
        
        if category:
            query = query.filter(QuestionBank.category.ilike(f'%{category}%'))
        if field:
            query = query.filter(QuestionBank.field.ilike(f'%{field}%'))
        if difficulty:
            query = query.filter(QuestionBank.difficulty.ilike(f'%{difficulty}%'))
        if search:
            query = query.filter(QuestionBank.text.ilike(f'%{search}%'))
        
        questions = query.order_by(QuestionBank.times_used.desc()).limit(50).all()
        
        return jsonify({
            'questions': [q.to_dict() for q in questions],
            'total': len(questions)
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ── ANALYTICS ──────────────────────────────────────────────────────────────────

@app.route('/api/analytics', methods=['GET'])
@jwt_required()
def get_analytics():
    """
    REAL-TIME Analytics Endpoint
    Returns comprehensive analytics with all details refreshed from database
    """
    try:
        user_id = int(get_jwt_identity())
        user = db.session.get(User, user_id)
        if not user: return jsonify({'error': 'User not found'}), 404
        
        # REAL-TIME: Refresh stats from database
        recalculate_user_stats(user_id)
        db.session.refresh(user)
        
        # Get all completed interviews (real-time from DB)
        interviews = Interview.query.filter_by(
            user_id=user_id, status='completed'
        ).order_by(Interview.completed_at.desc()).all()
        
        total_interviews = len(interviews)
        
        if not interviews:
            return jsonify({
                'total_interviews': 0,
                'average_score': 0,
                'best_score': 0,
                'total_time_spent': 0,
                'score_distribution': {'A': 0, 'B': 0, 'C': 0, 'D': 0, 'F': 0},
                'field_breakdown': [],
                'level_breakdown': [],
                'recent_trend': [],
                'all_interviews': [],
                'timestamp': datetime.utcnow().isoformat(),
            }), 200
        
        score_dist = {'A': 0, 'B': 0, 'C': 0, 'D': 0, 'F': 0}
        total_score = 0
        total_time = 0
        field_scores = {}
        level_scores = {}
        all_interviews_data = []
        
        for i in interviews:
            # Count questions answered for this interview
            answers_count = len(Answer.query.filter_by(interview_id=i.id).all())
            
            interview_data = {
                'id': i.id,
                'uuid': i.uuid,
                'field': i.field,
                'level': i.level,
                'company': i.company,
                'interview_type': i.interview_type,
                'overall_score': round(i.overall_score, 2) if i.overall_score else 0,
                'performance_grade': i.performance_grade,
                'duration_seconds': i.duration_seconds or 0,
                'questions_answered': answers_count,
                'questions_total': i.questions_total or 5,
                'technical_score': round(i.technical_score, 2) if i.technical_score else None,
                'communication_score': round(i.communication_score, 2) if i.communication_score else None,
                'completed_at': i.completed_at.isoformat() if i.completed_at else None,
            }
            all_interviews_data.append(interview_data)
            
            if i.overall_score:
                total_score += i.overall_score
                grade = i.performance_grade or 'F'
                score_dist[grade[0]] = score_dist.get(grade[0], 0) + 1
            
            if i.duration_seconds:
                total_time += i.duration_seconds
            
            if i.field:
                if i.field not in field_scores:
                    field_scores[i.field] = {'count': 0, 'total_score': 0}
                field_scores[i.field]['count'] += 1
                if i.overall_score:
                    field_scores[i.field]['total_score'] += i.overall_score
            
            if i.level:
                if i.level not in level_scores:
                    level_scores[i.level] = {'count': 0, 'total_score': 0}
                level_scores[i.level]['count'] += 1
                if i.overall_score:
                    level_scores[i.level]['total_score'] += i.overall_score
        
        field_breakdown = []
        for field, data in field_scores.items():
            avg = data['total_score'] / data['count'] if data['count'] > 0 else 0
            field_breakdown.append({
                'field': field,
                'count': data['count'],
                'average_score': round(avg, 2)
            })
        
        level_breakdown = []
        for level, data in level_scores.items():
            avg = data['total_score'] / data['count'] if data['count'] > 0 else 0
            level_breakdown.append({
                'level': level,
                'count': data['count'],
                'average_score': round(avg, 2)
            })
        
        recent_trend = []
        for i in interviews[:10]:
            recent_trend.append({
                'date': i.completed_at.isoformat() if i.completed_at else None,
                'score': round(i.overall_score, 2) if i.overall_score else 0,
                'field': i.field,
                'grade': i.performance_grade
            })
        
        best_score = max([i.overall_score for i in interviews if i.overall_score] or [0])
        avg_score = round(total_score / total_interviews, 2) if total_interviews > 0 else 0
        
        return jsonify({
            'total_interviews': total_interviews,
            'average_score': avg_score,
            'best_score': round(best_score, 2) if best_score else 0,
            'total_time_spent': total_time,
            'total_questions_answered': sum(len(Answer.query.filter_by(interview_id=i.id).all()) for i in interviews),
            'score_distribution': score_dist,
            'field_breakdown': field_breakdown,
            'level_breakdown': level_breakdown,
            'recent_trend': recent_trend,
            'all_interviews': all_interviews_data,  # ALL INTERVIEW DATA
            'timestamp': datetime.utcnow().isoformat(),  # Real-time indicator
        }), 200
    except Exception as e:
        app.logger.error(f"[Analytics] Error: {e}\n{traceback.format_exc()}")
        return jsonify({'error': str(e)}), 500


# ── INTERVIEW ────────────────────────────────────────────────────────────────────

@app.route('/api/interview/start', methods=['POST'])
@jwt_required()
def start_interview():
    """
    AI-DIRECT MODE: Mistral generates questions in a single fast call.
    - No database question-bank dependency
    - Questions personalized from user profile
    - Adaptive: subsequent questions generated from /next-question endpoint
    """
    import time as time_module
    start_time = time_module.time()

    try:
        user_id = int(get_jwt_identity())
        user    = db.session.get(User, user_id)
        if not user: return jsonify({'error': 'User not found'}), 404

        data    = request.get_json(force=True, silent=True) or {}

        # Validate interview configuration using InterviewSessionManager
        if _interview_manager_loaded:
            is_valid, validation_error = InterviewSessionManager.validate_interview_config(data)
            if not is_valid:
                return jsonify({'error': validation_error}), 400

        # Normalize ALL user-selected options from frontend
        raw_field   = data.get('field', 'software').lower().strip()
        raw_level   = data.get('level', 'mid').lower().strip()
        raw_company = data.get('company', '').lower().strip()
        raw_question_type = data.get('question_type', 'mock').lower().strip()
        raw_interview_type = data.get('interview_type', data.get('answer_type', 'technical')).lower().strip()

        field   = FIELD_NAME_MAP.get(raw_field, raw_field.title())
        level   = LEVEL_NAME_MAP.get(raw_level, raw_level.title())
        company = COMPANY_NAME_MAP.get(raw_company, raw_company.title()) if raw_company else 'Tech Company'
        question_type = 'mock' if raw_question_type in ['mock', 'mock_question', 'mock-question'] else 'written'
        # Normalize interview_type from button selection (technical/behavioral/system-design/hr)
        INTERVIEW_TYPE_MAP = {
            'technical': 'technical', 'behavioral': 'behavioral',
            'system-design': 'system-design', 'system_design': 'system-design',
            'hr': 'hr', 'human-resources': 'hr',
        }
        interview_type = INTERVIEW_TYPE_MAP.get(raw_interview_type, 'technical')
        num_q   = 5  # Always exactly 5 questions per session — non-negotiable

        app.logger.info(f"[Interview] AI-Direct: User {user_id}, {field} ({level}) at {company}, type={question_type}, interview_type={interview_type}")

        # Snapshot user profile for personalised question generation
        profile_snap = {
            'skills': user.skills_list(),
            'experience_years': user.experience_years,
            'current_role': user.current_role,
            'resume_summary': user.resume_summary,
            'dream_companies': user.dream_companies_list(),
        }

        raw_mode = data.get('mode', 'text').lower().strip()
        interview_mode = 'voice' if raw_mode == 'voice' else 'text'

        # ── STEP 1: CREATE INTERVIEW RECORD ──────────────────────────────────
        interview = Interview(
            user_id=user_id, field=field, level=level, company=company,
            interview_type=interview_type, question_type=question_type, status='in_progress',
            questions_total=num_q, answer_type=interview_type,
            mode=interview_mode,
            ai_model_used=mistral_agent.model_name,
            user_profile_snapshot=json.dumps(profile_snap),
        )
        db.session.add(interview)
        db.session.commit()

        # ── STEP 2: GENERATE QUESTIONS VIA MISTRAL (FAST, SINGLE CALL) ───────
        app.logger.info(f"[Interview] {interview.id}: Calling Mistral AI (fast mode, 1 call for {num_q} questions)...")
        ai_questions = mistral_agent.generate_questions_fast(
            field, level, company, num_q,
            user_profile=profile_snap,
            question_type=question_type,
            interview_mode=interview_mode,
            user_id=user_id,
            interview_type=interview_type,
        )
        load_time = time_module.time() - start_time
        app.logger.info(f"[Interview] {interview.id}: {len(ai_questions)} questions ready in {load_time:.1f}s (AI-direct)")

        # ── SAFETY PAD: guarantee exactly 5 questions ─────────────────────────
        if len(ai_questions) < num_q:
            app.logger.warning(f"[Interview] {interview.id}: Only {len(ai_questions)} questions from AI, padding to {num_q}")
            pad = mistral_agent._fallback_questions(
                field, level, company, num_q - len(ai_questions), question_type, interview_type=interview_type)
            ai_questions = ai_questions + pad
        ai_questions = ai_questions[:num_q]  # Exactly 5, never more

        # ── STEP 3: PERSIST QUESTIONS ─────────────────────────────────────────
        stored_qs = []
        try:
            for i, qdata in enumerate(ai_questions):
                is_mc = qdata.get('is_multiple_choice', False)
                q = Question(
                    interview_id=interview.id,
                    text=qdata['text'],
                    category=qdata.get('category', 'technical'),
                    field=field, level=level, company=company,
                    difficulty=qdata.get('difficulty', 'medium'),
                    topic_tags=qdata.get('topic_tags', json.dumps([field.lower()])),
                    is_multiple_choice=is_mc,
                    options=json.dumps(qdata['options']) if is_mc and qdata.get('options') else None,
                    correct_answers=json.dumps(qdata['correct_answers']) if is_mc and qdata.get('correct_answers') else None,
                    multiple_allowed=qdata.get('multiple_allowed', False),
                    question_number=i + 1,
                    source='ai_generated',
                )
                db.session.add(q)
                stored_qs.append(q)

            if len(stored_qs) == 0:
                raise ValueError("No questions were generated")

            # ── STEP 4: UPDATE USER STATS AND COMMIT EVERYTHING ──────────────────
            user.total_interviews += 1
            db.session.commit()  # Single commit: questions + user stats
        except Exception as e:
            db.session.rollback()
            # Clean up orphaned interview
            try:
                db.session.delete(interview)
                db.session.commit()
            except Exception:
                db.session.rollback()
            app.logger.error(f"[Interview] Question storage failed, rolled back: {str(e)[:100]}")
            return jsonify({'error': 'Failed to generate interview questions. Please try again.'}), 500

        response_data = {
            'interview_id': interview.uuid,
            'interview': interview.to_dict(),
            'questions': [q.to_dict() for q in stored_qs],
            'loading_mode': 'ai_direct',
            'load_time_seconds': round(load_time, 1),
            'message': f'AI generated {len(stored_qs)} personalised questions in {load_time:.1f}s',
            'mistral_active': mistral_agent.is_available,
        }

        app.logger.info(f"[Interview] {interview.id}: AI-direct interview ready, {len(stored_qs)} questions")
        return jsonify(response_data), 201

    except Exception as e:
        db.session.rollback()
        app.logger.error(f"[Interview] start_interview error: {e}\n{traceback.format_exc()}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/interview/<interview_uuid>/next-question', methods=['POST'])
@jwt_required()
def get_next_adaptive_question(interview_uuid):
    """
    Adaptive question endpoint: Mistral analyzes the user's previous answers and
    generates the next question targeting weak areas or advancing to harder topics.
    Called after each answer submission for truly adaptive interviewing.
    """
    try:
        user_id   = int(get_jwt_identity())
        interview = Interview.query.filter_by(uuid=interview_uuid).first()
        if not interview:              return jsonify({'error': 'Interview not found'}), 404
        if interview.user_id != user_id: return jsonify({'error': 'Unauthorized'}), 403

        data            = request.get_json(force=True, silent=True) or {}
        question_number = int(data.get('question_number', 1))
        previous_qa     = data.get('previous_qa', [])  # [{question, answer, score}, ...]

        profile_snap = {}
        try:
            profile_snap = json.loads(interview.user_profile_snapshot or '{}')
        except Exception:
            pass

        next_q_data = mistral_agent.generate_adaptive_question(
            field=interview.field,
            level=interview.level,
            company=interview.company,
            question_number=question_number,
            total_questions=interview.questions_total,
            previous_questions_answers=previous_qa,
            user_profile=profile_snap,
        )

        if not next_q_data:
            return jsonify({'error': 'Failed to generate adaptive question'}), 500

        # Store the adaptively generated question
        q = Question(
            interview_id=interview.id,
            text=next_q_data['text'],
            category=next_q_data.get('category', 'adaptive'),
            field=interview.field, level=interview.level, company=interview.company,
            difficulty=next_q_data.get('difficulty', 'medium'),
            topic_tags=next_q_data.get('topic_tags', json.dumps([interview.field.lower()])),
            is_multiple_choice=False,
            question_number=question_number,
            source='ai_adaptive',
        )
        db.session.add(q)
        db.session.commit()

        app.logger.info(f"[Adaptive] Q{question_number} generated for interview {interview_uuid}")
        return jsonify({'question': q.to_dict()}), 200

    except Exception as e:
        db.session.rollback()
        app.logger.error(f"[Adaptive] next-question error: {e}\n{traceback.format_exc()}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/interview/<interview_uuid>/hybrid-status', methods=['GET'])
@jwt_required()
def get_hybrid_status(interview_uuid):
    """Check if AI questions are ready for a hybrid interview"""
    try:
        user_id   = int(get_jwt_identity())
        interview = Interview.query.filter_by(uuid=interview_uuid).first()
        
        if not interview:
            return jsonify({'error': 'Interview not found'}), 404
        if interview.user_id != user_id:
            return jsonify({'error': 'Unauthorized'}), 403
        
        hybrid = HybridInterviewSession.query.filter_by(interview_id=interview.id).first()
        
        if not hybrid:
            return jsonify({'status': 'not_hybrid', 'ai_ready': False}), 200
        
        data = {
            'status': 'hybrid',
            'db_loaded': hybrid.db_questions_loaded,
            'ai_loaded': hybrid.ai_questions_loaded,
            'initial_load_time_ms': round(hybrid.initial_load_time_ms, 1) if hybrid.initial_load_time_ms else None,
            'ai_load_time_sec': round(hybrid.ai_load_time_sec, 2) if hybrid.ai_load_time_sec else None,
            'total_load_time_sec': round(hybrid.total_load_time_sec, 2) if hybrid.total_load_time_sec else None,
            'ai_ready': hybrid.ai_questions_loaded,
        }
        
        # If AI questions are ready, provide info about them
        if hybrid.ai_questions_loaded:
            ai_questions = Question.query.filter_by(
                interview_id=interview.id,
                source='ai_generated_async'
            ).all()
            data['available_ai_questions'] = len(ai_questions)
            data['message'] = f'AI finished! {len(ai_questions)} bonus questions available.'
        else:
            data['message'] = 'AI still generating questions...'
        
        return jsonify(data), 200
    
    except Exception as e:
        app.logger.error(f"[Hybrid Status] Error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/interview/<interview_uuid>/submit', methods=['POST'])
@jwt_required()
def submit_answer(interview_uuid):
    import time as time_module  # For performance timing
    try:
        user_id   = int(get_jwt_identity())
        data      = request.get_json(force=True, silent=True) or {}
        interview = Interview.query.filter_by(uuid=interview_uuid).first()

        if not interview:   return jsonify({'error': 'Interview not found'}), 404
        if interview.user_id != user_id: return jsonify({'error': 'Unauthorized'}), 403

        question_id  = data.get('question_id')
        answer_text  = (data.get('answer', '') or '').strip()
        selected_options_input = data.get('selected_options', [])  # For multiple-choice
        time_spent   = int(data.get('time_spent', 0))

        # Find question in this session (or allow by ID only)
        question = None
        if question_id:
            question = Question.query.filter_by(id=question_id,
                                                interview_id=interview.id).first()

        if not question:
            app.logger.error(f"[Submit] Question not found: question_id={question_id}, interview_id={interview.id}")
            return jsonify({'error': 'Question not found in this session'}), 404

        app.logger.info(f"[Submit] Processing answer for Q{question.question_number}, Interview={interview_uuid}, Field={interview.field}, Level={interview.level}")

        # Handle multiple-choice questions
        if question.is_multiple_choice:
            # Use MockQuestionInterviewHandler for validated MC answer processing
            if _interview_manager_loaded:
                is_valid, mc_error = MockQuestionInterviewHandler.validate_mock_answer(selected_options_input, question)
                if not is_valid:
                    return jsonify({'error': mc_error}), 400

            if not selected_options_input:
                return jsonify({'error': 'Please select at least one option'}), 400

            # Validate selected options
            selected_options = []
            try:
                for opt in selected_options_input:
                    idx = int(opt)
                    if 0 <= idx < len(question.options_list()):
                        selected_options.append(idx)
            except (ValueError, TypeError):
                return jsonify({'error': 'Invalid option selection'}), 400
            
            if not selected_options:
                return jsonify({'error': 'Please select valid options'}), 400
            
            # Score the multiple-choice answer
            correct_answers = question.correct_answers_list()
            selected_set = set(selected_options)
            correct_set = set(correct_answers)
            
            # Store the multiple-choice answer
            answer_text_display = json.dumps({
                'type': 'multiple_choice',
                'selected_options': selected_options,
                'correct_answers': correct_answers,
                'options': question.options_list()
            })

            # ── INSTANT MC scoring — no AI blocking ──────────────────────────
            # generate_mc_feedback now returns heuristic immediately and fires AI
            # in background; answer_uuid set below after Answer row is committed.
            is_answer_correct = set(selected_options) == set(correct_answers)
            # STRICT SCORING: 10.0 for correct, 0.0 for incorrect — no partial credit
            mc_score  = 10.0 if is_answer_correct else 0.0
            accuracy  = 10.0 if is_answer_correct else 0.0
            letter_sel = [chr(65+i) for i in selected_options]
            letter_cor = [chr(65+i) for i in correct_answers]
            analysis = {
                'score': mc_score, 'technical_accuracy': accuracy,
                'depth_score': 10.0 if is_answer_correct else 0.0,
                'clarity_score': 10.0 if is_answer_correct else 0.0,
                'relevance_score': 10.0 if is_answer_correct else 0.0,
                'communication_score': 10.0 if is_answer_correct else 0.0,
                'confidence_score': 10.0 if is_answer_correct else 0.0,
                'strengths': ['Perfect! Correct answer selected.' if is_answer_correct else 'Attempted the question'],
                'weaknesses': [] if is_answer_correct else ['Incorrect answer selected. Review the concept thoroughly.'],
                'feedback': f"{'✓ Correct — Full marks awarded!' if is_answer_correct else '✗ Incorrect — The correct answer is ' + ', '.join(letter_cor)} — Your selection: {', '.join(letter_sel)}",
                'improvement_plan': [] if is_answer_correct else ['Study the correct answer explanation', 'Review this topic in depth', 'Practice similar questions'],
                'model': 'instant-mc',
                'source': 'instant',
                '_mc_pending': True,   # flag: AI feedback will be stored async
                '_mc_correct_options': correct_answers,
                '_mc_user_selected': selected_options,
            }
        else:
            # Handle text answers (written interview)
            if not answer_text:
                return jsonify({'error': 'Answer text required'}), 400

            # Validate written answer quality (minimum standards)
            if _interview_manager_loaded:
                is_valid, validation_error = WrittenInterviewHandler.validate_written_answer(answer_text)
                if not is_valid:
                    return jsonify({'error': validation_error}), 400

            # ── STEP 1: CHECK ANSWER CACHE (FAST PATH - <10ms) ──────────────
            from hashlib import sha256
            answer_hash = sha256(answer_text.lower().encode()).hexdigest()
            question_hash = sha256(question.text.lower().encode()).hexdigest()
            answer_length_bucket = len(answer_text.split()) // 10

            cached_result = AnswerCache.query.filter_by(
                question_hash=question_hash,
                answer_hash=answer_hash,
                answer_length=answer_length_bucket
            ).first()

            if cached_result:
                analysis = cached_result.cached_analysis_dict()
                analysis['source'] = 'cache'
                # Bump hit count for cache stats
                cached_result.hit_count    = (cached_result.hit_count or 0) + 1
                cached_result.last_accessed = datetime.utcnow()
                db.session.commit()
                app.logger.info(f"[Analysis] CACHE HIT — instant response (hits={cached_result.hit_count})")
            else:
                # ── STEP 2: INSTANT HEURISTIC — AI fires post-commit with real UUID
                analysis = mistral_agent._fallback_analysis(question.text, answer_text)
                analysis['source'] = 'heuristic_pending'

            answer_text_display = answer_text

        # Store answer with all dimensions (using quick/cached analysis for immediate response)
        answer = Answer(
            interview_id=interview.id,
            question_id=question.id,
            text=answer_text_display,
            selected_options=json.dumps(selected_options) if question.is_multiple_choice else None,
            word_count=len(answer_text_display.split()) if not question.is_multiple_choice else 0,
            score=analysis['score'],
            technical_accuracy=analysis['technical_accuracy'],
            depth_score=analysis['depth_score'],
            clarity_score=analysis['clarity_score'],
            relevance_score=analysis['relevance_score'],
            communication_score=analysis['communication_score'],
            confidence_score=analysis['confidence_score'],
            time_spent_seconds=time_spent,
        )
        db.session.add(answer)
        db.session.commit()

        # ── After commit we have answer.uuid — wire async jobs to it ─────────
        real_uuid = answer.uuid

        # For pending async text analysis: fire AI with real UUID now
        if analysis.get('source') == 'heuristic_pending':
            with _pending_analysis_lock:
                _pending_analysis[real_uuid] = {'status': 'pending', 'analysis': analysis}
            _q_type = (getattr(question, 'question_type', None)
                       or getattr(interview, 'question_type', 'mock') or 'mock')
            _mode   = getattr(interview, 'mode', None) or 'text'
            _i_type = getattr(interview, 'interview_type', None) or 'technical'
            mistral_agent.analyze_answer_fast(
                question=question.text,
                answer=answer_text_display,
                field=interview.field,
                level=interview.level,
                company=interview.company,
                answer_uuid=real_uuid,
                store_async=True,
                question_type=_q_type,
                interview_mode=_mode,
                interview_type=_i_type,
            )

        # For MC pending: kick off AI feedback now with real UUID
        if analysis.get('_mc_pending'):
            _q_type = (getattr(question, 'question_type', None)
                       or getattr(interview, 'question_type', 'mock') or 'mock')
            mistral_agent.generate_mc_feedback(
                question=question.text,
                correct_options=analysis['_mc_correct_options'],
                user_selected=analysis['_mc_user_selected'],
                field=interview.field,
                level=interview.level,
                company=interview.company,
                answer_uuid=real_uuid,
                question_type=_q_type,
            )

        # Store feedback
        feedback = Feedback(
            user_id=user_id,
            answer_id=answer.id,
            score=analysis['score'],
            strengths=json.dumps(analysis['strengths']),
            improvements=json.dumps(analysis['weaknesses']),
            detailed_feedback=analysis['feedback'],
            improvement_plan=json.dumps(analysis.get('improvement_plan', [])),
            model_used=analysis.get('model', 'rag-enhanced-mistral'),
        )
        db.session.add(feedback)

        # Update interview progress + duration + user totals in single atomic commit
        interview.questions_answered += 1
        if interview.started_at:
            interview.duration_seconds = int((datetime.utcnow() - interview.started_at).total_seconds())
        user = db.session.get(User, user_id)
        if user:
            user.total_questions_answered += 1
        db.session.commit()
        
        # Async task: Save to FAISS in background (non-blocking)
        _q_text_copy, _a_text_copy = question.text, answer.text
        _a_feedback_copy, _a_score_copy, _q_id_copy = analysis['feedback'], analysis['score'], question.id
        def save_to_rag_async():
            try:
                from rag.rag_engine import rag_engine
                if hasattr(rag_engine, 'is_available') and rag_engine.is_available:
                    rag_engine.record_session(
                        question=_q_text_copy, user_answer=_a_text_copy,
                        ai_feedback=_a_feedback_copy, rating=_a_score_copy,
                        question_id=_q_id_copy
                    )
                    app.logger.info(f"[FAISS] Async session recorded successfully")
            except Exception as e:
                app.logger.debug(f'[FAISS] Background save skipped: {str(e)[:80]}')
        
        threading.Thread(target=save_to_rag_async, daemon=True).start()

        app.logger.info(f"[Interview] Answer stored: Q{question.question_number}, Score={analysis['score']}")
        return jsonify({
            'answer_id': answer.uuid,
            'question_number': question.question_number,
            'analysis_pending': analysis.get('source') in ('heuristic_pending', 'instant'),
            'analysis': {
                'score': analysis['score'],
                'technical_accuracy': analysis['technical_accuracy'],
                'depth_score': analysis['depth_score'],
                'clarity_score': analysis['clarity_score'],
                'relevance_score': analysis['relevance_score'],
                'communication_score': analysis['communication_score'],
                'confidence_score': analysis['confidence_score'],
                'strengths': analysis['strengths'],
                'weaknesses': analysis['weaknesses'],
                'feedback': analysis['feedback'],
                'improvement_plan': analysis.get('improvement_plan', []),
                'source': analysis.get('source', 'unknown'),
            }
        }), 201

    except Exception as e:
        db.session.rollback()
        app.logger.error(f"[Interview] submit_answer error: {e}\n{traceback.format_exc()}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/interview/<interview_uuid>/answer/<answer_uuid>/analysis', methods=['GET'])
@jwt_required()
def poll_answer_analysis(interview_uuid, answer_uuid):
    """
    Poll endpoint for async AI analysis results.
    Returns:
      { status: 'pending'|'done'|'error', analysis: {...} }
    Frontend should poll every 2-3s until status == 'done'.
    Falls back to DB Feedback row if not in memory store (e.g. after server restart).
    """
    with _pending_analysis_lock:
        entry = _pending_analysis.get(answer_uuid)

    if entry:
        return jsonify(entry), 200

    # Not in memory — check DB for completed feedback
    try:
        ans = Answer.query.filter_by(uuid=answer_uuid).first()
        if not ans:
            return jsonify({'status': 'error', 'message': 'Answer not found'}), 404
        fb = Feedback.query.filter_by(answer_id=ans.id).first()
        if fb:
            analysis = {
                'score': ans.score or fb.score,
                'technical_accuracy': ans.technical_accuracy or ans.score,
                'depth_score': ans.depth_score or ans.score,
                'clarity_score': ans.clarity_score or ans.score,
                'relevance_score': ans.relevance_score or ans.score,
                'communication_score': ans.communication_score or ans.score,
                'confidence_score': ans.confidence_score or ans.score,
                'strengths': fb.strengths_list(),
                'weaknesses': fb.improvements_list(),
                'feedback': fb.detailed_feedback or '',
                'improvement_plan': fb.improvement_plan_list(),
                'model': fb.model_used or 'db',
                'source': 'db',
            }
            return jsonify({'status': 'done', 'analysis': analysis}), 200
        # Answer exists but no feedback yet — still computing
        return jsonify({'status': 'pending', 'analysis': {}}), 200
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)[:80]}), 500


@app.route('/api/interview/<interview_uuid>/complete', methods=['POST'])
@jwt_required()
def complete_interview(interview_uuid):
    try:
        user_id   = int(get_jwt_identity())
        interview = Interview.query.filter_by(uuid=interview_uuid).first()
        if not interview:   return jsonify({'error': 'Interview not found'}), 404
        if interview.user_id != user_id: return jsonify({'error': 'Unauthorized'}), 403

        answers = Answer.query.filter_by(interview_id=interview.id).all()

        # Enforce that all questions have been answered before allowing completion
        expected_total = interview.questions_total or 5
        if len(answers) < expected_total:
            return jsonify({
                'error': f'Interview not complete. Answered {len(answers)}/{expected_total} questions.',
                'answered': len(answers),
                'total': expected_total
            }), 400

        scored  = [a for a in answers if a.score is not None]

        overall     = round(sum(a.score for a in scored) / len(scored), 2) if scored else 0.0
        tech_avg    = round(sum(a.technical_accuracy or 0 for a in scored) / max(len(scored),1), 2)
        comm_avg    = round(sum(a.communication_score or 0 for a in scored) / max(len(scored),1), 2)
        clarity_avg = round(sum(a.clarity_score or 0 for a in scored) / max(len(scored),1), 2)
        depth_avg   = round(sum(a.depth_score or 0 for a in scored) / max(len(scored),1), 2)

        def grade(s):
            if s >= 9.0: return 'A+'
            if s >= 8.0: return 'A'
            if s >= 7.0: return 'B'
            if s >= 6.0: return 'C'
            if s >= 5.0: return 'D'
            return 'F'

        interview.status             = 'completed'
        interview.completed_at       = datetime.utcnow()
        interview.overall_score      = overall
        interview.technical_score    = tech_avg
        interview.communication_score= comm_avg
        interview.clarity_score      = clarity_avg
        interview.depth_score        = depth_avg
        interview.performance_grade  = grade(overall)
        if interview.started_at:
            interview.duration_seconds = int((datetime.utcnow() - interview.started_at).total_seconds())

        # Commit interview changes first
        db.session.commit()
        
        # Recalculate ALL user aggregate statistics from actual data
        # This ensures perfect sync between User model stats and actual Interview records
        recalculate_user_stats(user_id)

        # Build per-question feedback for the results screen
        qa_pairs = []
        for a in answers:
            question = db.session.get(Question, a.question_id) if a.question_id else None
            fb = Feedback.query.filter_by(answer_id=a.id).first()
            qa_pairs.append({
                'question_number': question.question_number if question else None,
                'question_text':   question.text if question else '',
                'is_multiple_choice': question.is_multiple_choice if question else False,
                'answer_text':     a.text or '',
                'score':           round(a.score, 2) if a.score is not None else None,
                'technical_accuracy': round(a.technical_accuracy, 2) if a.technical_accuracy is not None else None,
                'depth_score':     round(a.depth_score, 2) if a.depth_score is not None else None,
                'clarity_score':   round(a.clarity_score, 2) if a.clarity_score is not None else None,
                'communication_score': round(a.communication_score, 2) if a.communication_score is not None else None,
                'strengths':       fb.strengths_list() if fb else [],
                'weaknesses':      fb.improvements_list() if fb else [],
                'feedback_text':   fb.detailed_feedback if fb else '',
            })

        app.logger.info(f"[Interview] Completed {interview.id} | Score: {overall} | Grade: {grade(overall)}")
        return jsonify({
            'message': 'Interview completed',
            'interview': interview.to_dict(),
            'overall_score': overall,
            'performance_grade': grade(overall),
            'breakdown': {
                'technical': tech_avg,
                'communication': comm_avg,
                'clarity': clarity_avg,
                'depth': depth_avg,
            },
            'total_answered': len(scored),
            'qa_pairs': qa_pairs,
            'duration_seconds': interview.duration_seconds or 0,
        }), 200

    except Exception as e:
        db.session.rollback()
        app.logger.error(f"[Interview] complete error: {e}\n{traceback.format_exc()}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/interview/history', methods=['GET'])
@jwt_required()
def interview_history():
    """
    REAL-TIME Past Sessions History Endpoint
    Shows all completed and in-progress interview sessions with full details
    """
    try:
        user_id = int(get_jwt_identity())
        page    = int(request.args.get('page', 1))
        per_page= min(int(request.args.get('per_page', 10)), 50)
        status  = request.args.get('status')

        q = Interview.query.filter_by(user_id=user_id)
        if status: q = q.filter_by(status=status)
        q = q.order_by(Interview.started_at.desc())
        total   = q.count()
        sessions= q.offset((page-1)*per_page).limit(per_page).all()

        # Enhance session data with answers count and detailed info
        sessions_data = []
        for s in sessions:
            session_dict = s.to_dict()
            answers_count = len(Answer.query.filter_by(interview_id=s.id).all())
            session_dict['answers_count'] = answers_count
            session_dict['total_practice_time'] = s.duration_seconds or 0
            session_dict['completed'] = s.status == 'completed'
            session_dict['in_progress'] = s.status == 'in_progress'
            sessions_data.append(session_dict)

        return jsonify({
            'sessions': sessions_data,
            'total': total,
            'page': page,
            'per_page': per_page,
            'pages': (total + per_page - 1) // per_page,
            'timestamp': datetime.utcnow().isoformat(),  # Real-time indicator
        }), 200
    except Exception as e:
        app.logger.error(f"[History] Error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/interview/<interview_uuid>/full-report', methods=['GET'])
@jwt_required()
def full_report(interview_uuid):
    try:
        user_id   = int(get_jwt_identity())
        interview = Interview.query.filter_by(uuid=interview_uuid).first()
        if not interview:   return jsonify({'error': 'Interview not found'}), 404
        if interview.user_id != user_id: return jsonify({'error': 'Unauthorized'}), 403

        answers = Answer.query.filter_by(interview_id=interview.id).all()
        qa_pairs = []
        for a in answers:
            question = db.session.get(Question, a.question_id) if a.question_id else None
            fb       = Feedback.query.filter_by(answer_id=a.id).first()
            qa_pairs.append({
                'question': question.to_dict() if question else None,
                'answer':   a.to_dict(),
                'feedback': fb.to_dict() if fb else None,
            })

        return jsonify({
            'interview': interview.to_dict(),
            'qa_pairs': qa_pairs,
            'total_questions_answered': len(answers),
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ── DASHBOARD ──────────────────────────────────────────────────────────────────

@app.route('/api/dashboard/stats', methods=['GET'])
@jwt_required()
def dashboard_stats():
    """
    REAL-TIME Dashboard Statistics Endpoint
    Always fetches fresh data from database - NEVER cached
    """
    try:
        user_id = int(get_jwt_identity())
        user    = db.session.get(User, user_id)
        if not user: return jsonify({'error': 'User not found'}), 404

        # REAL-TIME: Always recalculate from database
        recalculate_user_stats(user_id)
        
        # REFRESH user object from database
        db.session.refresh(user)
        
        # Get completion metrics fresh from database
        completed_interviews = Interview.query.filter_by(
            user_id=user_id, status='completed'
        ).order_by(Interview.started_at.desc()).all()
        
        completed_count = len(completed_interviews)
        
        # Get recent sessions (latest 5)
        recent = Interview.query.filter_by(user_id=user_id)\
                          .order_by(Interview.started_at.desc()).limit(5).all()
        
        # Calculate real-time stats
        completed_scores = [i.overall_score for i in completed_interviews 
                           if i.overall_score is not None]
        
        real_avg = round(sum(completed_scores) / len(completed_scores), 2) if completed_scores else 0.0
        real_best = round(max(completed_scores), 2) if completed_scores else 0.0
        real_total_time = sum(i.duration_seconds or 0 for i in completed_interviews)
        real_total_questions = sum(
            len(Answer.query.filter_by(interview_id=i.id).all()) 
            for i in completed_interviews
        )

        return jsonify({
            'total_interviews':          completed_count,
            'total_questions_answered':  real_total_questions,
            'average_score':             real_avg,
            'avg_score':                 real_avg,
            'best_score':                real_best,
            'current_streak':            user.current_streak or 0,
            'longest_streak':            user.longest_streak or 0,
            'total_practice_time':       real_total_time,
            'completed_interviews':      completed_count,
            'recent_sessions':           [s.to_dict() for s in recent],
            'timestamp': datetime.utcnow().isoformat(),  # Real-time indicator
        }), 200
    except Exception as e:
        app.logger.error(f"[Dashboard] Error: {e}")
        return jsonify({'error': str(e)}), 500


# ── DATABASE RECOVERY & MAINTENANCE ─────────────────────────────────────────

@app.route('/api/data/refresh', methods=['POST'])
@jwt_required()
def refresh_realtime_data():
    """
    REAL-TIME Data Refresh Endpoint
    Forces immediate recalculation and returns fresh data for all views
    Frontend can call this every 5-10 seconds to keep data current
    """
    try:
        user_id = int(get_jwt_identity())
        user = db.session.get(User, user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Force recalculation of all stats
        recalculate_user_stats(user_id)
        db.session.refresh(user)
        
        # Get fresh data
        completed_interviews = Interview.query.filter_by(
            user_id=user_id, status='completed'
        ).order_by(Interview.started_at.desc()).all()
        
        # Calculate current metrics
        completed_count = len(completed_interviews)
        scores = [i.overall_score for i in completed_interviews if i.overall_score]
        total_questions = sum(
            len(Answer.query.filter_by(interview_id=i.id).all()) 
            for i in completed_interviews
        )
        total_time = sum(i.duration_seconds or 0 for i in completed_interviews)
        
        return jsonify({
            'status': 'refresh_complete',
            'user_stats': {
                'completed_interviews': completed_count,
                'average_score': round(sum(scores) / len(scores), 2) if scores else 0,
                'best_score': round(max(scores), 2) if scores else 0,
                'total_questions_answered': total_questions,
                'total_practice_time': total_time,
                'current_streak': user.current_streak or 0,
                'longest_streak': user.longest_streak or 0,
            },
            'timestamp': datetime.utcnow().isoformat(),
        }), 200
        
    except Exception as e:
        app.logger.error(f"[Refresh] Error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/interview/current/<interview_uuid>', methods=['GET'])
@jwt_required()
def get_current_interview_realtime(interview_uuid):
    """
    REAL-TIME Current Interview Status Endpoint
    Gets live data for a specific interview in progress
    """
    try:
        user_id = int(get_jwt_identity())
        interview = Interview.query.filter_by(uuid=interview_uuid).first()
        
        if not interview:
            return jsonify({'error': 'Interview not found'}), 404
        
        if interview.user_id != user_id:
            return jsonify({'error': 'Unauthorized'}), 403
        
        # Get all answers for this interview
        answers = Answer.query.filter_by(interview_id=interview.id).all()
        
        # Get all questions for this interview
        questions = Question.query.filter_by(interview_id=interview.id).all()
        
        # Calculate current score if any answers scored
        scored_answers = [a for a in answers if a.score is not None]
        current_score = round(sum(a.score for a in scored_answers) / len(scored_answers), 2) if scored_answers else 0
        
        return jsonify({
            'interview': interview.to_dict(),
            'current_score': current_score,
            'questions_total': len(questions),
            'questions_answered': len(answers),
            'answers': [a.to_dict() for a in answers],
            'status': interview.status,
            'timestamp': datetime.utcnow().isoformat(),
        }), 200
        
    except Exception as e:
        app.logger.error(f"[Interview Current] Error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/admin/recover-analytics', methods=['POST'])
@jwt_required()
def recover_analytics():
    """
    RECOVERY ENDPOINT: Recalculate and synchronize analytics for current user.
    Fixes any corrupted or stale statistics by recomputing from raw interview data.
    
    This endpoint is safe to call and will restore data integrity.
    """
    try:
        user_id = int(get_jwt_identity())
        user = db.session.get(User, user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Recalculate all stats
        success = recalculate_user_stats(user_id)
        
        if success:
            # Refresh user from DB
            db.session.refresh(user)
            return jsonify({
                'message': 'Analytics recovery completed successfully',
                'user_stats': {
                    'total_interviews': user.total_interviews,
                    'total_questions_answered': user.total_questions_answered,
                    'average_score': round(user.average_score or 0.0, 2),
                    'best_score': round(user.best_score or 0.0, 2),
                    'total_practice_time': user.total_practice_time or 0,
                    'last_activity_date': user.last_activity_date.isoformat() if user.last_activity_date else None,
                }
            }), 200
        else:
            return jsonify({'error': 'Failed to recalculate analytics'}), 500
            
    except Exception as e:
        app.logger.error(f"[Recovery] Error in recover_analytics: {e}")
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


# ── ERROR HANDLERS ──────────────────────────────────────────────────────────────

@app.errorhandler(404)
def not_found(e):
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(405)
def method_not_allowed(e):
    return jsonify({'error': 'Method not allowed'}), 405

@app.errorhandler(413)
def payload_too_large(e):
    return jsonify({'error': 'Request payload too large'}), 413

@app.errorhandler(429)
def too_many_requests(e):
    return jsonify({'error': 'Too many requests. Please slow down.'}), 429

@app.errorhandler(500)
def server_error(e):
    db.session.rollback()
    app.logger.error(f"[500] Internal server error: {e}")
    return jsonify({'error': 'Internal server error'}), 500

@app.errorhandler(Exception)
def unhandled_exception(e):
    db.session.rollback()
    app.logger.error(f"[Unhandled] {type(e).__name__}: {str(e)[:200]}\n{traceback.format_exc()}")
    return jsonify({'error': 'An unexpected error occurred'}), 500


# ==============================================================================
#  MAIN
# ==============================================================================

if __name__ == '__main__':
    with app.app_context():
        db.create_all()

        # Seed demo user
        demo = User.query.filter_by(email='demo@interviewcoach.ai').first()
        if not demo:
            demo = User(email='demo@interviewcoach.ai', first_name='Demo', last_name='User',
                        headline='Full Stack Developer | AI Enthusiast',
                        experience_years=3, current_role='Software Developer',
                        skills=json.dumps(['Python','JavaScript','React','Node.js','SQL','Docker']),
                        dream_companies=json.dumps(['Google','Amazon','Microsoft']),
                        target_roles=json.dumps(['Senior Software Engineer','Backend Engineer']))
            demo.set_password('demo123456')
            db.session.add(demo)
            db.session.commit()
            print("[DB] Demo user created: demo@interviewcoach.ai / demo123456")
        elif not demo.check_password('demo123456'):
            demo.set_password('demo123456')
            db.session.commit()
            print("[DB] Demo user password reset to demo123456")
        else:
            print("[DB] Demo user already exists")

        # Seed QuestionBank with verified questions
        if QuestionBank.query.count() == 0:
            seed_qs = [
                QuestionBank(text="Design a scalable URL-shortening service. Walk through your system design.", category='technical', field='software', level='senior', company='google', difficulty='hard', is_verified=True),
                QuestionBank(text="Explain the difference between a process and a thread and when you'd use each.", category='technical', field='software', level='mid', difficulty='medium', is_verified=True),
                QuestionBank(text="How do you handle class imbalance in a machine learning classification problem?", category='technical', field='data-science', level='mid', difficulty='medium', is_verified=True),
                QuestionBank(text="Describe a time you resolved a conflict with a teammate. What was the outcome?", category='behavioral', field='software', level='mid', difficulty='easy', is_verified=True),
                QuestionBank(text="How would you measure success of a new product feature launch?", category='technical', field='product', level='mid', difficulty='medium', is_verified=True),
                QuestionBank(text="Explain CAP theorem and how you'd design a payment system given those constraints.", category='technical', field='software', level='senior', difficulty='hard', is_verified=True),
            ]
            db.session.add_all(seed_qs)
            db.session.commit()
            print(f"[DB] Seeded {len(seed_qs)} verified questions to QuestionBank")

    print("\n" + "="*70)
    print("  AI INTERVIEW COACH - ENTERPRISE BACKEND v3.0")
    print("="*70)
    print(f"  Database: {os.path.join(basedir,'interview_coach.db')}")
    print(f"  Mistral:  {'ONLINE' if mistral_agent.is_available else 'OFFLINE (fallback active)'}")
    print(f"  Server:   http://127.0.0.1:5000")
    print("="*70 + "\n")

    app.run(host='0.0.0.0', port=5000, debug=True)
