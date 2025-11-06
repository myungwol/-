# main.py 상단부

import discord
from discord.ext import commands, tasks
import os
import sys # sys 모듈 추가
import asyncio
from supabase import create_client, Client

# --- 환경 변수 설정 (오류 진단 기능 추가) ---
try:
    SUPABASE_URL = os.environ["SUPABASE_URL"]
    SUPABASE_KEY = os.environ["SUPABASE_KEY"]
    DISCORD_TOKEN = os.environ["DISCORD_TOKEN"]
    TARGET_CHANNEL_ID = int(os.environ["TARGET_CHANNEL_ID"]) # 멤버 카운트 채널 ID
except KeyError as e:
    print(f"오류: 필수 환경 변수 '{e.args[0]}'가 설정되지 않았습니다.")
    print("Railway의 'Variables' 탭에서 모든 환경 변수가 올바르게 설정되었는지 확인하세요.")
    sys.exit(1) # 오류 발생 시 스크립트 종료
except (ValueError, TypeError):
    print(f"오류: TARGET_CHANNEL_ID 환경 변수가 올바른 숫자(채널 ID)가 아닙니다.")
    sys.exit(1)


# --- Supabase 클라이언트 생성 ---
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# --- 디스코드 봇 Intents 설정 ---
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.voice_states = True # 음성 상태 감지를 위해 필요!

# Client 대신 Bot을 사용합니다. command_prefix는 코그를 사용하기 위해 필요합니다.
bot = commands.Bot(command_prefix="!", intents=intents)

# --- 기존 멤버 카운트 기능 (Bot 클래스에 맞게 수정) ---

# on_ready 이벤트는 여러 파일에 있을 수 있으므로, Cog가 아닌 곳에서는 리스너로 등록합니다.
@bot.listen()
async def on_ready():
    print(f'{bot.user}으로 로그인 성공!')
    update_member_count.start() # 주기적 멤버 수 업데이트 시작
    await bot.tree.sync() # <<<< 이 줄을 추가해주세요!
    print("슬래시 커맨드를 성공적으로 동기화했습니다.")

@bot.listen()
async def on_member_join(member):
    print(f'{member.name}님이 서버에 참여했습니다.')
    await update_channel_name(member.guild)

@bot.listen()
async def on_member_remove(member):
    print(f'{member.name}님이 서버에서 나갔습니다.')
    await update_channel_name(member.guild)

@tasks.loop(minutes=30)
async def update_member_count():
    await bot.wait_until_ready()
    print("주기적인 멤버 수 동기화를 시작합니다.")
    for guild in bot.guilds:
        await update_channel_name(guild)
    print("주기적인 멤버 수 동기화를 완료했습니다.")

async def update_channel_name(guild):
    try:
        channel = bot.get_channel(TARGET_CHANNEL_ID)
        if channel and channel.guild.id == guild.id:
            member_count = guild.member_count
            new_name = f"전체 멤버: {member_count}"
            if channel.name != new_name:
                await channel.edit(name=new_name)
                print(f"'{guild.name}' 서버의 채널 이름을 '{new_name}'으로 변경했습니다.")
        else:
            print(f"'{guild.name}' 서버에서 ID({TARGET_CHANNEL_ID})에 해당하는 채널을 찾을 수 없습니다.")
    except discord.errors.Forbidden:
        print(f"오류: '{guild.name}' 서버의 채널({TARGET_CHANNEL_ID}) 이름을 변경할 권한이 없습니다.")
    except Exception as e:
        print(f"채널 이름 변경 중 오류 발생: {e}")

# --- 메인 실행 함수 ---
async def main():
    # cogs 폴더에 있는 모든 .py 파일을 찾아 로드합니다.
    for filename in os.listdir('./cogs'):
        if filename.endswith('.py'):
            try:
                await bot.load_extension(f'cogs.{filename[:-3]}')
                print(f'{filename} 코그를 성공적으로 로드했습니다.')
            except Exception as e:
                print(f'{filename} 코그를 로드하는 중 오류 발생: {e}')
    
    # 봇을 실행합니다.
    await bot.start(DISCORD_TOKEN)

if __name__ == '__main__':
    asyncio.run(main())
