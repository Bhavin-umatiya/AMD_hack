// API Configuration
const API_BASE_URL = '';

// DOM Elements
const generateBtn = document.getElementById('generateBtn');
const userPromptInput = document.getElementById('userPrompt');
const statusSection = document.getElementById('statusSection');
const resultsSection = document.getElementById('resultsSection');
const errorSection = document.getElementById('errorSection');
const downloadZipBtn = document.getElementById('downloadZipBtn');

// Progress Bar Elements
const progressBar = document.getElementById('progressBar');
const progressText = document.getElementById('progressText');
const progressPercent = document.getElementById('progressPercent');
const elapsedTime = document.getElementById('elapsedTime');
const estimatedTime = document.getElementById('estimatedTime');

// Store current project data
let currentProjectData = null;
let progressInterval = null;
let startTime = null;

// Agent Status Elements
const agent1Element = document.getElementById('agent1');
const agent2Element = document.getElementById('agent2');
const agent3Element = document.getElementById('agent3');

// Result Elements
const projectTitleElement = document.getElementById('projectTitle');
const architectureDescElement = document.getElementById('architectureDescription');
const moduleListElement = document.getElementById('moduleList');
const verilogCodeElement = document.getElementById('verilogCode');
const testbenchCodeElement = document.getElementById('testbenchCode');
const vivadoTclScriptElement = document.getElementById('vivadoTclScript');
const resourceEstimationElement = document.getElementById('resourceEstimation');
const errorMessageElement = document.getElementById('errorMessage');

// New Hardware Verification Elements
const agentVerifyElement = document.getElementById('agentVerify');
const schematicContainer = document.getElementById('schematicContainer');
const simLogsElement = document.getElementById('simLogs');
const simStatusBadge = document.getElementById('simStatusBadge');

// Event Listeners
generateBtn.addEventListener('click', handleGenerate);

// Download ZIP button
downloadZipBtn.addEventListener('click', handleDownloadZip);

// Copy Button Event Listeners
document.querySelectorAll('.copy-btn').forEach(btn => {
    btn.addEventListener('click', handleCopy);
});

// Main Generation Function
async function handleGenerate() {
    const userPrompt = userPromptInput.value.trim();

    // Validation
    if (!userPrompt) {
        alert('Please describe what you want to build');
        return;
    }

    // Reset UI
    resetUI();

    // Show status section and start progress
    statusSection.style.display = 'block';
    resultsSection.style.display = 'none';
    errorSection.style.display = 'none';
    
    // Start progress bar
    startProgress();

    // Disable button
    generateBtn.disabled = true;
    document.querySelector('.btn-text').style.display = 'none';
    document.querySelector('.loading-spinner').style.display = 'inline';

    try {
        // Update Agent 1 Status
        updateAgentStatus(agent1Element, 'running', '🔄 Working...');

        // Make API Request with timeout
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 180000); // 3 minute timeout
        
        const response = await fetch(`${API_BASE_URL}/generate-agentic-project`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                userPrompt: userPrompt
            }),
            signal: controller.signal
        });
        
        clearTimeout(timeoutId);

        if (!response.ok) {
            let errorMsg = `HTTP ${response.status}`;
            try {
                const errorData = await response.json();
                errorMsg = errorData.error || errorMsg;
            } catch (e) {
                // If JSON parsing fails, try to get text
                try {
                    const errorText = await response.text();
                    errorMsg = errorText || errorMsg;
                } catch (e2) {
                    // Use default error message
                }
            }
            throw new Error(errorMsg);
        }

        let data;
        try {
            data = await response.json();
        } catch (jsonError) {
            console.error('JSON parse error:', jsonError);
            const responseText = await response.text();
            console.error('Response text:', responseText.substring(0, 500));
            throw new Error('Server returned invalid JSON. Please check console for details.');
        }

        // Simulate Agent Progress (in real implementation, you'd use WebSockets or SSE)
        await simulateAgentProgress();

        // Complete progress bar
        completeProgress();
        
        // Mark all agents as complete
        updateAgentStatus(agent1Element, 'done', '✅ Complete');
        updateAgentStatus(agent2Element, 'done', '✅ Complete');
        
        if (data.rtl && data.rtl.simPassed) {
            updateAgentStatus(agentVerifyElement, 'done', '✅ Verified');
        } else {
            updateAgentStatus(agentVerifyElement, 'failed', '⚠️ Issues Found');
        }
        
        updateAgentStatus(agent3Element, 'done', '✅ Complete');

        // Display Results
        displayResults(data);

        // Mark all agents as complete
        updateAgentStatus(agent1Element, 'done', '✅ Complete');
        updateAgentStatus(agent2Element, 'done', '✅ Complete');
        updateAgentStatus(agent3Element, 'done', '✅ Complete');

    } catch (error) {
        console.error('Error:', error);
        
        let errorMessage = error.message;
        if (error.name === 'AbortError') {
            errorMessage = 'Request timed out after 3 minutes. Please try a simpler design or try again.';
        }
        
        showError(errorMessage);
        
        // Stop progress on error
        if (progressInterval) clearInterval(progressInterval);
        updateProgress(0, '❌ Error occurred', 0, 0);
        
        // Mark current agent as failed
        updateAgentStatus(agent1Element, 'failed', '❌ Failed');
        updateAgentStatus(agent2Element, 'failed', '❌ Failed');
        updateAgentStatus(agent3Element, 'failed', '❌ Failed');
    } finally {
        // Re-enable button
        generateBtn.disabled = false;
        document.querySelector('.btn-text').style.display = 'inline';
        document.querySelector('.loading-spinner').style.display = 'none';
    }
}

// Simulate Agent Progress
async function simulateAgentProgress() {
    // Agent 1
    updateAgentStatus(agent1Element, 'running', '🔄 Designing...');
    await sleep(800);
    updateAgentStatus(agent1Element, 'done', '✅ Complete');

    // Agent 2
    updateAgentStatus(agent2Element, 'running', '🔄 Coding...');
    await sleep(1000);
    updateAgentStatus(agent2Element, 'done', '✅ Complete');

    // Agent Verification (New)
    updateAgentStatus(agentVerifyElement, 'running', '🔬 Simulating...');
    await sleep(1200);
    updateAgentStatus(agentVerifyElement, 'done', '✅ Verified');

    // Agent 3
    updateAgentStatus(agent3Element, 'running', '🔄 Integrating...');
    await sleep(800);
    updateAgentStatus(agent3Element, 'done', '✅ Complete');
}

// Update Agent Status
function updateAgentStatus(element, status, text) {
    const stateElement = element.querySelector('.agent-state');
    
    // Remove all status classes
    element.classList.remove('active', 'complete', 'error');
    stateElement.classList.remove('pending', 'running', 'done', 'failed');

    // Add new status
    if (status === 'running') {
        element.classList.add('active');
        stateElement.classList.add('running');
    } else if (status === 'done') {
        element.classList.add('complete');
        stateElement.classList.add('done');
    } else if (status === 'failed') {
        element.classList.add('error');
        stateElement.classList.add('failed');
    }

    stateElement.textContent = text;
}

// Display Results
function displayResults(data) {
    resultsSection.style.display = 'block';
    
    // Store data for download
    currentProjectData = data;

    // Architecture
    if (data.architecture) {
        projectTitleElement.textContent = data.architecture.projectTitle || 'Untitled Project';
        architectureDescElement.textContent = data.architecture.architectureDescription || 'No description available';

        if (data.architecture.moduleList && data.architecture.moduleList.length > 0) {
            moduleListElement.innerHTML = `
                <h4>📦 Required Modules:</h4>
                <ul>
                    ${data.architecture.moduleList.map(module => `<li>${module}</li>`).join('')}
                </ul>
            `;
            
            // Draw block diagram
            drawBlockDiagram(data.architecture.moduleList, data.architecture.projectTitle);
        } else {
            moduleListElement.innerHTML = '<p>No modules listed</p>';
        }
    }
    
    // Display models used (if available)
    if (data.modelsUsed && data.modelsUsed.length > 0) {
        const modelInfo = document.createElement('div');
        modelInfo.className = 'model-info';
        modelInfo.style.cssText = 'background: linear-gradient(135deg, rgba(14, 165, 233, 0.1) 0%, rgba(2, 132, 199, 0.1) 100%); padding: 12px 20px; border-radius: 8px; margin: 15px 0; border-left: 3px solid #0ea5e9;';
        modelInfo.innerHTML = `
            <div style="font-weight: 600; color: #0ea5e9; margin-bottom: 8px; font-size: 14px;">
                🤖 AI Models Used:
            </div>
            <div style="font-family: 'Courier New', monospace; font-size: 13px; color: #94a3b8;">
                ${data.modelsUsed.map(model => `<div style="padding: 2px 0;">• ${model}</div>`).join('')}
            </div>
        `;
        
        // Insert after project title safely
        const architectureSection = document.getElementById('architectureContent');
        if (architectureSection && architectureSection.firstElementChild) {
            const insertPoint = architectureSection.firstElementChild.nextElementSibling;
            if (insertPoint) {
                architectureSection.insertBefore(modelInfo, insertPoint);
            } else {
                // If no next sibling, just append
                architectureSection.appendChild(modelInfo);
            }
        }
    }

    // RTL Code
    if (data.rtl) {
        verilogCodeElement.textContent = data.rtl.verilogCode || '// No Verilog code generated';
        testbenchCodeElement.textContent = data.rtl.testbenchCode || '// No testbench generated';
    }

    // Vivado
    if (data.vivado) {
        vivadoTclScriptElement.textContent = data.vivado.vivadoTclScript || '# No TCL script generated';
        
        if (data.vivado.resourceEstimation) {
            resourceEstimationElement.innerHTML = `
                <strong>📊 Resource Estimation:</strong><br>
                ${data.vivado.resourceEstimation}
            `;
        }
    }

    // NEW: Handle Simulation Results
    if (data.rtl) {
        if (simLogsElement) {
            simLogsElement.textContent = data.rtl.simulationLogs || 'No simulation logs generated.';
        }
        
        if (simStatusBadge) {
            if (data.rtl.simPassed) {
                simStatusBadge.textContent = '✅ PASSED';
                simStatusBadge.className = 'badge success';
            } else {
                simStatusBadge.textContent = '❌ FAILED';
                simStatusBadge.className = 'badge error';
            }
        }

        // Generate and display professional schematic
        updateRTLSchematic(data.rtl.verilogCode);
    }

    // Scroll to results
    resultsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

// Professional RTL Schematic Logic
async function updateRTLSchematic(verilogCode) {
    if (!schematicContainer) return;
    
    schematicContainer.innerHTML = `
        <div class="schematic-loading">
            <div class="mini-spinner"></div>
            <p>Synthesizing professional RTL schematic...</p>
        </div>
    `;

    try {
        const response = await fetch(`${API_BASE_URL}/api/synthesize`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ verilogCode })
        });

        if (!response.ok) throw new Error('Synthesis failed');

        const data = await response.json();
        if (data.svg) {
            // Success: Inject the SVG into the container
            schematicContainer.innerHTML = data.svg;
            
            // Add zoom/pan support if library is available or just let it scale
            const svg = schematicContainer.querySelector('svg');
            if (svg) {
                svg.setAttribute('width', '100%');
                svg.style.height = 'auto'; // Fixed attribute error
                svg.style.borderRadius = '8px';
            }
        } else {
            throw new Error(data.error || 'Unknown synthesis error');
        }
    } catch (error) {
        console.error('Schematic Error:', error);
        schematicContainer.innerHTML = `
            <div class="schematic-error">
                <p>⚠️ Schematic visualization unavailable on this system.</p>
                <small>Requires Yosys and NetlistSVG to be installed.</small>
            </div>
        `;
    }
}

// Show Error
function showError(message) {
    errorSection.style.display = 'block';
    errorMessageElement.textContent = message;
    statusSection.style.display = 'none';
    resultsSection.style.display = 'none';

    // Scroll to error
    errorSection.scrollIntoView({ behavior: 'smooth' });
}

// Reset UI
function resetUI() {
    // Reset agent statuses
    [agent1Element, agent2Element, agentVerifyElement, agent3Element].forEach(element => {
        if (!element) return;
        element.classList.remove('active', 'complete', 'error');
        const stateElement = element.querySelector('.agent-state');
        stateElement.classList.remove('running', 'done', 'failed');
        stateElement.classList.add('pending');
        stateElement.textContent = '⏳ Waiting';
    });

    // Clear results
    projectTitleElement.textContent = '';
    architectureDescElement.textContent = '';
    moduleListElement.innerHTML = '';
    verilogCodeElement.textContent = '';
    testbenchCodeElement.textContent = '';
    vivadoTclScriptElement.textContent = '';
    resourceEstimationElement.innerHTML = '';
    
    if (schematicContainer) {
        schematicContainer.innerHTML = `
            <div class="schematic-placeholder">
                <p>Generating hardware schematic...</p>
            </div>
        `;
    }
    
    if (simLogsElement) simLogsElement.textContent = '';
}

// Copy to Clipboard
async function handleCopy(event) {
    const targetId = event.currentTarget.getAttribute('data-target');
    const targetElement = document.getElementById(targetId);
    
    let textToCopy = '';

    if (targetId === 'architectureContent') {
        // Copy architecture information
        textToCopy = `
PROJECT TITLE:
${projectTitleElement.textContent}

ARCHITECTURE DESCRIPTION:
${architectureDescElement.textContent}

MODULES:
${moduleListElement.textContent}
        `.trim();
    } else {
        textToCopy = targetElement.textContent;
    }

    try {
        await navigator.clipboard.writeText(textToCopy);
        
        // Visual feedback
        const btn = event.currentTarget;
        const originalText = btn.textContent;
        btn.textContent = '✅ Copied!';
        btn.style.background = '#22c55e';
        
        setTimeout(() => {
            btn.textContent = originalText;
            btn.style.background = '';
        }, 2000);
    } catch (err) {
        console.error('Failed to copy:', err);
        alert('Failed to copy to clipboard');
    }
}

// Utility: Sleep
function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

// Show save prompt for non-authenticated users
function showSavePrompt() {
    const promptDiv = document.createElement('div');
    promptDiv.style.cssText = `
        position: fixed;
        bottom: 20px;
        right: 20px;
        background: linear-gradient(135deg, #0ea5e9 0%, #0284c7 100%);
        color: white;
        padding: 20px 25px;
        border-radius: 12px;
        box-shadow: 0 8px 30px rgba(14, 165, 233, 0.5);
        z-index: 10000;
        max-width: 350px;
        animation: slideInUp 0.5s ease;
    `;
    
    promptDiv.innerHTML = `
        <div style="display: flex; align-items: start; gap: 15px;">
            <div style="font-size: 32px;">💾</div>
            <div style="flex: 1;">
                <div style="font-weight: 700; font-size: 16px; margin-bottom: 8px;">Save Your Work?</div>
                <div style="font-size: 14px; opacity: 0.95; margin-bottom: 15px;">Sign in to save this design and access it later from any device!</div>
                <div style="display: flex; gap: 10px;">
                    <button onclick="document.querySelector('.sign-in-btn').click(); this.parentElement.parentElement.parentElement.parentElement.remove();" 
                            style="flex: 1; padding: 10px; background: white; color: #0284c7; border: none; border-radius: 8px; font-weight: 700; cursor: pointer;">
                        Sign In to Save
                    </button>
                    <button onclick="this.parentElement.parentElement.parentElement.parentElement.remove();" 
                            style="padding: 10px 15px; background: rgba(255,255,255,0.2); color: white; border: none; border-radius: 8px; cursor: pointer;">
                        Skip
                    </button>
                </div>
            </div>
        </div>
    `;
    
    document.body.appendChild(promptDiv);
    
    // Auto-remove after 10 seconds
    setTimeout(() => {
        if (promptDiv.parentElement) {
            promptDiv.style.animation = 'slideOutDown 0.5s ease';
            setTimeout(() => promptDiv.remove(), 500);
        }
    }, 10000);
}

// ========================================
// PROGRESS BAR FUNCTIONS
// ========================================

function updateProgress(percent, text, elapsed, estimated) {
    if (progressBar) progressBar.style.width = percent + '%';
    if (progressText) progressText.textContent = text;
    if (progressPercent) progressPercent.textContent = Math.round(percent) + '%';
    if (elapsedTime) elapsedTime.textContent = `Elapsed: ${elapsed}s`;
    if (estimatedTime) estimatedTime.textContent = `Estimated: ~${estimated}s`;
}

function startProgress() {
    startTime = Date.now();
    let progress = 0;
    const totalEstimated = 30; // 30 seconds estimated
    
    updateProgress(0, 'Initializing AI agents...', 0, totalEstimated);
    
    progressInterval = setInterval(() => {
        const elapsed = Math.floor((Date.now() - startTime) / 1000);
        const remaining = Math.max(0, totalEstimated - elapsed);
        
        // Smooth progress increase
        if (progress < 25) {
            progress += 0.5; // Slower at start
        } else if (progress < 90) {
            progress += 0.3; // Medium speed
        } else if (progress < 95) {
            progress += 0.1; // Very slow near end
        }
        
        // Update text based on progress
        let text = 'Initializing AI agents...';
        if (progress >= 10 && progress < 40) {
            text = '🕵️‍♂️ System Architect analyzing requirements...';
        } else if (progress >= 40 && progress < 70) {
            text = '👨‍💻 RTL Engineer writing Verilog code...';
        } else if (progress >= 70 && progress < 95) {
            text = '🧐 Vivado Integrator creating build scripts...';
        } else if (progress >= 95) {
            text = 'Finalizing design...';
        }
        
        updateProgress(progress, text, elapsed, remaining);
        
        if (progress >= 99) {
            clearInterval(progressInterval);
        }
    }, 200);
}

function completeProgress() {
    if (progressInterval) clearInterval(progressInterval);
    const elapsed = Math.floor((Date.now() - startTime) / 1000);
    updateProgress(100, '✅ Design generation complete!', elapsed, 0);
}

function resetProgress() {
    if (progressInterval) clearInterval(progressInterval);
    updateProgress(0, 'Ready', 0, 30);
}

// ========================================
// AI CHAT ASSISTANT
// ========================================

let chatHistory = [];

function toggleChat() {
    const chatPanel = document.getElementById('chatPanel');
    const chatToggle = document.getElementById('chatToggle');
    
    if (chatPanel.classList.contains('open')) {
        chatPanel.classList.remove('open');
        chatToggle.textContent = '💬';
    } else {
        chatPanel.classList.add('open');
        chatToggle.textContent = '✕';
    }
}

async function sendChatMessage() {
    const chatInput = document.getElementById('chatInput');
    const message = chatInput.value.trim();
    
    if (!message) return;
    
    // Add user message
    addChatMessage(message, 'user');
    chatInput.value = '';
    
    // Disable send button
    const sendBtn = document.getElementById('chatSendBtn');
    sendBtn.disabled = true;
    sendBtn.textContent = 'Thinking...';
    
    try {
        // Send to backend
        const response = await fetch(`${API_BASE_URL}/chat-assistant`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                message: message,
                projectData: currentProjectData,
                history: chatHistory
            })
        });
        
        const data = await response.json();
        
        if (data.status === 'success') {
            addChatMessage(data.response, 'assistant');
        } else {
            addChatMessage('Sorry, I encountered an error. Please try again.', 'assistant');
        }
    } catch (error) {
        console.error('Chat error:', error);
        addChatMessage('Sorry, I\'m having trouble connecting. Please try again later.', 'assistant');
    } finally {
        sendBtn.disabled = false;
        sendBtn.textContent = 'Send 🚀';
    }
}

function addChatMessage(content, type) {
    const chatMessages = document.getElementById('chatMessages');
    const messageDiv = document.createElement('div');
    messageDiv.className = `chat-message ${type}`;
    
    const avatar = type === 'user' ? '👤' : '🤖';
    
    // Build DOM safely to prevent XSS
    const avatarDiv = document.createElement('div');
    avatarDiv.className = 'message-avatar';
    avatarDiv.textContent = avatar;
    
    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';
    
    // Split by newlines and create separate <p> elements
    const lines = content.split('\n');
    lines.forEach(line => {
        const p = document.createElement('p');
        p.textContent = line;
        contentDiv.appendChild(p);
    });
    
    messageDiv.appendChild(avatarDiv);
    messageDiv.appendChild(contentDiv);
    
    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
    
    // Store in history
    chatHistory.push({ role: type, content: content });
}

// Initialize
console.log('AMD Agentic Hardware Co-Design Platform - Frontend Loaded');
console.log('API Endpoint:', API_BASE_URL);

// Current authenticated user
let currentUser = null;

// Load project history when page loads
document.addEventListener('DOMContentLoaded', () => {
    initAuth();
});

// ========================================
// FIREBASE AUTHENTICATION
// ========================================

function initAuth() {
    if (typeof firebase === 'undefined' || !auth) {
        console.log('Firebase Auth not available');
        return;
    }
    
    // Listen for auth state changes
    auth.onAuthStateChanged((user) => {
        if (user) {
            // User is signed in
            currentUser = user;
            console.log('✅ User signed in:', user.email);
            updateUIForSignedInUser(user);
            loadProjectHistory();
        } else {
            // User is signed out
            currentUser = null;
            console.log('❌ User signed out');
            updateUIForSignedOutUser();
        }
    });
}

function signInWithGoogle() {
    if (typeof firebase === 'undefined' || !auth) {
        alert('Firebase Auth not available');
        return;
    }
    
    const provider = new firebase.auth.GoogleAuthProvider();
    
    auth.signInWithPopup(provider)
        .then((result) => {
            console.log('✅ Signed in successfully:', result.user.email);
        })
        .catch((error) => {
            console.error('❌ Sign-in error:', error);
            alert('Failed to sign in: ' + error.message);
        });
}

function signOut() {
    if (typeof firebase === 'undefined' || !auth) {
        alert('Firebase Auth not available');
        return;
    }
    
    auth.signOut()
        .then(() => {
            console.log('✅ Signed out successfully');
        })
        .catch((error) => {
            console.error('❌ Sign-out error:', error);
            alert('Failed to sign out: ' + error.message);
        });
}

function updateUIForSignedInUser(user) {
    document.getElementById('signedOut').style.display = 'none';
    document.getElementById('signedIn').style.display = 'flex';
    document.getElementById('userAvatar').src = user.photoURL || 'https://via.placeholder.com/40';
    document.getElementById('userName').textContent = user.displayName || 'User';
    document.getElementById('userEmail').textContent = user.email;
}

function updateUIForSignedOutUser() {
    document.getElementById('signedOut').style.display = 'block';
    document.getElementById('signedIn').style.display = 'none';
    
    // Clear history
    const historyContainer = document.getElementById('projectHistory');
    historyContainer.innerHTML = '<p class="no-history">Please sign in to view your projects</p>';
}

// ========================================
// FIREBASE PROJECT HISTORY (User-Specific)
// ========================================

function toggleSidebar() {
    const sidebar = document.getElementById('historySidebar');
    sidebar.classList.toggle('open');
}

function saveProjectToFirebase(projectData) {
    if (typeof firebase === 'undefined' || !db) {
        console.log('Firebase not available, skipping save');
        return;
    }
    
    if (!currentUser) {
        console.log('User not signed in, skipping auto-save');
        return;
    }
    
    const projectDoc = {
        timestamp: firebase.firestore.FieldValue.serverTimestamp(),
        prompt: document.getElementById('userPrompt').value,
        title: projectData.architecture.projectTitle,
        data: projectData,
        createdAt: new Date().toISOString(),
        userId: currentUser.uid,
        userEmail: currentUser.email,
        userName: currentUser.displayName
    };
    
    db.collection('users').doc(currentUser.uid).collection('projects')
        .add(projectDoc)
        .then((docRef) => {
            console.log('✅ Project saved to Firebase with ID:', docRef.id);
            loadProjectHistory();
        })
        .catch((error) => {
            console.error('❌ Error saving to Firebase:', error);
        });
}

function loadProjectHistory() {
    if (typeof firebase === 'undefined' || !db) {
        console.log('Firebase not available');
        return;
    }
    
    if (!currentUser) {
        console.log('User not signed in');
        return;
    }
    
    const historyContainer = document.getElementById('projectHistory');
    
    db.collection('users').doc(currentUser.uid).collection('projects')
        .orderBy('createdAt', 'desc')
        .limit(20)
        .get()
        .then((snapshot) => {
            if (snapshot.empty) {
                historyContainer.innerHTML = '<p class="no-history">No projects yet. Start by generating a design!</p>';
                return;
            }
            
            historyContainer.innerHTML = '';
            
            snapshot.forEach((doc) => {
                const project = doc.data();
                const historyItem = createHistoryItem(doc.id, project);
                historyContainer.appendChild(historyItem);
            });
        })
        .catch((error) => {
            console.error('Error loading history:', error);
            historyContainer.innerHTML = '<p class="no-history">Error loading projects</p>';
        });
}

function createHistoryItem(projectId, project) {
    const div = document.createElement('div');
    div.className = 'history-item';
    
    const timeAgo = getTimeAgo(project.createdAt);
    
    div.innerHTML = `
        <div class="history-item-title">${project.title || 'Untitled Project'}</div>
        <div class="history-item-prompt">${project.prompt || 'No description'}</div>
        <div class="history-item-time">🕐 ${timeAgo}</div>
        <div class="history-item-actions">
            <button class="load-btn" onclick="loadProjectById('${projectId}')">📂 Load</button>
            <button class="delete-btn" onclick="deleteProject('${projectId}')">🗑️ Delete</button>
        </div>
    `;
    
    return div;
}

function loadProjectById(projectId) {
    if (typeof firebase === 'undefined' || !db) {
        alert('Firebase not available');
        return;
    }
    
    if (!currentUser) {
        alert('Please sign in to load projects');
        return;
    }
    
    db.collection('users').doc(currentUser.uid).collection('projects').doc(projectId).get()
        .then((doc) => {
            if (doc.exists) {
                const project = doc.data();
                currentProjectData = project.data;
                displayResults(project.data);
                toggleSidebar();
                
                // Scroll to results
                document.getElementById('resultsSection').scrollIntoView({ behavior: 'smooth' });
            } else {
                alert('Project not found');
            }
        })
        .catch((error) => {
            console.error('Error loading project:', error);
            alert('Failed to load project');
        });
}

function deleteProject(projectId) {
    if (!confirm('Are you sure you want to delete this project?')) {
        return;
    }
    
    if (typeof firebase === 'undefined' || !db) {
        alert('Firebase not available');
        return;
    }
    
    if (!currentUser) {
        alert('Please sign in to delete projects');
        return;
    }
    
    db.collection('users').doc(currentUser.uid).collection('projects').doc(projectId).delete()
        .then(() => {
            console.log('Project deleted');
            loadProjectHistory();
        })
        .catch((error) => {
            console.error('Error deleting project:', error);
            alert('Failed to delete project');
        });
}

function clearHistory() {
    if (!confirm('Are you sure you want to delete ALL projects? This cannot be undone!')) {
        return;
    }
    
    if (typeof firebase === 'undefined' || !db) {
        alert('Firebase not available');
        return;
    }
    
    if (!currentUser) {
        alert('Please sign in');
        return;
    }
    
    db.collection('users').doc(currentUser.uid).collection('projects').get()
        .then((snapshot) => {
            const batch = db.batch();
            snapshot.docs.forEach((doc) => {
                batch.delete(doc.ref);
            });
            return batch.commit();
        })
        .then(() => {
            console.log('All projects deleted');
            loadProjectHistory();
        })
        .catch((error) => {
            console.error('Error clearing history:', error);
            alert('Failed to clear history');
        });
}

function getTimeAgo(dateString) {
    if (!dateString) return 'Unknown';
    
    const date = new Date(dateString);
    const now = new Date();
    const seconds = Math.floor((now - date) / 1000);
    
    if (seconds < 60) return 'Just now';
    if (seconds < 3600) return `${Math.floor(seconds / 60)} minutes ago`;
    if (seconds < 86400) return `${Math.floor(seconds / 3600)} hours ago`;
    if (seconds < 604800) return `${Math.floor(seconds / 86400)} days ago`;
    
    return date.toLocaleDateString();
}

// ========================================
// BLOCK DIAGRAM GENERATOR
// ========================================
function drawBlockDiagram(moduleList, projectTitle) {
    const canvas = document.getElementById('blockDiagram');
    const ctx = canvas.getContext('2d');
    
    // Clear canvas
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    
    // Set background
    ctx.fillStyle = '#1a1a1a';
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    
    // Add watermark at top-right
    ctx.fillStyle = 'rgba(237, 28, 36, 0.2)';
    ctx.font = 'bold 14px Arial';
    ctx.textAlign = 'right';
    ctx.fillText('AMD Sling Shot Hackathon 2026', canvas.width - 20, 25);
    ctx.font = '12px Arial';
    ctx.fillText('Bhavin / Nishant', canvas.width - 20, 45);
    ctx.textAlign = 'left';
    
    // Draw title
    ctx.fillStyle = '#ED1C24';
    ctx.font = 'bold 24px Arial';
    ctx.fillText(projectTitle, 20, 40);
    
    // Calculate layout
    const moduleCount = moduleList.length;
    const maxPerRow = 4;
    const blockWidth = 200;
    const blockHeight = 80;
    const horizontalSpacing = 80;
    const verticalSpacing = 120;
    const startX = 50;
    const startY = 80;
    
    // Draw modules
    moduleList.forEach((module, index) => {
        const col = index % maxPerRow;
        const row = Math.floor(index / maxPerRow);
        const x = startX + col * (blockWidth + horizontalSpacing);
        const y = startY + row * (blockHeight + verticalSpacing);
        
        // Draw module box with gradient
        const gradient = ctx.createLinearGradient(x, y, x, y + blockHeight);
        gradient.addColorStop(0, '#ED1C24');
        gradient.addColorStop(1, '#c41e3a');
        ctx.fillStyle = gradient;
        ctx.fillRect(x, y, blockWidth, blockHeight);
        
        // Draw border
        ctx.strokeStyle = '#ffffff';
        ctx.lineWidth = 2;
        ctx.strokeRect(x, y, blockWidth, blockHeight);
        
        // Draw module name
        ctx.fillStyle = '#FFFFFF';
        ctx.font = 'bold 14px Arial';
        ctx.textAlign = 'center';
        ctx.fillText(module, x + blockWidth / 2, y + blockHeight / 2);
        
        // Draw connection arrows to next module in same row
        if (col < maxPerRow - 1 && index < moduleCount - 1 && Math.floor((index + 1) / maxPerRow) === row) {
            drawArrow(ctx, x + blockWidth, y + blockHeight / 2, x + blockWidth + horizontalSpacing, y + blockHeight / 2);
        }
        
        // Draw connection arrows to next row
        if (index + maxPerRow < moduleCount) {
            const nextY = y + blockHeight + verticalSpacing;
            drawArrow(ctx, x + blockWidth / 2, y + blockHeight, x + blockWidth / 2, nextY - blockHeight);
        }
    });
    
    // Reset text alignment
    ctx.textAlign = 'left';
}

function drawArrow(ctx, fromX, fromY, toX, toY) {
    const headLength = 10;
    const angle = Math.atan2(toY - fromY, toX - fromX);
    
    // Draw line
    ctx.strokeStyle = '#4ade80';
    ctx.lineWidth = 3;
    ctx.beginPath();
    ctx.moveTo(fromX, fromY);
    ctx.lineTo(toX, toY);
    ctx.stroke();
    
    // Draw arrowhead
    ctx.fillStyle = '#4ade80';
    ctx.beginPath();
    ctx.moveTo(toX, toY);
    ctx.lineTo(toX - headLength * Math.cos(angle - Math.PI / 6), toY - headLength * Math.sin(angle - Math.PI / 6));
    ctx.lineTo(toX - headLength * Math.cos(angle + Math.PI / 6), toY - headLength * Math.sin(angle + Math.PI / 6));
    ctx.closePath();
    ctx.fill();
}

// ========================================
// DOWNLOAD ZIP FUNCTIONALITY
// ========================================
async function handleDownloadZip() {
    if (!currentProjectData) {
        alert('No project data available. Please generate a design first.');
        return;
    }
    
    try {
        downloadZipBtn.disabled = true;
        downloadZipBtn.textContent = '⏳ Generating ZIP...';
        
        const response = await fetch(`${API_BASE_URL}/download-project`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(currentProjectData)
        });
        
        if (!response.ok) {
            throw new Error('Failed to generate ZIP file');
        }
        
        // Download the file
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${currentProjectData.architecture.projectTitle.replace(/\s+/g, '_')}.zip`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
        
        // Reset button
        downloadZipBtn.textContent = '✅ Downloaded!';
        setTimeout(() => {
            downloadZipBtn.textContent = '📦 Download Complete Project (.zip)';
        }, 2000);
        
    } catch (error) {
        console.error('Download error:', error);
        alert('Failed to download project: ' + error.message);
    } finally {
        downloadZipBtn.disabled = false;
    }
}

