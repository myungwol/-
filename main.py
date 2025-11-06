import discord
import os
from supabase import create_client, Client
from discord.ext import tasks # tasks 라이브러리 임포트

# --- 환경 변수 및 클라이언트 설정 (기존과 동일) ---
# Supabase 연결 설정
url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)

# 디스코드 봇 Intents 설정 (멤버 관련 Intent 추가)
intents = discord.Intents.default()
intents.message_content = True
intents.members = True # 멤버 관련 이벤트를 받기 위해 꼭 필요합니다!
client = discord.Client(intents=intents)

# --- 멤버 카운트 기능 관련 설정 ---
# 이 채널 ID를 실제 여러분 서버의 '멤버 수 표시용' 음성 채널 ID로 변경해주세요.
# 채널 ID 확인 방법: 디스코드에서 채널 우클릭 -> 'ID 복사'
TARGET_CHANNEL_ID = 1435963289556484099 # <<< 중요: 실제 채널 ID로 변경하세요!

# --- 이벤트 핸들러 ---
@client.event
async def on_ready():
    """봇이 준비되었을 때 실행되는 이벤트"""
    print(f'{client.user}으로 로그인 성공!')
    # 봇이 시작될 때 주기적으로 멤버 수를 업데이트하는 작업을 시작합니다.
    update_member_count.start()


@client.event
async def on_message(message):
    """메시지를 수신했을 때 실행되는 이벤트 (기존 코드)"""
    if message.author == client.user:
        return

    if message.content.startswith('!안녕'):
        await message.channel.send('안녕하세요!')

        # Supabase에 데이터 저장 예시
        user_id = message.author.id
        user_name = message.author.name
        data, count = supabase.table('users').insert({"user_id": user_id, "name": user_name}).execute()


@client.event
async def on_member_join(member):
    """새로운 멤버가 서버에 들어왔을 때 실행되는 이벤트"""
    print(f'{member.name}님이 서버에 참여했습니다.')
    await update_channel_name(member.guild)


@client.event
async def on_member_remove(member):
    """멤버가 서버에서 나갔을 때 (또는 킥/밴 당했을 때) 실행되는 이벤트"""
    print(f'{member.name}님이 서버에서 나갔습니다.')
    await update_channel_name(member.guild)


# --- 주기적인 작업 (Tasks) ---
@tasks.loop(minutes=30) # 30분에 한 번씩 이 함수를 실행합니다.
async def update_member_count():
    """주기적으로 모든 서버의 멤버 수를 동기화하는 함수"""
    # 봇이 켜지기 전에 이 루프가 먼저 실행되는 것을 방지
    await client.wait_until_ready()
    
    print("주기적인 멤버 수 동기화를 시작합니다.")
    # 봇이 들어가 있는 모든 서버(guild)를 순회합니다.
    for guild in client.guilds:
        await update_channel_name(guild)
    print("주기적인 멤버 수 동기화를 완료했습니다.")


# --- 핵심 로직 함수 ---
async def update_channel_name(guild):
    """채널 이름을 현재 멤버 수로 변경하는 함수"""
    try:
        # 설정한 ID를 가진 채널 객체를 가져옵니다.
        channel = client.get_channel(TARGET_CHANNEL_ID)
        
        # 채널이 존재하고, 해당 채널이 이 함수를 호출한 서버(guild)에 속해있는지 확인합니다.
        if channel and channel.guild.id == guild.id:
            member_count = guild.member_count # 현재 서버의 멤버 수를 가져옵니다.
            new_name = f"서버 멤버: {member_count}" # 변경할 채널 이름
            
            # 현재 채널 이름과 변경될 이름이 다를 경우에만 변경을 시도합니다.
            # (API 호출 최소화를 위해)
            if channel.name != new_name:
                await channel.edit(name=new_name)
                print(f"'{guild.name}' 서버의 채널 이름을 '{new_name}'으로 변경했습니다.")
        else:
            # 설정한 ID의 채널을 찾지 못한 경우 로그를 남깁니다.
            print(f"'{guild.name}' 서버에서 ID({TARGET_CHANNEL_ID})에 해당하는 채널을 찾을 수 없습니다.")
    except discord.errors.Forbidden:
        # 봇이 채널을 수정할 권한이 없는 경우 로그를 남깁니다.
        print(f"오류: '{guild.name}' 서버의 채널({TARGET_CHANNEL_ID}) 이름을 변경할 권한이 없습니다.")
    except Exception as e:
        # 그 외 다른 예외가 발생한 경우 로그를 남깁니다.
        print(f"채널 이름 변경 중 오류 발생: {e}")


# --- 봇 실행 (기존과 동일) ---
client.run(os.environ.get("DISCORD_TOKEN"))
