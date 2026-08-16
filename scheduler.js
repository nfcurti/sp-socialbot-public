const cron = require('node-cron');
const actions = require('./actions');

let schedulerJob = null;
let executionCount = 0;

function getRandomInterval() {
    // Random interval between 5-15 minutes
    const minutes = Math.floor(Math.random() * 11) + 5;
    const nextTime = new Date(Date.now() + minutes * 60 * 1000);
    console.log(`⏰ Next execution scheduled in ${minutes} minutes (at ${nextTime.toLocaleTimeString()})`);
    return minutes;
}

function scheduleNext() {
    if (!schedulerJob) {
        console.log('🛑 Scheduler stopped, not scheduling next execution');
        return;
    }
    
    const minutes = getRandomInterval();
    console.log(`📅 Setting timeout for ${minutes} minutes...`);
    
    const timeoutId = setTimeout(() => {
        if (!schedulerJob) {
            console.log('🛑 Scheduler was stopped during timeout, skipping execution');
            return;
        }
        
        try {
            executionCount++;
            console.log(`🤖 Scheduled execution triggered (execution #${executionCount}) at ${new Date().toLocaleTimeString()}`);
            
            // Execute the script with error handling
            actions.executeRandomScript();
            console.log(`✅ Script execution completed for execution #${executionCount}`);
            
        } catch (error) {
            console.error(`❌ Error during execution #${executionCount}:`, error);
            // Continue scheduling even if execution fails
        }
        
        // Always schedule the next execution, even if current one failed
        console.log(`🔄 Scheduling next execution after execution #${executionCount}...`);
        scheduleNext();
        
    }, minutes * 60 * 1000); // Convert minutes to milliseconds
    
    console.log(`⏱️ Timeout set with ID: ${timeoutId} for ${minutes} minutes`);
}

function startScheduler() {
    if (schedulerJob !== null) {
        console.log('⚠️  Scheduler is already running');
        return false;
    }

    console.log(`⏰ Starting scheduler with random intervals (5-15 minutes) at ${new Date().toLocaleTimeString()}`);
    
    // Use a simple flag to track if scheduler is running
    schedulerJob = true;
    executionCount = 0;
    
    try {
        // Execute immediately on start
        executionCount++;
        console.log(`🤖 Initial execution triggered (execution #${executionCount}) at ${new Date().toLocaleTimeString()}`);
        actions.executeRandomScript();
        console.log(`✅ Initial script execution completed`);
    } catch (error) {
        console.error(`❌ Error during initial execution:`, error);
        // Continue with scheduling even if initial execution fails
    }
    
    // Schedule the next execution
    console.log('🔄 Scheduling first recurring execution...');
    scheduleNext();
    
    actions.setSchedulerStatus(true);
    console.log('✅ Scheduler started successfully with recursive scheduling enabled');
    return true;
}

function stopScheduler() {
    if (schedulerJob === null) {
        console.log('⚠️  Scheduler is not running');
        return false;
    }

    console.log(`🛑 Stopping scheduler after ${executionCount} executions`);
    schedulerJob = null; // This will stop the recursive scheduling
    actions.setSchedulerStatus(false);
    console.log('🛑 Scheduler stopped successfully');
    return true;
}

function isRunning() {
    const running = schedulerJob !== null;
    console.log(`📊 Scheduler status check: ${running ? 'RUNNING' : 'STOPPED'} (${executionCount} executions so far)`);
    return running;
}

// Add a status function for debugging
function getStatus() {
    return {
        running: schedulerJob !== null,
        executionCount: executionCount,
        startTime: schedulerJob ? 'Running' : 'Not started'
    };
}

module.exports = {
    startScheduler,
    stopScheduler,
    isRunning,
    getStatus
}; 