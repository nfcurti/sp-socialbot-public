const express = require('express');
const cors = require('cors');
const path = require('path');
const fs = require('fs');
const scheduler = require('./scheduler');
const actions = require('./actions');
const cron = require('node-cron');
const { v4: uuidv4 } = require('uuid');
const { exec } = require('child_process');

const app = express();
const PORT = process.env.PORT || 3010;
const CONFIG_FILE = path.join(__dirname, 'config.json');
const FACEBOOK_POSTS_FILE = path.join(__dirname, 'facebook-posts.json');
const PYTHON_BIN = process.env.PYTHON_BIN || 'python3.11';

// Store for active Facebook post cron jobs
const activeFacebookJobs = new Map();

app.use(cors());
app.use(express.json());

app.use(express.static(path.join(__dirname, 'public')));

function loadConfig() {
    return JSON.parse(fs.readFileSync(CONFIG_FILE, 'utf8'));
}

function saveConfig(config) {
    fs.writeFileSync(CONFIG_FILE, JSON.stringify(config, null, 2));
}

function loadFacebookPosts() {
    try {
        if (!fs.existsSync(FACEBOOK_POSTS_FILE)) {
            return { posts: [] };
        }
        return JSON.parse(fs.readFileSync(FACEBOOK_POSTS_FILE, 'utf8'));
    } catch (error) {
        console.error('Error loading Facebook posts:', error);
        return { posts: [] };
    }
}

function saveFacebookPosts(data) {
    try {
        fs.writeFileSync(FACEBOOK_POSTS_FILE, JSON.stringify(data, null, 2));
    } catch (error) {
        console.error('Error saving Facebook posts:', error);
    }
}

app.get('/status', (req, res) => {
    const isRunning = scheduler.isRunning();
    const status = actions.getSchedulerStatus();
    const detailedStatus = scheduler.getStatus();
    
    res.json({
        schedulerRunning: isRunning,
        status: isRunning ? 'running' : 'stopped',
        executionCount: detailedStatus.executionCount,
        startTime: detailedStatus.startTime,
        timestamp: new Date().toISOString(),
        uptime: process.uptime(),
        lastCheck: new Date().toLocaleTimeString()
    });
});

app.post('/start', (req, res) => {
    const success = scheduler.startScheduler();
    
    if (success) {
        res.json({
            success: true,
            message: 'Scheduler started successfully',
            timestamp: new Date().toISOString()
        });
    } else {
        res.status(400).json({
            success: false,
            message: 'Scheduler is already running',
            timestamp: new Date().toISOString()
        });
    }
});

app.post('/stop', (req, res) => {
    const success = scheduler.stopScheduler();
    
    if (success) {
        res.json({
            success: true,
            message: 'Scheduler stopped successfully',
            timestamp: new Date().toISOString()
        });
    } else {
        res.status(400).json({
            success: false,
            message: 'Scheduler is not running',
            timestamp: new Date().toISOString()
        });
    }
});

app.get('/logs', (req, res) => {
    const logs = actions.getLogs();
    
    res.json({
        logs,
        total: logs.length,
        timestamp: new Date().toISOString()
    });
});

app.get('/bots', (req, res) => {
    const bots = actions.getBots();
    
    res.json({
        bots,
        total: bots.length,
        timestamp: new Date().toISOString()
    });
});

app.get('/bots/:botId', (req, res) => {
    const bot = actions.getBotById(req.params.botId);
    
    if (!bot) {
        return res.status(404).json({
            success: false,
            message: 'Bot not found',
            timestamp: new Date().toISOString()
        });
    }
    
    res.json({
        bot,
        timestamp: new Date().toISOString()
    });
});

app.post('/execute', (req, res) => {
    console.log('🎯 MANUAL EXECUTION VIA API - Random bot execution triggered');
    actions.addLog('manual_execution', true, 'Manual script execution triggered via API endpoint');
    actions.executeRandomScript();
    
    res.json({
        success: true,
        message: 'Manual execution triggered',
        timestamp: new Date().toISOString()
    });
});

app.post('/execute/:botId', (req, res) => {
    const bot = actions.getBotById(req.params.botId);
    
    if (!bot) {
        return res.status(404).json({
            success: false,
            message: 'Bot not found',
            timestamp: new Date().toISOString()
        });
    }
    
    if (!bot.enabled) {
        return res.status(400).json({
            success: false,
            message: 'Bot is disabled',
            timestamp: new Date().toISOString()
        });
    }
    
    console.log(`🎯 MANUAL EXECUTION VIA API - Specific bot execution triggered for: ${bot.name}`);
    actions.addLog('manual_execution', true, `Manual execution via API for bot: ${bot.name}`, bot.id);
    
    const scripts = ['openai-instagram.py', 'openai-comments.py'];
    const randomScript = scripts[Math.floor(Math.random() * scripts.length)];
    const randomHashtag = bot.hashtags[Math.floor(Math.random() * bot.hashtags.length)];
    
    const scriptPath = require('path').join(__dirname, randomScript);
    const command = `${PYTHON_BIN} "${scriptPath}" "${bot.credentials.username}" "${bot.credentials.password}" "${randomHashtag}"`;
    
    exec(command, { timeout: 300000 }, (error, stdout, stderr) => {
        if (error) {
            console.error(`❌ Error executing ${randomScript}:`, error.message);
            actions.addLog(`manual_api_execute_${randomScript}`, false, `Manual API Execution - Bot: ${bot.name}, Hashtag: #${randomHashtag}, Error: ${error.message}`, bot.id);
        } else {
            console.log(`✅ ${randomScript} executed successfully for manual API execution - bot: ${bot.name}`);
            actions.addLog(`manual_api_execute_${randomScript}`, true, `Manual API Execution - Bot: ${bot.name}, Hashtag: #${randomHashtag}, Output: ${stdout}`, bot.id);
        }
    });
    
    res.json({
        success: true,
        message: `Manual execution triggered for bot: ${bot.name}`,
        bot: bot.id,
        timestamp: new Date().toISOString()
    });
});

app.get('/api', (req, res) => {
    res.json({
        name: 'Instagram AI Scheduler',
        version: '1.0.0',
        endpoints: {
            'GET /status': 'Get scheduler status',
            'POST /start': 'Start the scheduler',
            'POST /stop': 'Stop the scheduler',
            'GET /logs': 'Get execution logs',
            'GET /bots': 'Get all enabled bots',
            'GET /bots/:botId': 'Get specific bot details',
            'POST /execute': 'Manually trigger random script execution',
            'POST /execute/:botId': 'Manually trigger execution for specific bot'
        },
        timestamp: new Date().toISOString()
    });
});

app.get('/', (req, res) => {
    res.sendFile(path.join(__dirname, 'public', 'index.html'));
});

// Clear logs endpoint
app.post('/logs/clear', (req, res) => {
    actions.setLogs([]);
    res.json({ success: true });
});

// Add a new bot
app.post('/bots', (req, res) => {
    const config = loadConfig();
    const bot = req.body;
    if (!bot.id || !bot.name || !bot.credentials || !bot.credentials.username || !bot.credentials.password || !Array.isArray(bot.hashtags)) {
        return res.status(400).json({ success: false, message: 'Missing required bot fields' });
    }
    if (config.bots.find(b => b.id === bot.id)) {
        return res.status(400).json({ success: false, message: 'Bot ID already exists' });
    }
    
    // Ensure location field exists (can be empty string)
    if (!bot.location) {
        bot.location = '';
    }
    
    config.bots.push(bot);
    saveConfig(config);
    actions.addLog('bot_created', true, `Bot created: ${bot.name} (${bot.id})${bot.location ? ` - Location Tag: ${bot.location}` : ''}`, bot.id);
    res.json({ success: true, bots: config.bots });
});

// Edit an existing bot (always disables it after edit)
app.put('/bots/:id', (req, res) => {
    const config = loadConfig();
    const botIndex = config.bots.findIndex(b => b.id === req.params.id);
    if (botIndex === -1) {
        return res.status(404).json({ success: false, message: 'Bot not found' });
    }
    const bot = req.body;
    if (!bot.id || !bot.name || !bot.credentials || !bot.credentials.username || !bot.credentials.password || !Array.isArray(bot.hashtags)) {
        return res.status(400).json({ success: false, message: 'Missing required bot fields' });
    }
    
    // Ensure location field exists (can be empty string)
    if (!bot.location) {
        bot.location = '';
    }
    
    bot.enabled = false; // Always stop after edit
    config.bots[botIndex] = bot;
    saveConfig(config);
    actions.addLog('bot_edited', true, `Bot edited: ${bot.name} (${bot.id})${bot.location ? ` - Location Tag: ${bot.location}` : ''}`, bot.id);
    res.json({ success: true, bots: config.bots });
});

// Enable/disable a bot
app.patch('/bots/:id/enabled', (req, res) => {
    const config = loadConfig();
    const botIndex = config.bots.findIndex(b => b.id === req.params.id);
    if (botIndex === -1) {
        return res.status(404).json({ success: false, message: 'Bot not found' });
    }
    const { enabled } = req.body;
    config.bots[botIndex].enabled = !!enabled;
    saveConfig(config);
    actions.addLog(enabled ? 'bot_started' : 'bot_stopped', true, `Bot ${enabled ? 'started' : 'stopped'}: ${config.bots[botIndex].name} (${config.bots[botIndex].id})`, config.bots[botIndex].id);
    if (enabled) {
        actions.executeScriptForBot(config.bots[botIndex]);
    }
    res.json({ success: true, bot: config.bots[botIndex] });
});

// Delete a bot
app.delete('/bots/:id', (req, res) => {
    const config = loadConfig();
    const requestedId = req.params.id;
    console.log(`🗑️ Tentativo eliminazione bot - ID richiesto: "${requestedId}"`);
    console.log(`📋 Bot disponibili:`, config.bots.map(b => `"${b.id}"`));
    
    const botIndex = config.bots.findIndex(b => b.id === requestedId);
    if (botIndex === -1) {
        console.log(`❌ Bot non trovato - ID cercato: "${requestedId}"`);
        return res.status(404).json({ success: false, message: 'Bot non trovato' });
    }
    
    const bot = config.bots[botIndex];
    console.log(`✅ Bot trovato: "${bot.id}" - Nome: ${bot.name}`);
    config.bots.splice(botIndex, 1);
    saveConfig(config);
    
    // If no bots left, stop the scheduler
    if (config.bots.length === 0) {
        scheduler.stopScheduler();
        actions.setSchedulerStatus(false);
    }
    actions.addLog('bot_deleted', true, `Bot eliminato: ${bot.name} (${bot.id})`, bot.id);
    res.json({ success: true, bots: config.bots });
});

// Facebook Post Scheduling Endpoints

// Schedule a Facebook post
app.post('/facebook/schedule', (req, res) => {
    try {
        const { username, password, scheduledTime, text, imagePath } = req.body;
        
        if (!username || !password || !scheduledTime || !text) {
            return res.status(400).json({
                success: false,
                message: 'Missing required fields: username, password, scheduledTime, text'
            });
        }

        const postId = uuidv4();
        const scheduleDate = new Date(scheduledTime);
        const now = new Date();

        if (scheduleDate <= now) {
            return res.status(400).json({
                success: false,
                message: 'Scheduled time must be in the future'
            });
        }

        // Load existing posts
        const postsData = loadFacebookPosts();
        
        // Create new post entry
        const newPost = {
            id: postId,
            username,
            password, // Note: In production, encrypt this!
            scheduledTime: scheduleDate.toISOString(),
            text,
            imagePath,
            status: 'scheduled',
            createdAt: now.toISOString()
        };

        postsData.posts.push(newPost);
        saveFacebookPosts(postsData);

        // Create cron expression for the specific time
        const cronExpression = `${scheduleDate.getMinutes()} ${scheduleDate.getHours()} ${scheduleDate.getDate()} ${scheduleDate.getMonth() + 1} *`;
        
        console.log(`Scheduling Facebook post for: ${scheduleDate.toISOString()}`);
        console.log(`Cron expression: ${cronExpression}`);

        // Schedule the post
        const job = cron.schedule(cronExpression, async () => {
            console.log(`Executing scheduled Facebook post: ${postId}`);
            await executeFacebookPost(postId);
        }, {
            scheduled: false,
            timezone: 'Europe/Rome'
        });

        // Start the job
        job.start();
        activeFacebookJobs.set(postId, job);

        actions.addLog('facebook_post_scheduled', true, `Facebook post scheduled for ${scheduleDate.toISOString()}: ${text.substring(0, 50)}...`);

        res.json({
            success: true,
            message: 'Facebook post scheduled successfully',
            postId,
            scheduledTime: scheduleDate.toISOString()
        });

    } catch (error) {
        console.error('Error scheduling Facebook post:', error);
        res.status(500).json({
            success: false,
            message: 'Internal server error while scheduling post'
        });
    }
});

// Get all scheduled Facebook posts
app.get('/facebook/scheduled', (req, res) => {
    try {
        const postsData = loadFacebookPosts();
        res.json({
            success: true,
            posts: postsData.posts
        });
    } catch (error) {
        console.error('Error loading scheduled posts:', error);
        res.status(500).json({
            success: false,
            message: 'Error loading scheduled posts'
        });
    }
});

// Cancel a scheduled Facebook post
app.post('/facebook/cancel/:postId', (req, res) => {
    try {
        const { postId } = req.params;
        const postsData = loadFacebookPosts();
        
        const postIndex = postsData.posts.findIndex(p => p.id === postId);
        if (postIndex === -1) {
            return res.status(404).json({
                success: false,
                message: 'Post not found'
            });
        }

        const post = postsData.posts[postIndex];
        if (post.status !== 'scheduled') {
            return res.status(400).json({
                success: false,
                message: 'Post is not in scheduled status'
            });
        }

        // Cancel the cron job
        const job = activeFacebookJobs.get(postId);
        if (job) {
            job.stop();
            activeFacebookJobs.delete(postId);
        }

        // Update post status
        post.status = 'cancelled';
        post.cancelledAt = new Date().toISOString();
        saveFacebookPosts(postsData);

        actions.addLog('facebook_post_cancelled', true, `Facebook post cancelled: ${post.text.substring(0, 50)}...`);

        res.json({
            success: true,
            message: 'Post cancelled successfully'
        });

    } catch (error) {
        console.error('Error cancelling Facebook post:', error);
        res.status(500).json({
            success: false,
            message: 'Error cancelling post'
        });
    }
});

// Delete a Facebook post record
app.delete('/facebook/delete/:postId', (req, res) => {
    try {
        const { postId } = req.params;
        const postsData = loadFacebookPosts();
        
        const postIndex = postsData.posts.findIndex(p => p.id === postId);
        if (postIndex === -1) {
            return res.status(404).json({
                success: false,
                message: 'Post not found'
            });
        }

        const post = postsData.posts[postIndex];

        // Cancel cron job if it's still scheduled
        if (post.status === 'scheduled') {
            const job = activeFacebookJobs.get(postId);
            if (job) {
                job.stop();
                activeFacebookJobs.delete(postId);
            }
        }

        // Remove post from array
        postsData.posts.splice(postIndex, 1);
        saveFacebookPosts(postsData);

        actions.addLog('facebook_post_deleted', true, `Facebook post record deleted: ${post.text.substring(0, 50)}...`);

        res.json({
            success: true,
            message: 'Post deleted successfully'
        });

    } catch (error) {
        console.error('Error deleting Facebook post:', error);
        res.status(500).json({
            success: false,
            message: 'Error deleting post'
        });
    }
});

// Function to execute a scheduled Facebook post
async function executeFacebookPost(postId) {
    try {
        const postsData = loadFacebookPosts();
        const postIndex = postsData.posts.findIndex(p => p.id === postId);
        
        if (postIndex === -1) {
            console.error(`Facebook post not found: ${postId}`);
            return;
        }

        const post = postsData.posts[postIndex];
        
        // Update status to posting
        post.status = 'posting';
        post.executedAt = new Date().toISOString();
        saveFacebookPosts(postsData);

        console.log(`Executing Facebook post: ${post.text.substring(0, 50)}...`);

        // Execute the Facebook post script
        const scriptPath = path.join(__dirname, 'facebook-post.py');
        const imagePath = post.imagePath || 'null';
        const command = `${PYTHON_BIN} "${scriptPath}" "${post.username}" "${post.password}" "${post.text}" "${imagePath}"`;

        console.log('Executing Facebook post command:', command.replace(post.password, '***'));

        exec(command, { timeout: 600000 }, (error, stdout, stderr) => {
            const postsData = loadFacebookPosts();
            const currentPostIndex = postsData.posts.findIndex(p => p.id === postId);
            
            if (currentPostIndex !== -1) {
                if (error) {
                    console.error(`Facebook post execution error: ${error}`);
                    postsData.posts[currentPostIndex].status = 'failed';
                    postsData.posts[currentPostIndex].error = error.message;
                    actions.addLog('facebook_post_failed', false, `Facebook post failed: ${error.message}`);
                } else {
                    console.log(`Facebook post executed successfully: ${postId}`);
                    postsData.posts[currentPostIndex].status = 'posted';
                    actions.addLog('facebook_post_success', true, `Facebook post published successfully: ${post.text.substring(0, 50)}...`);
                }
                
                postsData.posts[currentPostIndex].completedAt = new Date().toISOString();
                if (stdout) postsData.posts[currentPostIndex].output = stdout;
                if (stderr) postsData.posts[currentPostIndex].stderr = stderr;
                
                saveFacebookPosts(postsData);
            }

            // Remove from active jobs
            activeFacebookJobs.delete(postId);
        });

    } catch (error) {
        console.error(`Error executing Facebook post ${postId}:`, error);
        
        // Update post status to failed
        const postsData = loadFacebookPosts();
        const postIndex = postsData.posts.findIndex(p => p.id === postId);
        if (postIndex !== -1) {
            postsData.posts[postIndex].status = 'failed';
            postsData.posts[postIndex].error = error.message;
            postsData.posts[postIndex].completedAt = new Date().toISOString();
            saveFacebookPosts(postsData);
        }

        actions.addLog('facebook_post_error', false, `Error executing Facebook post: ${error.message}`);
        activeFacebookJobs.delete(postId);
    }
}

// Restore scheduled jobs on server startup
function restoreScheduledJobs() {
    try {
        const postsData = loadFacebookPosts();
        const now = new Date();

        postsData.posts.forEach(post => {
            if (post.status === 'scheduled') {
                const scheduleDate = new Date(post.scheduledTime);
                
                if (scheduleDate > now) {
                    // Job is still in the future, reschedule it
                    const cronExpression = `${scheduleDate.getMinutes()} ${scheduleDate.getHours()} ${scheduleDate.getDate()} ${scheduleDate.getMonth() + 1} *`;
                    
                    console.log(`Restoring scheduled Facebook post: ${post.id} for ${scheduleDate.toISOString()}`);
                    
                    const job = cron.schedule(cronExpression, async () => {
                        console.log(`Executing restored Facebook post: ${post.id}`);
                        await executeFacebookPost(post.id);
                    }, {
                        scheduled: false,
                        timezone: 'Europe/Rome'
                    });

                    job.start();
                    activeFacebookJobs.set(post.id, job);
                } else {
                    // Job was supposed to run in the past, mark as missed
                    console.log(`Marking past scheduled post as missed: ${post.id}`);
                    post.status = 'missed';
                    post.missedAt = now.toISOString();
                }
            }
        });

        saveFacebookPosts(postsData);
        console.log(`Restored ${activeFacebookJobs.size} scheduled Facebook posts`);
    } catch (error) {
        console.error('Error restoring scheduled jobs:', error);
    }
}

app.listen(PORT, '0.0.0.0', () => {
    console.log(`🤖 Instagram AI Scheduler running on port ${PORT}`);
    console.log(`🌐 Web interface available at http://0.0.0.0:${PORT}`);
    console.log(`🌍 External access: http://34.252.34.118:${PORT}`);
    console.log(`📊 API available at http://0.0.0.0:${PORT}/api`);
    console.log(`📅 Scheduler will run scripts with random intervals (5-15 minutes) when started`);
    console.log(`🤖 Multiple bot instances supported`);
    console.log(`📘 Facebook post scheduling available`);
    
    // Restore any scheduled Facebook posts from previous session
    restoreScheduledJobs();
}); 