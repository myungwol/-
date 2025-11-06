import discord
from discord.ext import commands
import os

class AutoVoiceCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # 환경 변수에서 채널 및 카테고리 ID를 가져옵니다.
        self.trigger_channel_id = int(os.environ.get("AUTO_VOICE_TRIGGER_CHANNEL_ID"))
        self.category_id = int(os.environ.get("AUTO_VOICE_CATEGORY_ID"))
        # 봇이 생성한 채널의 ID를 추적하기 위한 세트(set)
        self.created_channels = set()

    @commands.Cog.listener()
    async def on_ready(self):
        print("자동 음성 채널 코그(Auto Voice Cog)가 준비되었습니다.")

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        # 봇이거나, '채널 생성' 채널에 들어온 경우가 아니면 무시
        if member.bot or not after.channel or after.channel.id != self.trigger_channel_id:
            # 채널이 삭제되는 경우도 처리해야 합니다.
            if before.channel and before.channel.id in self.created_channels:
                # 채널에 아무도 남아있지 않으면 삭제
                if len(before.channel.members) == 0:
                    try:
                        await before.channel.delete(reason="자동 생성 채널: 사용자가 모두 나감")
                        self.created_channels.remove(before.channel.id)
                        print(f"자동 생성 채널 '{before.channel.name}' (ID: {before.channel.id})을(를) 삭제했습니다.")
                    except discord.NotFound:
                        # 이미 삭제된 경우를 대비한 예외 처리
                        pass
                    except discord.Forbidden:
                        print(f"오류: 채널 (ID: {before.channel.id})을(를) 삭제할 권한이 없습니다.")
            return

        # '채널 생성' 채널에 입장한 경우
        try:
            # 채널이 생성될 카테고리를 가져옵니다.
            category = self.bot.get_channel(self.category_id)
            if not category or not isinstance(category, discord.CategoryChannel):
                print(f"오류: ID({self.category_id})에 해당하는 카테고리를 찾을 수 없습니다.")
                return

            # 사용자별 채널 이름 설정
            channel_name = f"{member.display_name}님의 채널"
            
            # 새 음성 채널 생성
            # overwrites를 사용하여 채널 생성자에게 '채널 관리' 권한을 부여합니다.
            overwrites = {
                member: discord.PermissionOverwrite(manage_channels=True, manage_webhooks=True)
            }
            new_channel = await member.guild.create_voice_channel(
                name=channel_name,
                category=category,
                overwrites=overwrites,
                reason=f"{member.name} 님이 자동 채널 생성을 요청함"
            )
            
            # 생성된 채널로 사용자를 즉시 이동
            await member.move_to(new_channel)
            
            # 생성된 채널 ID를 추적 목록에 추가
            self.created_channels.add(new_channel.id)
            print(f"'{member.name}' 님을 위해 '{channel_name}' 채널 (ID: {new_channel.id})을(를) 생성했습니다.")

        except discord.Forbidden:
            print(f"오류: '{member.guild.name}' 서버에 채널을 생성하거나 멤버를 이동할 권한이 없습니다.")
        except Exception as e:
            print(f"자동 음성 채널 생성 중 오류 발생: {e}")

    # 채널 이름을 변경하는 슬래시 커맨드
    @discord.app_commands.command(name="채널이름", description="자신이 만든 음성 채널의 이름을 변경합니다.")
    @discord.app_commands.describe(new_name="새로운 채널 이름")
    async def rename_channel(self, interaction: discord.Interaction, new_name: str):
        user = interaction.user
        
        # 사용자가 음성 채널에 접속해 있는지 확인
        if not user.voice or not user.voice.channel:
            await interaction.response.send_message("음성 채널에 먼저 접속해주세요.", ephemeral=True)
            return

        channel = user.voice.channel

        # 현재 접속한 채널이 봇이 생성한 채널인지 확인
        if channel.id not in self.created_channels:
            await interaction.response.send_message("이 기능은 봇이 자동으로 생성한 채널에서만 사용할 수 있습니다.", ephemeral=True)
            return
            
        # 채널을 수정할 권한이 있는지 확인 (채널 생성자)
        if not channel.permissions_for(user).manage_channels:
            await interaction.response.send_message("채널 이름을 변경할 권한이 없습니다. 채널 생성자만 변경할 수 있습니다.", ephemeral=True)
            return

        try:
            old_name = channel.name
            await channel.edit(name=new_name, reason=f"{user.name} 님이 이름 변경 요청")
            await interaction.response.send_message(f"채널 이름이 '{old_name}'에서 '{new_name}'(으)로 변경되었습니다.")
        except discord.Forbidden:
            await interaction.response.send_message("오류: 채널 이름을 변경할 권한이 없습니다.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"오류가 발생했습니다: {e}", ephemeral=True)


async def setup(bot):
    await bot.add_cog(AutoVoiceCog(bot))
