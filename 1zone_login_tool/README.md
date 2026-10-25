# 1Zone.vn Selenium Login Tool

Tool tự động hóa đăng nhập cho nền tảng bán vé **1Zone.vn** (`ticket.1zone.vn` / `1zone.vn` / `account.1zone.vn`) bằng Python & Selenium.

---

## 🌟 Tính Năng Nổi Bật

1. **Đăng nhập tự động SSO 1Zone**:
   - Tự động điền email, mật khẩu và gửi yêu cầu đăng nhập qua cổng SSO `account.1zone.vn`.
   - Bắt và thông báo lỗi rõ ràng (sai mật khẩu, tài khoản không tồn tại, v.v.).
   - Tự động chuyển hướng về trang mua vé (`ticket.1zone.vn/events`).
2. **Lưu & Tái sử dụng Cookies (`cookies.json`)**:
   - Sau khi đăng nhập thành công, phiên làm việc (cookies) được lưu lại.
   - Các lần chạy sau có thể vào thẳng hệ thống mà không cần đăng nhập lại.
3. **Hỗ trợ Đăng nhập Google / Thủ công (Interactive Mode)**:
   - Mở trình duyệt để người dùng tự bấm "Đăng nhập với Google" hoặc xử lý OTP/2FA.
   - Tool tự động nhận diện thời điểm đăng nhập thành công và lưu lại phiên.
4. **Hỗ trợ Chrome Profile (`--profile-dir`)**:
   - Lưu trữ toàn bộ cache, session và thông tin đăng nhập Google vĩnh viễn trên máy.
5. **Chế độ Headless**:
   - Cho phép chạy ngầm không hiện cửa sổ (`--headless`), phù hợp chạy trên VPS/Server.
6. **Bypass cơ bản**:
   - Ẩn dấu vết `navigator.webdriver` và vô hiệu hóa flag `enable-automation` của Chrome.

---

## 📦 Cài Đặt

Mở Terminal hoặc PowerShell tại thư mục này và cài các thư viện cần thiết:

```bash
pip install -r requirements.txt
```

> **Lưu ý**: Bạn cần cài sẵn trình duyệt Google Chrome trên máy.

---

## 🚀 Hướng Dẫn Sử Dụng

### 1. Chạy Menu Tương Tác Trực Quan

Nếu bạn chỉ cần chạy nhanh và chọn từng bước:

```bash
python login_tool.py
```

Giao diện console sẽ hiển thị:
```text
==================================================
  TOOL ĐĂNG NHẬP 1ZONE.VN (SELENIUM)
==================================================
1. Đăng nhập bằng Email & Mật khẩu
2. Mở trình duyệt để đăng nhập thủ công (Google / Email) & Lưu Cookies
3. Đăng nhập nhanh bằng Cookies đã lưu
4. Thoát
```

---

### 2. Đăng nhập trực tiếp qua dòng lệnh (CLI)

```bash
python login_tool.py -e your_email@gmail.com -p your_password
```

Chạy ở chế độ ẩn cửa sổ (Headless):
```bash
python login_tool.py -e your_email@gmail.com -p your_password --headless
```

---

### 3. Đăng nhập bằng Google / Thủ công (Interactive)

Nếu tài khoản của bạn liên kết Google hoặc cần vượt mã xác thực:

```bash
python login_tool.py --interactive
```
- Trình duyệt sẽ mở ra. Bạn nhấn **"Đăng nhập với tài khoản Google"** và hoàn tất.
- Khi đăng nhập xong và chuyển về trang vé, tool sẽ tự động lưu lại cookie vào file `1zone_cookies.json`.

---

### 4. Đăng nhập nhanh bằng Cookie đã lưu

```bash
python login_tool.py --use-cookies
```

---

### 5. Dùng file cấu hình `.env`

Tạo file `.env` từ `.env.example`:
```env
ZONE_EMAIL=your_email@gmail.com
ZONE_PASSWORD=your_password_here
```

Sau đó chỉ cần chạy:
```bash
python login_tool.py
# Hoặc
python login_tool.py --headless
```

---

### 6. Tích hợp vào script săn vé (Code Python)

Xem chi tiết tại file [`demo_usage.py`](demo_usage.py):

```python
from login_tool import OneZoneLogin

# Khởi tạo
bot = OneZoneLogin(headless=False)
driver = bot.start_browser()

# Thử nạp cookie trước
if not bot.load_cookies():
    # Đăng nhập bằng email/pass nếu cookie hết hạn
    bot.login_with_credentials("your_email@gmail.com", "your_password")

# Thực hiện hành động tiếp theo
driver.get("https://ticket.1zone.vn/events")
# ... tiếp tục chọn vé / click mua vé ...
```

---

## 🛠 Danh Sách Tham Số Dòng Lệnh

| Tham số | Ý nghĩa |
|---|---|
| `-e`, `--email` | Email tài khoản 1Zone |
| `-p`, `--password` | Mật khẩu tài khoản |
| `--headless` | Chạy ẩn trình duyệt không mở cửa sổ |
| `--interactive` | Mở trình duyệt cho người dùng tự đăng nhập (Google, OTP) & tự lưu cookie |
| `--use-cookies` | Nạp cookie từ file để đăng nhập không cần mật khẩu |
| `--cookie-file` | Đường dẫn file JSON lưu/nạp cookies (mặc định: `1zone_cookies.json`) |
| `--profile-dir` | Đường dẫn thư mục Chrome Profile để duy trì phiên vĩnh viễn |
| `--target-url` | Trang đích muốn chuyển tới sau đăng nhập (mặc định: `https://ticket.1zone.vn/events`) |
