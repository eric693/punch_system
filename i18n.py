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
    # LINE messages
    '目前無可用假別，請聯絡管理員。': {
        'en': 'No leave types available. Please contact admin.',
        'ja': '利用可能な休暇種別がありません。管理者にお問い合わせください。',
        'vi': 'Hiện không có loại nghỉ phép. Vui lòng liên hệ quản trị viên.',
        'th': 'ไม่มีประเภทการลาที่ใช้ได้ กรุณาติดต่อผู้ดูแลระบบ',
    },
    '已取消請假申請。': {
        'en': 'Leave request cancelled.',
        'ja': '休暇申請をキャンセルしました。',
        'vi': 'Đã hủy đơn xin nghỉ.',
        'th': 'ยกเลิกคำขอลาแล้ว',
    },
    '已取消加班申請。': {
        'en': 'Overtime request cancelled.',
        'ja': '残業申請をキャンセルしました。',
        'vi': 'Đã hủy đơn xin làm thêm giờ.',
        'th': 'ยกเลิกคำขอล่วงเวลาแล้ว',
    },
    '⚠️ 結束日期不能早於開始日期': {
        'en': '⚠️ End date cannot be earlier than start date',
        'ja': '⚠️ 終了日は開始日より前にできません',
        'vi': '⚠️ Ngày kết thúc không được sớm hơn ngày bắt đầu',
        'th': '⚠️ วันที่สิ้นสุดต้องไม่ก่อนวันที่เริ่มต้น',
    },
    '此帳號已綁定其他 LINE 帳號，請聯絡管理員。': {
        'en': 'This account is already linked to another LINE account. Please contact admin.',
        'ja': 'このアカウントはすでに別のLINEアカウントと連携されています。管理者にお問い合わせください。',
        'vi': 'Tài khoản này đã được liên kết với LINE khác. Vui lòng liên hệ quản trị viên.',
        'th': 'บัญชีนี้เชื่อมโยงกับ LINE อื่นแล้ว กรุณาติดต่อผู้ดูแลระบบ',
    },
    '已解除 LINE 帳號綁定。': {
        'en': 'LINE account unlinked.',
        'ja': 'LINEアカウントの連携を解除しました。',
        'vi': 'Đã hủy liên kết tài khoản LINE.',
        'th': 'ยกเลิกการเชื่อมโยงบัญชี LINE แล้ว',
    },
    '日期格式錯誤。': {
        'en': 'Invalid date format.',
        'ja': '日付の形式が正しくありません。',
        'vi': 'Định dạng ngày không hợp lệ.',
        'th': 'รูปแบบวันที่ไม่ถูกต้อง',
    },
    # Training export — column headers
    '員工代碼': {
        'en': 'Employee Code',
        'ja': '社員コード',
        'vi': 'Mã nhân viên',
        'th': 'รหัสพนักงาน',
    },
    '姓名': {
        'en': 'Name',
        'ja': '氏名',
        'vi': 'Họ tên',
        'th': 'ชื่อ',
    },
    '部門': {
        'en': 'Department',
        'ja': '部門',
        'vi': 'Phòng ban',
        'th': 'แผนก',
    },
    '課程名稱': {
        'en': 'Course Name',
        'ja': 'コース名',
        'vi': 'Tên khóa học',
        'th': 'ชื่อหลักสูตร',
    },
    '類別': {
        'en': 'Category',
        'ja': 'カテゴリ',
        'vi': 'Danh mục',
        'th': 'หมวดหมู่',
    },
    '完成日期': {
        'en': 'Completion Date',
        'ja': '修了日',
        'vi': 'Ngày hoàn thành',
        'th': 'วันที่เสร็จสิ้น',
    },
    '到期日期': {
        'en': 'Expiry Date',
        'ja': '有効期限',
        'vi': 'Ngày hết hạn',
        'th': 'วันที่หมดอายุ',
    },
    '剩餘天數': {
        'en': 'Days Remaining',
        'ja': '残り日数',
        'vi': 'Số ngày còn lại',
        'th': 'วันที่เหลือ',
    },
    '證書號碼': {
        'en': 'Certificate No.',
        'ja': '証明書番号',
        'vi': 'Số chứng chỉ',
        'th': 'หมายเลขใบรับรอง',
    },
    '狀態': {
        'en': 'Status',
        'ja': 'ステータス',
        'vi': 'Trạng thái',
        'th': 'สถานะ',
    },
    '備註': {
        'en': 'Notes',
        'ja': 'メモ',
        'vi': 'Ghi chú',
        'th': 'หมายเหตุ',
    },
    '員工': {
        'en': 'Employee',
        'ja': '従業員',
        'vi': 'Nhân viên',
        'th': 'พนักงาน',
    },
    '課程': {
        'en': 'Course',
        'ja': 'コース',
        'vi': 'Khóa học',
        'th': 'หลักสูตร',
    },
    '到期日': {
        'en': 'Expiry Date',
        'ja': '有効期限',
        'vi': 'Ngày hết hạn',
        'th': 'วันที่หมดอายุ',
    },
    # Training export — status labels
    '有效': {
        'en': 'Valid',
        'ja': '有効',
        'vi': 'Còn hiệu lực',
        'th': 'ใช้งานได้',
    },
    '已過期': {
        'en': 'Expired',
        'ja': '期限切れ',
        'vi': 'Đã hết hạn',
        'th': 'หมดอายุแล้ว',
    },
    '即將到期': {
        'en': 'Expiring Soon',
        'ja': 'もうすぐ期限切れ',
        'vi': 'Sắp hết hạn',
        'th': 'ใกล้หมดอายุ',
    },
    # Training export — sheet titles
    '訓練記錄': {
        'en': 'Training Records',
        'ja': '訓練記録',
        'vi': 'Hồ sơ đào tạo',
        'th': 'บันทึกการฝึกอบรม',
    },
    '到期摘要': {
        'en': 'Expiry Summary',
        'ja': '有効期限サマリー',
        'vi': 'Tóm tắt hết hạn',
        'th': 'สรุปการหมดอายุ',
    },
    # Training categories
    '食品安全': {
        'en': 'Food Safety',
        'ja': '食品安全',
        'vi': 'An toàn thực phẩm',
        'th': 'ความปลอดภัยด้านอาหาร',
    },
    '消防安全': {
        'en': 'Fire Safety',
        'ja': '消防安全',
        'vi': 'An toàn phòng cháy',
        'th': 'ความปลอดภัยด้านอัคคีภัย',
    },
    '急救訓練': {
        'en': 'First Aid',
        'ja': '救急訓練',
        'vi': 'Sơ cứu',
        'th': 'การปฐมพยาบาล',
    },
    '衛生管理': {
        'en': 'Hygiene Management',
        'ja': '衛生管理',
        'vi': 'Quản lý vệ sinh',
        'th': 'การจัดการสุขอนามัย',
    },
    '服務禮儀': {
        'en': 'Service Etiquette',
        'ja': 'サービスマナー',
        'vi': 'Lễ nghi phục vụ',
        'th': 'มารยาทการให้บริการ',
    },
    '設備操作': {
        'en': 'Equipment Operation',
        'ja': '機器操作',
        'vi': 'Vận hành thiết bị',
        'th': 'การใช้งานอุปกรณ์',
    },
    '一般訓練': {
        'en': 'General Training',
        'ja': '一般訓練',
        'vi': 'Đào tạo chung',
        'th': 'การฝึกอบรมทั่วไป',
    },
    '其他': {
        'en': 'Other',
        'ja': 'その他',
        'vi': 'Khác',
        'th': 'อื่นๆ',
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
    # LINE dynamic messages
    (
        _re.compile(r'^找不到假別「(.+?)」，請點選按鈕選擇。$'),
        {
            'en': 'Leave type "{0}" not found. Please select from the buttons.',
            'ja': '休暇種別「{0}」が見つかりません。ボタンから選択してください。',
            'vi': 'Không tìm thấy loại nghỉ phép "{0}". Vui lòng chọn từ các nút.',
            'th': 'ไม่พบประเภทการลา "{0}" กรุณาเลือกจากปุ่ม',
        },
    ),
    (
        _re.compile(r'^⚠️ 結束時間須晚於開始時間（(.+?)），請重新選擇。$'),
        {
            'en': '⚠️ End time must be after start time ({0}). Please reselect.',
            'ja': '⚠️ 終了時間は開始時間（{0}）より後でなければなりません。再度選択してください。',
            'vi': '⚠️ Thời gian kết thúc phải sau thời gian bắt đầu ({0}). Vui lòng chọn lại.',
            'th': '⚠️ เวลาสิ้นสุดต้องหลังเวลาเริ่มต้น ({0}) กรุณาเลือกใหม่',
        },
    ),
    (
        _re.compile(r'^⚠️ 加班時數異常（(.+?)h），請重新確認時間。$'),
        {
            'en': '⚠️ Overtime hours unusual ({0}h). Please recheck the times.',
            'ja': '⚠️ 残業時間が異常です（{0}h）。時間を再確認してください。',
            'vi': '⚠️ Số giờ làm thêm bất thường ({0}h). Vui lòng kiểm tra lại thời gian.',
            'th': '⚠️ ชั่วโมงล่วงเวลาผิดปกติ ({0}h) กรุณาตรวจสอบเวลาอีกครั้ง',
        },
    ),
    (
        _re.compile(r'^⚠️ 1 分鐘內已打過(.+?)，請勿重複打卡。$'),
        {
            'en': '⚠️ Already punched {0} within 1 minute. Please avoid duplicate punches.',
            'ja': '⚠️ 1分以内に{0}を打刻済みです。重複打刻はしないでください。',
            'vi': '⚠️ Đã chấm công {0} trong vòng 1 phút. Vui lòng không chấm công trùng lặp.',
            'th': '⚠️ ตอกบัตร {0} ไปแล้วภายใน 1 นาที กรุณาอย่าตอกบัตรซ้ำ',
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
    # LINE date/time error prefixes
    '日期格式錯誤，請輸入 YYYY-MM-DD，例：': {
        'en': 'Invalid date format. Please enter YYYY-MM-DD, e.g.: ',
        'ja': '日付の形式が正しくありません。YYYY-MM-DD形式で入力してください。例：',
        'vi': 'Định dạng ngày không hợp lệ. Vui lòng nhập YYYY-MM-DD, ví dụ: ',
        'th': 'รูปแบบวันที่ไม่ถูกต้อง กรุณาใส่ YYYY-MM-DD เช่น: ',
    },
    '⚠️ 時間格式錯誤，請輸入 HH:MM，例：': {
        'en': '⚠️ Invalid time format. Please enter HH:MM, e.g.: ',
        'ja': '⚠️ 時刻の形式が正しくありません。HH:MM形式で入力してください。例：',
        'vi': '⚠️ Định dạng giờ không hợp lệ. Vui lòng nhập HH:MM, ví dụ: ',
        'th': '⚠️ รูปแบบเวลาไม่ถูกต้อง กรุณาใส่ HH:MM เช่น: ',
    },
    '請輸入有效時間，格式：HH:MM，例：': {
        'en': 'Please enter a valid time. Format: HH:MM, e.g.: ',
        'ja': '有効な時刻を入力してください。形式：HH:MM。例：',
        'vi': 'Vui lòng nhập thời gian hợp lệ. Định dạng: HH:MM, ví dụ: ',
        'th': 'กรุณาใส่เวลาที่ถูกต้อง รูปแบบ: HH:MM เช่น: ',
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


# ── LINE message templates ────────────────────────────────────────────────────

def line_msg(key: str, lang: str, **kwargs) -> str:
    """Return a translated LINE message template, formatted with kwargs."""
    tmpl = _LINE_TMPL.get(key, {})
    text = tmpl.get(lang) or tmpl.get('zh-TW', key)
    if kwargs:
        try:
            return text.format(**kwargs)
        except (KeyError, IndexError):
            return (tmpl.get('zh-TW', key)).format(**kwargs)
    return text


_LINE_TMPL = {
    # ── Binding / follow flow ────────────────────────────────────────────
    'follow_welcome': {
        'zh-TW': '歡迎使用員工打卡系統！👋\n\n請輸入您的登入帳號完成綁定。\n\n✏️ 輸入範例：\n  綁定 mary123\n（請將 mary123 換成您自己的帳號）\n\n不知道帳號？請詢問管理員。',
        'en': 'Welcome to the Employee Punch-In System! 👋\n\nPlease enter your login account to complete binding.\n\n✏️ Example:\n  bind mary123\n(Replace mary123 with your own account)\n\nDon\'t know your account? Ask your admin.',
        'ja': '従業員打刻システムへようこそ！👋\n\nログインアカウントを入力して連携を完了してください。\n\n✏️ 入力例：\n  連携 mary123\n（mary123をご自身のアカウントに変更してください）\n\nアカウントがわからない場合は管理者にお問い合わせください。',
        'vi': 'Chào mừng đến với Hệ thống Chấm Công Nhân Viên! 👋\n\nVui lòng nhập tài khoản đăng nhập để hoàn tất liên kết.\n\n✏️ Ví dụ:\n  liên kết mary123\n(Thay mary123 bằng tài khoản của bạn)\n\nKhông biết tài khoản? Hỏi quản trị viên.',
        'th': 'ยินดีต้อนรับสู่ระบบตอกบัตรพนักงาน! 👋\n\nกรุณาใส่บัญชีเข้าสู่ระบบเพื่อผูกบัญชี\n\n✏️ ตัวอย่าง:\n  ผูก mary123\n(เปลี่ยน mary123 เป็นบัญชีของคุณ)\n\nไม่รู้บัญชี? ถามผู้ดูแลระบบ',
    },
    'bind_placeholder_error': {
        'zh-TW': '請輸入您「實際的」登入帳號，而非說明文字。\n\n範例：綁定 mary123',
        'en': 'Please enter your actual login account, not the example text.\n\nExample: bind mary123',
        'ja': '説明文ではなく、ご自身の実際のログインアカウントを入力してください。\n\n例：連携 mary123',
        'vi': 'Vui lòng nhập tài khoản đăng nhập thực tế của bạn, không phải văn bản ví dụ.\n\nVí dụ: liên kết mary123',
        'th': 'กรุณาใส่บัญชีเข้าสู่ระบบจริงของคุณ ไม่ใช่ข้อความตัวอย่าง\n\nตัวอย่าง: ผูก mary123',
    },
    'bind_account_not_found': {
        'zh-TW': '找不到帳號「{username}」\n\n請確認帳號是否正確，或詢問管理員您的登入帳號。',
        'en': 'Account "{username}" not found.\n\nPlease verify your account or ask your admin for your login account.',
        'ja': 'アカウント「{username}」が見つかりません。\n\nアカウントが正しいか確認するか、管理者にログインアカウントをお問い合わせください。',
        'vi': 'Không tìm thấy tài khoản "{username}".\n\nVui lòng xác nhận tài khoản hoặc hỏi quản trị viên về tài khoản đăng nhập của bạn.',
        'th': 'ไม่พบบัญชี "{username}"\n\nกรุณาตรวจสอบบัญชีหรือถามผู้ดูแลระบบ',
    },
    'bind_success': {
        'zh-TW': '✅ 綁定成功！\n歡迎 {name}！\n\n打卡方式：\n📍 傳送位置訊息 → 自動打卡\n💬 或輸入：上班 / 下班 / 休息 / 回來\n\n輸入「狀態」可查看今日打卡記錄。',
        'en': '✅ Account linked successfully!\nWelcome {name}!\n\nHow to punch:\n📍 Send location → Auto punch\n💬 Or type: Clock In / Clock Out / Break / Return\n\nType "Status" to view today\'s records.',
        'ja': '✅ 連携完了！\nようこそ {name}！\n\n打刻方法：\n📍 位置情報を送信 → 自動打刻\n💬 または入力：出勤 / 退勤 / 休憩 / 戻る\n\n「状態」と入力すると本日の打刻記録を確認できます。',
        'vi': '✅ Liên kết thành công!\nChào mừng {name}!\n\nCách chấm công:\n📍 Gửi vị trí → Tự động chấm công\n💬 Hoặc nhập: Vào ca / Ra ca / Nghỉ / Trở lại\n\nNhập "Trạng thái" để xem hồ sơ hôm nay.',
        'th': '✅ ผูกบัญชีสำเร็จ!\nยินดีต้อนรับ {name}!\n\nวิธีตอกบัตร:\n📍 ส่งตำแหน่ง → ตอกบัตรอัตโนมัติ\n💬 หรือพิมพ์: เข้างาน / ออกงาน / พัก / กลับมา\n\nพิมพ์ "สถานะ" เพื่อดูบันทึกวันนี้',
    },
    'bind_not_bound': {
        'zh-TW': '您尚未綁定打卡帳號。\n\n請輸入您的登入帳號：\n  綁定 [您的帳號]\n\n範例：綁定 mary123',
        'en': 'You have not linked a punch account yet.\n\nPlease enter your login account:\n  bind [your account]\n\nExample: bind mary123',
        'ja': 'まだ打刻アカウントが連携されていません。\n\nログインアカウントを入力してください：\n  連携 [あなたのアカウント]\n\n例：連携 mary123',
        'vi': 'Bạn chưa liên kết tài khoản chấm công.\n\nVui lòng nhập tài khoản đăng nhập:\n  liên kết [tài khoản của bạn]\n\nVí dụ: liên kết mary123',
        'th': 'คุณยังไม่ได้ผูกบัญชีตอกบัตร\n\nกรุณาใส่บัญชีเข้าสู่ระบบ:\n  ผูก [บัญชีของคุณ]\n\nตัวอย่าง: ผูก mary123',
    },
    # ── Punch type labels ────────────────────────────────────────────────
    'label_in': {
        'zh-TW': '上班打卡',
        'en': 'Clock In',
        'ja': '出勤打刻',
        'vi': 'Vào ca',
        'th': 'เข้างาน',
    },
    'label_out': {
        'zh-TW': '下班打卡',
        'en': 'Clock Out',
        'ja': '退勤打刻',
        'vi': 'Ra ca',
        'th': 'ออกงาน',
    },
    'label_break_out': {
        'zh-TW': '休息開始',
        'en': 'Break Start',
        'ja': '休憩開始',
        'vi': 'Bắt đầu nghỉ',
        'th': 'เริ่มพัก',
    },
    'label_break_in': {
        'zh-TW': '休息結束',
        'en': 'Break End',
        'ja': '休憩終了',
        'vi': 'Kết thúc nghỉ',
        'th': 'สิ้นสุดพัก',
    },
    'slabel_in': {
        'zh-TW': '上班',
        'en': 'In',
        'ja': '出勤',
        'vi': 'Vào',
        'th': 'เข้า',
    },
    'slabel_out': {
        'zh-TW': '下班',
        'en': 'Out',
        'ja': '退勤',
        'vi': 'Ra',
        'th': 'ออก',
    },
    'slabel_break_out': {
        'zh-TW': '休息開始',
        'en': 'Break',
        'ja': '休憩開始',
        'vi': 'Nghỉ',
        'th': 'พัก',
    },
    'slabel_break_in': {
        'zh-TW': '休息結束',
        'en': 'Return',
        'ja': '休憩終了',
        'vi': 'Trở lại',
        'th': 'กลับมา',
    },
    # ── Punch flow ───────────────────────────────────────────────────────
    'punch_loc_title': {
        'zh-TW': '📍 需要位置驗證',
        'en': '📍 Location Required',
        'ja': '📍 位置情報が必要です',
        'vi': '📍 Cần Xác Minh Vị Trí',
        'th': '📍 ต้องการการยืนยันตำแหน่ง',
    },
    'punch_loc_question': {
        'zh-TW': '請傳送您的位置來完成{action}',
        'en': 'Please send your location to complete {action}',
        'ja': '{action}を完了するために位置情報を送信してください',
        'vi': 'Vui lòng gửi vị trí của bạn để hoàn tất {action}',
        'th': 'กรุณาส่งตำแหน่งของคุณเพื่อทำ {action} ให้เสร็จ',
    },
    'punch_loc_hint': {
        'zh-TW': '點下方「傳送位置」按鈕即可打卡',
        'en': 'Tap the "Send Location" button below to punch',
        'ja': '下の「位置情報を送信」ボタンをタップして打刻してください',
        'vi': 'Nhấn nút "Gửi vị trí" bên dưới để chấm công',
        'th': 'แตะปุ่ม "ส่งตำแหน่ง" ด้านล่างเพื่อตอกบัตร',
    },
    'punch_btn_send_loc': {
        'zh-TW': '📍 傳送位置',
        'en': '📍 Send Location',
        'ja': '📍 位置情報を送信',
        'vi': '📍 Gửi vị trí',
        'th': '📍 ส่งตำแหน่ง',
    },
    'punch_already_out': {
        'zh-TW': '⚠️ 您已於 {mins} 分鐘前下班打卡，\n請確認是否要重新上班打卡？\n\n若要繼續，請再次點選「上班」。',
        'en': '⚠️ You clocked out {mins} minutes ago.\nDo you want to clock in again?\n\nTo continue, tap "Clock In" again.',
        'ja': '⚠️ {mins}分前に退勤打刻しました。\n再度出勤打刻しますか？\n\n続ける場合は「出勤」をもう一度タップしてください。',
        'vi': '⚠️ Bạn đã ra ca {mins} phút trước.\nBạn có muốn vào ca lại không?\n\nNếu muốn tiếp tục, nhấn "Vào ca" lại.',
        'th': '⚠️ คุณออกงานไป {mins} นาทีที่แล้ว\nต้องการเข้างานอีกครั้งหรือไม่?\n\nหากต้องการดำเนินการต่อ กรุณาแตะ "เข้างาน" อีกครั้ง',
    },
    'punch_gps_fail': {
        'zh-TW': '❌ {label}失敗\n您距離「{loc}」{dist} 公尺\n超出允許範圍 {radius} 公尺\n\n請確認您在正確地點後重試。',
        'en': '❌ {label} failed\nYou are {dist}m from "{loc}"\nExceeds allowed range of {radius}m\n\nPlease confirm you are at the correct location and try again.',
        'ja': '❌ {label}失敗\n「{loc}」から{dist}メートルの距離にいます\n許容範囲{radius}メートルを超えています\n\n正しい場所にいることを確認して再試行してください。',
        'vi': '❌ {label} thất bại\nBạn cách "{loc}" {dist} mét\nVượt quá phạm vi cho phép {radius} mét\n\nVui lòng xác nhận bạn ở đúng địa điểm và thử lại.',
        'th': '❌ {label} ล้มเหลว\nคุณอยู่ห่างจาก "{loc}" {dist} เมตร\nเกินระยะที่อนุญาต {radius} เมตร\n\nกรุณาตรวจสอบว่าคุณอยู่ในสถานที่ที่ถูกต้องแล้วลองใหม่',
    },
    'punch_success': {
        'zh-TW': '✅ {label}成功\n👤 {name}\n🕐 {time}{gps}',
        'en': '✅ {label} successful\n👤 {name}\n🕐 {time}{gps}',
        'ja': '✅ {label}成功\n👤 {name}\n🕐 {time}{gps}',
        'vi': '✅ {label} thành công\n👤 {name}\n🕐 {time}{gps}',
        'th': '✅ {label} สำเร็จ\n👤 {name}\n🕐 {time}{gps}',
    },
    # ── Status ───────────────────────────────────────────────────────────
    'status_no_records': {
        'zh-TW': '📋 {name} 今日尚無打卡記錄。',
        'en': '📋 {name} has no punch records today.',
        'ja': '📋 {name} は本日まだ打刻記録がありません。',
        'vi': '📋 {name} chưa có bản ghi chấm công hôm nay.',
        'th': '📋 {name} ยังไม่มีบันทึกตอกบัตรวันนี้',
    },
    'status_header': {
        'zh-TW': '📋 {name} 今日打卡記錄',
        'en': "📋 {name}'s Punch Records Today",
        'ja': '📋 {name} 本日の打刻記録',
        'vi': '📋 Bản ghi chấm công hôm nay của {name}',
        'th': '📋 บันทึกตอกบัตรวันนี้ของ {name}',
    },
    'status_manual': {
        'zh-TW': '[補打]',
        'en': '[Manual]',
        'ja': '[補打]',
        'vi': '[Bù]',
        'th': '[แก้ไข]',
    },
    # ── Leave flow ───────────────────────────────────────────────────────
    'leave_title': {
        'zh-TW': '📝 請假申請',
        'en': '📝 Leave Request',
        'ja': '📝 休暇申請',
        'vi': '📝 Đơn Xin Nghỉ',
        'th': '📝 คำขอลา',
    },
    'leave_select_type': {
        'zh-TW': '請選擇假別（第{page}頁，共{total}種）',
        'en': 'Select leave type (Page {page} of {total})',
        'ja': '休暇種別を選択してください（{page}ページ目、全{total}種）',
        'vi': 'Chọn loại nghỉ phép (Trang {page}/{total})',
        'th': 'เลือกประเภทการลา (หน้า {page}/{total})',
    },
    'leave_select_type_hint': {
        'zh-TW': '點選下方按鈕',
        'en': 'Tap the buttons below',
        'ja': '下のボタンをタップしてください',
        'vi': 'Nhấn các nút bên dưới',
        'th': 'แตะปุ่มด้านล่าง',
    },
    'leave_btn_more': {
        'zh-TW': '➡️ 更多',
        'en': '➡️ More',
        'ja': '➡️ 次へ',
        'vi': '➡️ Thêm',
        'th': '➡️ เพิ่มเติม',
    },
    'leave_btn_cancel': {
        'zh-TW': '❌ 取消',
        'en': '❌ Cancel',
        'ja': '❌ キャンセル',
        'vi': '❌ Hủy',
        'th': '❌ ยกเลิก',
    },
    'leave_input_start': {
        'zh-TW': '假別：{type}\n\n請輸入開始日期',
        'en': 'Leave type: {type}\n\nPlease enter start date',
        'ja': '休暇種別：{type}\n\n開始日を入力してください',
        'vi': 'Loại nghỉ: {type}\n\nVui lòng nhập ngày bắt đầu',
        'th': 'ประเภทการลา: {type}\n\nกรุณาใส่วันที่เริ่มต้น',
    },
    'leave_input_start_hint': {
        'zh-TW': '格式：YYYY-MM-DD，或點選快速選擇',
        'en': 'Format: YYYY-MM-DD, or tap quick select',
        'ja': '形式：YYYY-MM-DD、またはクイック選択をタップ',
        'vi': 'Định dạng: YYYY-MM-DD, hoặc nhấn chọn nhanh',
        'th': 'รูปแบบ: YYYY-MM-DD หรือแตะเพื่อเลือกเร็ว',
    },
    'leave_btn_today': {
        'zh-TW': '今天 ({date})',
        'en': 'Today ({date})',
        'ja': '今日 ({date})',
        'vi': 'Hôm nay ({date})',
        'th': 'วันนี้ ({date})',
    },
    'leave_btn_tomorrow': {
        'zh-TW': '明天 ({date})',
        'en': 'Tomorrow ({date})',
        'ja': '明日 ({date})',
        'vi': 'Ngày mai ({date})',
        'th': 'พรุ่งนี้ ({date})',
    },
    'leave_input_end': {
        'zh-TW': '開始日期：{start}\n\n請輸入結束日期',
        'en': 'Start date: {start}\n\nPlease enter end date',
        'ja': '開始日：{start}\n\n終了日を入力してください',
        'vi': 'Ngày bắt đầu: {start}\n\nVui lòng nhập ngày kết thúc',
        'th': 'วันที่เริ่มต้น: {start}\n\nกรุณาใส่วันที่สิ้นสุด',
    },
    'leave_input_end_hint': {
        'zh-TW': '單日假點「同一天」，多日請直接輸入',
        'en': 'For single day tap "Same day", for multiple days type the date',
        'ja': '1日の場合は「同じ日」をタップ、複数日は直接入力してください',
        'vi': 'Nghỉ 1 ngày nhấn "Cùng ngày", nhiều ngày nhập trực tiếp',
        'th': 'วันเดียวแตะ "วันเดียวกัน" หลายวันพิมพ์วันที่โดยตรง',
    },
    'leave_btn_same_day': {
        'zh-TW': '同一天',
        'en': 'Same day',
        'ja': '同じ日',
        'vi': 'Cùng ngày',
        'th': 'วันเดียวกัน',
    },
    'leave_input_start_time': {
        'zh-TW': '假別：{type}\n日期：{dates}\n\n請選擇開始時間',
        'en': 'Leave type: {type}\nDate: {dates}\n\nPlease select start time',
        'ja': '休暇種別：{type}\n日付：{dates}\n\n開始時間を選択してください',
        'vi': 'Loại nghỉ: {type}\nNgày: {dates}\n\nVui lòng chọn giờ bắt đầu',
        'th': 'ประเภทการลา: {type}\nวันที่: {dates}\n\nกรุณาเลือกเวลาเริ่มต้น',
    },
    'leave_input_end_time': {
        'zh-TW': '假別：{type}\n日期：{dates}\n開始：{start}\n\n請選擇結束時間',
        'en': 'Leave type: {type}\nDate: {dates}\nStart: {start}\n\nPlease select end time',
        'ja': '休暇種別：{type}\n日付：{dates}\n開始：{start}\n\n終了時間を選択してください',
        'vi': 'Loại nghỉ: {type}\nNgày: {dates}\nBắt đầu: {start}\n\nVui lòng chọn giờ kết thúc',
        'th': 'ประเภทการลา: {type}\nวันที่: {dates}\nเริ่ม: {start}\n\nกรุณาเลือกเวลาสิ้นสุด',
    },
    'leave_time_page_hint': {
        'zh-TW': '{page_label}　或直接輸入 HH:MM',
        'en': '{page_label}  or type HH:MM directly',
        'ja': '{page_label}　またはHH:MMを直接入力',
        'vi': '{page_label}  hoặc nhập HH:MM trực tiếp',
        'th': '{page_label}  หรือพิมพ์ HH:MM โดยตรง',
    },
    'leave_input_reason': {
        'zh-TW': '假別：{type}\n日期：{dates}\n時間：{start} ～ {end}\n\n請輸入請假原因',
        'en': 'Leave type: {type}\nDate: {dates}\nTime: {start} - {end}\n\nPlease enter leave reason',
        'ja': '休暇種別：{type}\n日付：{dates}\n時間：{start} ～ {end}\n\n休暇理由を入力してください',
        'vi': 'Loại nghỉ: {type}\nNgày: {dates}\nGiờ: {start} - {end}\n\nVui lòng nhập lý do nghỉ',
        'th': 'ประเภทการลา: {type}\nวันที่: {dates}\nเวลา: {start} - {end}\n\nกรุณาใส่เหตุผลการลา',
    },
    'leave_input_reason_hint': {
        'zh-TW': '或點「跳過」',
        'en': 'Or tap "Skip"',
        'ja': 'または「スキップ」をタップ',
        'vi': 'Hoặc nhấn "Bỏ qua"',
        'th': 'หรือแตะ "ข้าม"',
    },
    'leave_btn_skip': {
        'zh-TW': '跳過',
        'en': 'Skip',
        'ja': 'スキップ',
        'vi': 'Bỏ qua',
        'th': 'ข้าม',
    },
    'leave_insufficient_balance': {
        'zh-TW': '⚠️ {type} 餘額不足\n剩餘 {remain} 天，申請 {days} 天\n\n請至員工系統調整後再申請。',
        'en': '⚠️ {type} balance insufficient\nRemaining {remain} days, requested {days} days\n\nPlease adjust in the employee system before applying.',
        'ja': '⚠️ {type}の残日数が不足しています\n残り{remain}日、申請{days}日\n\n従業員システムで調整してから申請してください。',
        'vi': '⚠️ Số dư {type} không đủ\nCòn {remain} ngày, yêu cầu {days} ngày\n\nVui lòng điều chỉnh trong hệ thống trước khi nộp đơn.',
        'th': '⚠️ ยอดคงเหลือ {type} ไม่เพียงพอ\nเหลือ {remain} วัน ขอ {days} วัน\n\nกรุณาปรับในระบบพนักงานก่อนยื่นคำขอ',
    },
    'leave_submitted': {
        'zh-TW': '✅ 請假申請已送出\n\n假別：{type}{bal}\n日期：{dates}\n{time}天數：{days} 天\n{reason}申請號：#{id}，等待管理員審核。',
        'en': '✅ Leave request submitted\n\nType: {type}{bal}\nDate: {dates}\n{time}Days: {days}\n{reason}Request #: #{id}, awaiting admin approval.',
        'ja': '✅ 休暇申請を送信しました\n\n種別：{type}{bal}\n日付：{dates}\n{time}日数：{days}日\n{reason}申請番号：#{id}、管理者の承認をお待ちください。',
        'vi': '✅ Đã gửi đơn xin nghỉ\n\nLoại: {type}{bal}\nNgày: {dates}\n{time}Số ngày: {days}\n{reason}Số đơn: #{id}, chờ quản trị viên duyệt.',
        'th': '✅ ส่งคำขอลาแล้ว\n\nประเภท: {type}{bal}\nวันที่: {dates}\n{time}จำนวนวัน: {days}\n{reason}เลขที่: #{id} รอผู้ดูแลอนุมัติ',
    },
    'leave_bal_suffix': {
        'zh-TW': '（剩餘 {remain} 天）',
        'en': ' (Remaining: {remain} days)',
        'ja': '（残り{remain}日）',
        'vi': ' (Còn lại: {remain} ngày)',
        'th': ' (เหลือ: {remain} วัน)',
    },
    'leave_time_line': {
        'zh-TW': '時間：{time}\n',
        'en': 'Time: {time}\n',
        'ja': '時間：{time}\n',
        'vi': 'Giờ: {time}\n',
        'th': 'เวลา: {time}\n',
    },
    'leave_reason_line': {
        'zh-TW': '原因：{reason}\n',
        'en': 'Reason: {reason}\n',
        'ja': '理由：{reason}\n',
        'vi': 'Lý do: {reason}\n',
        'th': 'เหตุผล: {reason}\n',
    },
    'leave_not_found_with_avail': {
        'zh-TW': '找不到假別「{type}」\n可用：{avail}',
        'en': 'Leave type "{type}" not found\nAvailable: {avail}',
        'ja': '休暇種別「{type}」が見つかりません\n利用可能：{avail}',
        'vi': 'Không tìm thấy loại nghỉ "{type}"\nCó sẵn: {avail}',
        'th': 'ไม่พบประเภทการลา "{type}"\nที่มี: {avail}',
    },
    'leave_type_not_found_names': {
        'zh-TW': '找不到假別「{type}」\n\n可用假別：{names}',
        'en': 'Leave type "{type}" not found\n\nAvailable types: {names}',
        'ja': '休暇種別「{type}」が見つかりません\n\n利用可能な種別：{names}',
        'vi': 'Không tìm thấy loại nghỉ "{type}"\n\nCác loại có sẵn: {names}',
        'th': 'ไม่พบประเภทการลา "{type}"\n\nประเภทที่มี: {names}',
    },
    'leave_format_help': {
        'zh-TW': '請假格式：\n請假 [假別] [日期]\n\n範例：\n請假 特休 2026-04-01\n請假 事假 2026-04-01 2026-04-02 家庭事務\n\n輸入「假別」查看可用假別。',
        'en': 'Leave format:\nleave [type] [date]\n\nExamples:\nleave annual 2026-04-01\nleave personal 2026-04-01 2026-04-02 Family matters\n\nType "leave types" to see available types.',
        'ja': '休暇申請の形式：\n休暇 [種別] [日付]\n\n例：\n休暇 特別休暇 2026-04-01\n休暇 私事 2026-04-01 2026-04-02 家庭の用事\n\n「休暇種別」と入力すると利用可能な種別を確認できます。',
        'vi': 'Định dạng nghỉ phép:\nnghỉ [loại] [ngày]\n\nVí dụ:\nnghỉ phép năm 2026-04-01\nnghỉ việc riêng 2026-04-01 2026-04-02 Việc gia đình\n\nNhập "loại nghỉ" để xem các loại có sẵn.',
        'th': 'รูปแบบการลา:\nลา [ประเภท] [วันที่]\n\nตัวอย่าง:\nลา พักร้อน 2026-04-01\nลา กิจส่วนตัว 2026-04-01 2026-04-02 ธุระครอบครัว\n\nพิมพ์ "ประเภทการลา" เพื่อดูประเภทที่มี',
    },
    'leave_date_format_error': {
        'zh-TW': '日期格式錯誤，請使用 YYYY-MM-DD，例：{today}',
        'en': 'Invalid date format. Please use YYYY-MM-DD, e.g.: {today}',
        'ja': '日付の形式が正しくありません。YYYY-MM-DD形式を使用してください。例：{today}',
        'vi': 'Định dạng ngày không hợp lệ. Vui lòng dùng YYYY-MM-DD, ví dụ: {today}',
        'th': 'รูปแบบวันที่ไม่ถูกต้อง กรุณาใช้ YYYY-MM-DD เช่น: {today}',
    },
    # ── Overtime flow ────────────────────────────────────────────────────
    'ot_title': {
        'zh-TW': '⏰ 加班申請',
        'en': '⏰ Overtime Request',
        'ja': '⏰ 残業申請',
        'vi': '⏰ Đơn Làm Thêm Giờ',
        'th': '⏰ คำขอล่วงเวลา',
    },
    'ot_select_date': {
        'zh-TW': '請選擇加班日期',
        'en': 'Please select overtime date',
        'ja': '残業日を選択してください',
        'vi': 'Vui lòng chọn ngày làm thêm',
        'th': 'กรุณาเลือกวันที่ทำงานล่วงเวลา',
    },
    'ot_select_date_hint': {
        'zh-TW': '或直接輸入 YYYY-MM-DD',
        'en': 'Or type YYYY-MM-DD directly',
        'ja': 'またはYYYY-MM-DDを直接入力',
        'vi': 'Hoặc nhập YYYY-MM-DD trực tiếp',
        'th': 'หรือพิมพ์ YYYY-MM-DD โดยตรง',
    },
    'ot_select_start_time': {
        'zh-TW': '加班日期：{date}\n\n請選擇或輸入開始時間',
        'en': 'Overtime date: {date}\n\nPlease select or enter start time',
        'ja': '残業日：{date}\n\n開始時間を選択または入力してください',
        'vi': 'Ngày làm thêm: {date}\n\nVui lòng chọn hoặc nhập giờ bắt đầu',
        'th': 'วันที่ทำงานล่วงเวลา: {date}\n\nกรุณาเลือกหรือใส่เวลาเริ่มต้น',
    },
    'ot_select_start_time_hint': {
        'zh-TW': '格式：HH:MM，例：18:00',
        'en': 'Format: HH:MM, e.g.: 18:00',
        'ja': '形式：HH:MM、例：18:00',
        'vi': 'Định dạng: HH:MM, ví dụ: 18:00',
        'th': 'รูปแบบ: HH:MM เช่น: 18:00',
    },
    'ot_select_end_time': {
        'zh-TW': '加班日期：{date}\n開始：{start}\n\n請選擇或輸入結束時間',
        'en': 'Overtime date: {date}\nStart: {start}\n\nPlease select or enter end time',
        'ja': '残業日：{date}\n開始：{start}\n\n終了時間を選択または入力してください',
        'vi': 'Ngày làm thêm: {date}\nBắt đầu: {start}\n\nVui lòng chọn hoặc nhập giờ kết thúc',
        'th': 'วันที่ทำงานล่วงเวลา: {date}\nเริ่ม: {start}\n\nกรุณาเลือกหรือใส่เวลาสิ้นสุด',
    },
    'ot_select_end_time_hint': {
        'zh-TW': '格式：HH:MM',
        'en': 'Format: HH:MM',
        'ja': '形式：HH:MM',
        'vi': 'Định dạng: HH:MM',
        'th': 'รูปแบบ: HH:MM',
    },
    'ot_input_reason': {
        'zh-TW': '加班日期：{date}\n時間：{start} ～ {end}\n時數：{hrs}h\n\n請輸入加班原因',
        'en': 'Overtime date: {date}\nTime: {start} - {end}\nHours: {hrs}h\n\nPlease enter overtime reason',
        'ja': '残業日：{date}\n時間：{start} ～ {end}\n時数：{hrs}h\n\n残業理由を入力してください',
        'vi': 'Ngày làm thêm: {date}\nGiờ: {start} - {end}\nSố giờ: {hrs}h\n\nVui lòng nhập lý do làm thêm',
        'th': 'วันที่ทำงานล่วงเวลา: {date}\nเวลา: {start} - {end}\nชั่วโมง: {hrs}h\n\nกรุณาใส่เหตุผลการทำงานล่วงเวลา',
    },
    'ot_input_reason_hint': {
        'zh-TW': '或點「跳過」',
        'en': 'Or tap "Skip"',
        'ja': 'または「スキップ」をタップ',
        'vi': 'Hoặc nhấn "Bỏ qua"',
        'th': 'หรือแตะ "ข้าม"',
    },
    'ot_btn_skip': {
        'zh-TW': '跳過',
        'en': 'Skip',
        'ja': 'スキップ',
        'vi': 'Bỏ qua',
        'th': 'ข้าม',
    },
    'ot_submitted': {
        'zh-TW': '✅ 加班申請已送出\n\n日期：{date}\n時間：{start} ～ {end}\n時數：{hrs}h\n{reason}申請編號：#{id}\n\n請等候管理員審核，審核結果將通知您。',
        'en': '✅ Overtime request submitted\n\nDate: {date}\nTime: {start} - {end}\nHours: {hrs}h\n{reason}Request #: #{id}\n\nPlease wait for admin review. You will be notified of the result.',
        'ja': '✅ 残業申請を送信しました\n\n日付：{date}\n時間：{start} ～ {end}\n時数：{hrs}h\n{reason}申請番号：#{id}\n\n管理者の審査をお待ちください。審査結果はお知らせします。',
        'vi': '✅ Đã gửi đơn làm thêm giờ\n\nNgày: {date}\nGiờ: {start} - {end}\nSố giờ: {hrs}h\n{reason}Số đơn: #{id}\n\nVui lòng chờ quản trị viên xét duyệt. Bạn sẽ được thông báo kết quả.',
        'th': '✅ ส่งคำขอล่วงเวลาแล้ว\n\nวันที่: {date}\nเวลา: {start} - {end}\nชั่วโมง: {hrs}h\n{reason}เลขที่: #{id}\n\nกรุณารอผู้ดูแลตรวจสอบ คุณจะได้รับการแจ้งเตือนผล',
    },
    'ot_reason_line': {
        'zh-TW': '原因：{reason}\n',
        'en': 'Reason: {reason}\n',
        'ja': '理由：{reason}\n',
        'vi': 'Lý do: {reason}\n',
        'th': 'เหตุผล: {reason}\n',
    },
    'ot_format_help': {
        'zh-TW': '加班申請格式：\n加班 [日期] [時數] [原因]\n\n範例：加班 2026-04-05 3 業績衝刺\n（時數可用小數，如 1.5）',
        'en': 'Overtime format:\novertime [date] [hours] [reason]\n\nExample: overtime 2026-04-05 3 Sales push\n(Hours can be decimal, e.g. 1.5)',
        'ja': '残業申請の形式：\n残業 [日付] [時間] [理由]\n\n例：残業 2026-04-05 3 業績向上\n（時間は小数可、例：1.5）',
        'vi': 'Định dạng làm thêm:\nlàm thêm [ngày] [giờ] [lý do]\n\nVí dụ: làm thêm 2026-04-05 3 Đẩy doanh số\n(Giờ có thể là số thập phân, ví dụ 1.5)',
        'th': 'รูปแบบล่วงเวลา:\nล่วงเวลา [วันที่] [ชั่วโมง] [เหตุผล]\n\nตัวอย่าง: ล่วงเวลา 2026-04-05 3 ดันยอดขาย\n(ชั่วโมงเป็นทศนิยมได้ เช่น 1.5)',
    },
    'ot_invalid_hours': {
        'zh-TW': '加班時數需為 0.5～24 之間的數字',
        'en': 'Overtime hours must be a number between 0.5 and 24',
        'ja': '残業時間は0.5〜24の数字である必要があります',
        'vi': 'Số giờ làm thêm phải là số từ 0.5 đến 24',
        'th': 'ชั่วโมงล่วงเวลาต้องเป็นตัวเลขระหว่าง 0.5 ถึง 24',
    },
    # ── Leave balance query ───────────────────────────────────────────────
    'bal_error': {
        'zh-TW': '查詢失敗：{e}',
        'en': 'Query failed: {e}',
        'ja': '照会に失敗しました：{e}',
        'vi': 'Truy vấn thất bại: {e}',
        'th': 'การค้นหาล้มเหลว: {e}',
    },
    'bal_no_records': {
        'zh-TW': '📋 {name} {year} 年\n尚無假期餘額記錄，請聯絡管理員。',
        'en': '📋 {name} {year}\nNo leave balance records found. Please contact admin.',
        'ja': '📋 {name} {year}年\n休暇残日数の記録がありません。管理者にお問い合わせください。',
        'vi': '📋 {name} {year}\nChưa có bản ghi số dư nghỉ phép. Vui lòng liên hệ quản trị viên.',
        'th': '📋 {name} {year}\nไม่มีบันทึกยอดคงเหลือวันลา กรุณาติดต่อผู้ดูแลระบบ',
    },
    'bal_header': {
        'zh-TW': '📋 {name} {year} 年假期餘額',
        'en': '📋 {name} {year} Leave Balance',
        'ja': '📋 {name} {year}年 休暇残日数',
        'vi': '📋 Số dư nghỉ phép {year} của {name}',
        'th': '📋 ยอดคงเหลือวันลาปี {year} ของ {name}',
    },
    'bal_row': {
        'zh-TW': '\n【{type}】\n  剩餘 {remain} 天 / 共 {total} 天\n  {bar}',
        'en': '\n[{type}]\n  Remaining {remain} / Total {total} days\n  {bar}',
        'ja': '\n【{type}】\n  残り{remain}日 / 合計{total}日\n  {bar}',
        'vi': '\n[{type}]\n  Còn lại {remain} / Tổng {total} ngày\n  {bar}',
        'th': '\n[{type}]\n  เหลือ {remain} / รวม {total} วัน\n  {bar}',
    },
    # ── Salary query ─────────────────────────────────────────────────────
    'salary_error': {
        'zh-TW': '查詢失敗：{e}',
        'en': 'Query failed: {e}',
        'ja': '照会に失敗しました：{e}',
        'vi': 'Truy vấn thất bại: {e}',
        'th': 'การค้นหาล้มเหลว: {e}',
    },
    'salary_no_records': {
        'zh-TW': '📊 {name}\n尚無薪資記錄。',
        'en': '📊 {name}\nNo salary records found.',
        'ja': '📊 {name}\n給与記録がありません。',
        'vi': '📊 {name}\nChưa có bản ghi lương.',
        'th': '📊 {name}\nไม่มีบันทึกเงินเดือน',
    },
    'salary_body': {
        'zh-TW': '📊 {name} {month} 薪資\n\n底薪：NT$ {base:,.0f}\n津貼：NT$ {allow:,.0f}\n加班費：NT$ {ot:,.0f}\n扣除：NT$ {ded:,.0f}\n━━━━━━━━━━━━\n實領：NT$ {net:,.0f}\n出勤：{actual}/{work} 天\n狀態：{status}{comp}\n\n詳細資訊請至員工系統薪資單查看。',
        'en': '📊 {name} {month} Salary\n\nBase: NT$ {base:,.0f}\nAllowance: NT$ {allow:,.0f}\nOvertime: NT$ {ot:,.0f}\nDeductions: NT$ {ded:,.0f}\n━━━━━━━━━━━━\nNet Pay: NT$ {net:,.0f}\nAttendance: {actual}/{work} days\nStatus: {status}{comp}\n\nFor details, check the payslip in the employee system.',
        'ja': '📊 {name} {month} 給与\n\n基本給：NT$ {base:,.0f}\n手当：NT$ {allow:,.0f}\n残業代：NT$ {ot:,.0f}\n控除：NT$ {ded:,.0f}\n━━━━━━━━━━━━\n手取り：NT$ {net:,.0f}\n出勤：{actual}/{work}日\n状態：{status}{comp}\n\n詳細は従業員システムの給与明細をご確認ください。',
        'vi': '📊 Lương {month} của {name}\n\nLương cơ bản: NT$ {base:,.0f}\nPhụ cấp: NT$ {allow:,.0f}\nThêm giờ: NT$ {ot:,.0f}\nKhấu trừ: NT$ {ded:,.0f}\n━━━━━━━━━━━━\nThực lĩnh: NT$ {net:,.0f}\nChuyên cần: {actual}/{work} ngày\nTrạng thái: {status}{comp}\n\nXem chi tiết trong phiếu lương trên hệ thống.',
        'th': '📊 เงินเดือน {month} ของ {name}\n\nเงินเดือนพื้นฐาน: NT$ {base:,.0f}\nเบี้ยเลี้ยง: NT$ {allow:,.0f}\nค่าล่วงเวลา: NT$ {ot:,.0f}\nหักออก: NT$ {ded:,.0f}\n━━━━━━━━━━━━\nรับจริง: NT$ {net:,.0f}\nเข้างาน: {actual}/{work} วัน\nสถานะ: {status}{comp}\n\nดูรายละเอียดในสลิปเงินเดือนในระบบพนักงาน',
    },
    'salary_comp_bal': {
        'zh-TW': '\n補休餘額：{remain} 天（{year}年）',
        'en': '\nComp Leave Balance: {remain} days ({year})',
        'ja': '\n振替休日残日数：{remain}日（{year}年）',
        'vi': '\nSố dư nghỉ bù: {remain} ngày ({year})',
        'th': '\nยอดวันหยุดชดเชย: {remain} วัน ({year})',
    },
    'salary_status_draft': {
        'zh-TW': '草稿',
        'en': 'Draft',
        'ja': '草稿',
        'vi': 'Bản nháp',
        'th': 'ร่าง',
    },
    'salary_status_confirmed': {
        'zh-TW': '已確認',
        'en': 'Confirmed',
        'ja': '確認済み',
        'vi': 'Đã xác nhận',
        'th': 'ยืนยันแล้ว',
    },
    'salary_status_paid': {
        'zh-TW': '已發放',
        'en': 'Paid',
        'ja': '支払済み',
        'vi': 'Đã trả',
        'th': 'จ่ายแล้ว',
    },
    # ── Performance query ─────────────────────────────────────────────────
    'perf_no_records': {
        'zh-TW': '{name}\n尚無績效考核記錄。',
        'en': '{name}\nNo performance review records found.',
        'ja': '{name}\n人事考課記録がありません。',
        'vi': '{name}\nChưa có hồ sơ đánh giá hiệu suất.',
        'th': '{name}\nไม่มีบันทึกการประเมินผลงาน',
    },
    'perf_body': {
        'zh-TW': '{name} 最近考核\n\n期間：{period}\n範本：{tpl}\n得分：{score} / {max}（{pct}%）\n評級：{grade} {grade_label}{adj}\n{comments}考核日：{reviewed}',
        'en': '{name} Latest Review\n\nPeriod: {period}\nTemplate: {tpl}\nScore: {score} / {max} ({pct}%)\nGrade: {grade} {grade_label}{adj}\n{comments}Review date: {reviewed}',
        'ja': '{name} 最新考課\n\n期間：{period}\nテンプレート：{tpl}\n得点：{score} / {max}（{pct}%）\n評価：{grade} {grade_label}{adj}\n{comments}考課日：{reviewed}',
        'vi': 'Đánh giá gần nhất của {name}\n\nKỳ: {period}\nMẫu: {tpl}\nĐiểm: {score} / {max} ({pct}%)\nXếp loại: {grade} {grade_label}{adj}\n{comments}Ngày đánh giá: {reviewed}',
        'th': 'การประเมินล่าสุดของ {name}\n\nช่วงเวลา: {period}\nแม่แบบ: {tpl}\nคะแนน: {score} / {max} ({pct}%)\nเกรด: {grade} {grade_label}{adj}\n{comments}วันที่ประเมิน: {reviewed}',
    },
    'perf_adj': {
        'zh-TW': '\n薪資調整：NT$ {delta:+,.0f}',
        'en': '\nSalary adjustment: NT$ {delta:+,.0f}',
        'ja': '\n給与調整：NT$ {delta:+,.0f}',
        'vi': '\nĐiều chỉnh lương: NT$ {delta:+,.0f}',
        'th': '\nปรับเงินเดือน: NT$ {delta:+,.0f}',
    },
    'perf_comments': {
        'zh-TW': '備注：{text}\n',
        'en': 'Comments: {text}\n',
        'ja': '備考：{text}\n',
        'vi': 'Nhận xét: {text}\n',
        'th': 'ความคิดเห็น: {text}\n',
    },
    # ── Monthly records ───────────────────────────────────────────────────
    'monthly_no_records': {
        'zh-TW': '📋 {name} {month}\n該月尚無打卡記錄。',
        'en': '📋 {name} {month}\nNo punch records for this month.',
        'ja': '📋 {name} {month}\nこの月の打刻記録はありません。',
        'vi': '📋 {name} {month}\nKhông có bản ghi chấm công tháng này.',
        'th': '📋 {name} {month}\nไม่มีบันทึกตอกบัตรเดือนนี้',
    },
    'monthly_header': {
        'zh-TW': '📋 {name} {month} 出勤\n出勤 {days} 天｜工時 {total}{anomaly}',
        'en': '📋 {name} {month} Attendance\n{days} days｜Hours {total}{anomaly}',
        'ja': '📋 {name} {month} 出勤\n出勤{days}日｜労働時間{total}{anomaly}',
        'vi': '📋 Chuyên cần {month} của {name}\n{days} ngày｜Giờ làm {total}{anomaly}',
        'th': '📋 การเข้างาน {month} ของ {name}\n{days} วัน｜ชั่วโมงงาน {total}{anomaly}',
    },
    'monthly_anomaly': {
        'zh-TW': '｜異常 {n} 天',
        'en': '｜{n} anomaly days',
        'ja': '｜異常{n}日',
        'vi': '｜{n} ngày bất thường',
        'th': '｜{n} วันผิดปกติ',
    },
    'monthly_missing_out': {
        'zh-TW': '⚠️缺下班',
        'en': '⚠️No clock-out',
        'ja': '⚠️退勤なし',
        'vi': '⚠️Thiếu ra ca',
        'th': '⚠️ไม่มีออกงาน',
    },
    'monthly_missing_in': {
        'zh-TW': '⚠️缺上班',
        'en': '⚠️No clock-in',
        'ja': '⚠️出勤なし',
        'vi': '⚠️Thiếu vào ca',
        'th': '⚠️ไม่มีเข้างาน',
    },
    'monthly_manual': {
        'zh-TW': '【補】',
        'en': '[M]',
        'ja': '【補】',
        'vi': '[Bù]',
        'th': '[แก้]',
    },
    # ── Leave types list ──────────────────────────────────────────────────
    'leave_types_empty': {
        'zh-TW': '目前無可用假別。',
        'en': 'No leave types available.',
        'ja': '利用可能な休暇種別がありません。',
        'vi': 'Hiện không có loại nghỉ phép.',
        'th': 'ไม่มีประเภทการลาที่ใช้ได้',
    },
    'leave_types_header': {
        'zh-TW': '🗂️ 可用假別清單\n',
        'en': '🗂️ Available Leave Types\n',
        'ja': '🗂️ 利用可能な休暇種別\n',
        'vi': '🗂️ Danh Sách Loại Nghỉ Phép\n',
        'th': '🗂️ รายการประเภทการลา\n',
    },
    'leave_types_limit': {
        'zh-TW': '（年限 {days} 天）',
        'en': '(Annual limit: {days} days)',
        'ja': '（年間上限{days}日）',
        'vi': '(Hạn mức năm: {days} ngày)',
        'th': '(จำกัดต่อปี: {days} วัน)',
    },
    'leave_types_footer': {
        'zh-TW': '\n申請方式：請假 [假別] [日期]',
        'en': '\nHow to apply: leave [type] [date]',
        'ja': '\n申請方法：休暇 [種別] [日付]',
        'vi': '\nCách nộp đơn: nghỉ [loại] [ngày]',
        'th': '\nวิธียื่นคำขอ: ลา [ประเภท] [วันที่]',
    },
    # ── Help ─────────────────────────────────────────────────────────────
    'help_body': {
        'zh-TW': (
            '哈囉 {name}！以下是可用的指令：\n\n'
            '─── 打卡 ───\n'
            '📍 傳送位置 → 自動打卡\n'
            '💬 上班 / 下班\n'
            '📋 狀態 → 今日打卡記錄\n\n'
            '─── 查詢 ───\n'
            '🌿 查餘假 → 本年假期餘額\n'
            '💰 查薪資 → 最近薪資單\n'
            '📊 出勤紀錄 → 本月出勤明細\n'
            '   出勤紀錄 2026-03 → 指定月份\n'
            '考核 → 最近績效考核\n\n'
            '─── 申請 ───\n'
            '📝 請假 [假別] [日期] → 送出請假\n'
            '   範例：請假 特休 2026-04-01\n'
            '⏰ 加班 [日期] [時數] → 加班申請\n'
            '   範例：加班 2026-04-05 3\n'
            '🗂️ 假別 → 查看可用假別清單\n\n'
            '─── 其他 ───\n'
            '🔓 解除綁定'
        ),
        'en': (
            'Hello {name}! Here are the available commands:\n\n'
            '─── Punch ───\n'
            '📍 Send Location → Auto punch\n'
            '💬 Clock In / Clock Out\n'
            '📋 Status → Today\'s records\n\n'
            '─── Query ───\n'
            '🌿 Leave Balance → Annual leave balance\n'
            '💰 Salary → Latest payslip\n'
            '📊 Attendance → This month\'s records\n'
            '   Attendance 2026-03 → Specific month\n'
            'Performance → Latest review\n\n'
            '─── Apply ───\n'
            '📝 Leave [type] [date] → Submit leave\n'
            '   Example: Leave Annual 2026-04-01\n'
            '⏰ Overtime [date] [hours] → OT request\n'
            '   Example: Overtime 2026-04-05 3\n'
            '🗂️ Leave Types → View available types\n\n'
            '─── Other ───\n'
            '🔓 Unlink Account'
        ),
        'ja': (
            'こんにちは {name}！利用可能なコマンドは以下の通りです：\n\n'
            '─── 打刻 ───\n'
            '📍 位置情報を送信 → 自動打刻\n'
            '💬 出勤 / 退勤\n'
            '📋 状態 → 本日の打刻記録\n\n'
            '─── 照会 ───\n'
            '🌿 休暇残日数 → 今年の休暇残日数\n'
            '💰 給与 → 最新給与明細\n'
            '📊 出勤記録 → 今月の出勤明細\n'
            '   出勤記録 2026-03 → 指定月\n'
            '考課 → 最新人事考課\n\n'
            '─── 申請 ───\n'
            '📝 休暇 [種別] [日付] → 休暇申請\n'
            '   例：休暇 特別休暇 2026-04-01\n'
            '⏰ 残業 [日付] [時間] → 残業申請\n'
            '   例：残業 2026-04-05 3\n'
            '🗂️ 休暇種別 → 利用可能な種別を確認\n\n'
            '─── その他 ───\n'
            '🔓 連携解除'
        ),
        'vi': (
            'Xin chào {name}! Đây là các lệnh có sẵn:\n\n'
            '─── Chấm công ───\n'
            '📍 Gửi vị trí → Tự động chấm công\n'
            '💬 Vào ca / Ra ca\n'
            '📋 Trạng thái → Bản ghi hôm nay\n\n'
            '─── Truy vấn ───\n'
            '🌿 Số dư nghỉ → Số dư nghỉ phép năm nay\n'
            '💰 Lương → Phiếu lương gần nhất\n'
            '📊 Chuyên cần → Chi tiết tháng này\n'
            '   Chuyên cần 2026-03 → Tháng cụ thể\n'
            'Hiệu suất → Đánh giá gần nhất\n\n'
            '─── Nộp đơn ───\n'
            '📝 Nghỉ [loại] [ngày] → Gửi đơn nghỉ\n'
            '   Ví dụ: Nghỉ phép năm 2026-04-01\n'
            '⏰ Làm thêm [ngày] [giờ] → Đơn làm thêm\n'
            '   Ví dụ: Làm thêm 2026-04-05 3\n'
            '🗂️ Loại nghỉ → Xem danh sách loại nghỉ\n\n'
            '─── Khác ───\n'
            '🔓 Hủy liên kết'
        ),
        'th': (
            'สวัสดี {name}! นี่คือคำสั่งที่ใช้ได้:\n\n'
            '─── ตอกบัตร ───\n'
            '📍 ส่งตำแหน่ง → ตอกบัตรอัตโนมัติ\n'
            '💬 เข้างาน / ออกงาน\n'
            '📋 สถานะ → บันทึกวันนี้\n\n'
            '─── ค้นหา ───\n'
            '🌿 ยอดวันลา → ยอดคงเหลือปีนี้\n'
            '💰 เงินเดือน → สลิปล่าสุด\n'
            '📊 การเข้างาน → รายละเอียดเดือนนี้\n'
            '   การเข้างาน 2026-03 → เดือนที่กำหนด\n'
            'ผลงาน → การประเมินล่าสุด\n\n'
            '─── ยื่นคำขอ ───\n'
            '📝 ลา [ประเภท] [วันที่] → ยื่นใบลา\n'
            '   ตัวอย่าง: ลา พักร้อน 2026-04-01\n'
            '⏰ ล่วงเวลา [วันที่] [ชั่วโมง] → คำขอล่วงเวลา\n'
            '   ตัวอย่าง: ล่วงเวลา 2026-04-05 3\n'
            '🗂️ ประเภทการลา → ดูรายการประเภท\n\n'
            '─── อื่นๆ ───\n'
            '🔓 ยกเลิกการผูกบัญชี'
        ),
    },
    # ── Time page labels ──────────────────────────────────────────────────
    'time_page_0': {
        'zh-TW': '凌晨(00-05)',
        'en': 'Night(00-05)',
        'ja': '深夜(00-05)',
        'vi': 'Đêm khuya(00-05)',
        'th': 'กลางคืน(00-05)',
    },
    'time_page_1': {
        'zh-TW': '上午(06-11)',
        'en': 'Morning(06-11)',
        'ja': '午前(06-11)',
        'vi': 'Sáng(06-11)',
        'th': 'เช้า(06-11)',
    },
    'time_page_2': {
        'zh-TW': '下午(12-17)',
        'en': 'Afternoon(12-17)',
        'ja': '午後(12-17)',
        'vi': 'Chiều(12-17)',
        'th': 'บ่าย(12-17)',
    },
    'time_page_3': {
        'zh-TW': '晚上(18-23)',
        'en': 'Evening(18-23)',
        'ja': '夜(18-23)',
        'vi': 'Tối(18-23)',
        'th': 'เย็น(18-23)',
    },
    # ── Errors / misc ────────────────────────────────────────────────────
    'leave_no_types_admin': {
        'zh-TW': '目前無可用假別，請聯絡管理員。',
        'en': 'No leave types available. Please contact your admin.',
        'ja': '利用可能な休暇種別がありません。管理者にお問い合わせください。',
        'vi': 'Hiện không có loại nghỉ phép. Vui lòng liên hệ quản trị viên.',
        'th': 'ไม่มีประเภทการลาที่ใช้ได้ กรุณาติดต่อผู้ดูแลระบบ',
    },
    'leave_type_not_found_btn': {
        'zh-TW': '找不到假別「{type}」，請點選按鈕選擇。',
        'en': 'Leave type "{type}" not found. Please tap a button to select.',
        'ja': '休暇種別「{type}」が見つかりません。ボタンをタップして選択してください。',
        'vi': 'Không tìm thấy loại nghỉ "{type}". Vui lòng nhấn nút để chọn.',
        'th': 'ไม่พบประเภทการลา "{type}" กรุณาแตะปุ่มเพื่อเลือก',
    },
    'date_end_before_start': {
        'zh-TW': '⚠️ 結束日期不能早於開始日期',
        'en': '⚠️ End date cannot be earlier than start date',
        'ja': '⚠️ 終了日は開始日より前にできません',
        'vi': '⚠️ Ngày kết thúc không thể trước ngày bắt đầu',
        'th': '⚠️ วันที่สิ้นสุดไม่สามารถก่อนวันที่เริ่มต้น',
    },
    'time_format_error': {
        'zh-TW': '⚠️ 時間格式錯誤，請輸入 HH:MM，例：{example}',
        'en': '⚠️ Invalid time format. Please enter HH:MM, e.g.: {example}',
        'ja': '⚠️ 時間の形式が正しくありません。HH:MMで入力してください。例：{example}',
        'vi': '⚠️ Định dạng giờ không hợp lệ. Vui lòng nhập HH:MM, ví dụ: {example}',
        'th': '⚠️ รูปแบบเวลาไม่ถูกต้อง กรุณาใส่ HH:MM เช่น: {example}',
    },
    'time_end_before_start': {
        'zh-TW': '⚠️ 結束時間須晚於開始時間（{start}），請重新選擇。',
        'en': '⚠️ End time must be later than start time ({start}). Please reselect.',
        'ja': '⚠️ 終了時間は開始時間（{start}）より後にしてください。再選択してください。',
        'vi': '⚠️ Giờ kết thúc phải sau giờ bắt đầu ({start}). Vui lòng chọn lại.',
        'th': '⚠️ เวลาสิ้นสุดต้องหลังเวลาเริ่มต้น ({start}) กรุณาเลือกใหม่',
    },
    'leave_cancelled': {
        'zh-TW': '已取消請假申請。',
        'en': 'Leave request cancelled.',
        'ja': '休暇申請をキャンセルしました。',
        'vi': 'Đã hủy đơn xin nghỉ.',
        'th': 'ยกเลิกคำขอลาแล้ว',
    },
    'ot_cancelled': {
        'zh-TW': '已取消加班申請。',
        'en': 'Overtime request cancelled.',
        'ja': '残業申請をキャンセルしました。',
        'vi': 'Đã hủy đơn làm thêm giờ.',
        'th': 'ยกเลิกคำขอล่วงเวลาแล้ว',
    },
    'ot_hours_anomaly': {
        'zh-TW': '⚠️ 加班時數異常（{hrs}h），請重新確認時間。',
        'en': '⚠️ Overtime hours anomaly ({hrs}h). Please recheck the times.',
        'ja': '⚠️ 残業時間が異常です（{hrs}h）。時間を再確認してください。',
        'vi': '⚠️ Số giờ làm thêm bất thường ({hrs}h). Vui lòng kiểm tra lại giờ.',
        'th': '⚠️ ชั่วโมงล่วงเวลาผิดปกติ ({hrs}h) กรุณาตรวจสอบเวลาอีกครั้ง',
    },
    'date_format_error': {
        'zh-TW': '日期格式錯誤。',
        'en': 'Invalid date format.',
        'ja': '日付の形式が正しくありません。',
        'vi': 'Định dạng ngày không hợp lệ.',
        'th': 'รูปแบบวันที่ไม่ถูกต้อง',
    },
    'bind_account_conflict': {
        'zh-TW': '此帳號已綁定其他 LINE 帳號，請聯絡管理員。',
        'en': 'This account is already linked to another LINE account. Please contact admin.',
        'ja': 'このアカウントは既に別のLINEアカウントに連携されています。管理者にお問い合わせください。',
        'vi': 'Tài khoản này đã được liên kết với tài khoản LINE khác. Vui lòng liên hệ quản trị viên.',
        'th': 'บัญชีนี้ผูกกับ LINE บัญชีอื่นแล้ว กรุณาติดต่อผู้ดูแลระบบ',
    },
    'unbind_success': {
        'zh-TW': '已解除 LINE 帳號綁定。',
        'en': 'LINE account unlinked.',
        'ja': 'LINEアカウントの連携を解除しました。',
        'vi': 'Đã hủy liên kết tài khoản LINE.',
        'th': 'ยกเลิกการผูกบัญชี LINE แล้ว',
    },
    'punch_duplicate': {
        'zh-TW': '⚠️ 1 分鐘內已打過{label}，請勿重複打卡。',
        'en': '⚠️ You already punched {label} within the last minute. Please do not repeat.',
        'ja': '⚠️ 1分以内に{label}を打刻済みです。重複打刻はご遠慮ください。',
        'vi': '⚠️ Bạn đã {label} trong vòng 1 phút qua. Vui lòng không chấm công lại.',
        'th': '⚠️ คุณตอกบัตร {label} ไปแล้วภายใน 1 นาที กรุณาอย่าตอกบัตรซ้ำ',
    },
    'ot_submitted_direct': {
        'zh-TW': '✅ 加班申請已送出\n\n日期：{date}\n時數：{hrs} 小時\n原因：{reason}\n申請編號：#{id}\n\n請等候管理員審核，審核結果將通知您。',
        'en': '✅ Overtime request submitted\n\nDate: {date}\nHours: {hrs} hours\nReason: {reason}\nRequest #: #{id}\n\nPlease wait for admin review. You will be notified of the result.',
        'ja': '✅ 残業申請を送信しました\n\n日付：{date}\n時数：{hrs}時間\n理由：{reason}\n申請番号：#{id}\n\n管理者の審査をお待ちください。審査結果はお知らせします。',
        'vi': '✅ Đã gửi đơn làm thêm giờ\n\nNgày: {date}\nSố giờ: {hrs} giờ\nLý do: {reason}\nSố đơn: #{id}\n\nVui lòng chờ quản trị viên xét duyệt. Bạn sẽ được thông báo kết quả.',
        'th': '✅ ส่งคำขอล่วงเวลาแล้ว\n\nวันที่: {date}\nชั่วโมง: {hrs} ชั่วโมง\nเหตุผล: {reason}\nเลขที่: #{id}\n\nกรุณารอผู้ดูแลตรวจสอบ คุณจะได้รับการแจ้งเตือนผล',
    },
}


WDAY_ABBR = {
    'zh-TW': ['一', '二', '三', '四', '五', '六', '日'],
    'en':    ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
    'ja':    ['月', '火', '水', '木', '金', '土', '日'],
    'vi':    ['Hai', 'Ba', 'Tư', 'Năm', 'Sáu', 'Bảy', 'CN'],
    'th':    ['จ', 'อ', 'พ', 'พฤ', 'ศ', 'ส', 'อา'],
}
