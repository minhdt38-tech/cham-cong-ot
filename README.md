# Hệ Thống Chấm Công OT

Ứng dụng web quản lý làm thêm giờ cho team nội bộ. Chạy hoàn toàn bằng Python thuần — không cần cài thêm thư viện nào.

## Yêu cầu
- Python 3.8 trở lên (thường đã có sẵn trên Windows 10/11)

## Khởi động

**Windows:** Double-click file `start.bat`

**Hoặc chạy thủ công:**
```
python server.py
```

Mở trình duyệt: **http://localhost:3000**

## Tài khoản mặc định
| Tài khoản | Mật khẩu | Vai trò |
|-----------|----------|---------|
| admin | admin123 | Quản lý |

> ⚠️ Đổi mật khẩu admin ngay sau khi đăng nhập lần đầu!

## Hướng dẫn sử dụng

### 1. Thêm nhân viên (Quản lý)
- Đăng nhập bằng tài khoản **admin**
- Vào **Quản lý nhân viên** → **Thêm nhân viên**
- Tạo tài khoản cho từng người trong team (16 người)

### 2. Nhân viên khai báo OT
- Đăng nhập bằng tài khoản riêng
- Vào **Khai báo OT**
- Chọn ngày, loại OT (ngày thường / cuối tuần)
- Điền giờ bắt đầu và kết thúc
- Nhập lý do / mô tả công việc
- Đính kèm ảnh chứng minh (tuỳ chọn, hỗ trợ JPG/PNG/PDF)
- Nhấn **Gửi yêu cầu**

### 3. Quản lý duyệt OT
- Vào **Duyệt OT** để xem danh sách chờ duyệt
- Nhấn **Duyệt** để xem chi tiết, xem ảnh chứng minh
- Nhập ghi chú (nếu cần) → **Duyệt** hoặc **Từ chối**

### 4. Xem báo cáo
- **Báo cáo**: Tổng hợp giờ OT theo nhân viên, lọc theo tháng
- **Tất cả chấm công**: Lịch sử đầy đủ, lọc theo người/tháng

## Truy cập từ điện thoại / máy khác
Đảm bảo cùng mạng WiFi/LAN, truy cập:
```
http://<IP_MÁY_TÍNH>:3000
```
IP máy tính hiển thị khi chạy `start.bat`

## Giờ làm việc quy định
- Thứ 2–6: 08:00–17:30
- Thứ 7: 08:00–12:30
- **OT ngày thường**: làm ngoài khung giờ trên (Thứ 2–6)
- **OT cuối tuần**: Thứ 7 chiều, Chủ nhật, Lễ

## Dữ liệu & Sao lưu
Dữ liệu lưu trong:
- `cham_cong.db` — database SQLite (toàn bộ chấm công)
- `uploads/` — ảnh chứng minh

**Sao lưu định kỳ 2 file/thư mục này!**
