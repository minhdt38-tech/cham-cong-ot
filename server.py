# -*- coding: utf-8 -*-
"""
Cham Cong OT - Web Server
Chay: python server.py
Truy cap: http://localhost:3000
Yeu cau: Python 3.8+ (khong can cai them thu vien)
"""

import http.server
import socketserver
import json
import sqlite3
import hashlib
import os
import mimetypes
import uuid
import io
import re
import threading
from urllib.parse import urlparse, parse_qs
from datetime import datetime, timedelta, timezone

VN_TZ = timezone(timedelta(hours=7))

try:
    from PIL import Image as PilImage
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

try:
    import openpyxl
    from openpyxl.styles import Font, PatternFill, Alignment
    OPENPYXL_AVAILABLE = True
except ImportError:
    OPENPYXL_AVAILABLE = False

try:
    import boto3
    from botocore.client import Config
    BOTO3_AVAILABLE = True
except ImportError:
    BOTO3_AVAILABLE = False

PORT = int(os.environ.get('PORT', 3000))
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# DATA_DIR: thu muc luu DB + uploads
# - Local: cung thu muc voi server.py
# - Railway/cloud: dat bien moi truong DATA_DIR=/data (persistent volume)
DATA_DIR    = os.environ.get('DATA_DIR', BASE_DIR)
UPLOADS_DIR = os.path.join(DATA_DIR, 'uploads')
PUBLIC_DIR  = os.path.join(BASE_DIR, 'public')
DB_PATH     = os.path.join(DATA_DIR, 'cham_cong.db')

os.makedirs(UPLOADS_DIR, exist_ok=True)
os.makedirs(PUBLIC_DIR,  exist_ok=True)

# R2 / S3-compatible storage
R2_ENDPOINT    = os.environ.get('R2_ENDPOINT_URL', '')
R2_ACCESS_KEY  = os.environ.get('R2_ACCESS_KEY_ID', '')
R2_SECRET_KEY  = os.environ.get('R2_SECRET_ACCESS_KEY', '')
R2_BUCKET      = os.environ.get('R2_BUCKET_NAME', '')
R2_ENABLED     = bool(BOTO3_AVAILABLE and R2_ENDPOINT and R2_ACCESS_KEY and R2_SECRET_KEY and R2_BUCKET)

def get_r2_client():
    return boto3.client(
        's3',
        endpoint_url=R2_ENDPOINT,
        aws_access_key_id=R2_ACCESS_KEY,
        aws_secret_access_key=R2_SECRET_KEY,
        config=Config(signature_version='s3v4'),
        region_name='auto'
    )

def r2_upload(file_bytes, key, content_type='application/octet-stream'):
    """Upload bytes len R2, tra ve True neu thanh cong"""
    try:
        client = get_r2_client()
        client.put_object(
            Bucket=R2_BUCKET,
            Key=key,
            Body=file_bytes,
            ContentType=content_type
        )
        return True
    except Exception as e:
        print(f'[R2 upload error] {e}')
        return False

def r2_delete(key):
    """Xoa object tren R2"""
    try:
        client = get_r2_client()
        client.delete_object(Bucket=R2_BUCKET, Key=key)
    except Exception as e:
        print(f'[R2 delete error] {e}')

def r2_presigned_url(key, expires=3600):
    """Tao presigned URL de download/preview file, het han sau `expires` giay"""
    try:
        client = get_r2_client()
        return client.generate_presigned_url(
            'get_object',
            Params={'Bucket': R2_BUCKET, 'Key': key},
            ExpiresIn=expires
        )
    except Exception as e:
        print(f'[R2 presign error] {e}')
        return None

# In-memory sessions: { token: {userId, role, fullName} }
SESSIONS = {}
SESSION_LOCK = threading.Lock()


# --- DATABASE ---

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db():
    with get_db() as db:
        db.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            username    TEXT UNIQUE NOT NULL,
            password    TEXT NOT NULL,
            full_name   TEXT NOT NULL,
            role        TEXT DEFAULT 'employee',
            department  TEXT DEFAULT '',
            created_at  TEXT DEFAULT (datetime('now','localtime'))
        );
        CREATE TABLE IF NOT EXISTS overtime_requests (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id      INTEGER NOT NULL,
            request_date TEXT NOT NULL,
            ot_type      TEXT NOT NULL,
            start_time   TEXT NOT NULL,
            end_time     TEXT NOT NULL,
            hours        REAL,
            reason       TEXT NOT NULL,
            image_path   TEXT,
            status       TEXT DEFAULT 'pending',
            manager_note TEXT,
            reviewed_by  INTEGER,
            reviewed_at  TEXT,
            created_at   TEXT DEFAULT (datetime('now','localtime')),
            FOREIGN KEY(user_id) REFERENCES users(id)
        );
        CREATE TABLE IF NOT EXISTS notifications (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     INTEGER NOT NULL,
            ot_id       INTEGER NOT NULL,
            title       TEXT NOT NULL,
            message     TEXT NOT NULL,
            is_read     INTEGER DEFAULT 0,
            created_at  TEXT DEFAULT (datetime('now','localtime')),
            FOREIGN KEY(user_id) REFERENCES users(id),
            FOREIGN KEY(ot_id)   REFERENCES overtime_requests(id)
        );
        CREATE TABLE IF NOT EXISTS doc_categories (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            name        TEXT NOT NULL,
            description TEXT DEFAULT '',
            color       TEXT DEFAULT '#1B2A4A',
            created_by  INTEGER,
            created_at  TEXT DEFAULT (datetime('now','localtime'))
        );
        CREATE TABLE IF NOT EXISTS doc_types (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            name        TEXT NOT NULL,
            description TEXT DEFAULT '',
            created_by  INTEGER,
            created_at  TEXT DEFAULT (datetime('now','localtime'))
        );
        CREATE TABLE IF NOT EXISTS documents (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            title       TEXT NOT NULL,
            description TEXT DEFAULT '',
            file_path   TEXT NOT NULL,
            file_name   TEXT NOT NULL,
            file_type   TEXT NOT NULL,
            file_size   INTEGER DEFAULT 0,
            category_id INTEGER,
            tags        TEXT DEFAULT '',
            uploaded_by INTEGER NOT NULL,
            created_at  TEXT DEFAULT (datetime('now','localtime')),
            FOREIGN KEY(category_id) REFERENCES doc_categories(id),
            FOREIGN KEY(uploaded_by) REFERENCES users(id)
        );
        """)
        # Migrations
        cols = [r[1] for r in db.execute("PRAGMA table_info(users)").fetchall()]
        if 'can_upload_docs' not in cols:
            db.execute("ALTER TABLE users ADD COLUMN can_upload_docs INTEGER DEFAULT 0")
        doc_cols = [r[1] for r in db.execute("PRAGMA table_info(documents)").fetchall()]
        if 'notes' not in doc_cols:
            db.execute("ALTER TABLE documents ADD COLUMN notes TEXT DEFAULT ''")
        if 'doc_number' not in doc_cols:
            db.execute("ALTER TABLE documents ADD COLUMN doc_number TEXT DEFAULT ''")
        if 'issued_date' not in doc_cols:
            db.execute("ALTER TABLE documents ADD COLUMN issued_date TEXT DEFAULT NULL")
        if 'issuer' not in doc_cols:
            db.execute("ALTER TABLE documents ADD COLUMN issuer TEXT DEFAULT ''")
        if 'doc_type_id' not in doc_cols:
            db.execute("ALTER TABLE documents ADD COLUMN doc_type_id INTEGER DEFAULT NULL")
        cat_cols = [r[1] for r in db.execute("PRAGMA table_info(doc_categories)").fetchall()]
        if 'parent_id' not in cat_cols:
            db.execute("ALTER TABLE doc_categories ADD COLUMN parent_id INTEGER DEFAULT NULL")
        row = db.execute("SELECT id FROM users WHERE username='admin'").fetchone()
        if not row:
            pwd = hash_password('admin123')
            db.execute(
                "INSERT INTO users (username,password,full_name,role) VALUES (?,?,?,?)",
                ('admin', pwd, 'Quan ly', 'manager')
            )
        db.commit()


def compress_image(file_bytes, ext):
    if not PIL_AVAILABLE:
        return file_bytes, ext
    try:
        img = PilImage.open(io.BytesIO(file_bytes))
        if img.mode in ('RGBA', 'P', 'LA'):
            bg = PilImage.new('RGB', img.size, (255, 255, 255))
            if img.mode == 'P':
                img = img.convert('RGBA')
            bg.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
            img = bg
        elif img.mode != 'RGB':
            img = img.convert('RGB')
        max_px = 1920
        w, h = img.size
        if w > max_px or h > max_px:
            ratio = min(max_px / w, max_px / h)
            img = img.resize((int(w * ratio), int(h * ratio)), PilImage.LANCZOS)
        out = io.BytesIO()
        img.save(out, format='JPEG', quality=75, optimize=True)
        return out.getvalue(), '.jpg'
    except Exception:
        return file_bytes, ext


def hash_password(pw):
    salt = 'chamcong_salt_2024'
    return hashlib.sha256((salt + pw).encode('utf-8')).hexdigest()


def check_password(pw, hashed):
    return hash_password(pw) == hashed


def rows_to_list(rows):
    return [dict(r) for r in rows]


def generate_temp_password():
    import random, string
    chars = string.ascii_letters + string.digits
    return ''.join(random.choices(chars, k=8))


# --- SESSION ---

def create_session(user_id, role, full_name):
    token = str(uuid.uuid4())
    with SESSION_LOCK:
        SESSIONS[token] = {'userId': user_id, 'role': role, 'fullName': full_name}
    return token


def get_session(token):
    if not token:
        return None
    with SESSION_LOCK:
        return SESSIONS.get(token)


def delete_session(token):
    with SESSION_LOCK:
        SESSIONS.pop(token, None)


def parse_cookie(cookie_str):
    cookies = {}
    if not cookie_str:
        return cookies
    for part in cookie_str.split(';'):
        if '=' in part:
            k, v = part.strip().split('=', 1)
            cookies[k.strip()] = v.strip()
    return cookies


# --- MULTIPART PARSER ---

def parse_multipart(content_type, body):
    boundary = None
    for part in content_type.split(';'):
        part = part.strip()
        if part.startswith('boundary='):
            boundary = part[9:].strip().encode('latin-1')
            break
    if not boundary:
        return {}, {}

    fields = {}
    files  = {}
    delimiter = b'--' + boundary
    raw_parts = body.split(delimiter)

    for raw in raw_parts:
        if raw in (b'', b'--\r\n', b'--', b'\r\n'):
            continue
        if raw.startswith(b'--'):
            continue
        if raw.startswith(b'\r\n'):
            raw = raw[2:]
        if b'\r\n\r\n' not in raw:
            continue

        header_block, _, body_part = raw.partition(b'\r\n\r\n')
        if body_part.endswith(b'\r\n'):
            body_part = body_part[:-2]

        headers = {}
        for line in header_block.decode('utf-8', errors='replace').split('\r\n'):
            if ':' in line:
                k, _, v = line.partition(':')
                headers[k.strip().lower()] = v.strip()

        disposition = headers.get('content-disposition', '')
        name     = None
        filename = None
        for seg in disposition.split(';'):
            seg = seg.strip()
            if seg.startswith('name='):
                name = seg[5:].strip('"')
            elif seg.startswith('filename='):
                filename = seg[9:].strip('"')

        if name is None:
            continue

        if filename:
            class FileItem:
                pass
            fi = FileItem()
            fi.filename = filename
            fi.file = io.BytesIO(body_part)
            fi.content_type = headers.get('content-type', 'application/octet-stream')
            files[name] = fi
        else:
            fields[name] = body_part.decode('utf-8', errors='replace')

    return fields, files


# --- HTTP HANDLER ---

class Handler(http.server.BaseHTTPRequestHandler):

    def log_message(self, fmt, *args):
        pass

    def get_token(self):
        cookies = parse_cookie(self.headers.get('Cookie', ''))
        return cookies.get('session_token')

    def get_session(self):
        return get_session(self.get_token())

    def require_auth(self):
        s = self.get_session()
        if not s:
            self.send_json({'error': 'Chua dang nhap'}, 401)
        return s

    def require_manager(self):
        s = self.get_session()
        if not s or s['role'] != 'manager':
            self.send_json({'error': 'Khong co quyen'}, 403)
            return None
        return s

    def send_json(self, data, code=200):
        body = json.dumps(data, ensure_ascii=False).encode('utf-8')
        self.send_response(code)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', len(body))
        self.end_headers()
        self.wfile.write(body)

    def send_file(self, path):
        try:
            with open(path, 'rb') as f:
                data = f.read()
            ct = mimetypes.guess_type(path)[0] or 'application/octet-stream'
            self.send_response(200)
            self.send_header('Content-Type', ct)
            self.send_header('Content-Length', len(data))
            self.end_headers()
            self.wfile.write(data)
        except FileNotFoundError:
            self.send_response(404)
            self.end_headers()

    def read_json(self):
        length = int(self.headers.get('Content-Length', 0))
        if length == 0:
            return {}
        return json.loads(self.rfile.read(length))

    def read_form(self):
        length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(length).decode('utf-8', errors='replace')
        raw = parse_qs(body, keep_blank_values=True)
        return {k: v[0] for k, v in raw.items()}

    def read_multipart(self):
        ct     = self.headers.get('Content-Type', '')
        length = int(self.headers.get('Content-Length', 0))
        body   = self.rfile.read(length)
        return parse_multipart(ct, body)

    def get_path_and_query(self):
        parsed = urlparse(self.path)
        return parsed.path, parse_qs(parsed.query)

    # Routing

    def do_GET(self):
        path, qs = self.get_path_and_query()

        if path.startswith('/uploads/'):
            fname = os.path.basename(path)
            fpath = os.path.join(UPLOADS_DIR, fname)
            self.send_file(fpath)
            return

        routes = {
            '/api/me':                   self.api_me,
            '/api/manager/users':        self.api_manager_users_list,
            '/api/notifications':        self.api_notifications_list,
            '/api/notifications/unread': self.api_notifications_unread_count,
        }
        if path in routes:
            routes[path]()
            return

        if path == '/api/overtime/my':
            self.api_overtime_my(qs); return
        if path == '/api/manager/overtime':
            self.api_manager_overtime_list(qs); return
        if path == '/api/manager/stats':
            self.api_manager_stats(qs); return
        if path == '/api/manager/export':
            self.api_manager_export(qs); return
        if path == '/api/manager/storage':
            self.api_manager_storage(); return
        if path == '/api/docs':
            self.api_docs_list(qs); return
        if path == '/api/docs/categories':
            self.api_doc_categories_list(); return
        if path == '/api/docs/types':
            self.api_doc_types_list(); return
        if path == '/api/docs/storage':
            self.api_docs_storage(); return
        m = re.match(r'^/api/docs/url/(\d+)$', path)
        if m:
            self.api_docs_presigned_url(int(m.group(1))); return
        if path == '/api/manager/doc-permissions':
            self.api_manager_doc_permissions(); return

        if path == '/docs':
            self.send_file(os.path.join(PUBLIC_DIR, 'docs.html'))
            return

        self.send_file(os.path.join(PUBLIC_DIR, 'index.html'))

    def do_POST(self):
        path, _ = self.get_path_and_query()
        routes = {
            '/api/login':                    self.api_login,
            '/api/logout':                   self.api_logout,
            '/api/change-password':          self.api_change_password,
            '/api/overtime':                 self.api_submit_overtime,
            '/api/manager/users':            self.api_manager_create_user,
            '/api/notifications/read-all':   self.api_notifications_read_all,
            '/api/docs/upload':              self.api_docs_upload,
            '/api/docs/categories':          self.api_doc_categories_create,
            '/api/docs/types':               self.api_doc_types_create,
        }
        if path in routes:
            routes[path]()
        else:
            self.send_json({'error': 'Not found'}, 404)

    def do_PUT(self):
        path, _ = self.get_path_and_query()
        m = re.match(r'^/api/overtime/(\d+)$', path)
        if m:
            self.api_overtime_edit(int(m.group(1))); return
        m = re.match(r'^/api/manager/overtime/(\d+)$', path)
        if m:
            self.api_manager_review_overtime(int(m.group(1))); return
        m = re.match(r'^/api/manager/overtime/(\d+)/cancel$', path)
        if m:
            self.api_manager_cancel_overtime(int(m.group(1))); return
        m = re.match(r'^/api/manager/users/(\d+)$', path)
        if m:
            self.api_manager_update_user(int(m.group(1))); return
        m = re.match(r'^/api/manager/users/(\d+)/reset-password$', path)
        if m:
            self.api_manager_reset_password(int(m.group(1))); return
        m = re.match(r'^/api/notifications/(\d+)/read$', path)
        if m:
            self.api_notification_mark_read(int(m.group(1))); return
        m = re.match(r'^/api/docs/(\d+)$', path)
        if m:
            self.api_docs_update(int(m.group(1))); return
        m = re.match(r'^/api/docs/categories/(\d+)$', path)
        if m:
            self.api_doc_categories_update(int(m.group(1))); return
        m = re.match(r'^/api/docs/types/(\d+)$', path)
        if m:
            self.api_doc_types_update(int(m.group(1))); return
        m = re.match(r'^/api/manager/doc-permissions/(\d+)$', path)
        if m:
            self.api_manager_doc_permission_set(int(m.group(1))); return
        self.send_json({'error': 'Not found'}, 404)

    def do_DELETE(self):
        path, _ = self.get_path_and_query()
        m = re.match(r'^/api/overtime/(\d+)$', path)
        if m:
            self.api_overtime_delete(int(m.group(1))); return
        m = re.match(r'^/api/manager/users/(\d+)$', path)
        if m:
            self.api_manager_delete_user(int(m.group(1))); return
        if path == '/api/manager/data/cleanup':
            self.api_manager_cleanup_data(); return
        if path == '/api/manager/data/reset-all':
            self.api_manager_reset_all(); return
        m = re.match(r'^/api/docs/(\d+)$', path)
        if m:
            self.api_docs_delete(int(m.group(1))); return
        m = re.match(r'^/api/docs/categories/(\d+)$', path)
        if m:
            self.api_doc_categories_delete(int(m.group(1))); return
        m = re.match(r'^/api/docs/types/(\d+)$', path)
        if m:
            self.api_doc_types_delete(int(m.group(1))); return
        self.send_json({'error': 'Not found'}, 404)

    def do_PATCH(self):
        path, _ = self.get_path_and_query()
        m = re.match(r'^/api/docs/categories/(\d+)/parent$', path)
        if m:
            self.api_doc_categories_reparent(int(m.group(1))); return
        self.send_json({'error': 'Not found'}, 404)

    def api_doc_categories_reparent(self, cat_id):
        sess = self.require_manager()
        if not sess: return
        body = self.read_json()
        raw = body.get('parent_id')
        parent_id = int(raw) if raw else None
        if parent_id == cat_id:
            self.send_json({'error': 'Khong the dat chinh no lam cha'}, 400); return
        with get_db() as db:
            if parent_id:
                # Prevent circular: parent_id must not be a child of cat_id
                child = db.execute('SELECT id FROM doc_categories WHERE parent_id=?', (cat_id,)).fetchall()
                if any(r[0] == parent_id for r in child):
                    self.send_json({'error': 'Khong the tao vong lap danh muc'}, 400); return
                # Enforce max 2 levels: target must be a root (no parent itself)
                target = db.execute('SELECT parent_id FROM doc_categories WHERE id=?', (parent_id,)).fetchone()
                if target and target[0]:
                    self.send_json({'error': 'Chi ho tro 2 cap danh muc'}, 400); return
            db.execute('UPDATE doc_categories SET parent_id=? WHERE id=?', (parent_id, cat_id))
            db.commit()
        self.send_json({'ok': True})

    # --- AUTH ---

    def api_login(self):
        ct = self.headers.get('Content-Type', '')
        body = self.read_json() if 'application/json' in ct else self.read_form()
        username = body.get('username', '').strip()
        password = body.get('password', '')
        with get_db() as db:
            row = db.execute('SELECT * FROM users WHERE username=?', (username,)).fetchone()
        if not row or not check_password(password, row['password']):
            self.send_json({'error': 'Sai tai khoan hoac mat khau'}, 401)
            return
        token = create_session(row['id'], row['role'], row['full_name'])
        data  = {
            'id': row['id'], 'username': row['username'],
            'full_name': row['full_name'], 'role': row['role']
        }
        body_bytes = json.dumps(data, ensure_ascii=False).encode('utf-8')
        self.send_response(200)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', len(body_bytes))
        self.send_header('Set-Cookie',
            f'session_token={token}; Path=/; HttpOnly; Max-Age=28800')
        self.end_headers()
        self.wfile.write(body_bytes)

    def api_logout(self):
        token = self.get_token()
        if token:
            delete_session(token)
        body_bytes = b'{"ok":true}'
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', len(body_bytes))
        self.send_header('Set-Cookie', 'session_token=; Path=/; Max-Age=0')
        self.end_headers()
        self.wfile.write(body_bytes)

    def api_me(self):
        sess = self.require_auth()
        if not sess:
            return
        with get_db() as db:
            row = db.execute(
                'SELECT id,username,full_name,role,department FROM users WHERE id=?',
                (sess['userId'],)
            ).fetchone()
        if not row:
            self.send_json({'error': 'Not found'}, 404)
            return
        self.send_json(dict(row))

    def api_change_password(self):
        sess = self.require_auth()
        if not sess:
            return
        body   = self.read_json()
        old_pw = body.get('old_password', '')
        new_pw = body.get('new_password', '')
        with get_db() as db:
            row = db.execute('SELECT password FROM users WHERE id=?',
                             (sess['userId'],)).fetchone()
            if not check_password(old_pw, row['password']):
                self.send_json({'error': 'Mat khau cu khong dung'}, 400)
                return
            if len(new_pw) < 6:
                self.send_json({'error': 'Mat khau moi it nhat 6 ky tu'}, 400)
                return
            db.execute('UPDATE users SET password=? WHERE id=?',
                       (hash_password(new_pw), sess['userId']))
            db.commit()
        self.send_json({'ok': True})

    # --- EMPLOYEE OVERTIME ---

    def api_submit_overtime(self):
        sess = self.require_auth()
        if not sess:
            return
        ct = self.headers.get('Content-Type', '')
        if 'multipart/form-data' in ct:
            fields, files = self.read_multipart()
        else:
            fields = self.read_form()
            files  = {}

        req_date   = fields.get('request_date', '').strip()
        start_time = fields.get('start_time', '').strip()
        end_time   = fields.get('end_time', '').strip()
        reason     = fields.get('reason', '').strip()

        if not all([req_date, start_time, end_time, reason]):
            self.send_json({'error': 'Vui long dien day du thong tin'}, 400)
            return

        try:
            from datetime import date as dclass
            y, mo, d = map(int, req_date.split('-'))
            dow = dclass(y, mo, d).weekday()
        except Exception:
            self.send_json({'error': 'Ngay khong hop le'}, 400)
            return

        if dow <= 4:
            ot_type = 'weekday'; min_start = (17,30); max_end = (23,0)
            rule_msg = 'OT ngay thuong chi duoc tu 17:30 den 23:00'
        elif dow == 5:
            ot_type = 'weekend'; min_start = (13,30); max_end = (23,0)
            rule_msg = 'OT thu 7 chi duoc tu 13:30 den 23:00'
        else:
            ot_type = 'weekend'; min_start = (8,0); max_end = (23,0)
            rule_msg = 'OT chu nhat chi duoc tu 08:00 den 23:00'

        try:
            sh, sm = map(int, start_time.split(':'))
            eh, em = map(int, end_time.split(':'))
        except Exception:
            self.send_json({'error': 'Gio khong hop le'}, 400)
            return

        start_min = sh*60+sm
        end_min   = eh*60+em
        min_start_min = min_start[0]*60+min_start[1]
        max_end_min   = max_end[0]*60+max_end[1]

        if start_min < min_start_min or end_min > max_end_min:
            self.send_json({'error': rule_msg}, 400)
            return
        if end_min <= start_min:
            self.send_json({'error': 'Gio ket thuc phai sau gio bat dau'}, 400)
            return

        now = datetime.now(VN_TZ).replace(tzinfo=None)
        today_str = now.strftime('%Y-%m-%d')
        if req_date == today_str:
            now_min = now.hour*60+now.minute
            now_hm  = now.strftime('%H:%M')
            if end_min > now_min:
                self.send_json({'error': 'Gio ket thuc (' + end_time + ') vuot qua thoi diem hien tai (' + now_hm + ')'}, 400)
                return
            if start_min >= now_min:
                self.send_json({'error': 'Gio bat dau (' + start_time + ') chua den gio hien tai (' + now_hm + ')'}, 400)
                return

        raw_minutes = end_min - start_min
        deduct_min  = 0
        if dow == 6:
            lunch_s = 720; lunch_e = 810
            overlap = max(0, min(end_min, lunch_e) - max(start_min, lunch_s))
            deduct_min = overlap

        hours = (raw_minutes - deduct_min) / 60.0
        if hours <= 0:
            self.send_json({'error': 'Tong gio OT sau khi tru nghi trua phai lon hon 0'}, 400)
            return

        image_path = None
        if 'image' in files:
            fitem = files['image']
            ext   = os.path.splitext(fitem.filename)[1].lower()
            if ext not in ('.jpg', '.jpeg', '.png', '.gif', '.webp', '.pdf'):
                self.send_json({'error': 'Dinh dang file khong ho tro'}, 400)
                return
            file_bytes = fitem.file.read()
            if ext != '.pdf':
                file_bytes, ext = compress_image(file_bytes, ext)
            fname = f"{int(datetime.now().timestamp()*1000)}_{sess['userId']}{ext}"
            fpath = os.path.join(UPLOADS_DIR, fname)
            with open(fpath, 'wb') as f:
                f.write(file_bytes)
            image_path = f'/uploads/{fname}'

        with get_db() as db:
            db.execute(
                """INSERT INTO overtime_requests
                   (user_id, request_date, ot_type, start_time, end_time,
                    hours, reason, image_path)
                   VALUES (?,?,?,?,?,?,?,?)""",
                (sess['userId'], req_date, ot_type, start_time,
                 end_time, hours, reason, image_path)
            )
            db.commit()
        self.send_json({'ok': True})

    def api_overtime_delete(self, ot_id):
        sess = self.require_auth()
        if not sess:
            return
        with get_db() as db:
            row = db.execute(
                'SELECT * FROM overtime_requests WHERE id=? AND user_id=?',
                (ot_id, sess['userId'])
            ).fetchone()
            if not row:
                self.send_json({'error': 'Khong tim thay khai bao'}, 404)
                return
            if row['status'] != 'pending':
                self.send_json({'error': 'Yeu cau huy Khai bao cua ban khong the thuc hien do Admin da phe duyet Khai bao nay'}, 400)
                return
            if row['image_path']:
                try:
                    fpath = os.path.join(DATA_DIR, row['image_path'].lstrip('/'))
                    if os.path.exists(fpath):
                        os.remove(fpath)
                except Exception:
                    pass
            db.execute('DELETE FROM overtime_requests WHERE id=?', (ot_id,))
            db.execute('DELETE FROM notifications WHERE ot_id=?', (ot_id,))
            db.commit()
        self.send_json({'ok': True})

    def api_overtime_edit(self, ot_id):
        sess = self.require_auth()
        if not sess:
            return
        with get_db() as db:
            row = db.execute(
                'SELECT * FROM overtime_requests WHERE id=? AND user_id=?',
                (ot_id, sess['userId'])
            ).fetchone()
            if not row:
                self.send_json({'error': 'Khong tim thay khai bao'}, 404)
                return
            if row['status'] != 'pending':
                self.send_json({'error': 'Yeu cau chinh sua Khai bao cua ban khong the thuc hien do Admin da phe duyet Khai bao nay'}, 400)
                return

        ct = self.headers.get('Content-Type', '')
        if 'multipart/form-data' in ct:
            fields, files = self.read_multipart()
        else:
            fields = self.read_form()
            files  = {}

        req_date   = fields.get('request_date', '').strip()
        start_time = fields.get('start_time', '').strip()
        end_time   = fields.get('end_time', '').strip()
        reason     = fields.get('reason', '').strip()

        if not all([req_date, start_time, end_time, reason]):
            self.send_json({'error': 'Vui long dien day du thong tin'}, 400)
            return

        try:
            from datetime import date as dclass
            y, mo, d = map(int, req_date.split('-'))
            dow = dclass(y, mo, d).weekday()
        except Exception:
            self.send_json({'error': 'Ngay khong hop le'}, 400)
            return

        if dow <= 4:
            ot_type = 'weekday'; min_start = (17,30); max_end = (23,0)
            rule_msg = 'OT ngay thuong chi duoc tu 17:30 den 23:00'
        elif dow == 5:
            ot_type = 'weekend'; min_start = (13,30); max_end = (23,0)
            rule_msg = 'OT thu 7 chi duoc tu 13:30 den 23:00'
        else:
            ot_type = 'weekend'; min_start = (8,0); max_end = (23,0)
            rule_msg = 'OT chu nhat chi duoc tu 08:00 den 23:00'

        try:
            sh, sm = map(int, start_time.split(':'))
            eh, em = map(int, end_time.split(':'))
        except Exception:
            self.send_json({'error': 'Gio khong hop le'}, 400)
            return

        start_min = sh*60+sm; end_min = eh*60+em
        min_start_min = min_start[0]*60+min_start[1]
        max_end_min   = max_end[0]*60+max_end[1]

        if start_min < min_start_min or end_min > max_end_min:
            self.send_json({'error': rule_msg}, 400); return
        if end_min <= start_min:
            self.send_json({'error': 'Gio ket thuc phai sau gio bat dau'}, 400); return

        now = datetime.now(VN_TZ).replace(tzinfo=None)
        today_str = now.strftime('%Y-%m-%d')
        if req_date == today_str:
            now_min = now.hour*60+now.minute
            now_hm  = now.strftime('%H:%M')
            if end_min > now_min:
                self.send_json({'error': 'Gio ket thuc (' + end_time + ') vuot qua thoi diem hien tai (' + now_hm + ')'}, 400); return
            if start_min >= now_min:
                self.send_json({'error': 'Gio bat dau (' + start_time + ') chua den gio hien tai (' + now_hm + ')'}, 400); return

        raw_minutes = end_min - start_min
        deduct_min = 0
        if dow == 6:
            lunch_s = 720; lunch_e = 810
            deduct_min = max(0, min(end_min, lunch_e) - max(start_min, lunch_s))
        hours = (raw_minutes - deduct_min) / 60.0
        if hours <= 0:
            self.send_json({'error': 'Tong gio OT phai lon hon 0'}, 400); return

        image_path = row['image_path']
        if 'image' in files:
            fitem = files['image']
            ext = os.path.splitext(fitem.filename)[1].lower()
            if ext not in ('.jpg','.jpeg','.png','.gif','.webp','.pdf'):
                self.send_json({'error': 'Dinh dang file khong ho tro'}, 400); return
            file_bytes = fitem.file.read()
            if ext != '.pdf':
                file_bytes, ext = compress_image(file_bytes, ext)
            fname = str(int(datetime.now().timestamp()*1000)) + '_' + str(sess['userId']) + ext
            fpath = os.path.join(UPLOADS_DIR, fname)
            with open(fpath, 'wb') as f:
                f.write(file_bytes)
            if row['image_path']:
                try:
                    old = os.path.join(DATA_DIR, row['image_path'].lstrip('/'))
                    if os.path.exists(old):
                        os.remove(old)
                except Exception:
                    pass
            image_path = '/uploads/' + fname

        with get_db() as db:
            db.execute(
                """UPDATE overtime_requests
                   SET request_date=?, ot_type=?, start_time=?, end_time=?,
                       hours=?, reason=?, image_path=?
                   WHERE id=? AND user_id=? AND status='pending'""",
                (req_date, ot_type, start_time, end_time,
                 hours, reason, image_path, ot_id, sess['userId'])
            )
            db.commit()
        self.send_json({'ok': True})

    def api_overtime_my(self, qs):
        sess = self.require_auth()
        if not sess:
            return
        month  = qs.get('month', [None])[0]
        year   = qs.get('year',  [None])[0]
        sql    = """SELECT r.*, u.full_name, u.department
                    FROM overtime_requests r
                    JOIN users u ON r.user_id = u.id
                    WHERE r.user_id = ?"""
        params = [sess['userId']]
        if month and year:
            sql += " AND strftime('%Y-%m', r.request_date) = ?"
            params.append(f"{year}-{month.zfill(2)}")
        sql += ' ORDER BY r.request_date DESC, r.created_at DESC'
        with get_db() as db:
            rows = db.execute(sql, params).fetchall()
        self.send_json(rows_to_list(rows))

    # --- NOTIFICATIONS ---

    def api_notifications_list(self):
        sess = self.require_auth()
        if not sess:
            return
        with get_db() as db:
            rows = db.execute(
                """SELECT n.*, r.request_date, r.start_time, r.end_time, r.ot_type
                   FROM notifications n
                   JOIN overtime_requests r ON n.ot_id = r.id
                   WHERE n.user_id = ?
                   ORDER BY n.created_at DESC
                   LIMIT 50""",
                (sess['userId'],)
            ).fetchall()
        self.send_json(rows_to_list(rows))

    def api_notifications_unread_count(self):
        sess = self.require_auth()
        if not sess:
            return
        with get_db() as db:
            row = db.execute(
                'SELECT COUNT(*) as cnt FROM notifications WHERE user_id=? AND is_read=0',
                (sess['userId'],)
            ).fetchone()
        self.send_json({'count': row['cnt']})

    def api_notification_mark_read(self, notif_id):
        sess = self.require_auth()
        if not sess:
            return
        with get_db() as db:
            db.execute(
                'UPDATE notifications SET is_read=1 WHERE id=? AND user_id=?',
                (notif_id, sess['userId'])
            )
            db.commit()
        self.send_json({'ok': True})

    def api_notifications_read_all(self):
        sess = self.require_auth()
        if not sess:
            return
        with get_db() as db:
            db.execute(
                'UPDATE notifications SET is_read=1 WHERE user_id=?',
                (sess['userId'],)
            )
            db.commit()
        self.send_json({'ok': True})

    # --- MANAGER ---

    def api_manager_overtime_list(self, qs):
        sess = self.require_manager()
        if not sess:
            return
        status  = qs.get('status',  [None])[0]
        month   = qs.get('month',   [None])[0]
        year    = qs.get('year',    [None])[0]
        user_id = qs.get('user_id', [None])[0]
        sql     = """SELECT r.*, u.full_name, u.department
                     FROM overtime_requests r
                     JOIN users u ON r.user_id = u.id
                     WHERE 1=1"""
        params  = []
        if status:
            sql += ' AND r.status = ?'
            params.append(status)
        if month and year:
            sql += " AND strftime('%Y-%m', r.request_date) = ?"
            params.append(f"{year}-{month.zfill(2)}")
        if user_id:
            sql += ' AND r.user_id = ?'
            params.append(int(user_id))
        sql += ' ORDER BY r.created_at DESC'
        with get_db() as db:
            rows = db.execute(sql, params).fetchall()
        self.send_json(rows_to_list(rows))

    def api_manager_review_overtime(self, ot_id):
        sess = self.require_manager()
        if not sess:
            return
        body   = self.read_json()
        status = body.get('status', '')
        note   = body.get('manager_note', '')
        if status not in ('approved', 'rejected'):
            self.send_json({'error': 'Trang thai khong hop le'}, 400)
            return
        now = datetime.now(VN_TZ).strftime('%Y-%m-%d %H:%M:%S')
        with get_db() as db:
            db.execute(
                """UPDATE overtime_requests
                   SET status=?, manager_note=?, reviewed_by=?, reviewed_at=?
                   WHERE id=?""",
                (status, note, sess['userId'], now, ot_id)
            )
            db.commit()
        self.send_json({'ok': True})

    def api_manager_cancel_overtime(self, ot_id):
        sess = self.require_manager()
        if not sess:
            return
        body   = self.read_json()
        reason = body.get('cancel_reason', '').strip()
        now    = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        with get_db() as db:
            row = db.execute(
                'SELECT * FROM overtime_requests WHERE id=?', (ot_id,)
            ).fetchone()
            if not row:
                self.send_json({'error': 'Khong tim thay yeu cau'}, 404)
                return
            if row['status'] != 'approved':
                self.send_json({'error': 'Chi huy duoc yeu cau da duyet'}, 400)
                return
            db.execute(
                """UPDATE overtime_requests
                   SET status='cancelled', manager_note=?, reviewed_by=?, reviewed_at=?
                   WHERE id=?""",
                (reason, sess['userId'], now, ot_id)
            )
            ot_date  = row['request_date']
            st_time  = row['start_time']
            en_time  = row['end_time']
            title    = 'Yeu cau OT bi huy'
            msg_body = (
                f"Yeu cau OT ngay {ot_date} ({st_time}-{en_time}) "
                f"da duoc duyet truoc do vua bi HUY boi quan ly."
            )
            if reason:
                msg_body += f" Ly do: {reason}"
            db.execute(
                'INSERT INTO notifications (user_id, ot_id, title, message) VALUES (?,?,?,?)',
                (row['user_id'], ot_id, title, msg_body)
            )
            db.commit()
        self.send_json({'ok': True})

    def api_manager_users_list(self):
        sess = self.require_manager()
        if not sess:
            return
        with get_db() as db:
            rows = db.execute(
                'SELECT id,username,full_name,role,department,created_at FROM users ORDER BY full_name'
            ).fetchall()
        self.send_json(rows_to_list(rows))

    def api_manager_create_user(self):
        sess = self.require_manager()
        if not sess:
            return
        body      = self.read_json()
        username  = body.get('username', '').strip()
        password  = body.get('password', '')
        full_name = body.get('full_name', '').strip()
        role      = body.get('role', 'employee')
        dept      = body.get('department', '')
        if not username or not password or not full_name:
            self.send_json({'error': 'Thieu thong tin bat buoc'}, 400)
            return
        try:
            with get_db() as db:
                db.execute(
                    'INSERT INTO users (username,password,full_name,role,department) VALUES (?,?,?,?,?)',
                    (username, hash_password(password), full_name, role, dept)
                )
                db.commit()
            self.send_json({'ok': True})
        except sqlite3.IntegrityError:
            self.send_json({'error': 'Ten dang nhap da ton tai'}, 400)

    def api_manager_update_user(self, uid):
        sess = self.require_manager()
        if not sess:
            return
        body      = self.read_json()
        full_name = body.get('full_name', '').strip()
        role      = body.get('role', 'employee')
        dept      = body.get('department', '')
        password  = body.get('password')
        with get_db() as db:
            if password:
                db.execute(
                    'UPDATE users SET full_name=?,role=?,department=?,password=? WHERE id=?',
                    (full_name, role, dept, hash_password(password), uid)
                )
            else:
                db.execute(
                    'UPDATE users SET full_name=?,role=?,department=? WHERE id=?',
                    (full_name, role, dept, uid)
                )
            db.commit()
        self.send_json({'ok': True})

    def api_manager_delete_user(self, uid):
        sess = self.require_manager()
        if not sess:
            return
        if uid == sess['userId']:
            self.send_json({'error': 'Khong the xoa chinh minh'}, 400)
            return
        with get_db() as db:
            db.execute('DELETE FROM users WHERE id=?', (uid,))
            db.commit()
        self.send_json({'ok': True})

    def api_manager_stats(self, qs):
        sess = self.require_manager()
        if not sess:
            return
        month  = qs.get('month', [None])[0]
        year   = qs.get('year',  [None])[0]
        date_filter = ''
        params = []
        if month and year:
            date_filter = "AND strftime('%Y-%m', r.request_date) = ?"
            params.append(f"{year}-{month.zfill(2)}")
        sql = f"""
            SELECT
                u.id, u.full_name, u.department,
                COUNT(CASE WHEN r.status='approved' THEN 1 END) as approved_count,
                COALESCE(SUM(CASE WHEN r.status='approved' THEN r.hours ELSE 0 END), 0) as total_hours,
                COALESCE(SUM(CASE WHEN r.status='approved' AND r.ot_type='weekday' THEN r.hours ELSE 0 END), 0) as weekday_hours,
                COALESCE(SUM(CASE WHEN r.status='approved' AND r.ot_type='weekend' THEN r.hours ELSE 0 END), 0) as weekend_hours,
                COUNT(CASE WHEN r.status='pending' THEN 1 END) as pending_count
            FROM users u
            LEFT JOIN overtime_requests r ON u.id = r.user_id {date_filter}
            WHERE u.role = 'employee'
            GROUP BY u.id
            ORDER BY u.full_name
        """
        with get_db() as db:
            rows = db.execute(sql, params).fetchall()
        self.send_json(rows_to_list(rows))

    def api_manager_export(self, qs):
        sess = self.require_manager()
        if not sess:
            return
        month = qs.get('month', [None])[0]
        year  = qs.get('year',  [None])[0]
        sql = """SELECT r.id, u.full_name, u.department,
                        r.request_date, r.ot_type,
                        r.start_time, r.end_time, r.hours,
                        r.reason, r.status, r.manager_note, r.created_at
                 FROM overtime_requests r
                 JOIN users u ON r.user_id = u.id
                 WHERE 1=1"""
        params = []
        if month and year:
            sql += " AND strftime('%Y-%m', r.request_date) = ?"
            params.append(f"{year}-{month.zfill(2)}")
        sql += ' ORDER BY r.request_date DESC, u.full_name'
        with get_db() as db:
            rows = db.execute(sql, params).fetchall()

        label_month = f'T{month}_{year}' if month and year else 'tat_ca'

        if OPENPYXL_AVAILABLE:
            wb = openpyxl.Workbook()
            ws = wb.active
            ws.title = 'Cham Cong OT'

            hdr_fill  = PatternFill('solid', fgColor='2563EB')
            hdr_font  = Font(bold=True, color='FFFFFF')
            hdr_align = Alignment(horizontal='center', vertical='center', wrap_text=True)

            headers = ['STT','Ho ten','Bo phan','Ngay OT','Loai OT',
                       'Gio bat dau','Gio ket thuc','So gio',
                       'Ly do','Trang thai','Ghi chu QT','Ngay gui']
            col_widths = [5, 22, 16, 13, 14, 13, 13, 9, 40, 14, 30, 18]

            for ci, (h, w) in enumerate(zip(headers, col_widths), 1):
                cell = ws.cell(row=1, column=ci, value=h)
                cell.fill = hdr_fill
                cell.font = hdr_font
                cell.alignment = hdr_align
                ws.column_dimensions[openpyxl.utils.get_column_letter(ci)].width = w
            ws.row_dimensions[1].height = 30
            ws.freeze_panes = 'A2'

            status_map = {
                'pending':   'Cho duyet',
                'approved':  'Da duyet',
                'rejected':  'Tu choi',
                'cancelled': 'Da huy',
            }
            status_colors = {
                'pending':   'FEF3C7',
                'approved':  'DCFCE7',
                'rejected':  'FEE2E2',
                'cancelled': 'F1F5F9',
            }

            for i, r in enumerate(rows, 1):
                ot_label = 'Ngay thuong' if r['ot_type'] == 'weekday' else 'Cuoi tuan/Le'
                status   = r['status']
                values   = [
                    i, r['full_name'], r['department'] or '',
                    r['request_date'], ot_label,
                    r['start_time'], r['end_time'],
                    round(r['hours'] or 0, 2),
                    r['reason'], status_map.get(status, status),
                    r['manager_note'] or '', r['created_at']
                ]
                fill = PatternFill('solid', fgColor=status_colors.get(status, 'FFFFFF')) if status in status_colors else None
                for ci, v in enumerate(values, 1):
                    cell = ws.cell(row=i+1, column=ci, value=v)
                    cell.alignment = Alignment(vertical='top', wrap_text=(ci == 9))
                    if fill and ci == 10:
                        cell.fill = fill

            total_row = len(rows) + 3
            ws.cell(row=total_row, column=1, value='Tong cong').font = Font(bold=True)
            approved_hours = sum(r['hours'] or 0 for r in rows if r['status'] == 'approved')
            ws.cell(row=total_row, column=8, value=round(approved_hours, 2)).font = Font(bold=True)
            ws.cell(row=total_row, column=9, value=f"Tong gio OT da duyet: {approved_hours:.1f}h").font = Font(bold=True)

            buf = io.BytesIO()
            wb.save(buf)
            data = buf.getvalue()
            fname = f'cham_cong_OT_{label_month}.xlsx'
            ct = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        else:
            import csv
            buf = io.StringIO()
            w = csv.writer(buf)
            w.writerow(['STT','Ho ten','Bo phan','Ngay OT','Loai OT',
                        'Gio bat dau','Gio ket thuc','So gio',
                        'Ly do','Trang thai','Ghi chu QT','Ngay gui'])
            for i, r in enumerate(rows, 1):
                w.writerow([i, r['full_name'], r['department'] or '',
                             r['request_date'],
                             'Ngay thuong' if r['ot_type']=='weekday' else 'Cuoi tuan',
                             r['start_time'], r['end_time'], r['hours'] or 0,
                             r['reason'], r['status'], r['manager_note'] or '', r['created_at']])
            data = buf.getvalue().encode('utf-8-sig')
            fname = f'cham_cong_OT_{label_month}.csv'
            ct = 'text/csv; charset=utf-8'

        self.send_response(200)
        self.send_header('Content-Type', ct)
        self.send_header('Content-Length', len(data))
        self.send_header('Content-Disposition', f'attachment; filename="{fname}"')
        self.end_headers()
        self.wfile.write(data)

    def api_manager_reset_password(self, uid):
        sess = self.require_manager()
        if not sess:
            return
        with get_db() as db:
            row = db.execute('SELECT id, full_name FROM users WHERE id=?', (uid,)).fetchone()
            if not row:
                self.send_json({'error': 'Khong tim thay tai khoan'}, 404)
                return
            new_pw = generate_temp_password()
            db.execute('UPDATE users SET password=? WHERE id=?',
                       (hash_password(new_pw), uid))
            db.commit()
        self.send_json({'ok': True, 'new_password': new_pw, 'full_name': row['full_name']})

    def api_manager_cleanup_data(self):
        sess = self.require_manager()
        if not sess:
            return
        body = self.read_json()
        before_month = body.get('before_month', '')
        if not before_month:
            self.send_json({'error': 'Thieu truong before_month'}, 400)
            return
        with get_db() as db:
            rows = db.execute(
                "SELECT image_path FROM overtime_requests WHERE strftime('%Y-%m', request_date) < ?",
                (before_month,)
            ).fetchall()
            for r in rows:
                if r['image_path']:
                    try:
                        fpath = os.path.join(DATA_DIR, r['image_path'].lstrip('/'))
                        if os.path.exists(fpath):
                            os.remove(fpath)
                    except Exception:
                        pass
            db.execute(
                "DELETE FROM overtime_requests WHERE strftime('%Y-%m', request_date) < ?",
                (before_month,)
            )
            db.execute(
                "DELETE FROM notifications WHERE ot_id NOT IN (SELECT id FROM overtime_requests)"
            )
            db.execute('VACUUM')
            db.commit()
        self.send_json({'ok': True})

    def api_manager_reset_all(self):
        sess = self.require_manager()
        if not sess:
            return
        body = self.read_json()
        if body.get('confirm') != 'XAC_NHAN_XOA_HET':
            self.send_json({'error': 'Xac nhan khong dung'}, 400)
            return
        for fname in os.listdir(UPLOADS_DIR):
            try:
                os.remove(os.path.join(UPLOADS_DIR, fname))
            except Exception:
                pass
        with get_db() as db:
            db.execute('DELETE FROM overtime_requests')
            db.execute('DELETE FROM notifications')
            db.execute('DELETE FROM users WHERE role != ?', ('manager',))
            db.execute('VACUUM')
            db.commit()
        self.send_json({'ok': True})

    def api_manager_storage(self):
        sess = self.require_manager()
        if not sess:
            return
        try:
            db_size = os.path.getsize(DB_PATH) if os.path.exists(DB_PATH) else 0
            uploads_size = sum(
                os.path.getsize(os.path.join(UPLOADS_DIR, f))
                for f in os.listdir(UPLOADS_DIR)
                if os.path.isfile(os.path.join(UPLOADS_DIR, f))
            ) if os.path.exists(UPLOADS_DIR) else 0
            total_bytes = db_size + uploads_size
            used_mb  = round(total_bytes / (1024*1024), 1)
            limit_mb = 500
            percent  = round(used_mb / limit_mb * 100, 1)
            self.send_json({
                'used_mb': used_mb,
                'limit_mb': limit_mb,
                'percent': percent,
                'is_warning': used_mb >= 410,
                'is_danger':  used_mb >= 480,
            })
        except Exception as e:
            self.send_json({'error': str(e)}, 500)

    # --- DOCUMENTS ---

    def can_upload_docs(self, sess):
        """Kiem tra quyen upload tai lieu: manager hoac co_upload_docs=1"""
        if sess['role'] == 'manager':
            return True
        with get_db() as db:
            row = db.execute('SELECT can_upload_docs FROM users WHERE id=?', (sess['userId'],)).fetchone()
        return row and row['can_upload_docs'] == 1

    def api_doc_categories_list(self):
        sess = self.require_auth()
        if not sess: return
        with get_db() as db:
            rows = db.execute(
                'SELECT c.*, u.full_name as creator FROM doc_categories c LEFT JOIN users u ON c.created_by=u.id ORDER BY c.name'
            ).fetchall()
        self.send_json(rows_to_list(rows))

    def api_doc_categories_create(self):
        sess = self.require_manager()
        if not sess: return
        body = self.read_json()
        name      = body.get('name', '').strip()
        desc      = body.get('description', '').strip()
        color     = body.get('color', '#1B2A4A').strip()
        parent_id = body.get('parent_id') or None
        if parent_id: parent_id = int(parent_id)
        if not name:
            self.send_json({'error': 'Ten danh muc khong duoc de trong'}, 400); return
        with get_db() as db:
            cur = db.execute(
                'INSERT INTO doc_categories (name, description, color, parent_id, created_by) VALUES (?,?,?,?,?)',
                (name, desc, color, parent_id, sess['userId'])
            )
            db.commit()
        self.send_json({'ok': True, 'id': cur.lastrowid})

    def api_doc_categories_update(self, cat_id):
        sess = self.require_manager()
        if not sess: return
        body = self.read_json()
        name      = body.get('name', '').strip()
        desc      = body.get('description', '').strip()
        color     = body.get('color', '#1B2A4A').strip()
        parent_id = body.get('parent_id') or None
        if parent_id: parent_id = int(parent_id)
        if parent_id == cat_id: parent_id = None  # prevent self-reference
        if not name:
            self.send_json({'error': 'Ten danh muc khong duoc de trong'}, 400); return
        with get_db() as db:
            db.execute('UPDATE doc_categories SET name=?, description=?, color=?, parent_id=? WHERE id=?',
                       (name, desc, color, parent_id, cat_id))
            db.commit()
        self.send_json({'ok': True})

    def api_doc_categories_delete(self, cat_id):
        sess = self.require_manager()
        if not sess: return
        with get_db() as db:
            child_cnt = db.execute('SELECT COUNT(*) FROM doc_categories WHERE parent_id=?', (cat_id,)).fetchone()[0]
            if child_cnt > 0:
                self.send_json({'error': f'Danh muc co {child_cnt} danh muc con, vui long xoa con truoc'}, 400); return
            cnt = db.execute('SELECT COUNT(*) FROM documents WHERE category_id=?', (cat_id,)).fetchone()[0]
            if cnt > 0:
                self.send_json({'error': f'Danh muc con {cnt} tai lieu, khong the xoa'}, 400); return
            db.execute('DELETE FROM doc_categories WHERE id=?', (cat_id,))
            db.commit()
        self.send_json({'ok': True})

    def api_docs_list(self, qs):
        sess = self.require_auth()
        if not sess: return
        cat_id      = qs.get('category_id', [None])[0]
        tag         = qs.get('tag', [None])[0]
        q           = qs.get('q', [None])[0]
        doc_type_id = qs.get('doc_type_id', [None])[0]
        issuer_f    = qs.get('issuer', [None])[0]
        sql = """SELECT d.*, u.full_name as uploader_name,
                        c.name as category_name, c.color as category_color,
                        t.name as doc_type_name
                 FROM documents d
                 LEFT JOIN users u ON d.uploaded_by = u.id
                 LEFT JOIN doc_categories c ON d.category_id = c.id
                 LEFT JOIN doc_types t ON d.doc_type_id = t.id
                 WHERE 1=1"""
        params = []
        if cat_id:
            sql += ' AND d.category_id IN (SELECT id FROM doc_categories WHERE id=? OR parent_id=?)'
            params += [int(cat_id), int(cat_id)]
        if doc_type_id:
            sql += ' AND d.doc_type_id=?'
            params.append(int(doc_type_id))
        if issuer_f:
            sql += ' AND d.issuer LIKE ?'
            params.append(f'%{issuer_f}%')
        if tag:
            sql += ' AND (d.tags LIKE ? OR d.tags LIKE ? OR d.tags LIKE ? OR d.tags = ?)'
            params += [f'{tag},%', f'%,{tag},%', f'%,{tag}', tag]
        if q:
            sql += ' AND (d.title LIKE ? OR d.description LIKE ? OR d.doc_number LIKE ? OR d.issuer LIKE ?)'
            params += [f'%{q}%', f'%{q}%', f'%{q}%', f'%{q}%']
        sql += ' ORDER BY d.issued_date DESC NULLS LAST, d.created_at DESC'
        with get_db() as db:
            rows = db.execute(sql, params).fetchall()
        self.send_json(rows_to_list(rows))

    def api_docs_upload(self):
        sess = self.require_auth()
        if not sess: return
        if not self.can_upload_docs(sess):
            self.send_json({'error': 'Ban khong co quyen upload tai lieu'}, 403); return
        ct = self.headers.get('Content-Type', '')
        if 'multipart/form-data' in ct:
            fields, files = self.read_multipart()
        else:
            self.send_json({'error': 'Yeu cau multipart/form-data'}, 400); return
        title       = fields.get('title', '').strip()
        desc        = fields.get('description', '').strip()
        cat_id      = fields.get('category_id', '').strip() or None
        tags        = fields.get('tags', '').strip()
        doc_number  = fields.get('doc_number', '').strip()
        issued_date = fields.get('issued_date', '').strip() or None
        issuer      = fields.get('issuer', '').strip()
        doc_type_id = fields.get('doc_type_id', '').strip() or None
        if not title:
            self.send_json({'error': 'Tieu de khong duoc de trong'}, 400); return
        if 'file' not in files:
            self.send_json({'error': 'Chua chon file'}, 400); return
        fitem = files['file']
        orig_name = fitem.filename
        ext = os.path.splitext(orig_name)[1].lower()
        allowed = {'.pdf': 'pdf', '.docx': 'docx', '.xlsx': 'xlsx',
                   '.jpg': 'image', '.jpeg': 'image', '.png': 'image'}
        if ext not in allowed:
            self.send_json({'error': 'Dinh dang khong ho tro (.pdf .docx .xlsx .jpg .png)'}, 400); return
        file_bytes = fitem.file.read()
        file_size  = len(file_bytes)
        ts = int(datetime.now(VN_TZ).timestamp() * 1000)
        safe_name = f'doc_{ts}_{sess["userId"]}{ext}'
        ct_map = {'.pdf':'application/pdf', '.docx':'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                  '.xlsx':'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                  '.jpg':'image/jpeg', '.jpeg':'image/jpeg', '.png':'image/png'}
        content_type = ct_map.get(ext, 'application/octet-stream')
        if R2_ENABLED:
            ok = r2_upload(file_bytes, safe_name, content_type)
            if not ok:
                self.send_json({'error': 'Loi upload len cloud storage'}, 500); return
            file_path = f'r2:{safe_name}'
        else:
            fpath = os.path.join(UPLOADS_DIR, safe_name)
            with open(fpath, 'wb') as f:
                f.write(file_bytes)
            file_path = f'/uploads/{safe_name}'
        with get_db() as db:
            cur = db.execute(
                """INSERT INTO documents (title, description, file_path, file_name, file_type,
                   file_size, category_id, tags, uploaded_by,
                   doc_number, issued_date, issuer, doc_type_id)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (title, desc, file_path, orig_name,
                 allowed[ext], file_size, cat_id, tags, sess['userId'],
                 doc_number, issued_date, issuer, doc_type_id)
            )
            db.commit()
            new_id = cur.lastrowid
        self.send_json({'ok': True, 'id': new_id})

    def api_docs_update(self, doc_id):
        sess = self.require_auth()
        if not sess: return
        ct = self.headers.get('Content-Type', '')
        if 'multipart/form-data' in ct:
            fields, files = self.read_multipart()
        else:
            fields = self.read_json()
            files = {}
        with get_db() as db:
            row = db.execute('SELECT * FROM documents WHERE id=?', (doc_id,)).fetchone()
            if not row:
                self.send_json({'error': 'Khong tim thay tai lieu'}, 404); return
            if sess['role'] != 'manager' and row['uploaded_by'] != sess['userId']:
                self.send_json({'error': 'Khong co quyen chinh sua'}, 403); return
            upd, params = [], []
            # Text fields
            for key, col in [('title','title'), ('description','description'),
                              ('doc_number','doc_number'), ('issuer','issuer'),
                              ('tags','tags'), ('notes','notes')]:
                if key in fields:
                    val = fields[key].strip() if isinstance(fields[key], str) else fields[key]
                    if key == 'title' and not val:
                        self.send_json({'error': 'Tieu de khong duoc de trong'}, 400); return
                    upd.append(f'{col}=?'); params.append(val)
            # Date field (nullable)
            if 'issued_date' in fields:
                val = (fields['issued_date'] or '').strip() or None
                upd.append('issued_date=?'); params.append(val)
            # FK fields (nullable int)
            for key, col in [('doc_type_id','doc_type_id'), ('category_id','category_id')]:
                if key in fields:
                    raw = fields[key]
                    try:
                        val = int(raw) if raw else None
                    except (ValueError, TypeError):
                        val = None
                    upd.append(f'{col}=?'); params.append(val)
            # File replacement
            if 'file' in files:
                fitem = files['file']
                orig_name = fitem.filename
                ext = os.path.splitext(orig_name)[1].lower()
                allowed = {'.pdf': 'pdf', '.docx': 'docx', '.xlsx': 'xlsx',
                           '.jpg': 'image', '.jpeg': 'image', '.png': 'image'}
                if ext not in allowed:
                    self.send_json({'error': 'Dinh dang khong ho tro (.pdf .docx .xlsx .jpg .png)'}, 400); return
                file_bytes = fitem.file.read()
                # No size limit — storage tracked separately
                ts = int(datetime.now(VN_TZ).timestamp() * 1000)
                safe_name = f'doc_{ts}_{sess["userId"]}{ext}'
                ct_map = {'.pdf':'application/pdf',
                          '.docx':'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                          '.xlsx':'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                          '.jpg':'image/jpeg', '.jpeg':'image/jpeg', '.png':'image/png'}
                content_type = ct_map.get(ext, 'application/octet-stream')
                # Delete old file
                try:
                    old_fp = row['file_path']
                    if old_fp.startswith('r2:'):
                        r2_delete(old_fp[3:])
                    else:
                        fpath = os.path.join(DATA_DIR, old_fp.lstrip('/'))
                        if os.path.exists(fpath):
                            os.remove(fpath)
                except Exception:
                    pass
                # Save new file
                if R2_ENABLED:
                    ok = r2_upload(file_bytes, safe_name, content_type)
                    if not ok:
                        self.send_json({'error': 'Loi upload len cloud storage'}, 500); return
                    new_fp = f'r2:{safe_name}'
                else:
                    fpath = os.path.join(UPLOADS_DIR, safe_name)
                    with open(fpath, 'wb') as f:
                        f.write(file_bytes)
                    new_fp = f'/uploads/{safe_name}'
                upd.extend(['file_path=?', 'file_name=?', 'file_type=?', 'file_size=?'])
                params.extend([new_fp, orig_name, allowed[ext], len(file_bytes)])
            if not upd:
                self.send_json({'ok': True}); return
            params.append(doc_id)
            db.execute(f"UPDATE documents SET {', '.join(upd)} WHERE id=?", params)
            db.commit()
        self.send_json({'ok': True})

    def api_docs_delete(self, doc_id):
        sess = self.require_auth()
        if not sess: return
        with get_db() as db:
            row = db.execute('SELECT * FROM documents WHERE id=?', (doc_id,)).fetchone()
            if not row:
                self.send_json({'error': 'Khong tim thay tai lieu'}, 404); return
            if sess['role'] != 'manager' and row['uploaded_by'] != sess['userId']:
                self.send_json({'error': 'Khong co quyen xoa'}, 403); return
            try:
                fp = row['file_path']
                if fp.startswith('r2:'):
                    r2_delete(fp[3:])
                else:
                    fpath = os.path.join(DATA_DIR, fp.lstrip('/'))
                    if os.path.exists(fpath):
                        os.remove(fpath)
            except Exception:
                pass
            db.execute('DELETE FROM documents WHERE id=?', (doc_id,))
            db.commit()
        self.send_json({'ok': True})

    def api_docs_presigned_url(self, doc_id):
        sess = self.require_auth()
        if not sess: return
        with get_db() as db:
            row = db.execute('SELECT file_path, file_name FROM documents WHERE id=?', (doc_id,)).fetchone()
        if not row:
            self.send_json({'error': 'Khong tim thay tai lieu'}, 404); return
        fp = row['file_path']
        if fp.startswith('r2:'):
            url = r2_presigned_url(fp[3:], expires=3600)
            if not url:
                self.send_json({'error': 'Khong the tao URL'}, 500); return
        else:
            url = fp
        self.send_json({'url': url, 'file_name': row['file_name']})

    # --- DOC STORAGE ---

    def api_docs_storage(self):
        sess = self.require_auth()
        if not sess: return
        with get_db() as db:
            row = db.execute(
                'SELECT COALESCE(SUM(file_size),0) as total_bytes, COUNT(*) as file_count FROM documents'
            ).fetchone()
        total_bytes = row['total_bytes']
        file_count  = row['file_count']
        limit_bytes = 1 * 1024 * 1024 * 1024 * 1024  # 1 TB
        self.send_json({
            'used_bytes':  total_bytes,
            'limit_bytes': limit_bytes,
            'file_count':  file_count,
            'percent':     round(total_bytes / limit_bytes * 100, 4)
        })

    # --- DOC TYPES ---

    def api_doc_types_list(self):
        sess = self.require_auth()
        if not sess: return
        with get_db() as db:
            rows = db.execute('SELECT * FROM doc_types ORDER BY name').fetchall()
        self.send_json(rows_to_list(rows))

    def api_doc_types_create(self):
        sess = self.require_manager()
        if not sess: return
        body = self.read_json()
        name = body.get('name', '').strip()
        if not name:
            self.send_json({'error': 'Ten loai van ban khong duoc de trong'}, 400); return
        with get_db() as db:
            db.execute('INSERT INTO doc_types (name, description, created_by) VALUES (?,?,?)',
                       (name, body.get('description', '').strip(), sess['userId']))
            db.commit()
        self.send_json({'ok': True})

    def api_doc_types_update(self, type_id):
        sess = self.require_manager()
        if not sess: return
        body = self.read_json()
        name = body.get('name', '').strip()
        if not name:
            self.send_json({'error': 'Ten loai van ban khong duoc de trong'}, 400); return
        with get_db() as db:
            db.execute('UPDATE doc_types SET name=?, description=? WHERE id=?',
                       (name, body.get('description', '').strip(), type_id))
            db.commit()
        self.send_json({'ok': True})

    def api_doc_types_delete(self, type_id):
        sess = self.require_manager()
        if not sess: return
        with get_db() as db:
            cnt = db.execute('SELECT COUNT(*) FROM documents WHERE doc_type_id=?', (type_id,)).fetchone()[0]
            if cnt > 0:
                self.send_json({'error': f'Loai van ban co {cnt} tai lieu, khong the xoa'}, 400); return
            db.execute('DELETE FROM doc_types WHERE id=?', (type_id,))
            db.commit()
        self.send_json({'ok': True})

    def api_manager_doc_permissions(self):
        sess = self.require_manager()
        if not sess: return
        with get_db() as db:
            rows = db.execute(
                """SELECT id, username, full_name, department, can_upload_docs
                   FROM users WHERE role='employee' ORDER BY full_name"""
            ).fetchall()
        self.send_json(rows_to_list(rows))

    def api_manager_doc_permission_set(self, uid):
        sess = self.require_manager()
        if not sess: return
        body = self.read_json()
        val  = 1 if body.get('can_upload_docs') else 0
        with get_db() as db:
            db.execute('UPDATE users SET can_upload_docs=? WHERE id=?', (val, uid))
            db.commit()
        self.send_json({'ok': True})

def run():
    os.chdir(PUBLIC_DIR)
    init_db()
    handler = Handler
    with socketserver.TCPServer(('', PORT), handler) as httpd:
        httpd.allow_reuse_address = True
        print(f'Server running on port {PORT}')
        print(f'DATA_DIR: {DATA_DIR}')
        print(f'R2 enabled: {R2_ENABLED}')
        httpd.serve_forever()

if __name__ == '__main__':
    run()
