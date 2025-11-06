import discord
import os
from supabase import create_client, Client

# Supabase 연결 설정
url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f'{client.user}으로 로그인 성공!')

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.content.startswith('!안녕'):
        await message.channel.send('안녕하세요!')

        # Supabase에 데이터 저장 예시
        user_id = message.author.id
        user_name = message.author.name

        # 'users' 테이블에 데이터 삽입
        data, count = supabase.table('users').insert({"user_id": user_id, "name": user_name}).execute()


# 봇 토큰으로 봇 실행
client.run(os.environ.get("DISCORD_TOKEN"))
