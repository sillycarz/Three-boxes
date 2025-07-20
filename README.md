# Reflective Pause Core Library

A shared Python library providing toxicity checking and prompt generation for the Reflective Pause Bot system.

## Features

- **Toxicity Detection**: Multiple engine support (ONNX on-device, Google Perspective API)
- **CBT Prompt Generation**: Cognitive Behavioral Therapy question rotation with i18n support
- **Decision Logging**: Anonymized analytics for user decisions
- **Strategy Pattern**: Pluggable toxicity detection engines
- **Performance Optimized**: <50ms latency for modal rendering

## Installation

```bash
pip install reflectpause-core
```

Or from source:

```bash
git clone <repository-url>
cd reflectpause-core
pip install -e .
```

## Quick Start

```python
from reflectpause_core import check, generate_prompt, log_decision
from reflectpause_core.logging import DecisionType

# Check text toxicity
is_toxic = check("This is a test message")

# Generate localized CBT prompt
prompt_data = generate_prompt("en")
print(prompt_data.question)

# Log user decision
log_decision(DecisionType.CONTINUED_SENDING)
```

## Configuration

### ONNX Engine (Default)

```python
from reflectpause_core.toxicity import ONNXEngine

engine = ONNXEngine({
    'model_path': 'path/to/model.onnx',
    'max_sequence_length': 512
})
```

### Perspective API Engine

```python
from reflectpause_core.toxicity import PerspectiveAPIEngine

engine = PerspectiveAPIEngine({
    'api_key': 'your-api-key',
    'timeout': 10
})
```

## Supported Locales

- English (`en`)
- Vietnamese (`vi`)

## Discord Bot Setup

A complete Discord bot implementation is available in the `discord_bot/` directory.

### Quick Start

1. **Create Discord Application**
   - Go to https://discord.com/developers/applications
   - Create a new application and bot user
   - Copy the bot token
   - Enable required permissions: Manage Messages, Send Messages, Read Message History

2. **Install and Configure**
   ```bash
   cd discord_bot
   pip install -r requirements.txt
   cp .env.example .env
   # Edit .env with your Discord token
   ```

3. **Run the Bot**
   ```bash
   python bot.py
   ```

### Features

- **Automatic Detection**: Monitors messages for toxicity using the core library
- **Private Reflection**: Sends CBT-inspired prompts via DM when toxic content is detected
- **User Choice**: Users can post anyway (✅), edit first (✏️), or cancel (❌)
- **Admin Commands**: `!pause enable/disable/status/config/stats`
- **Multi-language**: Supports 14+ languages for prompts
- **Privacy-Focused**: No message content stored, only anonymized decisions
- **Docker Ready**: Includes Dockerfile and docker-compose.yml

### Admin Commands

```bash
!pause enable          # Enable bot for server
!pause disable         # Disable bot for server  
!pause status          # Check bot status & stats
!pause config          # View/change settings
!pause test <message>  # Test toxicity detection
!pause stats           # Detailed statistics
```

### Configuration

```env
DISCORD_TOKEN=your_discord_bot_token_here
TOXICITY_THRESHOLD=0.7
USE_PERSPECTIVE_API=false
DEFAULT_LOCALE=en
```

### Docker Deployment

```bash
cd discord_bot
cp .env.example .env
# Edit .env with your settings
docker-compose up -d
```

See `discord_bot/README.md` for complete documentation.

## Development

```bash
# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Format code
black reflectpause_core/

# Type checking
mypy reflectpause_core/
```

## Performance Requirements

- Modal rendering: ≤50ms latency
- Bot DM round-trip: ≤250ms
- Cost-zero operation: <$10/month with on-device inference

## License

MIT License - see LICENSE file for details.