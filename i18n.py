"""Lightweight backend i18n — translates JSON error/message fields via after_request.

Language is detected from the X-Lang request header (set by the frontend).
Falls back to Accept-Language, then defaults to zh-TW.
"""
import re as _re
from flask import request as _req
import json as _json

SUPPORTED_LANGS = {'zh-TW', 'en', 'ja', 'vi', 'th'}


def get_lang() -> str:
    lang = _req.headers.get('X-Lang', '').strip()
    if lang in SUPPORTED_LANGS:
        return lang
    al = _req.headers.get('Accept-Language', '')
    for part in al.split(','):
        code = part.split(';')[0].strip().lower()
        if code.startswith('zh'):
            return 'zh-TW'
        if code.startswith('ja'):
            return 'ja'
        if code.startswith('vi'):
            return 'vi'
        if code.startswith('th'):
            return 'th'
        if code.startswith('en'):
            return 'en'
    return 'zh-TW'


def translate_message(text: str, lang: str) -> str:
    if lang == 'zh-TW' or not text:
        return text
    if text in _EXACT:
        return _EXACT[text].get(lang, text)
    for pattern, tmpl in _REGEX:
        m = pattern.match(text)
        if m:
            return tmpl.get(lang, text).format(*m.groups())
    for prefix, tr in _PREFIX:
        if text.startswith(prefix):
            return tr.get(lang, prefix) + text[len(prefix):]
    for suffix, tr in _SUFFIX:
        if text.endswith(suffix):
            return text[:-len(suffix)] + tr.get(lang, suffix)
    return text


def register_translate_hook(app) -> None:
    """Register an after_request hook that auto-translates JSON error/message/detail fields."""
    @app.after_request
    def _translate_json(response):
        if not response.content_type or 'application/json' not in response.content_type:
            return response
        lang = get_lang()
        if lang == 'zh-TW':
            return response
        try:
            data = _json.loads(response.get_data(as_text=True))
            changed = False
            for key in ('error', 'message', 'detail'):
                if key in data and isinstance(data[key], str):
                    t = translate_message(data[key], lang)
                    if t != data[key]:
                        data[key] = t
                        changed = True
            if changed:
                response.set_data(_json.dumps(data, ensure_ascii=False))
        except Exception:
            pass
        return response


# ── Exact-match translations ──────────────────────────────────────────────────
_EXACT = {
    # Auth
    '請先登入': {
        'en': 'Please log in first',
        'ja': 'ログインしてください',
        'vi': 'Vui lòng đăng nhập trước',
        'th': 'กรุณาเข้าสู่ระบบก่อน',
    },
    '需要超級管理員權限': {
        'en': 'Super admin access required',
        'ja': 'スーパー管理者権限が必要です',
        'vi': 'Yêu cầu quyền quản trị viên cấp cao',
        'th': 'ต้องการสิทธิ์ผู้ดูแลระบบระดับสูง',
    },
    '需要管理員權限': {
        'en': 'Admin access required',
        'ja': '管理者権限が必要です',
        'vi': 'Yêu cầu quyền quản trị viên',
        'th': 'ต้องการสิทธิ์ผู้ดูแลระบบ',
    },
    '無權限': {
        'en': 'No permission',
        'ja': '権限がありません',
        'vi': 'Không có quyền',
        'th': 'ไม่มีสิทธิ์',
    },
    '未授權': {
        'en': 'Unauthorized',
        'ja': '未認証',
        'vi': 'Không được ủy quyền',
        'th': 'ไม่ได้รับอนุญาต',
    },
    # Credentials
    '帳號為必填': {
        'en': 'Username is required',
        'ja': 'ユーザー名は必須です',
        'vi': 'Tên tài khoản là bắt buộc',
        'th': 'ต้องระบุชื่อผู้ใช้',
    },
    '帳號已存在': {
        'en': 'Username already exists',
        'ja': 'このユーザー名はすでに使用されています',
        'vi': 'Tên tài khoản đã tồn tại',
        'th': 'ชื่อผู้ใช้นี้มีอยู่แล้ว',
    },
    '帳號不存在或已停用': {
        'en': 'Account not found or disabled',
        'ja': 'アカウントが存在しないか無効になっています',
        'vi': 'Tài khoản không tồn tại hoặc đã bị vô hiệu hóa',
        'th': 'ไม่พบบัญชีหรือบัญชีถูกปิดใช้งาน',
    },
    '帳號不存在': {
        'en': 'Account not found',
        'ja': 'アカウントが存在しません',
        'vi': 'Tài khoản không tồn tại',
        'th': 'ไม่พบบัญชีผู้ใช้',
    },
    '帳號或密碼錯誤': {
        'en': 'Incorrect username or password',
        'ja': 'ユーザー名またはパスワードが正しくありません',
        'vi': 'Tên tài khoản hoặc mật khẩu không đúng',
        'th': 'ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง',
    },
    '密碼至少 4 個字元': {
        'en': 'Password must be at least 4 characters',
        'ja': 'パスワードは4文字以上必要です',
        'vi': 'Mật khẩu phải có ít nhất 4 ký tự',
        'th': 'รหัสผ่านต้องมีอย่างน้อย 4 ตัวอักษร',
    },
    '請輸入帳號及密碼': {
        'en': 'Please enter username and password',
        'ja': 'ユーザー名とパスワードを入力してください',
        'vi': 'Vui lòng nhập tên tài khoản và mật khẩu',
        'th': 'กรุณาใส่ชื่อผู้ใช้และรหัสผ่าน',
    },
    '請輸入帳號與密碼': {
        'en': 'Please enter username and password',
        'ja': 'ユーザー名とパスワードを入力してください',
        'vi': 'Vui lòng nhập tên tài khoản và mật khẩu',
        'th': 'กรุณาใส่ชื่อผู้ใช้และรหัสผ่าน',
    },
    # Staff / name
    '姓名為必填': {
        'en': 'Name is required',
        'ja': '氏名は必須です',
        'vi': 'Họ tên là bắt buộc',
        'th': 'ต้องระบุชื่อ',
    },
    '姓名和帳號為必填': {
        'en': 'Name and username are required',
        'ja': '氏名とユーザー名は必須です',
        'vi': 'Họ tên và tên tài khoản là bắt buộc',
        'th': 'ต้องระบุชื่อและชื่อผู้ใช้',
    },
    '姓名或帳號已存在，請換一個': {
        'en': 'Name or username already exists, please choose another',
        'ja': '氏名またはユーザー名がすでに使用されています',
        'vi': 'Họ tên hoặc tên tài khoản đã tồn tại, vui lòng chọn tên khác',
        'th': 'ชื่อหรือชื่อผู้ใช้มีอยู่แล้ว กรุณาเปลี่ยนชื่อ',
    },
    '不能刪除自己的帳號': {
        'en': 'Cannot delete your own account',
        'ja': '自分のアカウントは削除できません',
        'vi': 'Không thể xóa tài khoản của chính bạn',
        'th': 'ไม่สามารถลบบัญชีของตัวเองได้',
    },
    '員工不存在': {
        'en': 'Employee not found',
        'ja': '従業員が存在しません',
        'vi': 'Nhân viên không tồn tại',
        'th': 'ไม่พบพนักงาน',
    },
    # Required fields
    '店名為必填': {
        'en': 'Store name is required',
        'ja': '店舗名は必須です',
        'vi': 'Tên cửa hàng là bắt buộc',
        'th': 'ต้องระบุชื่อร้าน',
    },
    '標題為必填': {
        'en': 'Title is required',
        'ja': 'タイトルは必須です',
        'vi': 'Tiêu đề là bắt buộc',
        'th': 'ต้องระบุหัวข้อ',
    },
    '日期為必填': {
        'en': 'Date is required',
        'ja': '日付は必須です',
        'vi': 'Ngày là bắt buộc',
        'th': 'ต้องระบุวันที่',
    },
    '名稱為必填': {
        'en': 'Name is required',
        'ja': '名前は必須です',
        'vi': 'Tên là bắt buộc',
        'th': 'ต้องระบุชื่อ',
    },
    '名稱必填': {
        'en': 'Name is required',
        'ja': '名前は必須です',
        'vi': 'Tên là bắt buộc',
        'th': 'ต้องระบุชื่อ',
    },
    '開始日期為必填': {
        'en': 'Start date is required',
        'ja': '開始日は必須です',
        'vi': 'Ngày bắt đầu là bắt buộc',
        'th': 'ต้องระบุวันที่เริ่มต้น',
    },
    '金額必填': {
        'en': 'Amount is required',
        'ja': '金額は必須です',
        'vi': 'Số tiền là bắt buộc',
        'th': 'ต้องระบุจำนวนเงิน',
    },
    '年月為必填': {
        'en': 'Year and month are required',
        'ja': '年月は必須です',
        'vi': 'Năm và tháng là bắt buộc',
        'th': 'ต้องระบุปีและเดือน',
    },
    '缺少必填欄位': {
        'en': 'Missing required fields',
        'ja': '必須項目が不足しています',
        'vi': 'Thiếu các trường bắt buộc',
        'th': 'ขาดข้อมูลที่จำเป็น',
    },
    '缺少必要欄位': {
        'en': 'Missing required fields',
        'ja': '必須項目が不足しています',
        'vi': 'Thiếu các trường bắt buộc',
        'th': 'ขาดข้อมูลที่จำเป็น',
    },
    # Date/time format
    '日期格式錯誤': {
        'en': 'Invalid date format',
        'ja': '日付の形式が正しくありません',
        'vi': 'Định dạng ngày không hợp lệ',
        'th': 'รูปแบบวันที่ไม่ถูกต้อง',
    },
    '月份格式錯誤': {
        'en': 'Invalid month format',
        'ja': '月の形式が正しくありません',
        'vi': 'Định dạng tháng không hợp lệ',
        'th': 'รูปแบบเดือนไม่ถูกต้อง',
    },
    '時間格式錯誤': {
        'en': 'Invalid time format',
        'ja': '時刻の形式が正しくありません',
        'vi': 'Định dạng giờ không hợp lệ',
        'th': 'รูปแบบเวลาไม่ถูกต้อง',
    },
    '格式錯誤': {
        'en': 'Invalid format',
        'ja': '形式が正しくありません',
        'vi': 'Định dạng không hợp lệ',
        'th': 'รูปแบบไม่ถูกต้อง',
    },
    # Punch
    '1 分鐘內已打過卡': {
        'en': 'Already punched within 1 minute',
        'ja': '1分以内にすでに打刻済みです',
        'vi': 'Đã chấm công trong vòng 1 phút',
        'th': 'ตอกบัตรไปแล้วภายใน 1 นาที',
    },
    '無效的打卡類型': {
        'en': 'Invalid punch type',
        'ja': '無効な打刻タイプです',
        'vi': 'Loại chấm công không hợp lệ',
        'th': 'ประเภทการตอกบัตรไม่ถูกต้อง',
    },
    '無法取得 GPS，請允許定位權限後重試': {
        'en': 'Unable to get GPS. Please allow location access and try again',
        'ja': 'GPSを取得できません。位置情報の許可をしてから再試行してください',
        'vi': 'Không thể lấy GPS. Vui lòng cho phép quyền vị trí và thử lại',
        'th': 'ไม่สามารถรับ GPS ได้ กรุณาอนุญาตการเข้าถึงตำแหน่งแล้วลองใหม่',
    },
    '管理員尚未設定任何打卡地點': {
        'en': 'No punch locations have been configured by admin',
        'ja': '管理者がまだ打刻場所を設定していません',
        'vi': 'Quản trị viên chưa thiết lập địa điểm chấm công',
        'th': 'ผู้ดูแลระบบยังไม่ได้ตั้งค่าสถานที่ตอกบัตร',
    },
    '此門市需要 GPS 定位才能打卡': {
        'en': 'This store requires GPS location to punch',
        'ja': 'この店舗ではGPS位置情報が必要です',
        'vi': 'Cửa hàng này yêu cầu GPS để chấm công',
        'th': 'ร้านนี้ต้องการ GPS เพื่อตอกบัตร',
    },
    '僅員工可打卡': {
        'en': 'Only employees can punch',
        'ja': '従業員のみ打刻できます',
        'vi': 'Chỉ nhân viên mới có thể chấm công',
        'th': 'เฉพาะพนักงานเท่านั้นที่สามารถตอกบัตรได้',
    },
    '僅員工可查詢': {
        'en': 'Only employees can query records',
        'ja': '従業員のみ照会できます',
        'vi': 'Chỉ nhân viên mới có thể truy vấn',
        'th': 'เฉพาะพนักงานเท่านั้นที่สามารถสอบถามได้',
    },
    '僅員工可申請': {
        'en': 'Only employees can submit requests',
        'ja': '従業員のみ申請できます',
        'vi': 'Chỉ nhân viên mới có thể gửi yêu cầu',
        'th': 'เฉพาะพนักงานเท่านั้นที่สามารถยื่นคำขอได้',
    },
    '請選擇補打時間': {
        'en': 'Please select a punch time',
        'ja': '補打時間を選択してください',
        'vi': 'Vui lòng chọn thời gian chấm công bù',
        'th': 'กรุณาเลือกเวลาตอกบัตรย้อนหลัง',
    },
    # Leave
    '請假天數不合理，請檢查日期': {
        'en': 'Invalid leave days, please check the dates',
        'ja': '休暇日数が不合理です。日付を確認してください',
        'vi': 'Số ngày nghỉ không hợp lệ, vui lòng kiểm tra ngày',
        'th': 'จำนวนวันลาไม่ถูกต้อง กรุณาตรวจสอบวันที่',
    },
    '找不到特休假類型': {
        'en': 'Leave type not found',
        'ja': '特別休暇タイプが見つかりません',
        'vi': 'Không tìm thấy loại nghỉ phép đặc biệt',
        'th': 'ไม่พบประเภทวันหยุดพิเศษ',
    },
    '找不到請假申請': {
        'en': 'Leave request not found',
        'ja': '休暇申請が見つかりません',
        'vi': 'Không tìm thấy đơn xin nghỉ',
        'th': 'ไม่พบคำขอลา',
    },
    '申請已審核，不可修改費用': {
        'en': 'Request already reviewed, cannot modify expenses',
        'ja': '申請はすでに審査済みです。費用は変更できません',
        'vi': 'Yêu cầu đã được xem xét, không thể sửa đổi chi phí',
        'th': 'คำขอได้รับการอนุมัติแล้ว ไม่สามารถแก้ไขค่าใช้จ่ายได้',
    },
    '請指定月份': {
        'en': 'Please specify a month',
        'ja': '月を指定してください',
        'vi': 'Vui lòng chỉ định tháng',
        'th': 'กรุณาระบุเดือน',
    },
    '請提供月份': {
        'en': 'Please provide a month',
        'ja': '月を指定してください',
        'vi': 'Vui lòng cung cấp tháng',
        'th': 'กรุณาระบุเดือน',
    },
    # Schedule
    '下班時間不得早於或等於上班時間': {
        'en': 'End time must be after start time',
        'ja': '終業時間は始業時間より後でなければなりません',
        'vi': 'Giờ tan ca phải sau giờ bắt đầu',
        'th': 'เวลาเลิกงานต้องหลังเวลาเริ่มงาน',
    },
    '上班時間不得晚於或等於已存在的下班時間': {
        'en': 'Start time must be before the existing end time',
        'ja': '始業時間は既存の終業時間より前でなければなりません',
        'vi': 'Giờ bắt đầu phải trước giờ tan ca hiện có',
        'th': 'เวลาเริ่มงานต้องก่อนเวลาเลิกงานที่มีอยู่',
    },
    # Overtime
    '請填寫加班日期及時間': {
        'en': 'Please fill in the overtime date and time',
        'ja': '残業日時を記入してください',
        'vi': 'Vui lòng điền ngày và giờ làm thêm',
        'th': 'กรุณากรอกวันที่และเวลาทำงานล่วงเวลา',
    },
    '請填寫加班原因': {
        'en': 'Please fill in the overtime reason',
        'ja': '残業理由を記入してください',
        'vi': 'Vui lòng điền lý do làm thêm giờ',
        'th': 'กรุณากรอกเหตุผลการทำงานล่วงเวลา',
    },
    '加班時數不合理（0~12小時）': {
        'en': 'Overtime hours invalid (must be 0–12 hours)',
        'ja': '残業時間が不合理です（0〜12時間）',
        'vi': 'Số giờ làm thêm không hợp lệ (phải từ 0–12 giờ)',
        'th': 'ชั่วโมงล่วงเวลาไม่ถูกต้อง (ต้องอยู่ระหว่าง 0–12 ชั่วโมง)',
    },
    # File upload
    '檔案大小不能超過 10MB': {
        'en': 'File size cannot exceed 10MB',
        'ja': 'ファイルサイズは10MB以下にしてください',
        'vi': 'Kích thước file không được vượt quá 10MB',
        'th': 'ขนาดไฟล์ต้องไม่เกิน 10MB',
    },
    '請選擇檔案': {
        'en': 'Please select a file',
        'ja': 'ファイルを選択してください',
        'vi': 'Vui lòng chọn file',
        'th': 'กรุณาเลือกไฟล์',
    },
    '請上傳 CSV 檔案': {
        'en': 'Please upload a CSV file',
        'ja': 'CSVファイルをアップロードしてください',
        'vi': 'Vui lòng tải lên file CSV',
        'th': 'กรุณาอัปโหลดไฟล์ CSV',
    },
    '請上傳圖片': {
        'en': 'Please upload an image',
        'ja': '画像をアップロードしてください',
        'vi': 'Vui lòng tải lên hình ảnh',
        'th': 'กรุณาอัปโหลดรูปภาพ',
    },
    '請上傳圖片或 PDF 檔案': {
        'en': 'Please upload an image or PDF file',
        'ja': '画像またはPDFファイルをアップロードしてください',
        'vi': 'Vui lòng tải lên hình ảnh hoặc file PDF',
        'th': 'กรุณาอัปโหลดรูปภาพหรือไฟล์ PDF',
    },
    'CSV 無資料': {
        'en': 'CSV has no data',
        'ja': 'CSVにデータがありません',
        'vi': 'CSV không có dữ liệu',
        'th': 'CSV ไม่มีข้อมูล',
    },
    '檔案內容為空': {
        'en': 'File is empty',
        'ja': 'ファイルの内容が空です',
        'vi': 'File rỗng',
        'th': 'ไฟล์ว่างเปล่า',
    },
    '無法解析 CSV 欄位': {
        'en': 'Cannot parse CSV columns',
        'ja': 'CSV列を解析できません',
        'vi': 'Không thể phân tích cột CSV',
        'th': 'ไม่สามารถแยกวิเคราะห์คอลัมน์ CSV ได้',
    },
    '無資料列': {
        'en': 'No data rows',
        'ja': 'データ行がありません',
        'vi': 'Không có dòng dữ liệu',
        'th': 'ไม่มีแถวข้อมูล',
    },
    '檔案缺少「姓名」或「代碼」欄位': {
        'en': 'File is missing the "Name" or "Code" column',
        'ja': 'ファイルに「名前」または「コード」列がありません',
        'vi': 'File thiếu cột "Họ tên" hoặc "Mã nhân viên"',
        'th': 'ไฟล์ขาดคอลัมน์ "ชื่อ" หรือ "รหัส"',
    },
    '檔案缺少「日期」欄位': {
        'en': 'File is missing the "Date" column',
        'ja': 'ファイルに「日付」列がありません',
        'vi': 'File thiếu cột "Ngày"',
        'th': 'ไฟล์ขาดคอลัมน์ "วันที่"',
    },
    '檔案缺少「班別」欄位': {
        'en': 'File is missing the "Shift" column',
        'ja': 'ファイルに「シフト」列がありません',
        'vi': 'File thiếu cột "Ca làm việc"',
        'th': 'ไฟล์ขาดคอลัมน์ "กะ"',
    },
    # Token
    'token 已過期，請重新登入': {
        'en': 'Token expired, please log in again',
        'ja': 'トークンが期限切れです。再度ログインしてください',
        'vi': 'Token đã hết hạn, vui lòng đăng nhập lại',
        'th': 'โทเค็นหมดอายุ กรุณาเข้าสู่ระบบอีกครั้ง',
    },
    'token 無效': {
        'en': 'Invalid token',
        'ja': 'トークンが無効です',
        'vi': 'Token không hợp lệ',
        'th': 'โทเค็นไม่ถูกต้อง',
    },
    '未設定 Token': {
        'en': 'Token not configured',
        'ja': 'トークンが設定されていません',
        'vi': 'Chưa cấu hình Token',
        'th': 'ยังไม่ได้ตั้งค่า Token',
    },
    '請先設定 Channel Access Token': {
        'en': 'Please configure the Channel Access Token first',
        'ja': 'まずChannel Access Tokenを設定してください',
        'vi': 'Vui lòng cấu hình Channel Access Token trước',
        'th': 'กรุณาตั้งค่า Channel Access Token ก่อน',
    },
    # System / API
    '尚未設定 ANTHROPIC_API_KEY 環境變數': {
        'en': 'ANTHROPIC_API_KEY environment variable is not set',
        'ja': 'ANTHROPIC_API_KEY 環境変数が設定されていません',
        'vi': 'Biến môi trường ANTHROPIC_API_KEY chưa được thiết lập',
        'th': 'ยังไม่ได้ตั้งค่าตัวแปรสภาพแวดล้อม ANTHROPIC_API_KEY',
    },
    '尚未設定 ANTHROPIC_API_KEY': {
        'en': 'ANTHROPIC_API_KEY is not set',
        'ja': 'ANTHROPIC_API_KEY が設定されていません',
        'vi': 'ANTHROPIC_API_KEY chưa được thiết lập',
        'th': 'ยังไม่ได้ตั้งค่า ANTHROPIC_API_KEY',
    },
    '參數錯誤': {
        'en': 'Invalid parameter',
        'ja': 'パラメータが正しくありません',
        'vi': 'Tham số không hợp lệ',
        'th': 'พารามิเตอร์ไม่ถูกต้อง',
    },
    '無效操作': {
        'en': 'Invalid operation',
        'ja': '無効な操作です',
        'vi': 'Thao tác không hợp lệ',
        'th': 'การดำเนินการไม่ถูกต้อง',
    },
    # Survey / rating
    '期別需為 1-6': {
        'en': 'Period must be between 1 and 6',
        'ja': '期別は1〜6の範囲で入力してください',
        'vi': 'Kỳ phải từ 1 đến 6',
        'th': 'ช่วงเวลาต้องอยู่ระหว่าง 1 ถึง 6',
    },
    '必須有一個評級的門檻設為 0%（作為最低等級）': {
        'en': 'One rating must have a threshold of 0% (as the lowest level)',
        'ja': '0%のしきい値を持つ評価が最低1つ必要です（最低レベルとして）',
        'vi': 'Phải có ít nhất một mức đánh giá với ngưỡng 0% (làm mức thấp nhất)',
        'th': 'ต้องมีระดับการให้คะแนนที่มีเกณฑ์ 0% อย่างน้อยหนึ่งระดับ (เป็นระดับต่ำสุด)',
    },
    '請至少設定一個評級': {
        'en': 'Please set at least one rating',
        'ja': '少なくとも1つの評価を設定してください',
        'vi': 'Vui lòng thiết lập ít nhất một mức đánh giá',
        'th': 'กรุณาตั้งค่าการให้คะแนนอย่างน้อยหนึ่งระดับ',
    },
    '評級代碼與標籤不可為空': {
        'en': 'Rating code and label cannot be empty',
        'ja': '評価コードとラベルは空にできません',
        'vi': 'Mã đánh giá và nhãn không được để trống',
        'th': 'รหัสและป้ายกำกับการให้คะแนนต้องไม่ว่างเปล่า',
    },
    '門檻百分比需介於 0~100': {
        'en': 'Threshold percentage must be between 0 and 100',
        'ja': 'しきい値のパーセンテージは0〜100の範囲で入力してください',
        'vi': 'Tỷ lệ phần trăm ngưỡng phải từ 0 đến 100',
        'th': 'เปอร์เซ็นต์เกณฑ์ต้องอยู่ระหว่าง 0 ถึง 100',
    },
    '調薪金額不可為 0': {
        'en': 'Salary adjustment amount cannot be 0',
        'ja': '昇給額は0にできません',
        'vi': 'Số tiền điều chỉnh lương không được là 0',
        'th': 'จำนวนการปรับเงินเดือนต้องไม่เป็น 0',
    },
    # Approval
    '找不到或已審核': {
        'en': 'Not found or already reviewed',
        'ja': '見つからないか、すでに審査済みです',
        'vi': 'Không tìm thấy hoặc đã được xem xét',
        'th': 'ไม่พบหรือได้รับการอนุมัติแล้ว',
    },
    '找不到或已審核，無法修改': {
        'en': 'Not found or already reviewed, cannot edit',
        'ja': '見つからないか、すでに審査済みのため変更できません',
        'vi': 'Không tìm thấy hoặc đã được xem xét, không thể chỉnh sửa',
        'th': 'ไม่พบหรือได้รับการอนุมัติแล้ว ไม่สามารถแก้ไขได้',
    },
    '找不到或申請已審核，不可刪除費用': {
        'en': 'Not found or request already reviewed, cannot delete expense',
        'ja': '見つからないか、申請がすでに審査済みのため費用を削除できません',
        'vi': 'Không tìm thấy hoặc yêu cầu đã được xem xét, không thể xóa chi phí',
        'th': 'ไม่พบหรือคำขอได้รับการอนุมัติแล้ว ไม่สามารถลบค่าใช้จ่ายได้',
    },
    '請選擇員工及日期': {
        'en': 'Please select an employee and date',
        'ja': '従業員と日付を選択してください',
        'vi': 'Vui lòng chọn nhân viên và ngày',
        'th': 'กรุณาเลือกพนักงานและวันที่',
    },
    '請選擇員工、班別及日期': {
        'en': 'Please select an employee, shift, and date',
        'ja': '従業員、シフト、日付を選択してください',
        'vi': 'Vui lòng chọn nhân viên, ca làm việc và ngày',
        'th': 'กรุณาเลือกพนักงาน กะ และวันที่',
    },
    '請選擇員工及考核期間': {
        'en': 'Please select an employee and review period',
        'ja': '従業員と考課期間を選択してください',
        'vi': 'Vui lòng chọn nhân viên và kỳ đánh giá',
        'th': 'กรุณาเลือกพนักงานและช่วงการประเมิน',
    },
    '請填寫日期和名稱': {
        'en': 'Please fill in the date and name',
        'ja': '日付と名前を記入してください',
        'vi': 'Vui lòng điền ngày và tên',
        'th': 'กรุณากรอกวันที่และชื่อ',
    },
    '請填寫公告標題': {
        'en': 'Please fill in the announcement title',
        'ja': 'お知らせのタイトルを記入してください',
        'vi': 'Vui lòng điền tiêu đề thông báo',
        'th': 'กรุณากรอกชื่อประกาศ',
    },
    '請填寫公告內容': {
        'en': 'Please fill in the announcement content',
        'ja': 'お知らせの内容を記入してください',
        'vi': 'Vui lòng điền nội dung thông báo',
        'th': 'กรุณากรอกเนื้อหาประกาศ',
    },
    '請填寫費用日期': {
        'en': 'Please fill in the expense date',
        'ja': '費用日を記入してください',
        'vi': 'Vui lòng điền ngày chi phí',
        'th': 'กรุณากรอกวันที่ค่าใช้จ่าย',
    },
    '請填寫標題': {
        'en': 'Please fill in the title',
        'ja': 'タイトルを記入してください',
        'vi': 'Vui lòng điền tiêu đề',
        'th': 'กรุณากรอกหัวข้อ',
    },
    '請填寫範本名稱': {
        'en': 'Please fill in the template name',
        'ja': 'テンプレート名を記入してください',
        'vi': 'Vui lòng điền tên mẫu',
        'th': 'กรุณากรอกชื่อแม่แบบ',
    },
    '請填寫離職日期': {
        'en': 'Please fill in the resignation date',
        'ja': '退職日を記入してください',
        'vi': 'Vui lòng điền ngày nghỉ việc',
        'th': 'กรุณากรอกวันที่ลาออก',
    },
    '請填入有效的緯度和經度': {
        'en': 'Please enter valid latitude and longitude',
        'ja': '有効な緯度と経度を入力してください',
        'vi': 'Vui lòng nhập vĩ độ và kinh độ hợp lệ',
        'th': 'กรุณาใส่ละติจูดและลองจิจูดที่ถูกต้อง',
    },
    '請選擇月份': {
        'en': 'Please select a month',
        'ja': '月を選択してください',
        'vi': 'Vui lòng chọn tháng',
        'th': 'กรุณาเลือกเดือน',
    },
    # Salary
    '薪資批次正在產生中，請稍後再試': {
        'en': 'Salary batch is being generated, please try again later',
        'ja': '給与バッチを生成中です。後でもう一度お試しください',
        'vi': 'Đang tạo bảng lương, vui lòng thử lại sau',
        'th': 'กำลังสร้างชุดเงินเดือน กรุณาลองใหม่ภายหลัง',
    },
    '無需同步的薪資記錄': {
        'en': 'No salary records to sync',
        'ja': '同期する給与記録はありません',
        'vi': 'Không có bảng lương cần đồng bộ',
        'th': 'ไม่มีบันทึกเงินเดือนที่ต้องซิงค์',
    },
    '稅額為零，無需建立分錄': {
        'en': 'Tax is zero, no entry required',
        'ja': '税額がゼロのため、仕訳は不要です',
        'vi': 'Thuế bằng không, không cần tạo bút toán',
        'th': 'ภาษีเป็นศูนย์ ไม่จำเป็นต้องสร้างรายการ',
    },
    # Assets
    '借用人及日期必填': {
        'en': 'Borrower and date are required',
        'ja': '借用者と日付は必須です',
        'vi': 'Người mượn và ngày là bắt buộc',
        'th': 'ต้องระบุผู้ยืมและวันที่',
    },
    '設備及借用日期必填': {
        'en': 'Equipment and loan date are required',
        'ja': '設備と借用日は必須です',
        'vi': 'Thiết bị và ngày mượn là bắt buộc',
        'th': 'ต้องระบุอุปกรณ์และวันที่ยืม',
    },
    '設備不存在': {
        'en': 'Equipment not found',
        'ja': '設備が存在しません',
        'vi': 'Thiết bị không tồn tại',
        'th': 'ไม่พบอุปกรณ์',
    },
    '此設備目前已被借出': {
        'en': 'This equipment is currently on loan',
        'ja': 'この設備は現在貸し出し中です',
        'vi': 'Thiết bị này hiện đang được mượn',
        'th': 'อุปกรณ์นี้กำลังถูกยืมอยู่',
    },
    '此設備目前無法借用': {
        'en': 'This equipment is currently unavailable for loan',
        'ja': 'この設備は現在借用できません',
        'vi': 'Thiết bị này hiện không thể mượn',
        'th': 'อุปกรณ์นี้ไม่สามารถยืมได้ในขณะนี้',
    },
    '您已有待審的借用申請': {
        'en': 'You already have a pending loan request',
        'ja': '審査中の借用申請がすでにあります',
        'vi': 'Bạn đã có yêu cầu mượn đang chờ xử lý',
        'th': 'คุณมีคำขอยืมที่รอดำเนินการอยู่แล้ว',
    },
    '僅可歸還借用中的設備': {
        'en': 'Can only return equipment that is currently on loan',
        'ja': '貸し出し中の設備のみ返却できます',
        'vi': 'Chỉ có thể trả lại thiết bị đang được mượn',
        'th': 'สามารถคืนได้เฉพาะอุปกรณ์ที่กำลังถูกยืมอยู่',
    },
    # WebAuthn
    '找不到已綁定的裝置，請先綁定': {
        'en': 'No registered device found, please register first',
        'ja': '登録済みのデバイスが見つかりません。先に登録してください',
        'vi': 'Không tìm thấy thiết bị đã đăng ký, vui lòng đăng ký trước',
        'th': 'ไม่พบอุปกรณ์ที่ลงทะเบียน กรุณาลงทะเบียนก่อน',
    },
    '找不到挑戰，請重新開始': {
        'en': 'Challenge not found, please start again',
        'ja': 'チャレンジが見つかりません。最初からやり直してください',
        'vi': 'Không tìm thấy challenge, vui lòng bắt đầu lại',
        'th': 'ไม่พบ challenge กรุณาเริ่มใหม่',
    },
    '未知帳號類型': {
        'en': 'Unknown account type',
        'ja': '不明なアカウントタイプです',
        'vi': 'Loại tài khoản không xác định',
        'th': 'ประเภทบัญชีที่ไม่รู้จัก',
    },
}

# ── Regex-match (complex dynamic patterns with captured groups) ───────────────
# Each entry: (compiled_pattern, {lang: format_string_with_{0}_{1}...})
_REGEX = [
    (
        _re.compile(r'^無「(.+?)」模組的存取權限$'),
        {
            'en': 'No access to the "{0}" module',
            'ja': '「{0}」モジュールへのアクセス権限がありません',
            'vi': 'Không có quyền truy cập module "{0}"',
            'th': 'ไม่มีสิทธิ์เข้าถึงโมดูล "{0}"',
        },
    ),
]

# ── Prefix-match (dynamic messages, variable suffix) ─────────────────────────
# Key = fixed Chinese prefix; value = {lang: translated prefix}
_PREFIX = list({
    '距離打卡地點 ': {
        'en': 'Distance from punch location: ',
        'ja': '打刻地点からの距離: ',
        'vi': 'Khoảng cách đến địa điểm chấm công: ',
        'th': 'ระยะห่างจากจุดตอกบัตร: ',
    },
    '該員工當日已有「': {
        'en': 'The employee already has a "',
        'ja': '従業員はすでにその日に「',
        'vi': 'Nhân viên đã có bản ghi "',
        'th': 'พนักงานมีรายการ "',
    },
    '申請天數（': {
        'en': 'Requested days (',
        'ja': '申請日数（',
        'vi': 'Số ngày yêu cầu (',
        'th': 'จำนวนวันที่ขอ (',
    },
    '以下日期休假人數已達上限：': {
        'en': 'The following dates have reached the maximum leave capacity: ',
        'ja': '以下の日付は休暇人数の上限に達しています：',
        'vi': 'Các ngày sau đây đã đạt số lượng nghỉ tối đa: ',
        'th': 'วันต่อไปนี้มีจำนวนการลาครบแล้ว: ',
    },
    '系統錯誤：': {
        'en': 'System error: ',
        'ja': 'システムエラー：',
        'vi': 'Lỗi hệ thống: ',
        'th': 'ข้อผิดพลาดของระบบ: ',
    },
    '新增失敗：': {
        'en': 'Creation failed: ',
        'ja': '追加に失敗しました：',
        'vi': 'Thêm mới thất bại: ',
        'th': 'การเพิ่มล้มเหลว: ',
    },
    '建立失敗 (': {
        'en': 'Creation failed (',
        'ja': '作成に失敗しました (',
        'vi': 'Tạo thất bại (',
        'th': 'การสร้างล้มเหลว (',
    },
    'OCR 失敗：': {
        'en': 'OCR failed: ',
        'ja': 'OCRに失敗しました：',
        'vi': 'OCR thất bại: ',
        'th': 'OCR ล้มเหลว: ',
    },
    '初始化失敗：': {
        'en': 'Initialization failed: ',
        'ja': '初期化に失敗しました：',
        'vi': 'Khởi tạo thất bại: ',
        'th': 'การเริ่มต้นล้มเหลว: ',
    },
    '綁定失敗：': {
        'en': 'Binding failed: ',
        'ja': '連携に失敗しました：',
        'vi': 'Liên kết thất bại: ',
        'th': 'การผูกล้มเหลว: ',
    },
    '驗證失敗：': {
        'en': 'Verification failed: ',
        'ja': '認証に失敗しました：',
        'vi': 'Xác minh thất bại: ',
        'th': 'การตรวจสอบล้มเหลว: ',
    },
    '日期 ': {
        'en': 'Date ',
        'ja': '日付 ',
        'vi': 'Ngày ',
        'th': 'วันที่ ',
    },
}.items())

# ── Suffix-match (dynamic messages, variable prefix) ─────────────────────────
# Key = fixed Chinese suffix; value = {lang: translated suffix}
_SUFFIX = list({
    ' 尚無薪資記錄，請聯絡管理員': {
        'en': ' has no salary record, please contact admin',
        'ja': ' の給与記録がありません。管理者にお問い合わせください',
        'vi': ' chưa có bảng lương, vui lòng liên hệ quản trị viên',
        'th': ' ยังไม่มีบันทึกเงินเดือน กรุณาติดต่อผู้ดูแลระบบ',
    },
}.items())
