# Discord Bot - Tài liệu API

## Cấu trúc dự án 

## API References

### Discord.py
- Version: 2.0+
- [Discord.py Documentation](https://discordpy.readthedocs.io/)

### yt-dlp
- [yt-dlp Documentation](https://github.com/yt-dlp/yt-dlp#readme)

### OpenAI API
- [OpenAI API Documentation](https://platform.openai.com/docs/api-reference)

## Classes

### YTDLSource
Xử lý phát nhạc từ YouTube.

#### Methods:
- `from_url(url, *, loop=None, stream=False)`
- `start()`
- `pause()`
- `resume()`
- `get_current_time()`

### MusicQueue
Quản lý hàng đợi phát nhạc.

#### Methods:
- `add(source)`
- `next()`
- `clear()`
- `is_empty()`

### QuizGame
Quản lý trò chơi câu đố.

#### Methods:
- `start_new_quiz(channel)`
- `check_answer(message)`
- `get_next_question()`
- `end_quiz(channel)`

## Error Handling
```python
try:
    # Code block
except Exception as e:
    print(f"Error: {str(e)}")
    # Error handling
```