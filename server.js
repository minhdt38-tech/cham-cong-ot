const express = require('express');
const session = require('express-session');
const multer = require('multer');
const bcrypt = require('bcryptjs');
const path = require('path');
const fs = require('fs');
const Database = require('better-sqlite3');

const app = express();
const PORT = process.env.PORT || 3000;

// Tạo thư mục uploads nếu chưa có
const uploadsDir = path.join(__dirname, 'uploads');
if (!fs.existsSync(uploadsDir)) fs.mkdirSync(uploadsDir, { recursive: true });

// Database
const db = new Database(path.join(__dirname, 'cham_cong.db'));
initDB();

// Middleware
app.use(express.json());
app.use(express.urlencoded({ extended: true }));
app.use(express.static(path.join(__dirname, 'public')));
app.use('/uploads', express.static(uploadsDir));
app.use(session({
  secret: 'chamcong_secret_2024',
  resave: false,
  saveUninitialized: false,
  cookie: { maxAge: 8 * 60 * 60 * 1000 } // 8 giờ
}));

// Multer config
const storage = multer.diskStorage({
  destination: (req, file, cb) => cb(null, uploadsDir),
  filename: (req, file, cb) => {
    const ext = path.extname(file.originalname);
    cb(null, `${Date.now()}_${req.session.userId}${ext}`);
  }
});
const upload = multer({
  storage,
  limits: { fileSize: 10 * 1024 * 1024 }, // 10MB
  fileFilter: (req, file, cb) => {
    const allowed = /jpeg|jpg|png|gif|webp|pdf/;
    const ok = allowed.test(path.extname(file.originalname).toLowerCase());
    cb(null, ok);
  }
});

// ─── DB INIT ───────────────────────────────────────────────────────────────
function initDB() {
  db.exec(`
    CREATE TABLE IF NOT EXISTS users (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      username TEXT UNIQUE NOT NULL,
      password TEXT NOT NULL,
      full_name TEXT NOT NULL,
      role TEXT DEFAULT 'employee', -- 'employee' | 'manager'
      department TEXT DEFAULT '',
      created_at TEXT DEFAULT (datetime('now','localtime'))
    );

    CREATE TABLE IF NOT EXISTS overtime_requests (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      user_id INTEGER NOT NULL,
      request_date TEXT NOT NULL,         -- ngày OT (YYYY-MM-DD)
      ot_type TEXT NOT NULL,              -- 'weekday' | 'weekend'
      start_time TEXT NOT NULL,           -- HH:MM
      end_time TEXT NOT NULL,             -- HH:MM
      hours REAL,                         -- số giờ OT
      reason TEXT NOT NULL,
      image_path TEXT,                    -- đường dẫn ảnh
      status TEXT DEFAULT 'pending',      -- 'pending' | 'approved' | 'rejected'
      manager_note TEXT,
      reviewed_by INTEGER,
      reviewed_at TEXT,
      created_at TEXT DEFAULT (datetime('now','localtime')),
      FOREIGN KEY(user_id) REFERENCES users(id)
    );
  `);

  // Tạo tài khoản manager mặc định nếu chưa có
  const manager = db.prepare('SELECT id FROM users WHERE username = ?').get('admin');
  if (!manager) {
    const hash = bcrypt.hashSync('admin123', 10);
    db.prepare(`INSERT INTO users (username, password, full_name, role) VALUES (?, ?, ?, ?)`)
      .run('admin', hash, 'Quản lý', 'manager');
    console.log('✅ Tài khoản mặc định: admin / admin123');
  }
}

// ─── AUTH MIDDLEWARE ────────────────────────────────────────────────────────
function requireAuth(req, res, next) {
  if (!req.session.userId) return res.status(401).json({ error: 'Chưa đăng nhập' });
  next();
}
function requireManager(req, res, next) {
  if (!req.session.userId || req.session.role !== 'manager') {
    return res.status(403).json({ error: 'Không có quyền' });
  }
  next();
}

// ─── AUTH ROUTES ────────────────────────────────────────────────────────────
app.post('/api/login', (req, res) => {
  const { username, password } = req.body;
  const user = db.prepare('SELECT * FROM users WHERE username = ?').get(username);
  if (!user || !bcrypt.compareSync(password, user.password)) {
    return res.status(401).json({ error: 'Sai tài khoản hoặc mật khẩu' });
  }
  req.session.userId = user.id;
  req.session.role = user.role;
  req.session.fullName = user.full_name;
  res.json({ id: user.id, username: user.username, full_name: user.full_name, role: user.role });
});

app.post('/api/logout', (req, res) => {
  req.session.destroy();
  res.json({ ok: true });
});

app.get('/api/me', requireAuth, (req, res) => {
  const user = db.prepare('SELECT id, username, full_name, role, department FROM users WHERE id = ?').get(req.session.userId);
  res.json(user);
});

app.post('/api/change-password', requireAuth, (req, res) => {
  const { old_password, new_password } = req.body;
  const user = db.prepare('SELECT * FROM users WHERE id = ?').get(req.session.userId);
  if (!bcrypt.compareSync(old_password, user.password)) {
    return res.status(400).json({ error: 'Mật khẩu cũ không đúng' });
  }
  if (new_password.length < 6) return res.status(400).json({ error: 'Mật khẩu mới ít nhất 6 ký tự' });
  const hash = bcrypt.hashSync(new_password, 10);
  db.prepare('UPDATE users SET password = ? WHERE id = ?').run(hash, req.session.userId);
  res.json({ ok: true });
});

// ─── OVERTIME ROUTES ─────────────────────────────────────────────────────────
// Nhân viên submit OT
app.post('/api/overtime', requireAuth, upload.single('image'), (req, res) => {
  const { request_date, ot_type, start_time, end_time, reason } = req.body;
  if (!request_date || !ot_type || !start_time || !end_time || !reason) {
    return res.status(400).json({ error: 'Vui lòng điền đầy đủ thông tin' });
  }

  // Validate OT type vs ngày
  const d = new Date(request_date);
  const dow = d.getDay(); // 0=CN, 6=T7

  // Tính số giờ OT
  const [sh, sm] = start_time.split(':').map(Number);
  const [eh, em] = end_time.split(':').map(Number);
  const hours = ((eh * 60 + em) - (sh * 60 + sm)) / 60;
  if (hours <= 0) return res.status(400).json({ error: 'Giờ kết thúc phải sau giờ bắt đầu' });

  const image_path = req.file ? `/uploads/${req.file.filename}` : null;

  db.prepare(`
    INSERT INTO overtime_requests (user_id, request_date, ot_type, start_time, end_time, hours, reason, image_path)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
  `).run(req.session.userId, request_date, ot_type, start_time, end_time, hours, reason, image_path);

  res.json({ ok: true });
});

// Lấy danh sách OT của nhân viên
app.get('/api/overtime/my', requireAuth, (req, res) => {
  const { month, year } = req.query;
  let sql = `
    SELECT r.*, u.full_name, u.department
    FROM overtime_requests r
    JOIN users u ON r.user_id = u.id
    WHERE r.user_id = ?
  `;
  const params = [req.session.userId];
  if (month && year) {
    sql += ` AND strftime('%Y-%m', r.request_date) = ?`;
    params.push(`${year}-${String(month).padStart(2, '0')}`);
  }
  sql += ' ORDER BY r.request_date DESC, r.created_at DESC';
  res.json(db.prepare(sql).all(...params));
});

// ─── MANAGER ROUTES ───────────────────────────────────────────────────────────
// Lấy tất cả OT pending
app.get('/api/manager/overtime', requireManager, (req, res) => {
  const { status, month, year, user_id } = req.query;
  let sql = `
    SELECT r.*, u.full_name, u.department
    FROM overtime_requests r
    JOIN users u ON r.user_id = u.id
    WHERE 1=1
  `;
  const params = [];
  if (status) { sql += ' AND r.status = ?'; params.push(status); }
  if (month && year) {
    sql += ` AND strftime('%Y-%m', r.request_date) = ?`;
    params.push(`${year}-${String(month).padStart(2, '0')}`);
  }
  if (user_id) { sql += ' AND r.user_id = ?'; params.push(user_id); }
  sql += ' ORDER BY r.created_at DESC';
  res.json(db.prepare(sql).all(...params));
});

// Duyệt / từ chối OT
app.put('/api/manager/overtime/:id', requireManager, (req, res) => {
  const { status, manager_note } = req.body;
  if (!['approved', 'rejected'].includes(status)) {
    return res.status(400).json({ error: 'Trạng thái không hợp lệ' });
  }
  db.prepare(`
    UPDATE overtime_requests
    SET status = ?, manager_note = ?, reviewed_by = ?, reviewed_at = datetime('now','localtime')
    WHERE id = ?
  `).run(status, manager_note || '', req.session.userId, req.params.id);
  res.json({ ok: true });
});

// Quản lý nhân viên
app.get('/api/manager/users', requireManager, (req, res) => {
  res.json(db.prepare('SELECT id, username, full_name, role, department, created_at FROM users ORDER BY full_name').all());
});

app.post('/api/manager/users', requireManager, (req, res) => {
  const { username, password, full_name, role, department } = req.body;
  if (!username || !password || !full_name) return res.status(400).json({ error: 'Thiếu thông tin' });
  try {
    const hash = bcrypt.hashSync(password, 10);
    db.prepare('INSERT INTO users (username, password, full_name, role, department) VALUES (?, ?, ?, ?, ?)')
      .run(username, hash, full_name, role || 'employee', department || '');
    res.json({ ok: true });
  } catch (e) {
    res.status(400).json({ error: 'Tên đăng nhập đã tồn tại' });
  }
});

app.put('/api/manager/users/:id', requireManager, (req, res) => {
  const { full_name, role, department, password } = req.body;
  if (password) {
    const hash = bcrypt.hashSync(password, 10);
    db.prepare('UPDATE users SET full_name=?, role=?, department=?, password=? WHERE id=?')
      .run(full_name, role, department || '', hash, req.params.id);
  } else {
    db.prepare('UPDATE users SET full_name=?, role=?, department=? WHERE id=?')
      .run(full_name, role, department || '', req.params.id);
  }
  res.json({ ok: true });
});

app.delete('/api/manager/users/:id', requireManager, (req, res) => {
  if (req.params.id == req.session.userId) return res.status(400).json({ error: 'Không thể xoá chính mình' });
  db.prepare('DELETE FROM users WHERE id = ?').run(req.params.id);
  res.json({ ok: true });
});

// Thống kê tổng hợp
app.get('/api/manager/stats', requireManager, (req, res) => {
  const { month, year } = req.query;
  let dateFilter = '';
  const params = [];
  if (month && year) {
    dateFilter = `AND strftime('%Y-%m', r.request_date) = ?`;
    params.push(`${year}-${String(month).padStart(2, '0')}`);
  }

  const stats = db.prepare(`
    SELECT
      u.id, u.full_name, u.department,
      COUNT(CASE WHEN r.status='approved' THEN 1 END) as approved_count,
      SUM(CASE WHEN r.status='approved' THEN r.hours ELSE 0 END) as total_hours,
      SUM(CASE WHEN r.status='approved' AND r.ot_type='weekday' THEN r.hours ELSE 0 END) as weekday_hours,
      SUM(CASE WHEN r.status='approved' AND r.ot_type='weekend' THEN r.hours ELSE 0 END) as weekend_hours,
      COUNT(CASE WHEN r.status='pending' THEN 1 END) as pending_count
    FROM users u
    LEFT JOIN overtime_requests r ON u.id = r.user_id ${dateFilter}
    WHERE u.role = 'employee'
    GROUP BY u.id
    ORDER BY u.full_name
  `).all(...params);

  res.json(stats);
});

// ─── SERVE SPA ───────────────────────────────────────────────────────────────
app.get('*', (req, res) => {
  res.sendFile(path.join(__dirname, 'public', 'index.html'));
});

app.listen(PORT, '0.0.0.0', () => {
  console.log(`\n🚀 Chấm công OT đang chạy tại: http://localhost:${PORT}`);
  console.log(`📱 Truy cập từ thiết bị khác: http://<IP_MÁY_TÍNH>:${PORT}`);
  console.log(`👤 Tài khoản quản lý: admin / admin123\n`);
});
