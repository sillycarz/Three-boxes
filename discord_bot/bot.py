import os
import sys
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple
from pathlib import Path

import discord
from discord.ext import commands
from dotenv import load_dotenv

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from reflectpause_core import check, generate_prompt
from reflectpause_core.logging import DecisionType, log_decision
from storage import MessageStorage
from config import BotConfig

# Load environment variables
load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ReflectivePauseBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.reactions = True
        
        super().__init__(
            command_prefix='!pause ',
            intents=intents,
            help_command=None
        )
        
        self.config = BotConfig()
        self.storage = MessageStorage()
        self.pending_messages: Dict[int, Tuple[discord.Message, datetime]] = {}
        
    async def setup_hook(self):
        await self.storage.initialize()
        # Load admin commands
        await self.load_extension('commands')
        logger.info("Bot setup complete")
        
    async def on_ready(self):
        logger.info(f'{self.user} has connected to Discord!')
        logger.info(f'Bot is in {len(self.guilds)} guilds')
        
        # Clean up old pending messages
        self.cleanup_pending_messages.start()
        
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return
            
        # Process commands first
        await self.process_commands(message)
        
        # Skip if in DM or bot disabled for this guild
        if isinstance(message.channel, discord.DMChannel):
            return
            
        if not await self.storage.is_enabled(message.guild.id):
            return
            
        try:
            # Check if message needs reflection pause
            needs_pause = check(message.content)
            
            if needs_pause:
                # Store original message
                original_data = {
                    'content': message.content,
                    'channel_id': message.channel.id,
                    'guild_id': message.guild.id,
                    'author_id': message.author.id,
                    'attachments': [att.url for att in message.attachments],
                    'timestamp': datetime.utcnow()
                }
                
                # Delete the message
                await message.delete()
                
                # Send reflection prompt
                await self.send_reflection_prompt(message.author, original_data)
                
        except discord.Forbidden:
            logger.warning(f"Missing permissions to delete message in {message.guild.name}")
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            
    async def send_reflection_prompt(self, user: discord.User, message_data: dict):
        try:
            # Generate CBT prompt
            prompt_data = generate_prompt("en")  # TODO: Add locale detection
            
            embed = discord.Embed(
                title="🛑 Reflective Pause",
                description="Before we share that message, let's take a moment to reflect:",
                color=0x00ff9f,
                timestamp=datetime.utcnow()
            )
            
            embed.add_field(
                name="1️⃣ Accuracy & Fairness",
                value=prompt_data.question,
                inline=False
            )
            embed.add_field(
                name="2️⃣ Potential Impact", 
                value="Could this message harm someone or escalate conflict?",
                inline=False
            )
            embed.add_field(
                name="3️⃣ Self-Reflection",
                value="Does this reflect the person you want to be?",
                inline=False
            )
            embed.add_field(
                name="📝 Your Options",
                value="✅ **Post anyway** - Send the original message\n✏️ **Edit first** - Modify before posting\n❌ **Cancel** - Don't post this message",
                inline=False
            )
            
            embed.set_footer(text="This pause helps create healthier online conversations")
            
            dm_message = await user.send(embed=embed)
            
            # Add reaction options
            for emoji in ["✅", "✏️", "❌"]:
                await dm_message.add_reaction(emoji)
                
            # Store message data for later retrieval
            message_id = await self.storage.store_pending_message(user.id, message_data)
            self.pending_messages[dm_message.id] = (message_data, datetime.utcnow(), message_id)
            
        except discord.Forbidden:
            logger.warning(f"Cannot send DM to {user.name}")
        except Exception as e:
            logger.error(f"Error sending reflection prompt: {e}")
            
    async def on_reaction_add(self, reaction: discord.Reaction, user: discord.User):
        if user.bot:
            return
            
        # Check if this is a reaction to a reflection prompt
        if reaction.message.id not in self.pending_messages:
            return
            
        message_data, timestamp, storage_id = self.pending_messages[reaction.message.id]
        
        try:
            if reaction.emoji == "✅":
                await self.handle_post_anyway(user, message_data, storage_id)
                log_decision(DecisionType.CONTINUED_SENDING)
                
            elif reaction.emoji == "✏️":
                await self.handle_edit_request(user, message_data, storage_id)
                log_decision(DecisionType.EDITED_MESSAGE)
                
            elif reaction.emoji == "❌":
                await self.handle_cancel(user, storage_id)
                log_decision(DecisionType.CANCELLED)
                
            # Clean up
            del self.pending_messages[reaction.message.id]
            await self.storage.remove_pending_message(storage_id)
            
        except Exception as e:
            logger.error(f"Error handling reaction: {e}")
            
    async def handle_post_anyway(self, user: discord.User, message_data: dict, storage_id: int):
        try:
            guild = self.get_guild(message_data['guild_id'])
            channel = guild.get_channel(message_data['channel_id'])
            
            if channel and channel.permissions_for(guild.me).send_messages:
                await channel.send(
                    f"**{user.display_name}**: {message_data['content']}"
                )
                await user.send("✅ Your message has been posted.")
            else:
                await user.send("❌ Unable to post message - channel not found or no permissions.")
                
        except Exception as e:
            logger.error(f"Error posting message: {e}")
            await user.send("❌ An error occurred while posting your message.")
            
    async def handle_edit_request(self, user: discord.User, message_data: dict, storage_id: int):
        embed = discord.Embed(
            title="✏️ Edit Your Message",
            description="Please send your edited message now. You have 5 minutes.",
            color=0xffa500
        )
        embed.add_field(
            name="Original Message",
            value=f"```{message_data['content'][:1000]}```",
            inline=False
        )
        
        await user.send(embed=embed)
        
        # Wait for edited message
        def check(m):
            return m.author == user and isinstance(m.channel, discord.DMChannel)
            
        try:
            edited_msg = await self.wait_for('message', timeout=300.0, check=check)
            
            # Post the edited message
            guild = self.get_guild(message_data['guild_id'])
            channel = guild.get_channel(message_data['channel_id'])
            
            if channel and channel.permissions_for(guild.me).send_messages:
                await channel.send(
                    f"**{user.display_name}**: {edited_msg.content}"
                )
                await user.send("✅ Your edited message has been posted.")
            else:
                await user.send("❌ Unable to post message - channel not found or no permissions.")
                
        except asyncio.TimeoutError:
            await user.send("⏰ Edit timeout - your message was not posted.")
            
    async def handle_cancel(self, user: discord.User, storage_id: int):
        await user.send("❌ Message cancelled - nothing was posted.")
        
    @commands.loop(minutes=30)
    async def cleanup_pending_messages(self):
        cutoff = datetime.utcnow() - timedelta(hours=1)
        expired = [
            msg_id for msg_id, (_, timestamp, _) in self.pending_messages.items()
            if timestamp < cutoff
        ]
        
        for msg_id in expired:
            del self.pending_messages[msg_id]
            
        logger.info(f"Cleaned up {len(expired)} expired pending messages")

def main():
    # Initialize configuration and logging
    config = BotConfig()
    config.setup_logging()
    
    # Create bot instance
    bot = ReflectivePauseBot()
    
    # Run the bot
    if not config.discord_token:
        logger.error("DISCORD_TOKEN not found in environment variables or config file")
        logger.info("Please set DISCORD_TOKEN environment variable or create config.json")
        return
        
    try:
        bot.run(config.discord_token)
    except discord.LoginFailure:
        logger.error("Invalid Discord token")
    except Exception as e:
        logger.error(f"Failed to start bot: {e}")

if __name__ == "__main__":
    main()