import discord
from discord.ext import commands
import datetime
import os

class LogCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # 환경 변수에서 로그 채널 ID를 가져옵니다.
        self.log_channel_id = int(os.environ.get("LOG_CHANNEL_ID"))
        # 서버별 초대 링크 정보를 저장할 딕셔너리
        self.invites = {}

    # --- 이벤트 리스너 ---

    @commands.Cog.listener()
    async def on_ready(self):
        """Cog가 로드되고 봇이 준비되었을 때 실행"""
        print("로그 코그(Log Cog)가 준비되었습니다.")
        # 봇이 켜질 때 모든 서버의 초대 링크 정보를 가져와 캐시에 저장
        for guild in self.bot.guilds:
            try:
                # {초대코드: 사용횟수} 형태의 딕셔너리로 캐시 저장
                self.invites[guild.id] = {invite.code: invite.uses for invite in await guild.invites()}
            except discord.Forbidden:
                print(f"'{guild.name}' 서버의 초대 링크를 읽을 권한이 없습니다.")
        print("모든 서버의 초대 링크 정보를 캐시했습니다.")


    # --- 신규 멤버 입장 로그 (초대 추적 기능 추가) ---

    @commands.Cog.listener()
    async def on_member_join(self, member):
        """새로운 멤버가 서버에 들어왔을 때 실행"""
        log_channel = self.bot.get_channel(self.log_channel_id)
        if log_channel is None:
            return

        used_invite = None
        try:
            # 멤버가 들어온 후의 서버 초대 링크 목록
            new_invites = {invite.code: invite.uses for invite in await member.guild.invites()}
            # 봇이 켜지기 전의 캐시된 초대 링크 목록
            old_invites = self.invites.get(member.guild.id, {})

            # 사용 횟수를 비교하여 어떤 초대가 사용되었는지 찾기
            for code, uses in new_invites.items():
                if uses > old_invites.get(code, 0):
                    used_invite = await self.bot.fetch_invite(code)
                    break
            
            # 캐시 업데이트
            self.invites[member.guild.id] = new_invites

        except discord.Forbidden:
            print(f"'{member.guild.name}' 서버의 초대 링크를 읽을 권한이 없어 유입 경로 추적에 실패했습니다.")
        except Exception as e:
            print(f"초대 링크 추적 중 오류 발생: {e}")

        # 임베드 생성
        embed = discord.Embed(
            title="👋 신규 멤버 입장",
            description=f"**{member.mention}** 님이 서버에 참여했습니다.",
            color=discord.Color.teal(),
            timestamp=datetime.datetime.now(datetime.timezone.utc)
        )
        embed.set_thumbnail(url=member.avatar.url if member.avatar else member.default_avatar.url)
        embed.set_footer(text=f"유저 ID: {member.id}")

        if used_invite:
            embed.add_field(name="📥 유입 경로", value=f"**초대자:** {used_invite.inviter.mention}\n**코드:** `{used_invite.code}`\n**링크:** {used_invite.url}", inline=False)
        else:
            embed.add_field(name="📥 유입 경로", value="경로를 특정할 수 없습니다. (서버 탐색 기능 또는 Vanity URL)", inline=False)

        await log_channel.send(embed=embed)


    # --- 초대 링크가 생성/삭제될 때 캐시를 업데이트하여 정확도 유지 ---

    @commands.Cog.listener()
    async def on_invite_create(self, invite):
        """서버에 초대 링크가 생성되었을 때 실행"""
        print(f"'{invite.guild.name}' 서버에 새 초대(코드: {invite.code})가 생성되어 캐시를 업데이트합니다.")
        self.invites[invite.guild.id] = {i.code: i.uses for i in await invite.guild.invites()}

    @commands.Cog.listener()
    async def on_invite_delete(self, invite):
        """서버에서 초대 링크가 삭제되었을 때 실행"""
        print(f"'{invite.guild.name}' 서버의 초대(코드: {invite.code})가 삭제되어 캐시를 업데이트합니다.")
        self.invites[invite.guild.id] = {i.code: i.uses for i in await invite.guild.invites()}


    # --- 기존 로그 기능 (메시지, 음성 채널) ---
    # (이전 단계의 on_message_delete, on_message_edit, on_voice_state_update 코드는 이 아래에 그대로 유지됩니다)
    # ... (이하 기존 코드 생략) ...

    @commands.Cog.listener()
    async def on_message_delete(self, message):
        # 봇 자신의 메시지는 무시
        if message.author.bot:
            return

        # 로그를 보낼 채널을 가져옵니다.
        log_channel = self.bot.get_channel(self.log_channel_id)
        if log_channel is None:
            return

        embed = discord.Embed(
            title="🗑️ 메시지 삭제됨",
            description=f"**채널:** {message.channel.mention}\n**작성자:** {message.author.mention}",
            color=discord.Color.red(),
            timestamp=datetime.datetime.now(datetime.timezone.utc)
        )
        # 메시지 내용이 비어있지 않다면 필드에 추가합니다.
        if message.content:
            embed.add_field(name="내용", value=f"```{message.content}```", inline=False)
        embed.set_footer(text=f"유저 ID: {message.author.id}")

        await log_channel.send(embed=embed)


    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        # 봇 자신의 메시지는 무시
        if before.author.bot:
            return
        
        # 내용이 동일하면 (임베드 생성 등) 무시
        if before.content == after.content:
            return

        log_channel = self.bot.get_channel(self.log_channel_id)
        if log_channel is None:
            return

        embed = discord.Embed(
            title="✏️ 메시지 수정됨",
            description=f"**채널:** {after.channel.mention}\n**작성자:** {after.author.mention}\n[수정된 메시지로 이동](https://discord.com/channels/{after.guild.id}/{after.channel.id}/{after.id})",
            color=discord.Color.orange(),
            timestamp=datetime.datetime.now(datetime.timezone.utc)
        )
        embed.add_field(name="수정 전", value=f"```{before.content}```", inline=False)
        embed.add_field(name="수정 후", value=f"```{after.content}```", inline=False)
        embed.set_footer(text=f"유저 ID: {after.author.id}")

        await log_channel.send(embed=embed)


    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        # 봇은 무시
        if member.bot:
            return
            
        log_channel = self.bot.get_channel(self.log_channel_id)
        if log_channel is None:
            return

        # 채널에 입장했을 때
        if before.channel is None and after.channel is not None:
            embed = discord.Embed(
                title="🔊 음성 채널 입장",
                description=f"**{member.mention}** 님이 **{after.channel.name}** 채널에 입장했습니다.",
                color=discord.Color.green(),
                timestamp=datetime.datetime.now(datetime.timezone.utc)
            )
            embed.set_footer(text=f"유저 ID: {member.id}")
            await log_channel.send(embed=embed)
            
        # 채널에서 퇴장했을 때
        elif before.channel is not None and after.channel is None:
            embed = discord.Embed(
                title="🔇 음성 채널 퇴장",
                description=f"**{member.mention}** 님이 **{before.channel.name}** 채널에서 퇴장했습니다.",
                color=discord.Color.dark_grey(),
                timestamp=datetime.datetime.now(datetime.timezone.utc)
            )
            embed.set_footer(text=f"유저 ID: {member.id}")
            await log_channel.send(embed=embed)

        # 채널을 이동했을 때
        elif before.channel is not None and after.channel is not None and before.channel != after.channel:
            embed = discord.Embed(
                title="🔄 음성 채널 이동",
                description=f"**{member.mention}** 님이 채널을 이동했습니다.",
                color=discord.Color.blue(),
                timestamp=datetime.datetime.now(datetime.timezone.utc)
            )
            embed.add_field(name="이전 채널", value=before.channel.name, inline=True)
            embed.add_field(name="현재 채널", value=after.channel.name, inline=True)
            embed.set_footer(text=f"유저 ID: {member.id}")
            await log_channel.send(embed=embed)


async def setup(bot):
    await bot.add_cog(LogCog(bot))
