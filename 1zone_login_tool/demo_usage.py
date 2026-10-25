"""
Ví dụ tích hợp OneZoneLogin vào script săn vé hoặc tự động hóa khác.
"""

from login_tool import OneZoneLogin
import time

def run():
    # Khởi tạo bot với giao diện hiển thị
    bot = OneZoneLogin(headless=False)
    
    # 1. Khởi động trình duyệt
    driver = bot.start_browser()

    # 2. Thử nạp cookie cũ trước (nếu có)
    logged_in = bot.load_cookies("1zone_cookies.json")
    
    # Nếu chưa có cookie hoặc hết hạn, đăng nhập bằng email & password
    if not logged_in:
        # Thay bằng tài khoản thật của bạn hoặc đọc từ biến môi trường
        email = "your_email@gmail.com"
        password = "your_password"
        logged_in = bot.login_with_credentials(email, password)

    if logged_in:
        print("[SUCCESS] Đã đăng nhập vào hệ thống vé 1Zone!")
        
        # 3. Điều hướng đến sự kiện cụ thể muốn mua vé
        target_event_url = "https://ticket.1zone.vn/events"
        driver.get(target_event_url)
        print("Đang ở trang danh sách sự kiện vé:", driver.current_url)

        # Thực hiện các thao tác chọn vé, chọn ghế, thanh toán tại đây...
        time.sleep(5)
    else:
        print("[FAILED] Không thể đăng nhập.")

    # Đóng trình duyệt khi xong việc
    bot.close()

if __name__ == "__main__":
    run()
