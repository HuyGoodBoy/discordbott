# Discord Bot - Hướng dẫn sử dụng

## Giới thiệu
Bot Discord đa chức năng với khả năng phát nhạc và tổ chức trò chơi câu đố.

## Cài đặt

### Yêu cầu hệ thống
- Python 3.8+
- Discord.py 2.0+
- FFmpeg
- yt-dlp
- OpenAI API key
- Discord Bot Token

### Các bước cài đặt
1. Clone repository:
```bash
git clone <repository-url>
```

2. Cài đặt dependencies:
```bash
pip install -r requirements.txt
```

3. Tạo file `.env` với nội dung:
```env
DISCORD_TOKEN=your_discord_token
OPENAI_API_KEY=your_openai_api_key
```

## Tính năng chính

### 1. Phát nhạc
- `.join` - Bot tham gia kênh voice
- `.play [url/tên bài hát]` - Phát nhạc từ YouTube
- `.pause` - Tạm dừng
- `.resume` - Tiếp tục phát
- `.stop` - Dừng phát
- `.volume [0-100]` - Điều chỉnh âm lượng

### 2. Trò chơi câu đố
- `.mg` - Bắt đầu trò chơi mới
- `.as` - Trả lời câu hỏi

### 3. Tiện ích khác
- `.avt [@user]` - Hiển thị avatar
- `.server` - Thông tin server
- `.q [câu hỏi]` - Chat với GPT-4

## Hosting
- Có thể host trên Replit hoặc Glitch
- Hướng dẫn hosting chi tiết trong Documentation.md 