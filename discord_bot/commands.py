import discord
from discord.ext import commands
from discord import app_commands
import logging
from typing import Optional

logger = logging.getLogger(__name__)

class AdminCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
    @commands.group(name='pause', invoke_without_command=True)
    async def pause_group(self, ctx):
        """Main command group for Reflective Pause Bot"""
        if ctx.invoked_subcommand is None:
            await self.bot_help(ctx)
            
    @pause_group.command(name='enable')
    @commands.has_permissions(manage_guild=True)
    async def enable_bot(self, ctx):
        """Enable the Reflective Pause Bot for this server"""
        await self.bot.storage.set_enabled(ctx.guild.id, True)
        
        embed = discord.Embed(
            title="✅ Bot Enabled",
            description="Reflective Pause Bot is now active in this server.",
            color=0x00ff9f
        )
        embed.add_field(
            name="What happens now?",
            value="The bot will monitor messages for potentially toxic content and send private reflection prompts to help users pause before posting.",
            inline=False
        )
        await ctx.send(embed=embed)
        
    @pause_group.command(name='disable')
    @commands.has_permissions(manage_guild=True)
    async def disable_bot(self, ctx):
        """Disable the Reflective Pause Bot for this server"""
        await self.bot.storage.set_enabled(ctx.guild.id, False)
        
        embed = discord.Embed(
            title="❌ Bot Disabled",
            description="Reflective Pause Bot is now inactive in this server.",
            color=0xff6b6b
        )
        await ctx.send(embed=embed)
        
    @pause_group.command(name='status')
    async def bot_status(self, ctx):
        """Check the current status of the bot"""
        settings = await self.bot.storage.get_guild_settings(ctx.guild.id)
        stats = await self.bot.storage.get_guild_stats(ctx.guild.id)
        
        status_color = 0x00ff9f if settings['enabled'] else 0xff6b6b
        status_text = "🟢 Enabled" if settings['enabled'] else "🔴 Disabled"
        
        embed = discord.Embed(
            title="Reflective Pause Bot Status",
            color=status_color
        )
        
        embed.add_field(
            name="Status",
            value=status_text,
            inline=True
        )
        embed.add_field(
            name="Toxicity Threshold",
            value=f"{settings['toxicity_threshold']:.1%}",
            inline=True
        )
        embed.add_field(
            name="Language",
            value=settings['locale'].upper(),
            inline=True
        )
        
        # Usage statistics
        if stats['total_prompts'] > 0:
            embed.add_field(
                name="📊 Usage Statistics",
                value=f"**Total Prompts:** {stats['total_prompts']}\n"
                      f"**Messages Posted:** {stats['total_continued']}\n"
                      f"**Messages Edited:** {stats['total_edited']}\n"
                      f"**Messages Cancelled:** {stats['total_cancelled']}",
                inline=False
            )
            
            # Calculate effectiveness
            if stats['total_prompts'] > 0:
                reflection_rate = (stats['total_edited'] + stats['total_cancelled']) / stats['total_prompts']
                embed.add_field(
                    name="🎯 Effectiveness",
                    value=f"{reflection_rate:.1%} of users reflected and changed their behavior",
                    inline=False
                )
        
        await ctx.send(embed=embed)
        
    @pause_group.command(name='config')
    @commands.has_permissions(manage_guild=True)
    async def configure_bot(self, ctx, setting: str = None, value: str = None):
        """Configure bot settings for this server"""
        if setting is None:
            # Show current configuration
            settings = await self.bot.storage.get_guild_settings(ctx.guild.id)
            
            embed = discord.Embed(
                title="⚙️ Current Configuration",
                color=0x3498db
            )
            
            embed.add_field(
                name="Toxicity Threshold",
                value=f"{settings['toxicity_threshold']:.1%}\n*Sensitivity of toxicity detection*",
                inline=True
            )
            embed.add_field(
                name="Language", 
                value=f"{settings['locale'].upper()}\n*Language for prompts*",
                inline=True
            )
            embed.add_field(
                name="Status",
                value="🟢 Enabled" if settings['enabled'] else "🔴 Disabled",
                inline=True
            )
            
            embed.add_field(
                name="Available Settings",
                value="`threshold` - Set toxicity sensitivity (0.1-1.0)\n"
                      "`locale` - Set language (en, vi, es, fr, etc.)\n"
                      "Example: `!pause config threshold 0.8`",
                inline=False
            )
            
            await ctx.send(embed=embed)
            return
            
        # Update configuration
        if setting.lower() == 'threshold':
            try:
                threshold = float(value)
                if not 0.1 <= threshold <= 1.0:
                    raise ValueError("Threshold must be between 0.1 and 1.0")
                    
                await self.bot.storage.update_guild_settings(
                    ctx.guild.id, 
                    toxicity_threshold=threshold
                )
                
                embed = discord.Embed(
                    title="✅ Configuration Updated",
                    description=f"Toxicity threshold set to {threshold:.1%}",
                    color=0x00ff9f
                )
                
                if threshold < 0.5:
                    embed.add_field(
                        name="⚠️ Note",
                        value="Low threshold means more messages will trigger prompts",
                        inline=False
                    )
                elif threshold > 0.8:
                    embed.add_field(
                        name="⚠️ Note", 
                        value="High threshold means only very toxic messages will trigger prompts",
                        inline=False
                    )
                    
                await ctx.send(embed=embed)
                
            except ValueError as e:
                await ctx.send(f"❌ Invalid threshold value: {e}")
                
        elif setting.lower() == 'locale':
            supported_locales = ['en', 'vi', 'es', 'fr', 'de', 'it', 'ja', 'ko', 'zh', 'ru', 'ar', 'hi', 'pt', 'nl']
            
            if value.lower() not in supported_locales:
                await ctx.send(f"❌ Unsupported locale. Supported: {', '.join(supported_locales)}")
                return
                
            await self.bot.storage.update_guild_settings(
                ctx.guild.id,
                locale=value.lower()
            )
            
            embed = discord.Embed(
                title="✅ Configuration Updated",
                description=f"Language set to {value.upper()}",
                color=0x00ff9f
            )
            await ctx.send(embed=embed)
            
        else:
            await ctx.send(f"❌ Unknown setting '{setting}'. Available: threshold, locale")
            
    @pause_group.command(name='test')
    @commands.has_permissions(manage_guild=True)
    async def test_bot(self, ctx, *, message: str = "This is a test message"):
        """Test the toxicity detection on a message"""
        from reflectpause_core import check
        
        is_toxic = check(message)
        
        embed = discord.Embed(
            title="🧪 Toxicity Test",
            color=0xff6b6b if is_toxic else 0x00ff9f
        )
        
        embed.add_field(
            name="Test Message",
            value=f"```{message[:500]}```",
            inline=False
        )
        
        embed.add_field(
            name="Result",
            value="🚨 Would trigger reflection prompt" if is_toxic else "✅ Would not trigger prompt",
            inline=False
        )
        
        if is_toxic:
            embed.add_field(
                name="What happens next?",
                value="The message would be deleted and the user would receive a DM with reflection questions.",
                inline=False
            )
            
        await ctx.send(embed=embed)
        
    @pause_group.command(name='stats')
    async def detailed_stats(self, ctx):
        """Show detailed statistics for this server"""
        stats = await self.bot.storage.get_guild_stats(ctx.guild.id)
        
        embed = discord.Embed(
            title="📈 Detailed Statistics",
            description=f"Data for {ctx.guild.name}",
            color=0x3498db
        )
        
        if stats['total_prompts'] == 0:
            embed.add_field(
                name="No Data Yet",
                value="The bot hasn't processed any messages requiring reflection prompts in this server.",
                inline=False
            )
        else:
            # Basic stats
            embed.add_field(
                name="📊 Overall Usage",
                value=f"**Total Users:** {stats['total_users']}\n"
                      f"**Total Prompts:** {stats['total_prompts']}\n"
                      f"**Active Users:** {stats['total_users']}",
                inline=True
            )
            
            # User decisions
            embed.add_field(
                name="🎯 User Decisions",
                value=f"**Posted Anyway:** {stats['total_continued']}\n"
                      f"**Edited First:** {stats['total_edited']}\n"
                      f"**Cancelled:** {stats['total_cancelled']}",
                inline=True
            )
            
            # Calculate percentages
            total_decisions = stats['total_continued'] + stats['total_edited'] + stats['total_cancelled']
            if total_decisions > 0:
                continued_pct = stats['total_continued'] / total_decisions * 100
                edited_pct = stats['total_edited'] / total_decisions * 100
                cancelled_pct = stats['total_cancelled'] / total_decisions * 100
                
                embed.add_field(
                    name="📊 Decision Breakdown",
                    value=f"**Posted:** {continued_pct:.1f}%\n"
                          f"**Edited:** {edited_pct:.1f}%\n"
                          f"**Cancelled:** {cancelled_pct:.1f}%",
                    inline=True
                )
                
                # Effectiveness measure
                reflection_rate = (edited_pct + cancelled_pct)
                embed.add_field(
                    name="🌟 Impact",
                    value=f"**{reflection_rate:.1f}%** of users changed their behavior after reflection",
                    inline=False
                )
                
        embed.set_footer(text="Statistics help measure the bot's effectiveness in promoting thoughtful communication")
        await ctx.send(embed=embed)
        
    @pause_group.command(name='help')
    async def bot_help(self, ctx):
        """Show help information for the bot"""
        embed = discord.Embed(
            title="🤖 Reflective Pause Bot Help",
            description="Helping create healthier online conversations through mindful pauses",
            color=0x00ff9f
        )
        
        embed.add_field(
            name="🛡️ Admin Commands",
            value="`!pause enable` - Enable the bot\n"
                  "`!pause disable` - Disable the bot\n"
                  "`!pause status` - Check bot status\n"
                  "`!pause config` - View/change settings\n"
                  "`!pause test <message>` - Test toxicity detection\n"
                  "`!pause stats` - View detailed statistics",
            inline=False
        )
        
        embed.add_field(
            name="⚙️ Configuration",
            value="`!pause config threshold 0.7` - Set sensitivity\n"
                  "`!pause config locale en` - Set language\n"
                  "Threshold range: 0.1 (sensitive) to 1.0 (strict)",
            inline=False
        )
        
        embed.add_field(
            name="🧠 How It Works",
            value="1. Bot detects potentially harmful messages\n"
                  "2. Deletes message and sends private reflection prompt\n"
                  "3. User can post anyway, edit, or cancel\n"
                  "4. Promotes thoughtful communication",
            inline=False
        )
        
        embed.add_field(
            name="🔒 Privacy",
            value="• Messages are processed locally when possible\n"
                  "• Only anonymized decision data is stored\n"
                  "• Original message content is not logged\n"
                  "• Users can opt out at any time",
            inline=False
        )
        
        embed.set_footer(text="For more help: github.com/reflectpause/bot")
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(AdminCommands(bot))