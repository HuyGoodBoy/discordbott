import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
import yt_dlp
import asyncio
import openai
from openai import OpenAI
import random

# Load environment variables
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

# Khởi tạo OpenAI client
client = OpenAI(api_key=OPENAI_API_KEY)

# Configure yt-dlp
ytdl_format_options = {
    'format': 'bestaudio/best',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0',
    'extract_flat': False,
    'audio_quality': 0,  # Best quality
    'audio_format': 'mp3',
    'postprocessors': [{
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'mp3',
        'preferredquality': '320',  # Highest quality
    }]
}

ffmpeg_options = {
    'options': '-vn -b:a 320k -ar 48000 -ac 2',  # High quality audio settings
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5'
}

ytdl = yt_dlp.YoutubeDL(ytdl_format_options)

class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)
        self.data = data
        self.title = data.get('title')
        self.url = data.get('url')
        self.start_time = None
        self.duration = data.get('duration', 0)
        self.paused_time = 0
        self.is_paused = False
        self._start_timestamp = None

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))
        
        if 'entries' in data:
            data = data['entries'][0]
            
        filename = data['url'] if stream else ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)

    def start(self):
        if not self.start_time:
            self.start_time = asyncio.get_event_loop().time()
            self._start_timestamp = asyncio.get_event_loop().time()
        super().start()

    def pause(self):
        if not self.is_paused:
            self.paused_time = asyncio.get_event_loop().time()
            self.is_paused = True
        super().pause()

    def resume(self):
        if self.is_paused:
            pause_duration = asyncio.get_event_loop().time() - self.paused_time
            self.start_time += pause_duration
            self._start_timestamp += pause_duration
            self.is_paused = False
        super().resume()

    def get_current_time(self):
        if not self.start_time:
            return 0
        if self.is_paused:
            return self.paused_time - self.start_time
        current = asyncio.get_event_loop().time() - self._start_timestamp
        return min(current, self.duration)  # Đảm bảo không vượt quá thời lượng

class MusicQueue:
    def __init__(self):
        self.queue = []
        self.current = None
        self.loop = False

    def add(self, source):
        self.queue.append(source)
        return len(self.queue) - 1

    def next(self):
        if self.loop:
            return self.current
        if self.queue:
            self.current = self.queue.pop(0)
            return self.current
        return None

    def clear(self):
        self.queue.clear()
        self.current = None

    def is_empty(self):
        return len(self.queue) == 0 and self.current is None

# Tạo instance của MusicQueue
music_queue = MusicQueue()

# Create bot instance
intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True
bot = commands.Bot(
    command_prefix='.',
    intents=intents,
    help_command=commands.DefaultHelpCommand(),
    case_insensitive=True,
    description="Bot phát nhạc và hiển thị avatar"
)

@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')
    print('Bot is ready to use!')
    print('Các lệnh có sẵn:')
    print('!help - Hiển thị danh sách lệnh')
    print('!join - Vào kênh voice')
    print('!leave - Rời kênh voice')
    print('!play [url] - Phát nhạc từ YouTube')
    print('!pause - Tạm dừng nhạc')
    print('!resume - Tiếp tục phát nhạc')
    print('!stop - Dừng phát nhạc')
    print('!avt [@user] - Hiển thị avatar người dùng')
    print('!time - Hiển thị tổng thời gian bài hát')

@bot.event
async def on_voice_state_update(member, before, after):
    """Xử lý khi có thay đổi trạng thái voice"""
    if member == bot.user:
        if before.channel and not after.channel:
            print(f"Bot đã rời kênh {before.channel.name}")
        elif after.channel and not before.channel:
            print(f"Bot đã vào kênh {after.channel.name}")

@bot.command(name='join', help='Vào kênh voice hiện tại')
async def join(ctx):
    """Vào kênh voice hiện tại"""
    try:
        if not ctx.message.author.voice:
            await ctx.send("Bạn cần vào kênh voice trước khi sử dụng lệnh này!")
            return
        
        channel = ctx.message.author.voice.channel
        if ctx.voice_client is not None:
            if ctx.voice_client.is_connected():
                await ctx.voice_client.disconnect()
            else:
                ctx.voice_client = None
        
        try:
            await channel.connect()
            await ctx.send(f"Đã vào kênh {channel.name}!")
        except discord.ClientException as e:
            print(f"Lỗi kết nối: {str(e)}")
            await ctx.send("Không thể kết nối với kênh voice. Vui lòng thử lại.")
    except Exception as e:
        print(f"Error in join command: {str(e)}")
        await ctx.send(f"Có lỗi xảy ra: {str(e)}")

@bot.command(name='leave', help='Rời khỏi kênh voice')
async def leave(ctx):
    """Rời khỏi kênh voice"""
    voice_client = ctx.message.guild.voice_client
    if voice_client.is_connected():
        await voice_client.disconnect()
    else:
        await ctx.send("Bot chưa vào kênh voice.")

@bot.command(name='play', help='Phát nhạc từ YouTube (có thể nhập link hoặc tên bài hát)')
async def play(ctx, *, query):
    """Phát nhạc từ YouTube hoặc tìm kiếm bài hát"""
    try:
        if not ctx.voice_client:
            await ctx.send("Bot chưa vào kênh voice. Sử dụng lệnh !join trước.")
            return

        server = ctx.message.guild
        voice_channel = server.voice_client

        if not voice_channel.is_connected():
            await ctx.send("Bot đã mất kết nối. Sử dụng lệnh !join để kết nối lại.")
            return

        async with ctx.typing():
            # Kiểm tra xem query có phải là URL không
            if not query.startswith(('http://', 'https://')):
                # Nếu không phải URL, tìm kiếm trên YouTube
                search_query = f"ytsearch:{query}"
                player = await YTDLSource.from_url(search_query, loop=bot.loop, stream=True)
            else:
                # Nếu là URL, phát trực tiếp
                player = await YTDLSource.from_url(query, loop=bot.loop, stream=True)
            
            if voice_channel.is_playing():
                # Nếu đang phát, thêm vào hàng đợi
                position = music_queue.add(player)
                await ctx.send(f'Đã thêm vào hàng đợi: {player.title} (Vị trí: {position + 1})')
            else:
                # Nếu không đang phát, phát ngay
                music_queue.current = player
                voice_channel.play(player, after=lambda e: asyncio.run_coroutine_threadsafe(
                    check_queue(ctx), bot.loop
                ))
                await ctx.send(f'Đang phát: {player.title}')

    except Exception as e:
        print(f"Error in play command: {str(e)}")
        await ctx.send(f"Có lỗi xảy ra: {str(e)}")

async def check_queue(ctx):
    """Kiểm tra và phát bài tiếp theo trong hàng đợi"""
    if not ctx.voice_client:
        return

    next_source = music_queue.next()
    if next_source:
        ctx.voice_client.play(next_source, after=lambda e: asyncio.run_coroutine_threadsafe(
            check_queue(ctx), bot.loop
        ))
        await ctx.send(f'Đang phát: {next_source.title}')
    else:
        music_queue.current = None
        await ctx.send("Đã phát xong tất cả bài hát!")

@bot.command(name='pause', help='Tạm dừng phát nhạc')
async def pause(ctx):
    """Tạm dừng phát nhạc"""
    voice_client = ctx.message.guild.voice_client
    if voice_client.is_playing():
        voice_client.source.pause()
        voice_client.pause()
        await ctx.send("Đã tạm dừng ⏸️")

@bot.command(name='resume', help='Tiếp tục phát nhạc')
async def resume(ctx):
    """Tiếp tục phát nhạc"""
    voice_client = ctx.message.guild.voice_client
    if voice_client.is_paused():
        voice_client.source.resume()
        voice_client.resume()
        await ctx.send("Đã tiếp tục phát ▶️")

@bot.command(name='stop', help='Dừng phát nhạc')
async def stop(ctx):
    """Dừng phát nhạc"""
    voice_client = ctx.message.guild.voice_client
    if voice_client.is_playing():
        voice_client.stop()
        await ctx.send("Đã dừng phát ⏹️")

@bot.command(name='avt', help='Hiển thị avatar người dùng')
async def avatar(ctx, member: discord.Member = None):
    """Hiển thị avatar của người dùng"""
    if member is None:
        member = ctx.author
    
    embed = discord.Embed(title=f"Avatar của {member.name}", color=discord.Color.blue())
    embed.set_image(url=member.avatar.url if member.avatar else member.default_avatar.url)
    await ctx.send(embed=embed)

@bot.command(name='time', help='Hiển thị tổng thời gian bài hát')
async def time(ctx):
    """Hiển thị tổng thời gian bài hát"""
    voice_client = ctx.message.guild.voice_client
    if voice_client and voice_client.is_playing():
        source = voice_client.source
        if hasattr(source, 'duration'):
            duration = source.duration
            minutes = int(duration // 60)
            seconds = int(duration % 60)
            await ctx.send(f"⏱️ Thời lượng bài hát: {minutes}:{seconds:02d}")
        else:
            await ctx.send("Không thể lấy thời lượng bài hát!")
    else:
        await ctx.send("Không có nhạc đang phát!")

@bot.command(name='volume', help='Điều chỉnh âm lượng (0-100)')
async def volume(ctx, volume: int):
    """Điều chỉnh âm lượng"""
    if not ctx.voice_client:
        return await ctx.send("Bot chưa vào kênh voice!")
    
    if not 0 <= volume <= 100:
        return await ctx.send("Âm lượng phải từ 0 đến 100!")
    
    ctx.voice_client.source.volume = volume / 100
    await ctx.send(f"🔊 Âm lượng đã được đặt thành {volume}%")

@bot.command(name='server', help='Hiển thị thông tin server')
async def server_info(ctx):
    """Hiển thị thông tin server"""
    try:
        guild = ctx.guild
        embed = discord.Embed(title=f"Thông tin server {guild.name}", color=discord.Color.blue())
        
        # Thêm icon server nếu có
        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)
        
        # Thông tin cơ bản
        embed.add_field(name="👑 Chủ server", value=guild.owner.name, inline=True)
        embed.add_field(name="👥 Số thành viên", value=guild.member_count, inline=True)
        embed.add_field(name="📅 Ngày tạo", value=guild.created_at.strftime("%d/%m/%Y"), inline=True)
        
        # Thông tin kênh
        text_channels = len([c for c in guild.channels if isinstance(c, discord.TextChannel)])
        voice_channels = len([c for c in guild.channels if isinstance(c, discord.VoiceChannel)])
        embed.add_field(name="💬 Kênh text", value=text_channels, inline=True)
        embed.add_field(name="🔊 Kênh voice", value=voice_channels, inline=True)
        
        # Thông tin role
        embed.add_field(name="🎭 Số role", value=len(guild.roles), inline=True)
        
        # Thông tin boost
        if guild.premium_tier > 0:
            embed.add_field(name="🚀 Boost level", value=guild.premium_tier, inline=True)
            embed.add_field(name="💎 Số boost", value=guild.premium_subscription_count, inline=True)
        
        # Footer với ID server
        embed.set_footer(text=f"Server ID: {guild.id}")
        
        await ctx.send(embed=embed)
    except Exception as e:
        print(f"Error in server command: {str(e)}")
        await ctx.send("Có lỗi xảy ra khi lấy thông tin server. Vui lòng thử lại sau!")

@bot.command(name='queue', help='Hiển thị danh sách phát')
async def show_queue(ctx):
    """Hiển thị danh sách phát"""
    if music_queue.is_empty():
        await ctx.send("Không có bài hát nào trong hàng đợi!")
        return

    embed = discord.Embed(title="Danh sách phát", color=discord.Color.blue())
    
    # Hiển thị bài đang phát
    if music_queue.current:
        embed.add_field(
            name="🎵 Đang phát",
            value=music_queue.current.title,
            inline=False
        )
    
    # Hiển thị các bài trong hàng đợi
    if music_queue.queue:
        queue_list = ""
        for i, source in enumerate(music_queue.queue, 1):
            queue_list += f"{i}. {source.title}\n"
        embed.add_field(
            name="📋 Hàng đợi",
            value=queue_list,
            inline=False
        )
    
    await ctx.send(embed=embed)

@bot.command(name='skip', help='Bỏ qua bài hát hiện tại')
async def skip(ctx):
    """Bỏ qua bài hát hiện tại"""
    if not ctx.voice_client:
        return await ctx.send("Bot chưa vào kênh voice!")
    
    if not ctx.voice_client.is_playing():
        return await ctx.send("Không có bài hát nào đang phát!")
    
    ctx.voice_client.stop()
    await ctx.send("⏭️ Đã bỏ qua bài hát!")

@bot.command(name='clear', help='Xóa toàn bộ hàng đợi')
async def clear_queue(ctx):
    """Xóa toàn bộ hàng đợi"""
    music_queue.clear()
    await ctx.send("🗑️ Đã xóa toàn bộ hàng đợi!")

@bot.command(name='q', help='Hỏi đáp với GPT-4')
async def ask_gpt(ctx, *, question):
    """Hỏi đáp với GPT-4"""
    try:
        async with ctx.typing():
            # Gửi câu hỏi đến GPT-4
            response = await asyncio.to_thread(
                client.chat.completions.create,
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "Bạn là một trợ lý AI thông minh và hữu ích."},
                    {"role": "user", "content": question}
                ],
                max_tokens=750,  # Tăng lên 1000 tokens để có câu trả lời chi tiết hơn
                temperature=0.7
            )
            
            # Lấy câu trả lời
            answer = response.choices[0].message.content
            
            # Tạo embed để hiển thị câu trả lời
            embed = discord.Embed(
                title="🤖 Câu trả lời từ GPT-4 Turbo",
                description=answer,
                color=discord.Color.blue()
            )
            embed.set_footer(text=f"Được hỏi bởi {ctx.author.name}")
            
            await ctx.send(embed=embed)
            
    except Exception as e:
        print(f"Error in GPT command: {str(e)}")
        await ctx.send("Có lỗi xảy ra khi xử lý câu hỏi. Vui lòng thử lại sau!")

class QuizGame:
    def __init__(self):
        self.active = False
        self.current_question = None
        self.current_answer = None
        self.scores = {}
        self.current_question_index = 0
        self.total_questions = 10
        self.used_questions = []
        self.timer_task = None
        self.confirmed_players = set()
        self.accepting_answers = True  # Thêm biến kiểm soát việc nhận câu trả lời
        self.questions = [
            {
                "category": "Đố vui",
                "question": "Đuôi thì chẳng thấy, mà có hai đầu?",
                "answer": "cây cầu"
            },
            {
                "category": "Đố vui",
                "question": "Cái gì không có chân, không có đuôi, không có cơ thể mà có nhiều đầu?",
                "answer": "cầu truyền hình"
            },
            {
                "category": "Đố vui",
                "question": "Ba của Tèo gọi mẹ của Tý là em dâu, vậy ba của Tý gọi ba của Tèo là gì?",
                "answer": "anh trai"
            },
            {
                "category": "Đố vui",
                "question": "Phía trước bạn là quảng trường xanh, sau lưng bạn là quảng trường trắng, vậy quảng trường đỏ ở đâu?",
                "answer": "ở nga"
            },
            {
                "category": "Đố vui",
                "question": "Vào tháng nào con người sẽ ngủ ít nhất trong năm?",
                "answer": "tháng 2"
            },
            {
                "category": "Đố vui",
                "question": "Loại xe không có bánh thường thấy ở đâu?",
                "answer": "trong bàn cờ vua"
            },
            {
                "category": "Đố vui",
                "question": "Nhà nào lạnh lẽo nhưng ai cũng muốn tới?",
                "answer": "nhà băng"
            },
            {
                "category": "Đố vui",
                "question": "Hôn mà bị hôn lại gọi là gì?",
                "answer": "đính hôn"
            },
            {
                "category": "Đố vui",
                "question": "Tôi chu du khắp thế giới mà tôi vẫn ở nguyên một chỗ, tôi là ai?",
                "answer": "tem thư"
            },
            {
                "category": "Đố vui",
                "question": "Từ nào trong tiếng Việt có chín mẫu tự h?",
                "answer": "chính"
            },
            {
                "category": "Đố vui",
                "question": "Bánh gì nghe tên đã thấy sung sướng?",
                "answer": "bánh khoái"
            },
            {
                "category": "Đố vui",
                "question": "Bánh gì nghe tên đã thấy đau?",
                "answer": "bánh tét"
            },
            {
                "category": "Đố vui",
                "question": "Thứ gì mỗi ngày phải gỡ ra mới có công dụng?",
                "answer": "lịch treo tường"
            },
            {
                "category": "Đố vui",
                "question": "Cái gì luôn chạy không chờ ta bao giờ. Nhưng chúng ta vẫn có thể đứng một chỗ để chờ nó?",
                "answer": "đồng hồ"
            },
            {
                "category": "Đố vui",
                "question": "Con gì biết đi nhưng người ta vẫn nói nó không biết đi?",
                "answer": "con bò"
            },
            {
                "category": "Đố vui",
                "question": "Xe nào không bao giờ giảm đi?",
                "answer": "xe tăng"
            },
            {
                "category": "Đố vui",
                "question": "Cái gì khi xài thì quăng đi, nhưng khi không xài thì lấy lại?",
                "answer": "mỏ neo và lưỡi câu"
            },
            {
                "category": "Đố vui",
                "question": "Ở đâu 1 con voi có thể ăn 1 cái xe?",
                "answer": "cờ tướng"
            },
            {
                "category": "Đố vui",
                "question": "Cây nhang càng đốt càng ngắn. Vậy cây gì càng đốt nhiều càng dài?",
                "answer": "cây tre"
            },
            {
                "category": "Đố vui",
                "question": "Hạt đường và hạt cát, hạt nào dài hơn?",
                "answer": "hạt đường"
            },
            {
                "category": "Đố vui",
                "question": "Từ gì bỏ đầu thành tên quốc gia, mất đuôi ra một loài chim?",
                "answer": "cúc"
            },
            {
                "category": "Đố vui",
                "question": "Chữ gì mất đầu là hỏi, mất đuôi trả lời?",
                "answer": "chữ tai"
            },
            {
                "category": "Đố vui",
                "question": "Cái gì con người mua để ăn nhưng không bao giờ ăn?",
                "answer": "bát đũa dĩa thìa"
            },
            {
                "category": "Đố vui",
                "question": "Cái gì 2 lỗ: có gió thì sống, không gió thì chết?",
                "answer": "lỗ mũi"
            },
            {
                "category": "Đố vui",
                "question": "Đồng gì mà đa số ai cũng thích?",
                "answer": "đồng tiền"
            },
            {
                "category": "Đố vui",
                "question": "Cái gì càng cất lại càng thấy?",
                "answer": "cất nhà"
            },
            {
                "category": "Đố vui",
                "question": "Chim nào thích dùng ngón tay tác động vật lý?",
                "answer": "chim cốc"
            },
            {
                "category": "Đố vui",
                "question": "Sữa gì khi uống không được đứng yên 1 chỗ?",
                "answer": "sữa lắc"
            },
            {
                "category": "Đố vui",
                "question": "Một người năm nay đã 40 tuổi. Hỏi người đó có bao nhiêu ngày sinh nhật?",
                "answer": "1 ngày"
            },
            {
                "category": "Đố vui",
                "question": "Túi gì nghe tên tưởng ngọt, hoá ra đắng ngắt khó lọt khỏi người?",
                "answer": "túi mật"
            },
            {
                "category": "Đố vui",
                "question": "Trong cuộc sống, con người hay dùng vật này để đánh chính mình, đố là cái gì?",
                "answer": "bàn chải đánh răng"
            },
            {
                "category": "Đố vui",
                "question": "Một xương sống, một đống xương sườn là cái gì?",
                "answer": "cái lược"
            },
            {
                "category": "Đố vui",
                "question": "Hồ gì phụ nữ có chồng rất ghét?",
                "answer": "hồ ly tinh"
            },
            {
                "category": "Đố vui",
                "question": "Cái gì của con chim nhưng lại trên cơ thể con người?",
                "answer": "vết chân chim"
            },
            {
                "category": "Đố vui",
                "question": "Con nào ít ai dám ăn, một kẻ lầm lỗi cả bày chịu theo?",
                "answer": "con sâu"
            },
            {
                "category": "Đố vui",
                "question": "Con vật gì là thần nhưng thêm dấu lại thành ác ma?",
                "answer": "con rùa"
            },
            {
                "category": "Đố vui",
                "question": "Có cổ nhưng không có miệng là cái gì?",
                "answer": "cái áo"
            },
            {
                "category": "Đố vui",
                "question": "Sông gì vốn dĩ ồn ào?",
                "answer": "sông la"
            },
            {
                "category": "Đố vui",
                "question": "Vừa bằng hạt đỗ, ăn giỗ cả làng. Là con gì?",
                "answer": "con ruồi"
            },
            {
                "category": "Đố vui",
                "question": "Tôi có 4 cái chân, 1 cái lưng nhưng không có cơ thể. Tôi là ai?",
                "answer": "cái bàn"
            },
            {
                "category": "Đố vui",
                "question": "Nắng lửa mưa dầu tôi đâu bỏ bạn. Tối lửa tắt đèn sao bạn lại bỏ tôi. Đó là cái gì?",
                "answer": "cái bóng"
            },
            {
                "category": "Đố vui",
                "question": "Vì tao tao phải đánh tao, vì tao tao phải đánh mày. Hỏi đang làm gì?",
                "answer": "đập muỗi"
            },
            {
                "category": "Đố vui",
                "question": "Bàn gì xe ngựa sớm chiều giơ ra?",
                "answer": "bàn cờ tướng"
            },
            {
                "category": "Đố vui",
                "question": "Bàn gì mà lại bước gần bước xa?",
                "answer": "bàn chân"
            },
            {
                "category": "Đố vui",
                "question": "Con gì có mũi có lưỡi hẳn hoi. Có sống không chết người đời cầm luôn?",
                "answer": "con dao"
            },
            {
                "category": "Đố vui",
                "question": "Hột để sống: Một tên. Hột nấu lên: tên khác. Trong nhà nông các bác. Đều có mặt cả hai?",
                "answer": "hột gạo"
            },
            {
                "category": "Đố vui",
                "question": "Da thịt như than. Áo choàng như tuyết. Giúp người trị bệnh. Mà tên chẳng hiền.",
                "answer": "gà ác"
            },
            {
                "category": "Đố vui",
                "question": "Mặt gì tròn trịa trên cao. Toả ra những ánh nắng đào đẹp thay?",
                "answer": "mặt trời"
            },
            {
                "category": "Đố vui",
                "question": "Mặt gì mát dịu đêm nay. Cây đa, chú cuội, đứng đây rõ ràng?",
                "answer": "mặt trăng"
            },
            {
                "category": "Đố vui",
                "question": "Mặt gì bằng phẳng thênh thang. Người đi muôn lối dọc ngang phố phường?",
                "answer": "mặt đất"
            },
            {
                "category": "Đố vui",
                "question": "Hoa gì quân tử chẳng chê mùi bùn?",
                "answer": "hoa sen"
            },
            {
                "category": "Đố vui",
                "question": "Đi thì đứng, đứng thì ngã. Là cái gì?",
                "answer": "xe đạp"
            },
            {
                "category": "Đố vui",
                "question": "Quần rộng nhất là quần gì?",
                "answer": "quần đảo"
            },
            {
                "category": "Đố vui",
                "question": "Con gì không vú mà nuôi con?",
                "answer": "con gà mái"
            },
            {
                "category": "Đố vui",
                "question": "Con gì chân ngắn mà lại có màng, mỏ bẹt màu vàng, hay kêu cạp cạp?",
                "answer": "con vịt"
            },
            {
                "category": "Đố vui",
                "question": "Con gì một lòng khuya sớm chuyên cần, trách người vô nghĩa, sao chê ngu đần?",
                "answer": "con bò"
            },
            {
                "category": "Đố vui",
                "question": "Vừa bằng quả ổi, khi nổi khi chìm, là con gì?",
                "answer": "con ốc"
            },
            {
                "category": "Đố vui",
                "question": "Con gì ăn no, bụng to mắt híp, mồm kêu ụt ịt, nằm thở phì phò?",
                "answer": "con heo"
            },
            {
                "category": "Đố vui",
                "question": "Thân em nửa chuột, nửa chim, ngày treo chân ngủ, tối tìm mồi bay, trời cho tai mắt giỏi thay, tối đen tối mịt cứ bay vù vù là con gì?",
                "answer": "con dơi"
            },
            {
                "category": "Toán học",
                "question": "Số nào là số nguyên tố nhỏ nhất?",
                "answer": "2"
            },
            {
                "category": "Toán học",
                "question": "Tổng của các số từ 1 đến 10 là bao nhiêu?",
                "answer": "55"
            },
            {
                "category": "Toán học",
                "question": "Số nào là bình phương của 5?",
                "answer": "25"
            },
            {
                "category": "Toán học",
                "question": "Số nào là số lẻ nhỏ nhất có 2 chữ số?",
                "answer": "11"
            },
            {
                "category": "Toán học",
                "question": "Tích của 6 và 7 là bao nhiêu?",
                "answer": "42"
            },
            {
                "category": "Toán học",
                "question": "Số nào là số chẵn lớn nhất có 2 chữ số?",
                "answer": "98"
            },
            {
                "category": "Toán học",
                "question": "Số nào là số nguyên tố lớn nhất có 1 chữ số?",
                "answer": "7"
            },
            {
                "category": "Toán học",
                "question": "Tổng của 3 số liên tiếp là 15, số lớn nhất là bao nhiêu?",
                "answer": "6"
            },
            {
                "category": "Toán học",
                "question": "Số nào là số chính phương nhỏ nhất có 2 chữ số?",
                "answer": "16"
            },
            {
                "category": "Toán học",
                "question": "Tích của 4 số tự nhiên liên tiếp là 24, số lớn nhất là bao nhiêu?",
                "answer": "4"
            },
            {
                "category": "Toán học",
                "question": "Số nào là số lẻ lớn nhất có 2 chữ số?",
                "answer": "99"
            },
            {
                "category": "Toán học",
                "question": "Tổng của 2 số là 20, hiệu là 4, số lớn là bao nhiêu?",
                "answer": "12"
            },
            {
                "category": "Toán học",
                "question": "Số nào là số chính phương lớn nhất có 2 chữ số?",
                "answer": "81"
            },
            {
                "category": "Toán học",
                "question": "Tích của 2 số là 36, tổng là 13, số lớn là bao nhiêu?",
                "answer": "9"
            },
            {
                "category": "Toán học",
                "question": "Số nào là số nguyên tố lớn nhất có 2 chữ số?",
                "answer": "97"
            },
            {
                "category": "Địa lý",
                "question": "Thành phố nào được mệnh danh là 'Thành phố hoa phượng đỏ'?",
                "answer": "hải phòng"
            },
            {
                "category": "Địa lý",
                "question": "Sông nào dài nhất Việt Nam?",
                "answer": "sông hồng"
            },
            {
                "category": "Địa lý",
                "question": "Núi nào cao nhất Việt Nam?",
                "answer": "phan xi păng"
            },
            {
                "category": "Địa lý",
                "question": "Vịnh nào được UNESCO công nhận là di sản thế giới?",
                "answer": "vịnh hạ long"
            },
            {
                "category": "Địa lý",
                "question": "Thành phố nào được mệnh danh là 'Thành phố ngàn hoa'?",
                "answer": "đà lạt"
            },
            {
                "category": "Địa lý",
                "question": "Đảo nào lớn nhất Việt Nam?",
                "answer": "phú quốc"
            },
            {
                "category": "Địa lý",
                "question": "Quốc gia nào có chung biên giới với Việt Nam ở phía Bắc?",
                "answer": "trung quốc"
            },
            {
                "category": "Địa lý",
                "question": "Thành phố nào là thủ đô của Việt Nam?",
                "answer": "hà nội"
            },
            {
                "category": "Địa lý",
                "question": "Thành phố nào được mệnh danh là 'Thành phố không ngủ'?",
                "answer": "hồ chí minh"
            },
            {
                "category": "Địa lý",
                "question": "Quốc gia nào có chung biên giới với Việt Nam ở phía Tây?",
                "answer": "lào"
            },
            {
                "category": "Địa lý",
                "question": "Thành phố nào được mệnh danh là 'Thành phố cảng'?",
                "answer": "hải phòng"
            },
            {
                "category": "Địa lý",
                "question": "Quốc gia nào có chung biên giới với Việt Nam ở phía Nam?",
                "answer": "campuchia"
            },
            {
                "category": "Địa lý",
                "question": "Thành phố nào được mệnh danh là 'Thành phố biển'?",
                "answer": "nha trang"
            },
            {
                "category": "Địa lý",
                "question": "Quốc gia nào có chung biên giới với Việt Nam ở phía Đông?",
                "answer": "không có"
            },
            {
                "category": "Địa lý",
                "question": "Thành phố nào được mệnh danh là 'Thành phố hoa'?",
                "answer": "đà lạt"
            },
            {
                "category": "Lịch sử",
                "question": "Ai là vị vua đầu tiên của triều đại nhà Nguyễn?",
                "answer": "gia long"
            },
            {
                "category": "Lịch sử",
                "question": "Năm 1945, sự kiện nào đánh dấu sự kết thúc của Thế chiến II?",
                "answer": "nhật bản đầu hàng"
            },
            {
                "category": "Lịch sử",
                "question": "Ai là người sáng lập ra triều đại nhà Lý?",
                "answer": "lý thái tổ"
            },
            {
                "category": "Lịch sử",
                "question": "Trận đánh nào đánh dấu chiến thắng của quân dân ta trước quân Mông Cổ?",
                "answer": "bạch đằng"
            },
            {
                "category": "Lịch sử",
                "question": "Năm 1975, sự kiện nào đánh dấu sự thống nhất đất nước?",
                "answer": "giải phóng miền nam"
            },
            {
                "category": "Lịch sử",
                "question": "Ai là người lãnh đạo cuộc khởi nghĩa Lam Sơn?",
                "answer": "lê lợi"
            },
            {
                "category": "Lịch sử",
                "question": "Năm 1945, ai là người đọc bản Tuyên ngôn độc lập?",
                "answer": "hồ chí minh"
            },
            {
                "category": "Lịch sử",
                "question": "Ai là vị vua đầu tiên của triều đại nhà Trần?",
                "answer": "trần thái tông"
            },
            {
                "category": "Lịch sử",
                "question": "Năm 1789, trận đánh nào đánh dấu chiến thắng của quân Tây Sơn?",
                "answer": "ngọc hồi đống đa"
            },
            {
                "category": "Lịch sử",
                "question": "Ai là người sáng lập ra triều đại nhà Hồ?",
                "answer": "hồ quý ly"
            },
            {
                "category": "Lịch sử",
                "question": "Năm 1954, chiến thắng nào đánh dấu sự kết thúc của chế độ thực dân Pháp?",
                "answer": "điện biên phủ"
            },
            {
                "category": "Lịch sử",
                "question": "Ai là vị vua đầu tiên của triều đại nhà Mạc?",
                "answer": "mạc đăng dung"
            },
            {
                "category": "Lịch sử",
                "question": "Năm 1288, trận đánh nào đánh dấu chiến thắng của quân dân ta trước quân Nguyên?",
                "answer": "bạch đằng"
            },
            {
                "category": "Lịch sử",
                "question": "Ai là người sáng lập ra triều đại nhà Đinh?",
                "answer": "đinh bộ lĩnh"
            },
            {
                "category": "Lịch sử",
                "question": "Năm 1428, ai là người lãnh đạo cuộc khởi nghĩa Lam Sơn?",
                "answer": "lê lợi"
            }
        ]

    async def start_new_quiz(self, channel):
        if self.active:
            return False
        
        self.active = True
        self.scores = {}
        self.current_question_index = 0
        self.used_questions = []
        self.confirmed_players.clear()  # Xóa danh sách người chơi cũ
        
        # Tạo view với nút tham gia
        class JoinView(discord.ui.View):
            def __init__(self, quiz_game):
                super().__init__(timeout=None)
                self.quiz_game = quiz_game

            @discord.ui.button(label="Tham gia", style=discord.ButtonStyle.green)
            async def join_button(self, interaction: discord.Interaction, button: discord.ui.Button):
                if interaction.user.name in self.quiz_game.confirmed_players:
                    await interaction.response.send_message("Bạn đã tham gia rồi!", ephemeral=True)
                    return
                
                self.quiz_game.confirmed_players.add(interaction.user.name)
                await interaction.response.send_message(
                    f"✅ {interaction.user.mention} đã tham gia trò chơi!",
                    ephemeral=True
                )
        
        # Gửi thông báo với nút tham gia
        embed = discord.Embed(
            title="🎮 Trò chơi câu đố sắp bắt đầu!",
            description="Nhấn nút bên dưới để tham gia.\nTrò chơi sẽ bắt đầu sau 15 giây.",
            color=discord.Color.blue()
        )
        
        view = JoinView(self)
        confirmation_msg = await channel.send(embed=embed, view=view)
        
        # Đợi 15 giây cho người chơi xác nhận tham gia
        await asyncio.sleep(15)
        
        # Kiểm tra số người tham gia
        if len(self.confirmed_players) == 0:
            await channel.send("Không có người chơi nào tham gia. Trò chơi bị hủy!")
            self.active = False
            return False
        
        # Bắt đầu trò chơi
        self.active = True
        self.scores = {}
        self.current_question_index = 0
        self.used_questions = []
        
        # Thông báo người chơi tham gia
        players_list = "\n".join([f"• {player}" for player in self.confirmed_players])
        await channel.send(f"**Danh sách người chơi:**\n{players_list}\n\nTrò chơi bắt đầu!")
        
        # Lấy câu hỏi đầu tiên
        self.current_question = self.get_next_question()
        if not self.current_question:
            self.active = False
            return False
            
        self.current_answer = self.current_question["answer"]
        
        # Tạo embed cho câu hỏi
        embed = discord.Embed(
            title="🎮 Câu hỏi mới!",
            description=f"**Thể loại:** {self.current_question['category']}\n\n**Câu hỏi:** {self.current_question['question']}",
            color=discord.Color.blue()
        )
        embed.set_footer(text=f"Câu {self.current_question_index}/{self.total_questions}")
        
        # Gửi câu hỏi
        question_msg = await channel.send(embed=embed)
        
        # Bắt đầu đếm ngược 30 giây
        self.timer_task = asyncio.create_task(self.countdown_timer(channel, question_msg))
        
        return True

    async def countdown_timer(self, channel, question_msg):
        try:
            for i in range(30, 0, -1):
                if not self.active:  # Nếu trò chơi kết thúc
                    return
                    
                # Cập nhật embed với thời gian còn lại
                embed = question_msg.embeds[0]
                embed.description = f"**Thể loại:** {self.current_question['category']}\n\n**Câu hỏi:** {self.current_question['question']}\n\n⏰ Thời gian còn lại: {i} giây"
                await question_msg.edit(embed=embed)
                
                # Thông báo ở các mốc thời gian quan trọng
                if i in [15, 10, 5, 4, 3, 2, 1]:
                    warning_embed = discord.Embed(
                        title="⏰ Thông báo thời gian!",
                        description=f"Còn {i} giây để trả lời!",
                        color=discord.Color.orange()
                    )
                    await channel.send(embed=warning_embed)
                
                await asyncio.sleep(1)
            
            # Hết thời gian, công bố đáp án
            if self.active:
                # Ngừng nhận câu trả lời khi hết thời gian
                self.accepting_answers = False
                
                embed = question_msg.embeds[0]
                embed.description = f"**Thể loại:** {self.current_question['category']}\n\n**Câu hỏi:** {self.current_question['question']}\n\n❌ Hết thời gian!\n**Đáp án đúng:** {self.current_answer}"
                embed.color = discord.Color.red()
                await question_msg.edit(embed=embed)
                
                # Đợi 3 giây rồi chuyển câu tiếp
                await asyncio.sleep(3)
                await self.get_next_question_and_send(channel)
                
        except Exception as e:
            print(f"Lỗi trong countdown timer: {e}")

    async def get_next_question_and_send(self, channel):
        if not self.active:
            return
            
        # Lấy câu hỏi tiếp theo
        self.current_question = self.get_next_question()
        if not self.current_question:
            # Kết thúc trò chơi
            await self.end_quiz(channel)
            return
            
        self.current_answer = self.current_question["answer"]
        
        # Tạo embed cho câu hỏi mới
        embed = discord.Embed(
            title="🎮 Câu hỏi tiếp theo!",
            description=f"**Thể loại:** {self.current_question['category']}\n\n**Câu hỏi:** {self.current_question['question']}\n\n💡 Sử dụng lệnh `.as` để trả lời!",
            color=discord.Color.blue()
        )
        embed.set_footer(text=f"Câu {self.current_question_index}/{self.total_questions}")
        
        # Gửi câu hỏi
        question_msg = await channel.send(embed=embed)
        
        # Bắt đầu chấp nhận câu trả lời
        self.accepting_answers = True
        
        # Bắt đầu đếm ngược 30 giây cho câu hỏi mới
        self.timer_task = asyncio.create_task(self.countdown_timer(channel, question_msg))

    async def check_answer(self, message):
        # Kiểm tra xem người trả lời có trong danh sách người chơi không
        if str(message.author) not in self.confirmed_players:
            await message.channel.send(
                f"{message.author.mention} chưa tham gia trò chơi nên không thể trả lời!", 
                delete_after=5
            )
            return False
            
        if not self.active or not self.current_question:
            return False

        # Chuẩn hóa câu trả lời của người chơi
        user_answer = ' '.join(message.content.lower().split())  # Xử lý nhiều khoảng trắng thành một
        
        # Chuẩn hóa đáp án đúng
        correct_answer = ' '.join(self.current_answer.lower().split())

        # In ra để debug
        print(f"User answer: '{user_answer}'")
        print(f"Correct answer: '{correct_answer}'")

        # Kiểm tra câu trả lời
        is_correct = (user_answer == correct_answer)
        
        if is_correct:
            if not self.accepting_answers:
                await message.channel.send(
                    f"⚠️ {message.author.mention} câu trả lời của bạn đúng, nhưng đã có người trả lời đúng trước đó hoặc đang trong thời gian chờ!", 
                    delete_after=5
                )
                return False
            
            # Ngừng nhận câu trả lời ngay khi có người trả lời đúng
            self.accepting_answers = False
            
            # Hủy task đếm ngược nếu có
            if self.timer_task:
                self.timer_task.cancel()
                self.timer_task = None
                
            # Cập nhật điểm
            player = str(message.author)
            self.scores[player] = self.scores.get(player, 0) + 1
            
            # Gửi thông báo đúng
            embed = discord.Embed(
                title="🎉 Chúc mừng!",
                description=f"{message.author.mention} đã trả lời đúng!\n**Đáp án:** {self.current_answer}",
                color=discord.Color.green()
            )
            await message.channel.send(embed=embed)
            
            # Đợi 3 giây rồi chuyển câu tiếp
            await asyncio.sleep(3)
            await self.get_next_question_and_send(message.channel)
            
            return True
            
        else:
            # Nếu câu trả lời sai và đang trong thời gian chấp nhận câu trả lời
            if self.accepting_answers:
                await message.channel.send(
                    f"❌ {message.author.mention} câu trả lời của bạn chưa chính xác, hãy thử lại!", 
                    delete_after=3
                )
            
        return is_correct

    async def end_quiz(self, channel):
        self.active = False
        if self.timer_task:
            self.timer_task.cancel()
            self.timer_task = None
            
        # Tạo bảng xếp hạng
        leaderboard = self.get_leaderboard()
        
        # Tạo embed cho kết quả
        embed = discord.Embed(
            title="🏆 Kết thúc trò chơi!",
            description="Bảng xếp hạng:",
            color=discord.Color.gold()
        )
        
        if leaderboard:
            for i, (player, score) in enumerate(leaderboard, 1):
                medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else "•"
                embed.add_field(
                    name=f"{medal} {player}",
                    value=f"Điểm: {score}",
                    inline=False
                )
        else:
            embed.description = "Không có người chơi nào trả lời đúng câu nào cả!"
            
        await channel.send(embed=embed)

    def get_next_question(self):
        """Lấy câu hỏi tiếp theo"""
        # Kiểm tra xem đã đủ 10 câu chưa
        if self.current_question_index >= self.total_questions:
            return None

        # Lọc ra các câu chưa được hỏi
        available_questions = [q for q in self.questions if q not in self.used_questions]
        if not available_questions:
            return None

        # Chọn câu hỏi ngẫu nhiên
        question = random.choice(available_questions)
        self.used_questions.append(question)
        
        # Tăng số câu hỏi đã hỏi TRƯỚC khi trả về câu hỏi
        self.current_question_index += 1
        
        # Nếu đã đủ 10 câu, đánh dấu là câu cuối
        if self.current_question_index >= self.total_questions:
            self.accepting_answers = True  # Cho phép trả lời câu cuối
        
        return question

    def get_leaderboard(self):
        """Lấy bảng xếp hạng top 3"""
        sorted_scores = sorted(self.scores.items(), key=lambda x: x[1], reverse=True)
        return sorted_scores[:3]

    def remove_accents(self, text):
        """Loại bỏ các dấu tiếng Việt và ký tự đặc biệt"""
        import unicodedata
        import re
        
        # Loại bỏ dấu tiếng Việt
        text = unicodedata.normalize('NFD', text)
        text = text.encode('ascii', 'ignore').decode('ascii')
        
        # Loại bỏ các ký tự đặc biệt, chỉ giữ lại chữ và số
        text = re.sub(r'[^a-zA-Z0-9\s]', '', text)
        
        # Loại bỏ khoảng trắng thừa
        text = ' '.join(text.split())
        
        return text.lower()

# Tạo instance của QuizGame
quiz_game = QuizGame()

@bot.command(name='mg', help='Bắt đầu một ván câu đố vui (10 câu)')
async def start_quiz(ctx):
    """Bắt đầu một ván câu đố vui"""
    if quiz_game.active:
        await ctx.send("Đã có một ván câu đố đang diễn ra! Vui lòng đợi ván chơi kết thúc.")
        return

    success = await quiz_game.start_new_quiz(ctx.channel)
    if not success:
        await ctx.send("Không thể bắt đầu ván chơi mới. Vui lòng thử lại sau!")
        return

@bot.event
async def on_message(message):
    # Bỏ qua tin nhắn từ bot
    if message.author == bot.user:
        return

    # Kiểm tra nếu tin nhắn là chính xác từ "huy"
    if message.content.strip().lower() == "huy":
        await message.channel.send("yêu phương thảo ❤️")
        return

    # Xử lý các lệnh
    await bot.process_commands(message)

# Thêm class AnswerModal
class AnswerModal(discord.ui.Modal, title="Nhập câu trả lời của bạn"):
    answer = discord.ui.TextInput(
        label="Câu trả lời",
        placeholder="Nhập câu trả lời của bạn vào đây...",
        min_length=1,
        max_length=100,
        required=True,
    )

    async def on_submit(self, interaction: discord.Interaction):
        if not quiz_game.accepting_answers:
            await interaction.response.send_message(
                "Đã hết thời gian trả lời hoặc có người khác đã trả lời đúng!",
                ephemeral=True
            )
            return

        # Tạo message giả để sử dụng với hàm check_answer
        class FakeMessage:
            def __init__(self, content, author, channel):
                self.content = content
                self.author = author
                self.channel = channel

        message = FakeMessage(
            content=self.answer.value,
            author=interaction.user,
            channel=interaction.channel
        )
        
        # Gọi hàm check_answer
        await quiz_game.check_answer(message)
        
        # Thông báo đã nhận câu trả lời
        await interaction.response.send_message(
            "Đã nhận câu trả lời của bạn!",
            ephemeral=True
        )

# Thêm class AnswerView
class AnswerView(discord.ui.View):
    def __init__(self, quiz_game):
        super().__init__(timeout=None)
        self.quiz_game = quiz_game

    @discord.ui.button(label="Trả lời", style=discord.ButtonStyle.primary)
    async def answer_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self.quiz_game.accepting_answers:
            await interaction.response.send_message(
                "Không thể trả lời lúc này! Vui lòng đợi câu hỏi mới.",
                ephemeral=True
            )
            return
                
        if str(interaction.user) not in self.quiz_game.confirmed_players:
            await interaction.response.send_message(
                "Bạn chưa tham gia trò chơi nên không thể trả lời!",
                ephemeral=True
            )
            return
                    
        # Hiển thị modal để nhập câu trả lời
        modal = AnswerModal()
        await interaction.response.send_modal(modal)

# Thêm lệnh .as vào bot
@bot.command(name='as', help='Trả lời câu hỏi hiện tại')
async def answer(ctx):
    """Hiển thị modal để trả lời câu hỏi"""
    # Kiểm tra xem có trò chơi đang diễn ra không
    if not quiz_game.active:
        await ctx.send("Không có trò chơi nào đang diễn ra!", delete_after=3)
        return

    # Kiểm tra xem người chơi có trong danh sách không
    if str(ctx.author) not in quiz_game.confirmed_players:
        await ctx.send("Bạn chưa tham gia trò chơi nên không thể trả lời!", delete_after=3)
        return

    # Kiểm tra xem có đang nhận câu trả lời không
    if not quiz_game.accepting_answers:
        await ctx.send("Không thể trả lời lúc này! Vui lòng đợi câu hỏi mới.", delete_after=3)
        return

    # Tạo message giả để sử dụng với hàm check_answer
    class FakeMessage:
        def __init__(self, content, author, channel):
            self.content = content
            self.author = author
            self.channel = channel

    # Gửi tin nhắn yêu cầu nhập câu trả lời
    await ctx.send(f"{ctx.author.mention} Hãy nhập câu trả lời của bạn:")

    try:
        # Đợi tin nhắn trả lời từ người dùng
        response = await bot.wait_for(
            'message',
            timeout=30.0,
            check=lambda m: m.author == ctx.author and m.channel == ctx.channel
        )

        # Tạo message giả và kiểm tra câu trả lời
        message = FakeMessage(
            content=response.content,
            author=ctx.author,
            channel=ctx.channel
        )
        await quiz_game.check_answer(message)

    except asyncio.TimeoutError:
        await ctx.send(f"{ctx.author.mention} Hết thời gian trả lời!", delete_after=3)

# Run the bot
bot.run(TOKEN) 