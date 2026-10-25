"""
1Zone.vn Automation Login Tool using Selenium
Hỗ trợ đăng nhập tự động vào hệ thống bán vé 1Zone (ticket.1zone.vn / 1zone.vn)
"""

import os
import sys
import json
import time
import argparse
import logging
from typing import Optional, Dict, Any, List

# Cấu hình encoding UTF-8 cho Windows console để tránh UnicodeEncodeError
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Cấu hình logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger("1ZoneLogin")


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_COOKIE_FILE = os.path.join(SCRIPT_DIR, "1zone_cookies.json")

class OneZoneLogin:
    """Quản lý phiên đăng nhập và trình duyệt Selenium cho 1Zone.vn"""

    # URL SSO và trang đích mặc định
    BASE_URL = "https://1zone.vn/"
    TICKET_URL = "https://ticket.1zone.vn/events"
    SSO_LOGIN_URL = (
        "https://account.1zone.vn/login?"
        "next=%2Fsso%2Fauthorize%3Flang%3Dvi%26redirect_uri%3Dhttps%253A%252F%252Fticket.1zone.vn%252Fevents&lang=vi"
    )

    def __init__(
        self,
        headless: bool = False,
        detach: bool = True,
        user_data_dir: Optional[str] = None,
        cookie_file: str = DEFAULT_COOKIE_FILE,
        timeout: int = 15
    ):
        self.headless = headless
        self.detach = detach
        self.user_data_dir = user_data_dir
        self.cookie_file = cookie_file
        self.timeout = timeout
        self.driver: Optional[webdriver.Chrome] = None

    def start_browser(self) -> webdriver.Chrome:
        """Khởi tạo trình duyệt Chrome với cấu hình tối ưu chống bot-detection."""
        logger.info("Đang khởi động trình duyệt Chrome...")
        chrome_options = Options()

        if self.headless:
            chrome_options.add_argument("--headless=new")
            logger.info("Chế độ: Headless (chạy ngầm)")
        else:
            logger.info("Chế độ: Giao diện trực quan (mở cửa sổ Chrome hiển thị)")
            if self.detach:
                # Giữ nguyên cửa sổ Chrome mở trên màn hình
                chrome_options.add_experimental_option("detach", True)

        # Cấu hình bypass bot detection cơ bản & tối ưu hiệu năng
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--start-maximized")
        chrome_options.add_argument(
            "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        )

        # Lưu giữ Chrome Profile nếu có chỉ định (giúp lưu lại đăng nhập Google / SSO)
        if self.user_data_dir:
            abs_profile = os.path.abspath(self.user_data_dir)
            chrome_options.add_argument(f"--user-data-dir={abs_profile}")
            logger.info(f"Sử dụng Chrome User Data: {abs_profile}")

        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option("useAutomationExtension", False)

        try:
            self.driver = webdriver.Chrome(options=chrome_options)
        except Exception as e:
            logger.error(f"Không thể khởi chạy ChromeDriver: {e}")
            logger.info("Đang thử cài đặt tự động bằng webdriver-manager...")
            from webdriver_manager.chrome import ChromeDriverManager
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)

        # Ẩn thuộc tính navigator.webdriver
        self.driver.execute_cdp_cmd(
            "Page.addScriptToEvaluateOnNewDocument",
            {
                "source": """
                    Object.defineProperty(navigator, 'webdriver', {
                        get: () => undefined
                    });
                """
            }
        )

        logger.info("Khởi động Chrome thành công.")
        return self.driver

    def login_with_credentials(
        self,
        email: str,
        password: str,
        target_redirect: str = TICKET_URL
    ) -> bool:
        """
        Đăng nhập tự động bằng Email và Mật khẩu qua cổng SSO của 1Zone.
        """
        if not self.driver:
            self.start_browser()

        # Tạo URL đăng nhập với target_redirect tương ứng
        import urllib.parse
        encoded_redirect = urllib.parse.quote(target_redirect, safe='')
        sso_url = (
            f"https://account.1zone.vn/login?"
            f"next=%2Fsso%2Fauthorize%3Flang%3Dvi%26redirect_uri%3D{encoded_redirect}&lang=vi"
        )

        logger.info(f"Truy cập trang đăng nhập 1Zone...")
        self.driver.get(sso_url)

        wait = WebDriverWait(self.driver, self.timeout)

        try:
            # 1. Chờ ô nhập email xuất hiện
            logger.info("Đang tìm ô nhập email và mật khẩu...")
            email_field = wait.until(
                EC.visibility_of_element_located((By.CSS_SELECTOR, "input[name='email']"))
            )
            password_field = wait.until(
                EC.visibility_of_element_located((By.CSS_SELECTOR, "input[name='password']"))
            )

            # 2. Xóa và điền thông tin tài khoản
            email_field.clear()
            for ch in email:
                email_field.send_keys(ch)
                time.sleep(0.02)

            password_field.clear()
            for ch in password:
                password_field.send_keys(ch)
                time.sleep(0.02)

            time.sleep(0.5)

            # 3. Tìm và bấm nút Đăng nhập
            submit_btn = self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
            logger.info("Đang gửi yêu cầu đăng nhập...")
            submit_btn.click()

            # 4. Kiểm tra phản hồi (thành công hoặc thông báo lỗi)
            # Nếu đăng nhập thành công, URL sẽ chuyển hướng ra khỏi account.1zone.vn/login
            # Hoặc trang sẽ hiển thị lỗi nếu thông tin sai.
            start_time = time.time()
            login_success = False

            while time.time() - start_time < self.timeout:
                current_url = self.driver.current_url

                # Kiểm tra nếu đã chuyển hướng thành công
                if "account.1zone.vn/login" not in current_url:
                    login_success = True
                    break

                # Kiểm tra thông báo lỗi trên giao diện
                error_elems = self.driver.find_elements(
                    By.XPATH,
                    "//*[contains(text(), 'không chính xác') or contains(text(), 'Vui lòng nhập') or contains(@class, 'text-red')]"
                )
                visible_errors = [e.text.strip() for e in error_elems if e.is_displayed() and e.text.strip()]
                if visible_errors:
                    logger.error(f"Đăng nhập thất bại: {visible_errors[0]}")
                    return False

                time.sleep(0.5)

            if login_success:
                logger.info(f"Đăng nhập thành công! Trang hiện tại: {self.driver.current_url}")
                # Đợi trang đích tải xong
                time.sleep(2)
                self.save_cookies()
                return True
            else:
                logger.warning("Hết thời gian chờ chuyển hướng đăng nhập. Kiểm tra lại thông tin hoặc CAPTCHA nếu có.")
                return False

        except TimeoutException:
            logger.error("Quá thời gian tải trang hoặc không tìm thấy form đăng nhập.")
            return False
        except Exception as e:
            logger.error(f"Lỗi trong quá trình đăng nhập: {e}")
            return False

    def interactive_login(self, target_url: str = TICKET_URL) -> bool:
        """
        Mở trình duyệt để người dùng tự đăng nhập (hữu ích với đăng nhập Google, OTP, hoặc CAPTCHA).
        Script sẽ tự động nhận diện khi đăng nhập hoàn tất và lưu cookie.
        """
        if not self.driver:
            self.start_browser()

        logger.info("Chế độ đăng nhập tương tác:")
        logger.info("1. Cửa sổ trình duyệt đã mở.")
        logger.info("2. Hãy đăng nhập bằng Google hoặc Email/Mật khẩu trên trình duyệt.")
        logger.info("3. Tool sẽ tự động phát hiện khi đăng nhập xong và lưu cookie.")

        self.driver.get(
            f"https://account.1zone.vn/login?next=%2Fsso%2Fauthorize%3Flang%3Dvi%26redirect_uri%3Dhttps%253A%252F%252Fticket.1zone.vn%252Fevents&lang=vi"
        )

        # Chờ người dùng đăng nhập xong (URL đổi về ticket.1zone.vn hoặc 1zone.vn)
        max_wait = 180  # 3 phút
        start_time = time.time()

        while time.time() - start_time < max_wait:
            curr_url = self.driver.current_url
            if ("account.1zone.vn/login" not in curr_url) and ("account.1zone.vn" not in curr_url):
                logger.info(f"Phát hiện đăng nhập thành công! URL: {curr_url}")
                time.sleep(2)
                self.save_cookies()
                return True
            time.sleep(1)

        logger.warning("Đã hết thời gian chờ đăng nhập (3 phút).")
        return False

    def save_cookies(self, filepath: Optional[str] = None) -> bool:
        """Lưu toàn bộ cookies hiện tại vào file JSON để tái sử dụng."""
        path = filepath or self.cookie_file
        if not self.driver:
            return False
        try:
            cookies = self.driver.get_cookies()
            with open(path, "w", encoding="utf-8") as f:
                json.dump(cookies, f, indent=2, ensure_ascii=False)
            logger.info(f"Đã lưu {len(cookies)} cookies vào: {os.path.abspath(path)}")
            return True
        except Exception as e:
            logger.error(f"Lỗi khi lưu cookies: {e}")
            return False

    def load_cookies(self, filepath: Optional[str] = None) -> bool:
        """Đọc và inject cookies từ file JSON vào trình duyệt."""
        path = filepath or self.cookie_file
        if not os.path.exists(path):
            logger.warning(f"File cookie không tồn tại: {path}")
            return False

        if not self.driver:
            self.start_browser()

        try:
            with open(path, "r", encoding="utf-8") as f:
                cookies: List[Dict[str, Any]] = json.load(f)

            logger.info(f"Đang nạp {len(cookies)} cookies từ {path}...")
            
            # Phân nhóm cookie theo domain để inject chính xác
            # Domain 1zone.vn & ticket.1zone.vn
            ticket_cookies = [c for c in cookies if "account.1zone.vn" not in c.get("domain", "")]
            account_cookies = [c for c in cookies if "account.1zone.vn" in c.get("domain", "")]

            def inject_cookie_list(target_url: str, c_list: List[Dict[str, Any]]):
                if not c_list:
                    return 0
                self.driver.get(target_url)
                time.sleep(1)
                success = 0
                for c in c_list:
                    cookie_dict = dict(c)
                    if "sameSite" in cookie_dict and cookie_dict["sameSite"] not in ["Strict", "Lax", "None"]:
                        del cookie_dict["sameSite"]
                    try:
                        self.driver.add_cookie(cookie_dict)
                        success += 1
                    except Exception:
                        pass
                return success

            c1 = inject_cookie_list(self.BASE_URL, ticket_cookies)
            c2 = inject_cookie_list("https://account.1zone.vn/login", account_cookies)

            logger.info(f"Đã nạp thành công {c1 + c2}/{len(cookies)} cookies.")
            # Chuyển tới trang vé
            self.driver.get(self.TICKET_URL)
            time.sleep(2)

            if self.is_logged_in():
                logger.info("Đăng nhập bằng cookie thành công!")
                return True
            else:
                logger.warning("Cookie đã hết hạn hoặc không đủ quyền, cần đăng nhập lại.")
                return False

        except Exception as e:
            logger.error(f"Lỗi khi nạp cookies: {e}")
            return False

    def is_logged_in(self) -> bool:
        """Kiểm tra xem phiên hiện tại đã đăng nhập hay chưa."""
        if not self.driver:
            return False
        try:
            # Nếu có nút 'Đăng nhập', nghĩa là chưa đăng nhập
            login_buttons = self.driver.find_elements(
                By.XPATH,
                "//a[contains(text(), 'Đăng nhập') or contains(@href, 'account.1zone.vn')] | "
                "//button[contains(text(), 'Đăng nhập')]"
            )
            # Kiểm tra xem có button/a nào hiển thị không
            for btn in login_buttons:
                if btn.is_displayed():
                    return False
            return True
        except Exception:
            return False

    def close(self, force: bool = False):
        """Đóng trình duyệt (trừ khi bật detach để giữ cửa sổ mở cho người dùng xem)."""
        if self.driver:
            if not self.headless and self.detach and not force:
                logger.info("Chế độ hiển thị: Trình duyệt Chrome vẫn được giữ mở trên màn hình.")
                return
            try:
                self.driver.quit()
                logger.info("Đã đóng trình duyệt.")
            except Exception:
                pass
            self.driver = None


def main():
    parser = argparse.ArgumentParser(
        description="Tool Selenium đăng nhập tự động 1Zone.vn (ticket.1zone.vn)"
    )
    env_email = os.getenv("ZONE_EMAIL")
    env_password = os.getenv("ZONE_PASSWORD")

    parser.add_argument("-e", "--email", type=str, default=env_email, help="Email tài khoản 1Zone (hoặc cấu hình ZONE_EMAIL trong .env)")
    parser.add_argument("-p", "--password", type=str, default=env_password, help="Mật khẩu tài khoản 1Zone (hoặc cấu hình ZONE_PASSWORD trong .env)")
    parser.add_argument("--headless", action="store_true", help="Chạy ẩn trình duyệt (không hiện cửa sổ)")
    parser.add_argument("--no-detach", action="store_true", help="Tự động tắt trình duyệt khi chạy xong thay vì giữ mở")
    parser.add_argument("--interactive", action="store_true", help="Mở trình duyệt cho bạn tự đăng nhập (Google/Email), tool tự lưu cookie")
    parser.add_argument("--use-cookies", action="store_true", help="Đăng nhập lại bằng file cookie đã lưu từ trước")
    parser.add_argument("--cookie-file", type=str, default=DEFAULT_COOKIE_FILE, help="Đường dẫn file lưu/nạp cookies")
    parser.add_argument("--profile-dir", type=str, default=None, help="Thư mục Chrome Profile để lưu trạng thái phiên vĩnh viễn")
    parser.add_argument("--target-url", type=str, default="https://ticket.1zone.vn/events", help="URL chuyển tới sau khi đăng nhập")

    args = parser.parse_args()

    # Khởi tạo đối tượng 1ZoneLogin
    bot = OneZoneLogin(
        headless=args.headless,
        detach=not args.no_detach,
        user_data_dir=args.profile_dir,
        cookie_file=args.cookie_file
    )

    try:
        # Trường hợp 1: Sử dụng cookie có sẵn
        logged_in = False
        if args.use_cookies:
            logger.info("Bắt đầu đăng nhập bằng cookies đã lưu...")
            logged_in = bot.load_cookies(args.cookie_file)
            if not logged_in:
                logger.info("Cookie hết hạn hoặc không hợp lệ, chuyển sang yêu cầu đăng nhập trực tiếp...")

        # Trường hợp 2: Chế độ tương tác (mở trình duyệt đăng nhập tay/Google)
        if args.interactive and not logged_in:
            bot.interactive_login(target_url=args.target_url)

        # Trường hợp 3: Đăng nhập bằng Email/Password truyền từ dòng lệnh hoặc .env
        elif args.email and args.password and not logged_in:
            bot.login_with_credentials(
                email=args.email,
                password=args.password,
                target_redirect=args.target_url
            )

        # Trường hợp 4: Không truyền tham số -> Hiển thị menu tương tác
        elif not logged_in:
            print("\n" + "="*50)
            print("  TOOL ĐĂNG NHẬP 1ZONE.VN (SELENIUM)")
            print("="*50)
            print("1. Đăng nhập bằng Email & Mật khẩu")
            print("2. Mở trình duyệt để đăng nhập thủ công (Google / Email) & Lưu Cookies")
            print("3. Đăng nhập nhanh bằng Cookies đã lưu")
            print("4. Thoát")
            choice = input("\nChọn thao tác [1-4]: ").strip()

            if choice == "1":
                email = input("Nhập Email: ").strip()
                import getpass
                password = getpass.getpass("Nhập Mật khẩu: ").strip()
                bot.login_with_credentials(email, password, target_redirect=args.target_url)
            elif choice == "2":
                bot.interactive_login(target_url=args.target_url)
            elif choice == "3":
                bot.load_cookies(args.cookie_file)
            else:
                print("Đã thoát.")
                return

        # Giữ trình duyệt mở nếu không ở chế độ headless để người dùng thao tác tiếp
        if not args.headless and bot.driver:
            print("\n[INFO] Đăng nhập hoàn tất. Trình duyệt Chrome đang mở tại:", bot.driver.current_url)
            if not args.no_detach:
                print("[INFO] Chế độ hiển thị: Trình duyệt sẽ được giữ mở để bạn tiếp tục thao tác!")
            else:
                try:
                    if sys.stdin.isatty():
                        input("Nhấn ENTER trong cửa sổ dòng lệnh này để đóng trình duyệt...")
                    else:
                        time.sleep(5)
                except Exception:
                    pass

    finally:
        bot.close()


if __name__ == "__main__":
    main()
