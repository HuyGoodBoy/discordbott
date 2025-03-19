# Hướng dẫn phát triển Discord Quiz Bot

## Bước 1: Thiết lập môi trường

### 1.1. Tạo Bot trên Discord
1. Truy cập [Discord Developer Portal](https://discord.com/developers/applications)
2. Nhấn "New Application" và đặt tên
3. Vào mục "Bot" và tạo bot mới
4. Lưu token của bot
5. Bật các Intents cần thiết:
   - PRESENCE INTENT
   - SERVER MEMBERS INTENT
   - MESSAGE CONTENT INTENT

### 1.2. Cài đặt môi trường Python
```bash
# Tạo thư mục project
mkdir quiz-bot
cd quiz-bot

# Tạo môi trường ảo
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Cài đặt thư viện
pip install discord.py python-dotenv
```

## Bước 2: Tạo cấu trúc project

### 2.1. Tạo các file cần thiết 