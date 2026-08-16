const fs = require('fs');
const path = require('path');
const { exec } = require('child_process');

const STATE_FILE = 'state.json';
const CONFIG_FILE = 'config.json';

function loadConfig() {
    try {
        const data = fs.readFileSync(CONFIG_FILE, 'utf8');
        return JSON.parse(data);
    } catch (error) {
        console.error('Error loading config:', error);
        return {
            bots: [{
                id: 'default',
                name: 'Default Bot',
                credentials: {
                    username: 'YOUR_INSTAGRAM_USERNAME',
                    password: 'YOUR_INSTAGRAM_PASSWORD'
                },
                hashtags: ['food', 'cooking', 'pasta'],
                enabled: true
            }],
            scheduler: {
                interval: '*/30 * * * *',
                maxLogs: 100,
                scriptTimeout: 300000
            }
        };
    }
}

function getEnabledBots() {
    const config = loadConfig();
    return config.bots.filter(bot => bot.enabled);
}

function getRandomBot() {
    const enabledBots = getEnabledBots();
    if (enabledBots.length === 0) {
        throw new Error('No enabled bots found');
    }
    return enabledBots[Math.floor(Math.random() * enabledBots.length)];
}

function loadState() {
    try {
        const data = fs.readFileSync(STATE_FILE, 'utf8');
        return JSON.parse(data);
    } catch (error) {
        return { schedulerRunning: false, logs: [] };
    }
}

function saveState(state) {
    try {
        fs.writeFileSync(STATE_FILE, JSON.stringify(state, null, 2));
    } catch (error) {
        console.error('Error saving state:', error);
    }
}

function addLog(action, success, details = '', botId = null) {
    const state = loadState();
    const logEntry = {
        timestamp: new Date().toISOString(),
        action,
        success,
        details,
        botId
    };
    
    const config = loadConfig();
    if (state.logs.length >= config.scheduler.maxLogs) {
        state.logs = state.logs.slice(0, config.scheduler.maxLogs);
    }
    
    state.logs.unshift(logEntry);
    saveState(state);
    return logEntry;
}

function getLogs() {
    const state = loadState();
    return state.logs;
}

function setLogs(logs) {
    const state = loadState();
    state.logs = logs;
    saveState(state);
}

function setSchedulerStatus(running) {
    const state = loadState();
    state.schedulerRunning = running;
    saveState(state);
}

function getSchedulerStatus() {
    const state = loadState();
    return state.schedulerRunning;
}

function getRandomHashtag(bot) {
    return bot.hashtags[Math.floor(Math.random() * bot.hashtags.length)];
}

function executeRandomScript() {
    try {
        const bot = getRandomBot();
        const scripts = ['openai-instagram.py', 'openai-comments.py'];
        const randomScript = scripts[Math.floor(Math.random() * scripts.length)];
        const randomHashtag = getRandomHashtag(bot);
        
        console.log('🔄 SCHEDULER EXECUTION - Attempting to execute script for bot:', bot);
        console.log(`Selected script: ${randomScript}`);
        console.log(`Selected hashtag: #${randomHashtag}`);
        
        const scriptPath = path.join(__dirname, randomScript);
        const command = `${process.env.PYTHON_BIN || 'python3.11'} "${scriptPath}" "${bot.credentials.username}" "${bot.credentials.password}" "${randomHashtag}"`;
        console.log('Executing command:', command);
        
        const config = loadConfig();
        
        exec(command, { timeout: config.scheduler.scriptTimeout }, (error, stdout, stderr) => {
            console.log('Script stdout:', stdout);
            console.log('Script stderr:', stderr);
            if (error) {
                console.error(`❌ Error executing ${randomScript}:`, error.message);
                addLog(`execute_${randomScript}`, false, `Bot: ${bot.name}, Hashtag: #${randomHashtag}, Error: ${error.message}`, bot.id);
                return;
            }
            
            if (stderr) {
                console.warn(`⚠️  ${randomScript} stderr:`, stderr);
            }
            
            console.log(`✅ ${randomScript} executed successfully`);
            console.log(`📝 Output: ${stdout}`);
            
            addLog(`execute_${randomScript}`, true, `Bot: ${bot.name}, Hashtag: #${randomHashtag}, Output: ${stdout}`, bot.id);
        });
    } catch (error) {
        console.error('❌ Error in executeRandomScript:', error.message);
        addLog('execute_random_script', false, `Error: ${error.message}`);
    }
}

function executeScriptForBot(bot) {
    try {
        const scripts = ['openai-instagram.py', 'openai-comments.py'];
        const randomScript = scripts[Math.floor(Math.random() * scripts.length)];
        const randomHashtag = getRandomHashtag(bot);
        
        console.log('▶️ MANUAL BOT START - Attempting to execute script for bot:', bot);
        console.log(`Selected script: ${randomScript}`);
        console.log(`Selected hashtag: #${randomHashtag}`);
        
        const scriptPath = path.join(__dirname, randomScript);
        const command = `${process.env.PYTHON_BIN || 'python3.11'} "${scriptPath}" "${bot.credentials.username}" "${bot.credentials.password}" "${randomHashtag}"`;
        console.log('Executing command:', command);
        
        const config = loadConfig();
        
        exec(command, { timeout: config.scheduler.scriptTimeout }, (error, stdout, stderr) => {
            if (error) {
                console.error(`❌ Error executing ${randomScript}:`, error.message);
                addLog(`manual_execute_${randomScript}`, false, `Manual Bot Start - Bot: ${bot.name}, Hashtag: #${randomHashtag}, Error: ${error.message}`, bot.id);
                return;
            }
            
            console.log(`✅ ${randomScript} executed successfully for manual bot start`);
            addLog(`manual_execute_${randomScript}`, true, `Manual Bot Start - Bot: ${bot.name}, Hashtag: #${randomHashtag}, Output: ${stdout}`, bot.id);
        });
    } catch (error) {
        console.error('❌ Error in executeScriptForBot:', error.message);
        addLog('execute_script_for_bot', false, `Error: ${error.message}`, bot.id);
    }
}

function getBots() {
    const config = loadConfig();
    return config.bots;
}

function getBotById(botId) {
    const config = loadConfig();
    return config.bots.find(bot => bot.id === botId);
}

module.exports = {
    executeRandomScript,
    addLog,
    getLogs,
    setLogs,
    setSchedulerStatus,
    getSchedulerStatus,
    getBots,
    getBotById,
    executeScriptForBot
}; 