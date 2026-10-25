"""
Tool tự động đăng nhập 1Zone, tìm sự kiện CAPITANEUS MUTABILIS (Captain Boy),
chọn vé đắt nhất (hạng WINTER - 3.690.000 VNĐ), vượt Cloudflare Turnstile, qua bước Add-ons
và điền form Checkout để ra mã VietQR (ZaloPay) trên 1Zone.vn.

Sự kiện: CAPITANEUS MUTABILIS (https://ticket.1zone.vn/events/capitaneus-mutabilis-2026?calendarId=XDacU6)
Hạng vé đắt nhất: WINTER (3.690.000 VNĐ - ZoneId: 6ad88e302c6887e6983dd94a)
Tài khoản: namtt867@gmail.com
Người mua: Trần Quốc Huy - 0965165562
"""

import os
import sys
import time
import json
import ctypes
import logging

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Bỏ qua lỗi Handle Invalid khi tắt trình duyệt trên Windows
original_del = getattr(uc.Chrome, "__del__", None)
def safe_del(self):
    try:
        if original_del:
            original_del(self)
    except Exception:
        pass
uc.Chrome.__del__ = safe_del

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger("1ZoneAutoBuy")

# Thông tin tài khoản và người nhận vé
ZONE_EMAIL = os.getenv("ZONE_EMAIL", "namtt867@gmail.com")
ZONE_PASSWORD = os.getenv("ZONE_PASSWORD", "5hAusrwE.aP!9qP")
BUYER_NAME = os.getenv("BUYER_NAME", "Trần Quốc Huy")
BUYER_PHONE = os.getenv("BUYER_PHONE", "0965165562")

# Cấu hình sự kiện mục tiêu: CAPITANEUS MUTABILIS
EVENT_PATH = os.getenv("EVENT_PATH", "capitaneus-mutabilis-2026")
CALENDAR_ID = os.getenv("CALENDAR_ID", "XDacU6")
TARGET_EVENT_URL = f"https://ticket.1zone.vn/events/{EVENT_PATH}?calendarId={CALENDAR_ID}"

# Danh sách thứ tự ưu tiên các hạng vé (từ đắt nhất đến thấp hơn)
PRIORITY_ZONES = [
    {"name": "WINTER", "price": 3690000, "zoneId": "6ad88e302c6887e6983dd94a"},
    {"name": "AUTUMN", "price": 2690000, "zoneId": "6ad88e342c6887e6983dd94e"},
    {"name": "SUMMER", "price": 1690000, "zoneId": "6ad88e372c6887e6983dd952"},
    {"name": "SPRING", "price": 990000, "zoneId": "6ad88e3a2c6887e6983dd956"},
    {"name": "SVIP B", "price": 5000000, "zoneId": "6ac63d87d518d1b28f588e00"},
]


TARGET_SALE_TIME = os.getenv("SALE_TIME", "12:00:00").strip()


def cleanup_zombie_chrome():
    """Tự động dọn dẹp các tiến trình Chrome tự động cũ bị treo để tránh màn hình đen hoặc xung đột cổng."""
    try:
        import subprocess
        ps_cmd = """
        Get-CimInstance Win32_Process -Filter "name = 'chrome.exe'" | Where-Object {
            $_.CommandLine -like "*remote-debugging-port*" -or $_.CommandLine -like "*scoped_dir*"
        } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }
        """
        subprocess.run(["powershell", "-NoProfile", "-Command", ps_cmd], capture_output=True, timeout=5)
        time.sleep(0.5)
    except Exception:
        pass


def bring_window_to_front():
    """Đưa cửa sổ Google Chrome lên vị trí ưu tiên và phóng to tối đa màn hình."""
    try:
        user32 = ctypes.windll.user32
        hwnd = user32.FindWindowW("Chrome_WidgetWin_1", None)
        if hwnd:
            user32.ShowWindow(hwnd, 3)  # SW_MAXIMIZE
            user32.SetForegroundWindow(hwnd)
            time.sleep(0.3)
    except Exception:
        pass


def show_banner(driver, title, message, bg_color="#ea580c"):
    """Hiển thị thông báo nổi bật trên màn hình Chrome."""
    try:
        driver.execute_script(f"""
            let old = document.getElementById('automation-banner');
            if (old) old.remove();
            let b = document.createElement('div');
            b.id = 'automation-banner';
            b.innerHTML = '<b>{title}</b><br>{message}';
            b.style.cssText = 'position:fixed;top:20px;left:50%;transform:translateX(-50%);background:{bg_color};color:white;padding:16px 36px;border-radius:14px;font-size:16px;font-weight:bold;z-index:99999999;box-shadow:0 10px 40px rgba(0,0,0,0.6);text-align:center;line-height:1.5;pointer-events:none;';
            document.body.appendChild(b);
        """)
    except Exception:
        pass


def navigate_to_target_event(driver):
    """
    Điều hướng đến sự kiện mục tiêu CAPITANEUS MUTABILIS:
    1. Thử truy cập thẳng link sự kiện: https://ticket.1zone.vn/events/capitaneus-mutabilis-2026?calendarId=XDacU6
    2. Nếu không được, vào trang /events tìm sự kiện chứa 'capitaneus' và click vào.
    """
    logger.info(f"Đang điều hướng trực tiếp tới sự kiện: {TARGET_EVENT_URL}...")
    show_banner(driver, "🎫 TÌM SỰ KIỆN", "Đang truy cập: CAPITANEUS MUTABILIS...", bg_color="#0284c7")
    driver.get(TARGET_EVENT_URL)
    time.sleep(3)

    # Kiểm tra nếu trang đã tải đúng sự kiện
    is_on_event = driver.execute_script("""
        let title = document.title || '';
        let body = document.body ? document.body.innerText : '';
        return title.toLowerCase().includes('capitaneus') || body.toLowerCase().includes('capitaneus');
    """)

    if is_on_event:
        logger.info(">>> Đã vào trang sự kiện CAPITANEUS MUTABILIS thành công qua đường dẫn trực tiếp! <<<")
        return True

    # Fallback: Vào trang /events để tìm sự kiện
    logger.warning("Đường dẫn trực tiếp chưa mở được, đang chuyển sang quét tìm tại https://ticket.1zone.vn/events...")
    show_banner(driver, "🔍 TÌM KIẾM SỰ KIỆN", "Đang quét danh sách sự kiện tìm 'CAPITANEUS'...", bg_color="#0284c7")
    driver.get("https://ticket.1zone.vn/events")
    time.sleep(4)

    # Tìm card hoặc button có chứa chữ capitaneus
    found_event = driver.execute_script("""
        let all = Array.from(document.querySelectorAll('*'));
        let target = all.find(el => {
            let t = (el.innerText || '').toLowerCase();
            return t.includes('capitaneus');
        });
        if (target) {
            let clickable = target.closest('a, button, [role=\"button\"], .cursor-pointer') || target;
            clickable.scrollIntoView({block: 'center'});
            clickable.click();
            return true;
        }
        return false;
    """)

    if found_event:
        logger.info("Đã tìm thấy và bấm vào sự kiện CAPITANEUS trên danh sách sự kiện.")
        time.sleep(4)
        return True

    logger.warning("Chưa tìm thấy sự kiện CAPITANEUS trên danh sách, tải lại trang trực tiếp...")
    driver.get(TARGET_EVENT_URL)
    time.sleep(3)
    return True


def wait_and_click_buy_ticket(driver, target_time_str: str = TARGET_SALE_TIME, timeout: int = 1800):
    """
    Chuyên dụng canh giờ G mở bán (chuẩn từng mili-giây):
    - Hỗ trợ người dùng mở tool treo trước 5 - 30 phút (ví dụ mở lúc 11:55:00 cho đợt mở bán 12:00:00).
    - Tính toán chính xác thời gian còn lại đến giờ G (12:00:00).
    - Hiển thị đồng hồ đếm ngược trực tiếp trên màn hình Chrome và terminal.
    - Duy trì phiên và làm mới trang định kỳ khi còn > 20 giây.
    - Tại thời điểm 11:59:48 (trước 12s): Làm mới trang lần cuối để nạp DOM mới nhất.
    - Từ 11:59:55: Ngừng hoàn toàn tải lại trang, chuyển sang chế độ quét cao tần (30ms).
    - Đúng 12:00:00.000: Bấm Mua vé hoặc kích hoạt trực tiếp vào /booking/ để khóa vé tức thì!
    """
    from datetime import datetime, timedelta

    logger.info("=" * 65)
    logger.info(f"KHỞI ĐỘNG CHẾ ĐỘ CANH GIỜ G MỞ BÁN (MỤC TIÊU: {target_time_str})")
    logger.info("=" * 65)

    booking_direct_url = f"https://ticket.1zone.vn/booking/{EVENT_PATH}?calendarId={CALENDAR_ID}"
    start_wait = time.time()
    last_refresh = time.time()
    final_refreshed = False

    while time.time() - start_wait < timeout:
        now = datetime.now()

        # Tính thời gian còn lại đến giờ G
        diff_sec = 0.0
        has_target = False
        if target_time_str:
            try:
                parts = [int(p) for p in target_time_str.split(":")]
                target_dt = now.replace(hour=parts[0], minute=parts[1], second=parts[2], microsecond=0)
                # Nếu đã quá giờ hôm nay hơn 1 tiếng, tính cho ngày mai
                if (now - target_dt).total_seconds() > 3600:
                    target_dt += timedelta(days=1)
                diff_sec = (target_dt - now).total_seconds()
                has_target = True
            except Exception:
                has_target = False

        # Nếu đã tới giờ G hoặc quá giờ G (trong khoảng -30s đến 0s)
        is_opening_time = has_target and (-120 <= diff_sec <= 0.1)

        # 1. Kiểm tra nếu đã ở trang booking
        if "/booking/" in driver.current_url:
            logger.info(f">>> ĐÃ VÀO TRANG ĐẶT VÉ SEATMAP: {driver.current_url} <<<")
            return True

        # 2. Thử bấm nút Mua vé trên trang
        buy_clicked = driver.execute_script("""
            let btns = Array.from(document.querySelectorAll('button')).filter(b => {
                let t = (b.innerText || '').trim();
                return t.includes('Mua vé') || t.includes('Chọn vé') || t.includes('Book ticket');
            });
            if (btns.length > 0 && !btns[0].disabled) {
                btns[0].scrollIntoView({block: 'center'});
                btns[0].click();
                return btns[0].innerText.trim();
            }
            return null;
        """)

        if buy_clicked:
            logger.info(f">>> ĐÃ BẤM THÀNH CÔNG NÚT '{buy_clicked}'! <<<")
            return True

        # 3. Nếu đúng thời khắc giờ G (12:00:00) mà nút trên web chưa kịp update giao diện:
        # Bắn trực tiếp vào URL /booking/ để vượt mặt tất cả người dùng khác!
        if is_opening_time:
            logger.info(">>> ĐÚNG 12:00:00 GIỜ G! KÍCH HOẠT VÀO THẲNG SƠ ĐỒ GHẾ /BOOKING/ <<<")
            driver.execute_script(f"window.location.href = '{booking_direct_url}';")
            time.sleep(1)
            if "/booking/" in driver.current_url:
                return True

        # 4. Quản lý trạng thái đếm ngược trước giờ G
        if has_target and diff_sec > 0:
            rem_m, rem_s = divmod(int(diff_sec), 60)
            countdown_str = f"{rem_m:02d} phút {rem_s:02d} giây"

            # Hiển thị banner đếm ngược trên màn hình Chrome
            show_banner(
                driver,
                f"⏱️ ĐẾM NGƯỢC GIỜ G: {target_time_str} (CÒN {countdown_str})",
                "Tool đang trực canh và giữ phiên... ĐÚNG 12:00:00 sẽ tự động giật vé tức thì!",
                bg_color="#0284c7"
            )

            # Khi còn từ 10s đến 12s trước giờ G: Làm mới trang LẦN CUỐI CÙNG để nạp phiên sạch nhất
            if 10 <= diff_sec <= 14 and not final_refreshed:
                final_refreshed = True
                logger.info(">>> THỜI ĐIỂM VÀNG (CÒN 12 GIÂY TRƯỚC 12:00:00): TẢI LẠI TRANG LẦN CUỐI <<<")
                driver.refresh()
                time.sleep(2)
                continue

            # Khi còn dưới 10 giây trước 12:00:00: TUYỆT ĐỐI KHÔNG REFRESH, chạy chế độ quét siêu tốc (30ms)!
            if diff_sec <= 10:
                time.sleep(0.03)
                continue

            # Nếu còn nhiều thời gian (> 20 giây): cứ mỗi 20 giây làm mới nhẹ để giữ phiên không bị ngủ
            if diff_sec > 20 and (time.time() - last_refresh > 20):
                last_refresh = time.time()
                logger.info(f"Đang canh giờ G [{target_time_str}] - Còn {countdown_str}... Giữ phiên hoạt động...")
                driver.refresh()
                time.sleep(2)

            time.sleep(0.4)
        else:
            # Trường hợp không có giờ cụ thể hoặc đang đợi mở bán tự động
            show_banner(driver, "⏳ CHỜ MỞ BÁN", "Đang canh nút 'Mua vé'... Ngay khi mở bán tool sẽ bấm ngay!", bg_color="#0284c7")
            if time.time() - last_refresh > 15:
                last_refresh = time.time()
                driver.refresh()
                time.sleep(2)
            time.sleep(0.3)

    logger.error("Hết thời gian chờ mở bán.")
    return False


def select_best_ticket_on_seatmap(driver, timeout: int = 30):
    """
    Chọn hạng vé đắt nhất (ưu tiên: WINTER 3.690.000đ -> AUTUMN -> SUMMER -> SPRING)
    trên sơ đồ ghế Konva Canvas.
    """
    logger.info("Đang tìm và chọn hạng vé cao nhất trên sơ đồ ghế...")
    show_banner(driver, "💎 CHỌN HẠNG VÉ", "Đang tìm hạng vé WINTER (3.690.000 VNĐ - Đắt nhất)...", bg_color="#ea580c")

    start_find = time.time()
    while time.time() - start_find < timeout:
        res = driver.execute_script("""
            if (!window.Konva || !window.Konva.stages || window.Konva.stages.length === 0) {
                return { status: 'waiting_konva' };
            }
            let stage = window.Konva.stages[0];
            let shapes = stage.find('Shape');

            // Danh sách ưu tiên các hạng vé
            let priorityNames = arguments[0];
            let priorityZoneIds = arguments[1];

            let targetShape = null;
            let matchedName = null;

            // Tìm theo thứ tự ưu tiên
            for (let i = 0; i < priorityNames.length; i++) {
                let name = priorityNames[i];
                let zid = priorityZoneIds[i];

                let found = shapes.find(s => s.attrs && (
                    (s.attrs.text && s.attrs.text.toUpperCase() === name.toUpperCase()) ||
                    (s.attrs.zoneId && s.attrs.zoneId === zid)
                ));
                if (found) {
                    targetShape = found;
                    matchedName = name;
                    break;
                }
            }

            // Fallback nếu không khớp tên: lấy shape ghế đầu tiên
            if (!targetShape) {
                targetShape = shapes.find(s => s.attrs && (s.attrs.name === 'seat' || s.attrs.zoneId));
                matchedName = targetShape ? (targetShape.attrs.text || 'Ghế đầu tiên') : null;
            }

            if (targetShape) {
                let canvas = document.querySelector('canvas');
                let canvasRect = canvas.getBoundingClientRect();
                let box = targetShape.getClientRect();
                let clientX = canvasRect.left + box.x + box.width / 2;
                let clientY = canvasRect.top + box.y + box.height / 2;

                targetShape.fire('click');
                let opts = { bubbles: true, cancelable: true, view: window, clientX: clientX, clientY: clientY, pointerId: 1, pointerType: 'mouse', isPrimary: true };
                canvas.dispatchEvent(new PointerEvent('pointerdown', opts));
                canvas.dispatchEvent(new MouseEvent('mousedown', opts));
                canvas.dispatchEvent(new PointerEvent('pointerup', opts));
                canvas.dispatchEvent(new MouseEvent('mouseup', opts));
                canvas.dispatchEvent(new MouseEvent('click', opts));

                return { status: 'clicked', name: matchedName };
            }

            return { status: 'no_shape_yet' };
        """, [z["name"] for z in PRIORITY_ZONES], [z["zoneId"] for z in PRIORITY_ZONES])

        if res.get("status") == "clicked":
            logger.info(f">>> ĐÃ CHỌN THÀNH CÔNG HẠNG VÉ: {res.get('name')}! <<<")
            time.sleep(0.1)
            return True

        time.sleep(0.05)

    logger.warning("Không thể click vào sơ đồ ghế trong thời gian quy định.")
    return False


def run_full_booking():
    print("\n" + "=" * 70)
    print("  TOOL TỰ ĐỘNG ĐẶT VÉ 1ZONE - CAPITANEUS MUTABILIS")
    print(f"  Sự kiện: CAPITANEUS MUTABILIS ({TARGET_EVENT_URL})")
    print(f"  Hạng vé mục tiêu: WINTER (3.690.000 VNĐ - Đắt nhất)")
    print(f"  Tài khoản: {ZONE_EMAIL}")
    print(f"  Người nhận vé: {BUYER_NAME} - {BUYER_PHONE}")
    print("=" * 70 + "\n")

    # Dọn dẹp tiến trình cũ để tránh màn hình đen / kẹt cổng
    cleanup_zombie_chrome()

    # 1. Khởi động Chrome chế độ Undetected chống bot detection & Cloudflare
    logger.info("Bước 1: Khởi động trình duyệt Google Chrome hiển thị...")
    options = uc.ChromeOptions()
    options.add_argument("--start-maximized")
    options.add_argument("--disable-popup-blocking")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    driver = uc.Chrome(options=options, headless=False, version_main=155)

    try:
        bring_window_to_front()

        # 2. Đăng nhập tươi tài khoản qua cổng SSO
        logger.info("Bước 2: Đăng nhập tươi tài khoản 1Zone qua cổng SSO...")
        login_url = (
            "https://account.1zone.vn/login?"
            "next=%2Fsso%2Fauthorize%3Flang%3Dvi%26redirect_uri%3D"
            "https%253A%252F%252Fticket.1zone.vn%252Fevents&lang=vi"
        )
        driver.get(login_url)

        wait = WebDriverWait(driver, 20)
        email_inp = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "input[name='email']")))
        pass_inp = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "input[name='password']")))

        show_banner(driver, "🔐 ĐANG ĐĂNG NHẬP", f"Đang đăng nhập tài khoản: {ZONE_EMAIL}...", bg_color="#0284c7")

        email_inp.clear()
        email_inp.send_keys(ZONE_EMAIL)
        pass_inp.clear()
        pass_inp.send_keys(ZONE_PASSWORD)

        time.sleep(0.1)
        submit_btn = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
        submit_btn.click()
        logger.info("Đã gửi thông tin đăng nhập, đang chờ chuyển hướng...")

        # Chờ chuyển hướng về ticket.1zone.vn/events
        start_wait_events = time.time()
        while time.time() - start_wait_events < 25:
            curr_url = driver.current_url
            if "ticket.1zone.vn/events" in curr_url:
                logger.info(f"Đã đăng nhập thành công vào: {curr_url}")
                break
            time.sleep(0.5)

        time.sleep(2)
        bring_window_to_front()

        # 3. Mở sự kiện CAPITANEUS MUTABILIS (trực tiếp hoặc quét qua trang /events)
        logger.info("Bước 3: Mở sự kiện CAPITANEUS MUTABILIS...")
        navigate_to_target_event(driver)

        # 4. Chờ và bấm nút "Mua vé" (hỗ trợ treo trước 5 - 30 phút canh giờ G)
        logger.info(f"Bước 4: Kiểm tra và canh nút 'Mua vé' đúng {TARGET_SALE_TIME}...")
        clicked_buy = wait_and_click_buy_ticket(driver, target_time_str=TARGET_SALE_TIME, timeout=1800)
        if not clicked_buy:
            logger.error("Không thể mở giao diện chọn vé. Vui lòng thử lại!")
            return

        # Chờ vào trang đặt chỗ booking
        start_booking = time.time()
        while time.time() - start_booking < 20:
            if "/booking/" in driver.current_url:
                break
            time.sleep(0.5)

        logger.info(f"Đã vào trang đặt chỗ: {driver.current_url}")
        time.sleep(2)
        bring_window_to_front()

        # 5. Chờ sơ đồ ghế Konva tải xong (Chế độ Turbo: quét 50ms)
        logger.info("Bước 5: Chờ sơ đồ ghế (Seatmap Canvas)...")
        show_banner(driver, "🗺️ SƠ ĐỒ GHẾ", "Đang tải sơ đồ ghế sự kiện...", bg_color="#0284c7")
        start_konva = time.time()
        while time.time() - start_konva < 20:
            has_konva = driver.execute_script(
                "return !!(window.Konva && window.Konva.stages && window.Konva.stages.length > 0);"
            )
            if has_konva:
                logger.info(f"Sơ đồ ghế Konva đã sẵn sàng (sau {time.time() - start_konva:.2f}s).")
                break
            time.sleep(0.05)

        # 6. Chọn hạng vé đắt nhất: WINTER (3.690.000 VNĐ) ngay lập tức
        logger.info("Bước 6: Tự động chọn hạng vé đắt nhất: WINTER (3.690.000 VNĐ)...")
        selected = select_best_ticket_on_seatmap(driver, timeout=20)
        if not selected:
            logger.error("Không thể chọn hạng vé trên sơ đồ.")
            return

        logger.info("Đã mở modal 'Chọn số lượng vé'.")

        # 7. Xử lý Cloudflare Turnstile và bấm nút Tiếp tục trong modal (quét 30ms)
        logger.info("Bước 7: Xác thực Cloudflare Turnstile và bấm 'Tiếp tục'...")
        start_cf = time.time()
        cf_success = False
        while time.time() - start_cf < 30:
            status = driver.execute_script("""
                let inp = document.querySelector('[name=\"cf-turnstile-response\"]');
                let btn = Array.from(document.querySelectorAll('button')).find(b => b.innerText.trim() === 'Tiếp tục');
                let token = inp ? inp.value : '';
                let ready = (token.length > 10) && btn && !btn.disabled;
                if (ready) {
                    btn.click();
                    return { ready: true, tokenLen: token.length };
                }
                return { ready: false, tokenLen: token.length };
            """)
            if status.get('ready'):
                logger.info(f">>> VƯỢT CLOUDFLARE TURNSTILE & BẤM TIẾP TỤC TỨC THÌ! Token: {status.get('tokenLen')} <<<")
                cf_success = True
                break
            time.sleep(0.03)

        # 8. Chờ chuyển hướng sang trang Add-ons hoặc Checkout (quét 50ms)
        logger.info("Bước 8: Chờ hệ thống chuyển hướng sang trang thanh toán...")
        start_redirect = time.time()
        while time.time() - start_redirect < 25:
            curr_url = driver.current_url
            if "/checkout/add-ons" in curr_url or "/checkout" in curr_url:
                logger.info(f"Đã chuyển hướng thành công tới: {curr_url}")
                break
            # Liên tục thử bấm Tiếp tục nếu modal vẫn mở
            driver.execute_script("""
                let btn = Array.from(document.querySelectorAll('button')).find(b => b.innerText.trim() === 'Tiếp tục');
                if (btn && !btn.disabled) btn.click();
            """)
            time.sleep(0.05)

        # 9. Xử lý trang Add-ons (https://ticket.1zone.vn/checkout/add-ons...) - Siêu tốc
        if "/checkout/add-ons" in driver.current_url:
            logger.info("Bước 9: Đang ở trang Add-ons, bấm 'Tiếp tục' / 'Bỏ qua bước này' ngay...")
            start_addon = time.time()
            while time.time() - start_addon < 10:
                clicked_addons = driver.execute_script("""
                    let btns = Array.from(document.querySelectorAll('button'));
                    let btn = btns.find(b => {
                        let t = b.innerText.trim().toLowerCase();
                        return (t.includes('tiếp tục') || t.includes('bỏ qua')) && !t.includes('quay lại');
                    });
                    if (btn) {
                        btn.click();
                        return btn.innerText.trim();
                    }
                    return null;
                """)
                if clicked_addons:
                    logger.info(f"Đã bấm nút trang Add-ons tức thì: '{clicked_addons}'")
                    break
                time.sleep(0.05)

        # 10. Chờ trang Checkout và thực hiện điền thông tin + chọn ZaloPay + bấm Thanh toán trong 1 đòn (Turbo)
        logger.info("Bước 10: Xử lý trang Checkout - Điền thông tin, chọn ZaloPay và bấm Thanh toán (Turbo)...")
        show_banner(driver, "⚡ THANH TOÁN SIÊU TỐC", f"Đang điền {BUYER_NAME} và hoàn tất thanh toán...", bg_color="#0284c7")

        start_checkout = time.time()
        submitted = False
        while time.time() - start_checkout < 20:
            if "/checkout?" in driver.current_url:
                # Thực hiện đồng thời cả 5 thao tác trong 0.05 giây
                res = driver.execute_script("""
                    let name = arguments[0];
                    let phone = arguments[1];

                    // 1. Điền họ và tên
                    let nameInp = Array.from(document.querySelectorAll('input')).find(i => 
                        i.name === 'fullName' || i.name === 'name' || (i.placeholder && i.placeholder.toLowerCase().includes('họ'))
                    );
                    if (nameInp) {
                        let s = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
                        s.call(nameInp, name);
                        nameInp.dispatchEvent(new Event('input', { bubbles: true }));
                        nameInp.dispatchEvent(new Event('change', { bubbles: true }));
                    }

                    // 2. Điền Số điện thoại
                    let phoneInp = Array.from(document.querySelectorAll('input')).find(i => 
                        i.name === 'phoneNumber' || i.name === 'phone' || (i.placeholder && i.placeholder.toLowerCase().includes('thoại'))
                    );
                    if (phoneInp) {
                        let s = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
                        s.call(phoneInp, phone);
                        phoneInp.dispatchEvent(new Event('input', { bubbles: true }));
                        phoneInp.dispatchEvent(new Event('change', { bubbles: true }));
                    }

                    // 3. Tick điều khoản
                    for (let cb of document.querySelectorAll('input[type="checkbox"]')) {
                        if (!cb.checked) {
                            cb.click();
                            cb.dispatchEvent(new Event('change', { bubbles: true }));
                        }
                    }

                    // 4. Chọn ZaloPay (VietQR)
                    let all = Array.from(document.querySelectorAll('div, label, span, p'));
                    let zOption = all.find(el => el.innerText && (el.innerText.includes('ZaloPay') || el.innerText.includes('VietQR')));
                    if (zOption) zOption.click();

                    // 5. Bấm nút Thanh toán
                    let btns = Array.from(document.querySelectorAll('button'));
                    let pBtn = btns.find(b => {
                        let t = b.innerText.trim().toLowerCase();
                        return t === 'thanh toán' || t.includes('thanh toán');
                    });
                    if (pBtn && !pBtn.disabled) {
                        pBtn.click();
                        return 'paid';
                    }
                    return 'filling';
                """, BUYER_NAME, BUYER_PHONE)

                if res == 'paid':
                    logger.info(">>> ĐÃ ĐIỀN THÔNG TIN, CHỌN ZALOPAY VÀ BẤM THANH TOÁN TRONG 0.05S! <<<")
                    submitted = True
                    break

            time.sleep(0.05)

        # 11. Chờ chuyển hướng sang cổng thanh toán VietQR (gateway.zalopay.vn)
        logger.info("Bước 11: Đang chờ chuyển hướng tới cổng thanh toán VietQR (gateway.zalopay.vn)...")
        start_gateway = time.time()
        qr_ready = False
        while time.time() - start_gateway < 35:
            curr = driver.current_url
            if "gateway.zalopay.vn" in curr or "vietqr" in curr:
                qr_ready = True
                break
            time.sleep(0.2)

        bring_window_to_front()

        if qr_ready:
            logger.info("==================================================================")
            logger.info(">>> THÀNH CÔNG RỰC RỠ! ĐÃ ĐẾN CỔNG THANH TOÁN ZALOPAY VIETQR! <<<")
            logger.info(f"URL: {driver.current_url}")
            logger.info("==================================================================")

            show_banner(
                driver,
                "🎉 ĐÃ ĐẾN CỔNG THANH TOÁN VIETQR THÀNH CÔNG!",
                "Quý khách vui lòng quét mã VietQR trên màn hình bằng ứng dụng ngân hàng để hoàn tất.",
                bg_color="#16a34a"
            )

            print("\n" + "=" * 70)
            print("  THÀNH CÔNG RỰC RỠ!")
            print(f"  Sự kiện: CAPITANEUS MUTABILIS")
            print(f"  Hạng vé: WINTER (3.690.000 VNĐ - Đắt nhất)")
            print(f"  Cổng thanh toán: {driver.current_url}")
            print("  Cửa sổ Chrome đang hiển thị mã VietQR trên màn hình của bạn!")
            print("=" * 70 + "\n")
        else:
            logger.warning(f"URL hiện tại chưa nhận diện được cổng VietQR: {driver.current_url}")

        # Giữ nguyên trình duyệt mở trên màn hình để người dùng quét mã
        logger.info("Trình duyệt đang được giữ mở trên màn hình để bạn quét mã thanh toán...")
        try:
            while True:
                time.sleep(10)
        except KeyboardInterrupt:
            logger.info("Người dùng đã dừng tool.")

    except Exception as e:
        logger.error(f"Lỗi: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    run_full_booking()
