# Discord Bot - Hướng dẫn phát triển dự án

## 1. Khởi tạo dự án

### 1.1. Chuẩn bị môi trường
- Cài đặt Python 3.8+ 
- Tạo virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```
- Cài đặt các thư viện cần thiết:
```bash
pip install discord.py python-dotenv yt-dlp openai pytest
```

### 1.2. Cấu trúc thư mục 