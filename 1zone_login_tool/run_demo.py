"""
Demo trực quan quy trình đăng nhập 1Zone.vn bằng Selenium.
Có hiệu ứng highlight viền đỏ cho các nút bấm và ô nhập liệu để người xem dễ theo dõi.
"""

import os
import sys
import time
import ctypes
import logging

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger("1ZoneDemo")


def highlight(driver, element, color="red", duration=0.8):
    """Làm nổi bật phần tử đang thao tác bằng viền màu nổi bật."""
    try:
        driver.execute_script(
            f"arguments[0].style.border = '3px solid {color}';"
            f"arguments[0].style.boxShadow = '0 0 15px {color}';",
            element
        )
        time.sleep(duration)
    except Exception:
        pass


def bring_window_to_front():
    """Đưa cửa sổ Chrome lên đầu màn hình."""
    try:
        user32 = ctypes.windll.user32
        # Tìm cửa sổ Chrome
        hwnd = user32.FindWindowW("Chrome_WidgetWin_1", None)
        if hwnd:
            user32.ShowWindow(hwnd, 3)  # SW_MAXIMIZE = 3
            user32.SetForegroundWindow(hwnd)
    except Exception:
        pass


def main():
    email = "namtt867@gmail.com"
    password = "5hAusrwE.aP!9qP"

    logger.info("=== BẮT ĐẦU CHẠY DEMO ĐĂNG NHẬP 1ZONE.VN ===")
    logger.info("Khởi động Google Chrome hiển thị trên màn hình...")

    chrome_options = Options()
    chrome_options.add_experimental_option("detach", True)
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    )
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option("useAutomationExtension", False)

    driver = webdriver.Chrome(options=chrome_options)
    wait = WebDriverWait(driver, 15)

    try:
        bring_window_to_front()

        # BƯỚC 1: Vào trang chủ 1Zone
        logger.info("Bước 1: Truy cập trang chủ https://1zone.vn/ ...")
        driver.get("https://1zone.vn/")
        time.sleep(2)
        bring_window_to_front()

        # BƯỚC 2: Tìm nút "Đăng nhập" ở Header
        logger.info("Bước 2: Tìm và bấm nút 'Đăng nhập' ở góc trên màn hình...")
        login_btn = wait.until(
            EC.element_to_be_clickable((By.XPATH, "//a[contains(text(), 'Đăng nhập') or contains(@href, 'account.1zone.vn')]"))
        )
        highlight(driver, login_btn, color="#ED212A", duration=1.0)
        login_btn.click()

        # BƯỚC 3: Chờ chuyển đến trang SSO Login
        logger.info("Bước 3: Chờ trang đăng nhập SSO account.1zone.vn xuất hiện...")
        email_input = wait.until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, "input[name='email']"))
        )
        password_input = driver.find_element(By.CSS_SELECTOR, "input[name='password']")
        time.sleep(1)

        # BƯỚC 4: Nhập Email mô phỏng gõ phím người thật
        logger.info(f"Bước 4: Điền Email tài khoản: {email} ...")
        highlight(driver, email_input, color="#00C853", duration=0.5)
        email_input.clear()
        for char in email:
            email_input.send_keys(char)
            time.sleep(0.06)
        time.sleep(0.5)

        # BƯỚC 5: Nhập Password
        logger.info("Bước 5: Điền Mật khẩu...")
        highlight(driver, password_input, color="#00C853", duration=0.5)
        password_input.clear()
        for char in password:
            password_input.send_keys(char)
            time.sleep(0.05)
        time.sleep(0.8)

        # BƯỚC 6: Bấm nút Đăng nhập
        submit_btn = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
        logger.info("Bước 6: Nhấn nút 'Đăng nhập'...")
        highlight(driver, submit_btn, color="#FF6D00", duration=1.0)
        submit_btn.click()

        # BƯỚC 7: Chờ hệ thống xác thực và chuyển hướng về trang vé
        logger.info("Bước 7: Đang xác thực thông tin và chuyển hướng về hệ thống vé...")
        start_wait = time.time()
        success = False

        while time.time() - start_wait < 15:
            curr = driver.current_url
            if "ticket.1zone.vn" in curr or ("account.1zone.vn/login" not in curr and "account.1zone.vn" not in curr):
                success = True
                break
            time.sleep(0.5)

        if success:
            logger.info(">>> ĐĂNG NHẬP THÀNH CÔNG RỰC RỠ! <<<")
            logger.info(f"Trang hiện tại: {driver.current_url}")

            # Lưu lại cookies
            cookies = driver.get_cookies()
            cookie_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "1zone_cookies.json")
            import json
            with open(cookie_path, "w", encoding="utf-8") as f:
                json.dump(cookies, f, indent=2, ensure_ascii=False)
            logger.info(f"Đã lưu {len(cookies)} cookies vào file 1zone_cookies.json.")

            # Cuộn nhẹ trang để người xem thấy các sự kiện bán vé
            time.sleep(2)
            driver.execute_script("window.scrollBy({top: 400, behavior: 'smooth'});")
            time.sleep(1.5)
            driver.execute_script("window.scrollBy({top: -200, behavior: 'smooth'});")

            # Hiển thị thông báo chào mừng trực tiếp trên giao diện web
            driver.execute_script("""
                const toast = document.createElement('div');
                toast.innerHTML = '🎉 <b>ĐĂNG NHẬP 1ZONE THÀNH CÔNG!</b><br>Tài khoản: namtt867@gmail.com';
                toast.style.position = 'fixed';
                toast.style.top = '24px';
                toast.style.right = '24px';
                toast.style.backgroundColor = '#16a34a';
                toast.style.color = 'white';
                toast.style.padding = '16px 24px';
                toast.style.borderRadius = '12px';
                toast.style.boxShadow = '0 10px 25px rgba(0,0,0,0.3)';
                toast.style.fontSize = '16px';
                toast.style.zIndex = '999999';
                toast.style.transition = 'all 0.5s ease';
                document.body.appendChild(toast);
            """)

            logger.info("Cửa sổ Chrome đang mở trên màn hình để bạn xem. Hoàn tất!")
        else:
            logger.error("Không nhận được chuyển hướng sau khi bấm đăng nhập.")

    except Exception as e:
        logger.error(f"Lỗi trong quá trình chạy demo: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
