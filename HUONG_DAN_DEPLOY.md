# Hướng dẫn Deploy lên Railway (~130k VND/tháng)

---

## Bước 1 — Tạo tài khoản GitHub

1. Mở trình duyệt, vào: **https://github.com**
2. Nhấn **Sign up** → điền email, mật khẩu, username
3. Xác nhận email rồi đăng nhập

---

## Bước 2 — Tạo repository trên GitHub

1. Sau khi đăng nhập GitHub, nhấn dấu **+** góc trên phải → **New repository**
2. Điền:
   - **Repository name**: `cham-cong-ot`
   - Chọn **Private** (chỉ bạn thấy)
3. Nhấn **Create repository**
4. GitHub hiện trang trống — **giữ nguyên trang này**, dùng ở bước sau

---

## Bước 3 — Cài Git (nếu chưa có)

1. Vào **https://git-scm.com/download/win**
2. Tải bản **64-bit** → cài đặt, nhấn Next liên tục, giữ mặc định
3. Sau khi cài xong, mở **Start Menu** → tìm **Git Bash** → nếu thấy là đã cài thành công

---

## Bước 4 — Mở CMD trong thư mục Web_cham_cong

**Cách nhanh nhất:**

1. Mở **File Explorer** (Windows + E)
2. Điều hướng đến thư mục:
   ```
   C:\Users\dotha\Claude\Projects\Web_cham_cong
   ```
3. Nhấp vào **thanh địa chỉ** trên cùng của File Explorer (thanh hiện đường dẫn)
4. Xóa nội dung thanh địa chỉ, gõ: `cmd` rồi nhấn **Enter**
5. Cửa sổ CMD mở ra **đúng trong thư mục Web_cham_cong** ✅

> Kiểm tra: dòng đầu CMD phải hiện `C:\Users\dotha\Claude\Projects\Web_cham_cong>`

---

## Bước 5 — Cấu hình Git lần đầu

Trong cửa sổ CMD vừa mở, chạy 2 lệnh sau (thay thông tin của bạn):

```
git config --global user.name "Ten cua ban"
git config --global user.email "email@cua.ban"
```

---

## Bước 6 — Upload code lên GitHub

Chạy từng lệnh một trong CMD (copy & paste rồi Enter):

**1. Khởi tạo Git:**
```
git init
```

**2. Thêm tất cả file:**
```
git add .
```

**3. Tạo commit đầu tiên:**
```
git commit -m "cham cong OT v1"
```

**4. Đặt nhánh chính là `main`:**
```
git branch -M main
```

**5. Kết nối với GitHub** (thay `TEN_GITHUB` bằng username của bạn):
```
git remote add origin https://github.com/TEN_GITHUB/cham-cong-ot.git
```

**6. Push code lên:**
```
git push -u origin main
```

---

## Xử lý lỗi xác thực khi push

Khi chạy lệnh `git push`, GitHub sẽ yêu cầu đăng nhập:

- **Username**: nhập username GitHub của bạn
- **Password**: **KHÔNG nhập mật khẩu thường** — cần tạo **Personal Access Token**

**Tạo Personal Access Token:**
1. Trên GitHub → nhấn avatar góc trên phải → **Settings**
2. Cuộn xuống → **Developer settings** (góc trái dưới cùng)
3. **Personal access tokens** → **Tokens (classic)** → **Generate new token (classic)**
4. Điền **Note**: `cham-cong-ot`
5. **Expiration**: chọn **No expiration**
6. Tích chọn: **repo** (ô đầu tiên trong danh sách)
7. Nhấn **Generate token**
8. **Copy token ngay** (chỉ hiện 1 lần!) — dán vào ô Password khi push

---

## Bước 7 — Deploy trên Railway

1. Vào **https://railway.app** → **Login with GitHub** → xác nhận
2. Nhấn **New Project** → **Deploy from GitHub repo**
3. Chọn repo `cham-cong-ot` → Railway bắt đầu deploy (~2 phút)

---

## Bước 8 — Gắn ổ đĩa lưu dữ liệu (BẮT BUỘC)

> Nếu bỏ qua bước này, toàn bộ dữ liệu chấm công sẽ mất khi Railway restart!

1. Nhấn vào service `cham-cong-ot` trong Railway
2. Chọn tab **Volumes**
3. Nhấn **Add Volume**
4. **Mount Path**: nhập `/data`
5. Nhấn **Add** → Railway tự restart

---

## Bước 9 — Cấu hình biến môi trường

1. Chọn tab **Variables**
2. Nhấn **New Variable**
3. Nhập:
   - **Name**: `DATA_DIR`
   - **Value**: `/data`
4. Nhấn **Add** → Railway tự deploy lại

---

## Bước 10 — Lấy URL cho nhân viên

1. Chọn tab **Settings** → mục **Networking**
2. Nhấn **Generate Domain**
3. Xuất hiện URL dạng: `https://cham-cong-ot-xxxx.up.railway.app`
4. **Gửi URL này cho toàn bộ nhân viên** — họ truy cập từ điện thoại hoặc máy tính bất kỳ

---

## Chi phí Railway

| Gói | Giá | Phù hợp |
|-----|-----|---------|
| Trial | $5 credit miễn phí | Dùng thử ~1 tháng |
| Starter | $5/tháng (~130k VND) | Dùng lâu dài |

Thanh toán bằng thẻ Visa/Mastercard quốc tế.

---

## Cập nhật code sau này

Mỗi khi có thay đổi, mở CMD trong thư mục và chạy:
```
git add .
git commit -m "mo ta thay doi"
git push
```
Railway tự động deploy lại sau ~2 phút.

---

## Sao lưu dữ liệu định kỳ

Cài Railway CLI: https://docs.railway.app/guides/cli

Sau đó chạy:
```
railway run -- python -c "import shutil; shutil.copy('/data/cham_cong.db', '/app/backup.db')"
```

---

## Phương án thay thế — Ngrok (miễn phí, chạy trên máy bạn)

Nếu chỉ muốn thử hoặc tiết kiệm chi phí:

1. Tải tại **https://ngrok.com/download** → giải nén ra thư mục bất kỳ
2. Đăng ký tài khoản miễn phí tại https://ngrok.com → vào **Your Authtoken** → copy token
3. Mở CMD, chạy: `ngrok config add-authtoken TOKEN_VUA_COPY`
4. Khởi động server chấm công: `py server.py` (trong thư mục Web_cham_cong)
5. Mở CMD khác, chạy: `ngrok http 3000`
6. Ngrok hiện URL dạng `https://xxxx.ngrok-free.app` → gửi cho nhân viên

> **Lưu ý ngrok miễn phí:**
> - Máy tính phải luôn bật trong giờ làm việc
> - URL thay đổi mỗi lần khởi động lại (tài khoản trả phí $8/tháng có URL cố định)
> - Dữ liệu lưu trên máy bạn, an toàn
