# Discord Quiz Bot - Tài liệu hướng dẫn

## Giới thiệu
Discord Quiz Bot là một bot tương tác cho phép tổ chức các trò chơi câu đố trên Discord. Bot hỗ trợ nhiều người chơi, tính điểm tự động và có hệ thống xếp hạng.

## Cài đặt và Thiết lập

### Yêu cầu hệ thống
- Python 3.8+
- Discord.py library
- Discord Bot Token

### Cài đặt
1. Clone repository
2. Cài đặt dependencies:
```bash
pip install -r requirements.txt
```
3. Tạo file `.env` và thêm token:
```env
DISCORD_TOKEN=your_bot_token_here
```

## Cấu trúc Bot

### 1. Class QuizGame
Quản lý toàn bộ logic trò chơi.

#### Thuộc tính
- `active`: Trạng thái trò chơi
- `current_question`: Câu hỏi hiện tại
- `scores`: Điểm số người chơi
- `confirmed_players`: Danh sách người chơi
- `accepting_answers`: Trạng thái nhận câu trả lời

#### Phương thức chính
```python
async def start_new_quiz(self, channel)
async def get_next_question_and_send(self, channel)
async def check_answer(self, message)
async def end_quiz(self, channel)
```

### 2. Hệ thống Câu hỏi
- Câu hỏi được lưu dưới dạng JSON
- Mỗi câu hỏi có category, question và answer
- Hỗ trợ tiếng Việt có dấu

## Cách sử dụng

### Lệnh cho người chơi
1. `.mg` - Bắt đầu trò chơi mới
2. `.as` - Trả lời câu hỏi hiện tại

### Quy trình trò chơi
1. Admin/Mod sử dụng lệnh `.mg` để bắt đầu
2. Người chơi nhấn nút tham gia
3. Bot gửi câu hỏi đầu tiên
4. Người chơi sử dụng `.as` để trả lời
5. Bot kiểm tra và thông báo kết quả

## Xử lý câu trả lời

### Chuẩn hóa câu trả lời
```python
def normalize_answer(answer):
    # Chuyển về chữ thường
    answer = answer.lower()
    # Xử lý khoảng trắng
    answer = ' '.join(answer.split())
    return answer
```

### Kiểm tra câu trả lời
- So sánh chính xác với đáp án
- Bỏ qua khoảng trắng thừa
- Không phân biệt chữ hoa/thường
- Giữ nguyên dấu tiếng Việt

## Testing

### Unit Tests
```python
class TestQuizGame(unittest.TestCase):
    def test_check_answer_format(self):
        answer1 = "cây  cầu"
        answer2 = "cây cầu"
        self.assertEqual(
            ' '.join(answer1.lower().split()),
            ' '.join(answer2.lower().split())
        )
```

### Chạy Tests
```bash
python -m unittest test_bot.py
```

## Xử lý lỗi

### Try-Catch
```python
try:
    await process_answer(message)
except Exception as e:
    await message.channel.send(f"Có lỗi xảy ra: {str(e)}")
    logger.error(f"Error in process_answer: {str(e)}")
```

### Các lỗi thường gặp
1. Người chơi chưa tham gia
2. Hết thời gian trả lời
3. Trò chơi chưa bắt đầu
4. Định dạng câu trả lời không hợp lệ

## Tối ưu hóa

### Performance
- Sử dụng async/await cho các tác vụ bất đồng bộ
- Cache câu hỏi để giảm tải database
- Xử lý timeout cho mỗi câu hỏi

### Memory Management
- Xóa câu hỏi cũ sau khi hoàn thành
- Reset trạng thái sau mỗi game
- Giới hạn số người chơi tối đa

## Bảo mật

### Kiểm tra quyền
```python
if not message.author.guild_permissions.administrator:
    await message.channel.send("Bạn không có quyền sử dụng lệnh này!")
    return
```

### Xử lý Input
- Kiểm tra độ dài câu trả lời
- Lọc ký tự đặc biệt
- Giới hạn số lần trả lời

## Logging

### Debug Log
```python
logging.debug(f"User answer: {user_answer}")
logging.debug(f"Correct answer: {correct_answer}")
logging.debug(f"Comparison result: {is_correct}")
```

### Error Log
```python
logging.error(f"Error processing answer: {str(e)}")
logging.error(f"Stack trace: {traceback.format_exc()}")
```

## Phát triển thêm

### Tính năng có thể thêm
1. Hệ thống hint
2. Câu hỏi có hình ảnh
3. Chế độ tính điểm theo thời gian
4. Bảng xếp hạng toàn server

### Cải thiện
1. Thêm nhiều loại câu hỏi
2. Cải thiện UI/UX
3. Thêm animations
4. Tích hợp với database

## Liên hệ và Hỗ trợ
- GitHub Issues
- Discord Support Server
- Email Support 