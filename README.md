# Instagram AI Scheduler

A Node.js Express backend that acts as an AI-like scheduler for running Instagram automation Python scripts with support for multiple bot instances and a beautiful web interface.

## Features

- 🤖 **Multi-Bot Support**: Deploy multiple bot instances with different credentials
- 🎯 **AI-like Scheduling**: Randomly executes one of two Python scripts with random intervals (5-15 minutes)
- 🌐 **Web Interface**: Beautiful, responsive web dashboard for managing bots and viewing logs
- 📊 **REST API**: Full API for controlling the scheduler and individual bots
- 📝 **Logging**: Stores execution logs with timestamps, success/error status, and bot identification
- 🎯 **Manual Execution**: Trigger scripts manually via API or web interface for all bots or specific bots
- 🔄 **State Management**: Persistent state stored in `state.json`
- ⚙️ **Configurable**: Easy configuration via `config.json`

## Scripts

The scheduler randomly executes one of these Python scripts:
- `openai-instagram.py` - Likes Instagram posts from hashtags
- `openai-comments.py` - Comments on Instagram posts using ChatGPT

## Installation

1. Install Node.js dependencies:
```bash
npm install
```

2. Copy example config files and fill in your secrets locally (do not commit them):
```bash
cp config.example.json config.json
cp config.env.example config.env
```

3. Ensure Python scripts are in the same directory:
- `openai-instagram.py`
- `openai-comments.py`
- `config.env` (with OpenAI API key)
- `config.json` (with bot credentials)

## Configuration

### Bot Configuration (`config.json`)

Copy `config.example.json` to `config.json` and replace the placeholders. Real credentials must stay local — `config.json` is gitignored.

```json
{
  "bots": [
    {
      "id": "bot1",
      "name": "Restaurant Bot 1",
      "credentials": {
        "username": "YOUR_INSTAGRAM_USERNAME",
        "password": "YOUR_INSTAGRAM_PASSWORD"
      },
      "hashtags": [
        "food", "cooking", "pasta", "pizza", "restaurant"
      ],
      "enabled": true
    },
    {
      "id": "bot2",
      "name": "Restaurant Bot 2", 
      "credentials": {
        "username": "YOUR_INSTAGRAM_USERNAME_2",
        "password": "YOUR_INSTAGRAM_PASSWORD_2"
      },
      "hashtags": [
        "chef", "cuisine", "gastronomy", "dining"
      ],
      "enabled": true
    }
  ],
  "scheduler": {
    "interval": "*/30 * * * *",
    "maxLogs": 100,
    "scriptTimeout": 300000
  }
}
```

### Bot Properties

- **id**: Unique identifier for the bot
- **name**: Display name for the bot
- **credentials**: Instagram username and password
- **hashtags**: Array of hashtags this bot will use
- **enabled**: Whether this bot should be active

### Scheduler Properties

- **interval**: Cron expression for execution frequency (now uses random intervals)
- **maxLogs**: Maximum number of log entries to keep
- **scriptTimeout**: Timeout for Python script execution (ms)

## Usage

### Start the Server

```bash
npm start
```

The server will start on `http://localhost:3010`

### Web Interface

Visit `http://localhost:3010` to access the web dashboard featuring:

- **Real-time Status**: Live scheduler status with visual indicators
- **Bot Management**: View all configured bots with their details
- **Manual Execution**: Execute specific bots with one click
- **Live Logs**: Real-time execution logs with bot identification
- **Responsive Design**: Works on desktop and mobile devices

### API Endpoints

#### GET `/status`
Get scheduler status
```bash
curl http://localhost:3010/status
```

#### POST `/start`
Start the scheduler
```bash
curl -X POST http://localhost:3010/start
```

#### POST `/stop`
Stop the scheduler
```bash
curl -X POST http://localhost:3010/stop
```

#### GET `/logs`
Get execution logs (last 100 entries)
```bash
curl http://localhost:3010/logs
```

#### GET `/bots`
Get all enabled bots
```bash
curl http://localhost:3010/bots
```

#### GET `/bots/:botId`
Get specific bot details
```bash
curl http://localhost:3010/bots/bot1
```

#### POST `/execute`
Manually trigger random script execution (random bot)
```bash
curl -X POST http://localhost:3010/execute
```

#### POST `/execute/:botId`
Manually trigger execution for specific bot
```bash
curl -X POST http://localhost:3010/execute/bot1
```

## Multi-Bot Deployment

### Adding New Bots

1. **Edit `config.json`**:
   ```json
   {
     "id": "newbot",
     "name": "New Restaurant Bot",
     "credentials": {
       "username": "new_username",
       "password": "new_password"
     },
     "hashtags": ["food", "cooking"],
     "enabled": true
   }
   ```

2. **Restart the server**:
   ```bash
   npm start
   ```

3. **Access the web interface** at `http://localhost:3010` to see your new bot

### Bot Management

- **Enable/Disable**: Set `"enabled": false` to disable a bot
- **Different Hashtags**: Each bot can have its own hashtag list
- **Individual Execution**: Use the web interface or `/execute/:botId` to run specific bots
- **Logging**: All logs include bot identification

## Random Interval Scheduling

The scheduler now uses **random intervals between 5-15 minutes** for each execution:

- **More Natural**: Mimics human behavior patterns
- **Anti-Detection**: Reduces risk of being flagged as automated
- **Dynamic**: Each execution gets a new random interval
- **Configurable**: Can be adjusted in the scheduler code

## Example Usage

1. **Start the server**:
   ```bash
   npm start
   ```

2. **Open web interface**:
   ```
   http://localhost:3010
   ```

3. **Start the scheduler** via web interface or API:
   ```bash
   curl -X POST http://localhost:3010/start
   ```

4. **Execute specific bot** via web interface or API:
   ```bash
   curl -X POST http://localhost:3010/execute/bot1
   ```

5. **Monitor logs** via web interface or API:
   ```bash
   curl http://localhost:3010/logs
   ```

## Log Format

Each log entry contains:
```json
{
  "timestamp": "2024-01-15T10:30:00.000Z",
  "action": "execute_openai-comments.py",
  "success": true,
  "details": "Bot: Restaurant Bot 1, Hashtag: #food, Output: ...",
  "botId": "bot1"
}
```

## File Structure

```
├── index.js              # Express app with REST endpoints and web serving
├── scheduler.js          # node-cron setup with random intervals
├── actions.js            # Python script execution and log management
├── config.example.json   # Example bot config (copy to config.json)
├── config.env.example    # Example env file (copy to config.env)
├── package.json          # Node.js dependencies
├── public/
│   └── index.html        # Web interface
├── openai-instagram.py   # Instagram liking script
├── openai-comments.py    # Instagram commenting script
├── config.json           # Local bot credentials (gitignored)
└── config.env            # Local OpenAI API credentials (gitignored)
```

## Error Handling

- Script execution timeout: 5 minutes
- Automatic error logging with bot identification
- Graceful failure handling
- State persistence across restarts
- Bot-specific error tracking
- Web interface error display

## Security Notes

- Never commit real credentials. Use `config.example.json` / `config.env.example` as templates.
- Keep secrets only in local `config.json` and `config.env` (both are gitignored).
- Web interface is not authenticated (add authentication for production).
- Scripts run with system permissions.
- Logs may contain sensitive information — treat them as secret.
- Rotate any passwords that were previously committed to a public repository. 