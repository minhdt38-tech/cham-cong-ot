# -*- coding: utf-8 -*-
"""
Chay script nay mot lan duy nhat de tao 17 tai khoan nhan vien.
Cach chay:
  python create_users.py

Mat khau mac dinh: Vinhomes@2024
(Admin co the reset mat khau sau trong phan Quan ly nhan vien)
"""
import sqlite3
import hashlib
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.environ.get('DATA_DIR', BASE_DIR)
DB_PATH  = os.path.join(DATA_DIR, 'cham_cong.db')

SALT = 'chamcong_salt_2024'
DEFAULT_PASSWORD = 'Vinhomes@2024'

USERS = [
    ('tailt',   'Luong The Tai'),
    ('anhlv',   'Le Viet Anh'),
    ('longnv',  'Nguyen Vu Long'),
    ('hungtm',  'Tran Manh Hung'),
    ('tuannd',  'Nham Duc Tuan'),
    ('cuongnn', 'Nguyen Ngoc Cuong'),
    ('kienvt',  'Vu Trung Kien'),
    ('lamdt',   'Dam Tung Lam'),
    ('anhnl',   'Nguyen Le Anh'),
    ('nambk',   'Bui Khac Nam'),
    ('khanhnn', 'Ngo Ngoc Khanh'),
    ('vuvv',    'Nguyen Van Vu'),
    ('tubt',    'Bui Tho Tu'),
    ('hiepdm',  'Dinh Minh Hiep'),
    ('haodh',   'Do Huy Hao'),
    ('thenhhv', 'Ha Van Thenh'),
    ('congnk',  'Nguyen Kim Cong'),
]

def hash_password(pw):
    return hashlib.sha256((SALT + pw).encode('utf-8')).hexdigest()

def main():
    if not os.path.exists(DB_PATH):
        print(f'[LOI] Khong tim thay DB tai: {DB_PATH}')
        print('     Hay chay server.py truoc de khoi tao DB, sau do chay lai script nay.')
        return

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    pwd_hash = hash_password(DEFAULT_PASSWORD)
    created = 0
    skipped = 0

    for username, full_name in USERS:
        existing = conn.execute('SELECT id FROM users WHERE username=?', (username,)).fetchone()
        if existing:
            print(f'  [bo qua] {username} da ton tai')
            skipped += 1
        else:
            conn.execute(
                'INSERT INTO users (username, password, full_name, role) VALUES (?, ?, ?, ?)',
                (username, pwd_hash, full_name, 'employee')
            )
            print(f'  [tao]    {username} - {full_name}')
            created += 1

    conn.commit()
    conn.close()
    print(f'\nHoan thanh: {created} tai khoan moi, {skipped} bo qua.')
    print(f'Mat khau mac dinh: {DEFAULT_PASSWORD}')

if __name__ == '__main__':
    main()
