import discord
from discord.ext import commands
import datetime
import os

class LogCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # 환경 변수에서 로그 채널 ID를 가져옵니다.
        self.log_channel_id = int(os.environ.get("LOG_CHANNEL_ID"))

    # Cog가 로드될 때 콘솔에 메시지를 출력합니다.
    @commands.Cog.listener()
    async def on_ready(self):
        print("로그 코그(Log Cog)가 준비되었습니다.")

    # --- 메시지(채팅) 로그 ---

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


    # --- 음성 채널 로그 ---

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


# 이 함수는 main.py에서 Cog를 로드할 때 필수적으로 필요한 부분입니다.
async def setup(bot):
    await bot.add_cog(LogCog(bot))
