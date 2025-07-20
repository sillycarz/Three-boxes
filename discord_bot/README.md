# Reflective Pause Discord Bot

A Discord bot that helps create healthier online conversations by introducing brief, psychology-based pauses before potentially toxic messages are posted.

## Features

- **Automatic Toxicity Detection**: Uses the reflectpause-core library to detect potentially harmful messages
- **Private Reflection Prompts**: Sends CBT-inspired questions via DM to encourage thoughtful consideration
- **User Choice**: Users can post anyway, edit their message, or cancel entirely
- **Server Administration**: Comprehensive admin commands for configuration and monitoring
- **Privacy-Focused**: Only stores anonymized decision data, not message content
- **Multi-language Support**: Supports multiple locales for prompts

## Quick Start

### 1. Prerequisites

- Python 3.12+
- Discord bot token ([Create a bot](https://discord.com/developers/applications))
- Bot permissions: Manage Messages, Send Messages, Read Message History, Use Slash Commands

### 2. Installation

```bash
# Clone the repository
git clone <repository-url>
cd discord_bot

# Install dependencies
pip install -r requirements.txt

# Set up environment
cp .env.example .env
# Edit .env with your Discord token
```

### 3. Configuration

Create a `.env` file:

```env
DISCORD_TOKEN=your_discord_bot_token_here
TOXICITY_THRESHOLD=0.7
USE_PERSPECTIVE_API=false
DEFAULT_LOCALE=en
```

### 4. Run the Bot

```bash
python bot.py
```

## Bot Commands

### Admin Commands (Requires Manage Server permission)

- `!pause enable` - Enable the bot for this server
- `!pause disable` - Disable the bot for this server  
- `!pause status` - Check current bot status and statistics
- `!pause config` - View current configuration
- `!pause config threshold 0.8` - Set toxicity sensitivity (0.1-1.0)
- `!pause config locale en` - Set language for prompts
- `!pause test <message>` - Test toxicity detection on a message
- `!pause stats` - View detailed usage statistics
- `!pause help` - Show help information

### How It Works

1. **Detection**: Bot monitors messages for potentially toxic content
2. **Intervention**: Deletes flagged message and sends private reflection prompt
3. **Reflection**: User receives 3 CBT-inspired questions via DM:
   - "Is this accurate and fair?"
   - "Could this harm someone?"
   - "Does this reflect who you want to be?"
4. **Choice**: User can:
   - ✅ Post the original message anyway
   - ✏️ Edit the message first
   - ❌ Cancel and not post

## Configuration Options

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DISCORD_TOKEN` | Required | Your Discord bot token |
| `TOXICITY_THRESHOLD` | 0.7 | Sensitivity level (0.1-1.0) |
| `USE_PERSPECTIVE_API` | false | Enable Google Perspective API |
| `PERSPECTIVE_API_KEY` | None | Perspective API key (if enabled) |
| `DEFAULT_LOCALE` | en | Default language for prompts |
| `LOG_LEVEL` | INFO | Logging level |
| `DATABASE_PATH` | bot_data.db | SQLite database file path |

### Supported Languages

- English (en)
- Vietnamese (vi)  
- Spanish (es)
- French (fr)
- German (de)
- Italian (it)
- Japanese (ja)
- Korean (ko)
- Chinese (zh)
- Russian (ru)
- Arabic (ar)
- Hindi (hi)
- Portuguese (pt)
- Dutch (nl)

## Docker Deployment

### Using Docker Compose (Recommended)

```bash
# Copy environment file
cp .env.example .env
# Edit .env with your settings

# Start the bot
docker-compose up -d

# View logs
docker-compose logs -f reflectpause-bot

# Stop the bot
docker-compose down
```

### Using Docker directly

```bash
# Build the image
docker build -t reflectpause-bot .

# Run the container
docker run -d \
  --name reflectpause-bot \
  --env-file .env \
  -v $(pwd)/data:/app/data \
  reflectpause-bot
```

## Privacy & Security

- **No Message Storage**: Original message content is never stored in the database
- **Anonymized Analytics**: Only decision types (edit/post/cancel) are recorded
- **Local Processing**: Toxicity detection runs locally when possible
- **Opt-out Support**: Users can request data deletion
- **Secure Configuration**: Sensitive tokens loaded from environment variables

## Development

### Project Structure

```
discord_bot/
├── bot.py              # Main bot application
├── storage.py          # Database operations
├── config.py           # Configuration management
├── commands.py         # Admin command handlers
├── requirements.txt    # Python dependencies
├── Dockerfile          # Container configuration
├── docker-compose.yml  # Docker orchestration
└── .env.example        # Environment template
```

### Local Development

```bash
# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest tests/

# Format code
black discord_bot/

# Type checking
mypy discord_bot/
```

### Testing

```bash
# Test configuration
python config.py

# Test toxicity detection
python -c "from reflectpause_core import check; print(check('test message'))"

# Create example config
python config.py
```

## Performance & Scaling

- **Response Time**: <250ms for reflection prompt delivery
- **Memory Usage**: ~50MB base, scales with concurrent users
- **Database**: SQLite for single-instance, easily migrated to PostgreSQL
- **Rate Limiting**: Built-in cooldowns to prevent spam

## Monitoring

The bot provides comprehensive statistics:

- Total prompts sent
- User decision breakdown (post/edit/cancel)
- Effectiveness metrics
- Per-server analytics
- User engagement rates

Access via `!pause stats` command.

## Troubleshooting

### Common Issues

1. **Bot not responding to commands**
   - Check bot permissions in server
   - Verify bot token is correct
   - Check bot is online in Discord

2. **Messages not being detected**
   - Adjust toxicity threshold: `!pause config threshold 0.5`
   - Test detection: `!pause test your message here`
   - Check if bot is enabled: `!pause status`

3. **DMs not being sent**
   - User may have DMs disabled
   - Check bot permissions
   - Verify user is not blocking the bot

### Debug Mode

Enable debug logging:

```env
LOG_LEVEL=DEBUG
```

### Support

- GitHub Issues: [repository-url]/issues
- Documentation: [repository-url]/wiki
- Community: [Discord server link]

## License

MIT License - see LICENSE file for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

See CONTRIBUTING.md for detailed guidelines.