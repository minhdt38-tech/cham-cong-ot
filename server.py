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
from datetime import datetime

try:
    from PIL import Image as PilImage
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

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
        """)
        row = db.execute("SELECT id FROM users WHERE username='admin'").fetchone()
        if not row:
            pwd = hash_password('admin123')
            db.execute(
                "INSERT INTO users (username,password,full_name,role) VALUES (?,?,?,?)",
                ('admin', pwd, 'Quan ly', 'manager')
            )
        db.commit()


def compress_image(file_bytes, ext):
    """
    Nen anh truoc khi luu:
    - Resize max 1920px
    - Chuyen sang JPEG chat luong 75%
    - Giam tu ~5MB xuong con ~200-400KB
    """
    if not PIL_AVAILABLE:
        return file_bytes, ext
    try:
        img = PilImage.open(io.BytesIO(file_bytes))
        # Chuyen sang RGB (JPEG khong ho tro alpha)
        if img.mode in ('RGBA', 'P', 'LA'):
            bg = PilImage.new('RGB', img.size, (255, 255, 255))
            if img.mode == 'P':
                img = img.convert('RGBA')
            bg.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
            img = bg
        elif img.mode != 'RGB':
            img = img.convert('RGB')
        # Resize neu qua lon (max 1920px chieu dai nhat)
        max_px = 1920
        w, h = img.size
        if w > max_px or h > max_px:
            ratio = min(max_px / w, max_px / h)
            img = img.resize((int(w * ratio), int(h * ratio)), PilImage.LANCZOS)
        # Luu thanh JPEG chat luong 75
        out = io.BytesIO()
        img.save(out, format='JPEG', quality=75, optimize=True)
        return out.getvalue(), '.jpg'
    except Exception:
        return file_bytes, ext  # fallback: luu nguyen ban goc


def hash_password(pw):
    salt = 'chamcong_salt_2024'
    return hashlib.sha256((salt + pw).encode('utf-8')).hexdigest()


def check_password(pw, hashed):
    return hash_password(pw) == hashed


def rows_to_list(rows):
    return [dict(r) for r in rows]


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


# --- MULTIPART PARSER (replaces removed cgi module) ---

def parse_multipart(content_type, body):
    """
    Parse multipart/form-data body.
    Returns (fields: dict[str,str], files: dict[str, FileItem])
    Compatible with Python 3.13+
    """
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
        pass  # suppress default access log

    # Helpers

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

        # SPA fallback
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
        }
        if path in routes:
            routes[path]()
        else:
            self.send_json({'error': 'Not found'}, 404)

    def do_PUT(self):
        path, _ = self.get_path_and_query()
        m = re.match(r'^/api/manager/overtime/(\d+)$', path)
        if m:
            self.api_manager_review_overtime(int(m.group(1))); return
        m = re.match(r'^/api/manager/overtime/(\d+)/cancel$', path)
        if m:
            self.api_manager_cancel_overtime(int(m.group(1))); return
        m = re.match(r'^/api/manager/users/(\d+)$', path)
        if m:
            self.api_manager_update_user(int(m.group(1))); return
        m = re.match(r'^/api/notifications/(\d+)/read$', path)
        if m:
            self.api_notification_mark_read(int(m.group(1))); return
        self.send_json({'error': 'Not found'}, 404)

    def do_DELETE(self):
        path, _ = self.get_path_and_query()
        m = re.match(r'^/api/manager/users/(\d+)$', path)
        if m:
            self.api_manager_delete_user(int(m.group(1))); return
        self.send_json({'error': 'Not found'}, 404)

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
        ot_type    = fields.get('ot_type', '').strip()
        start_time = fields.get('start_time', '').strip()
        end_time   = fields.get('end_time', '').strip()
        reason     = fields.get('reason', '').strip()

        if not all([req_date, ot_type, start_time, end_time, reason]):
            self.send_json({'error': 'Vui long dien day du thong tin'}, 400)
            return

        try:
            sh, sm = map(int, start_time.split(':'))
            eh, em = map(int, end_time.split(':'))
            hours  = ((eh * 60 + em) - (sh * 60 + sm)) / 60.0
        except Exception:
            self.send_json({'error': 'Gio khong hop le'}, 400)
            return
        if hours <= 0:
            self.send_json({'error': 'Gio ket thuc phai sau gio bat dau'}, 400)
            return

        image_path = None
        if 'image' in files:
            fitem = files['image']
            ext   = os.path.splitext(fitem.filename)[1].lower()
            if ext not in ('.jpg', '.jpeg', '.png', '.gif', '.webp', '.pdf'):
                self.send_json({'error': 'Dinh dang file khong ho tro'}, 400)
                return
            file_bytes = fitem.file.read()
            # Nen anh (bo qua PDF)
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
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
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
            # Tao thong bao cho nhan vien
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


# --- SERVER ---

class ThreadedServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    daemon_threads      = True
    allow_reuse_address = True


def get_local_ip():
    import socket
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return 'localhost'


if __name__ == '__main__':
    init_db()
    ip = get_local_ip()
    print("")
    print("=" * 46)
    print("  HE THONG CHAM CONG OT - DANG CHAY")
    print("=" * 46)
    print(f"  Local   : http://localhost:{PORT}")
    print(f"  Mang LAN: http://{ip}:{PORT}")
    print("")
    print("  Tai khoan quan ly: admin / admin123")
    print("  Nhan Ctrl+C de dung server")
    print("=" * 46)
    print("")
    with ThreadedServer(('0.0.0.0', PORT), Handler) as server:
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            print('\nDa dung server.')
