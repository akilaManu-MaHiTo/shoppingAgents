// Shopping Agents Chat UI - JavaScript

const messagesContainer = document.getElementById('messagesContainer');
const messageInput = document.getElementById('messageInput');
const sendBtn = document.getElementById('sendBtn');
const chatForm = document.getElementById('chatForm');
const responseModal = document.getElementById('responseModal');
const modalBody = document.getElementById('modalBody');

// Auto-focus input
messageInput.focus();

/**
 * Send message to backend
 */
function sendMessage(e) {
    e.preventDefault();
    const message = messageInput.value.trim();
    
    if (!message) return;
    
    // Add user message to chat
    addMessage(message, 'user');
    messageInput.value = '';
    
    // Show loading indicator
    addLoadingMessage();
    
    // Disable send button
    sendBtn.disabled = true;
    
    // Send to backend
    fetch('/api/chat', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ message })
    })
    .then(res => res.json())
    .then(data => {
        removeLoadingMessage();
        
        if (data.error) {
            addMessage(`❌ Error: ${data.message}`, 'assistant');
        } else {
            displayResponse(data);
        }
    })
    .catch(error => {
        removeLoadingMessage();
        console.error('Error:', error);
        addMessage(`❌ Connection error. Please try again.`, 'assistant');
    })
    .finally(() => {
        sendBtn.disabled = false;
        messageInput.focus();
    });
}

/**
 * Add message to chat
 */
function addMessage(text, sender) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${sender}`;
    
    const avatar = document.createElement('div');
    avatar.className = 'message-avatar';
    avatar.textContent = sender === 'user' ? '👤' : '🤖';
    
    const content = document.createElement('div');
    content.className = 'message-content';
    
    const textDiv = document.createElement('div');
    textDiv.className = 'message-text';
    textDiv.textContent = text;
    
    content.appendChild(textDiv);
    
    if (sender === 'user') {
        messageDiv.appendChild(content);
        messageDiv.appendChild(avatar);
    } else {
        messageDiv.appendChild(avatar);
        messageDiv.appendChild(content);
    }
    
    messagesContainer.appendChild(messageDiv);
    scrollToBottom();
}

// Store response globally for modal display
let currentResponseData = null;

/**
 * Display full response from API
 */
function displayResponse(data) {
    // Store data globally for modal access
    currentResponseData = data;
    
    const { user_input, input_agent, search_agent, filter_agent, advisor } = data;
    
    // Create response message
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message assistant';
    
    const avatar = document.createElement('div');
    avatar.className = 'message-avatar';
    avatar.textContent = '🤖';
    
    const content = document.createElement('div');
    content.className = 'message-content';
    
    const textDiv = document.createElement('div');
    textDiv.className = 'message-text';
    
    // Build summary message
    let summary = '';
    
    if (advisor.fit_status === 'no_fit') {
        summary = `❌ No products found matching your criteria. Let me show you better alternatives!`;
    } else if (advisor.fit_status === 'perfect_fit') {
        summary = `✅ Perfect match found! "${advisor.selected_product?.name}" scores ${advisor.fit_score}/100`;
    } else if (advisor.fit_status === 'strong_fit') {
        summary = `✓ Great match! "${advisor.selected_product?.name}" scores ${advisor.fit_score}/100`;
    } else {
        summary = `✓ Found "${advisor.selected_product?.name}" (Score: ${advisor.fit_score}/100)`;
    }
    
    textDiv.innerHTML = `<strong>${summary}</strong>`;
    
    content.appendChild(textDiv);
    
    // Add response details box
    const responseBox = document.createElement('div');
    responseBox.className = 'message-response';
    responseBox.innerHTML = `
        <div class="response-section">
            <div class="response-label">📊 Analysis Results:</div>
            <div style="font-size: 0.85rem; color: #666;">
                ${filter_agent.total_filtered} products filtered • 
                ${search_agent.candidates_count} matches found
            </div>
        </div>
        <button class="view-details-btn" onclick="showDetailedResponse()">
            👁️ View Full Analysis
        </button>
    `;
    
    content.appendChild(responseBox);
    messageDiv.appendChild(avatar);
    messageDiv.appendChild(content);
    
    messagesContainer.appendChild(messageDiv);
    scrollToBottom();
}

/**
 * Show detailed response in modal
 */
function showDetailedResponse() {
    if (!currentResponseData) {
        alert('No response data available');
        return;
    }
    
    const data = currentResponseData;
    const { user_input, input_agent, search_agent, filter_agent, advisor } = data;
    
    let html = `
        <h2 style="color: #1f2937; margin-bottom: 1.5rem;">Analysis Results</h2>
        
        <div style="background: #f0f9ff; border-left: 4px solid #0ea5e9; padding: 1rem; margin-bottom: 1.5rem; border-radius: 8px;">
            <strong style="color: #0c4a6e;">Your Query:</strong>
            <p style="margin: 0.5rem 0 0 0; color: #1f2937;">"${user_input}"</p>
        </div>
    `;
    
    // Input Agent Section
    html += `
        <div class="detail-card">
            <h4>🧠 Input Agent - Intent Extraction</h4>
            <div class="detail-item">
                <span class="detail-label">Product:</span>
                <span class="detail-value">${input_agent.product}</span>
            </div>
            <div class="detail-item">
                <span class="detail-label">Category:</span>
                <span class="detail-value">${input_agent.category}</span>
            </div>
            ${input_agent.price ? `
            <div class="detail-item">
                <span class="detail-label">Budget:</span>
                <span class="detail-value">₹${input_agent.price.toLocaleString()}</span>
            </div>` : ''}
            ${input_agent.specs.CPU ? `
            <div class="detail-item">
                <span class="detail-label">CPU:</span>
                <span class="detail-value">${input_agent.specs.CPU}</span>
            </div>` : ''}
            ${input_agent.specs.RAM ? `
            <div class="detail-item">
                <span class="detail-label">RAM:</span>
                <span class="detail-value">${input_agent.specs.RAM}</span>
            </div>` : ''}
            ${input_agent.specs.Storage ? `
            <div class="detail-item">
                <span class="detail-label">Storage:</span>
                <span class="detail-value">${input_agent.specs.Storage}</span>
            </div>` : ''}
            ${input_agent.specs.GPU ? `
            <div class="detail-item">
                <span class="detail-label">GPU:</span>
                <span class="detail-value">${input_agent.specs.GPU}</span>
            </div>` : ''}
        </div>
    `;
    
    // Search Agent Section
    html += `
        <div class="detail-card">
            <h4>🔍 Search Agent - Database Search</h4>
            <div class="detail-item">
                <span class="detail-label">Total Candidates:</span>
                <span class="detail-value">${search_agent.candidates_count}</span>
            </div>
            <div class="detail-item">
                <span class="detail-label">Search Mode:</span>
                <span class="detail-value">${search_agent.result_mode}</span>
            </div>
        </div>
    `;
    
    // Filter Agent Section
    html += `
        <div class="detail-card">
            <h4>⚙️ Filter Agent - Rule-Based Filtering</h4>
            <div class="detail-item">
                <span class="detail-label">Filtered Results:</span>
                <span class="detail-value">${filter_agent.total_filtered}</span>
            </div>
            <div class="detail-item">
                <span class="detail-label">Filter Mode:</span>
                <span class="detail-value">${formatMode(filter_agent.filter_mode)}</span>
            </div>
            <div class="detail-item">
                <span class="detail-label">Rejected:</span>
                <span class="detail-value">${filter_agent.rejected_count}</span>
            </div>
            <div class="detail-item">
                <span class="detail-label">Duplicates Removed:</span>
                <span class="detail-value">${filter_agent.duplicates_removed}</span>
            </div>
            ${filter_agent.filters_applied.length > 0 ? `
            <div class="detail-item">
                <span class="detail-label">Active Filters:</span>
                <div style="margin-top: 0.25rem;">
                    ${filter_agent.filters_applied.map(f => `<span class="chip">${f}</span>`).join('')}
                </div>
            </div>` : ''}
        </div>
    `;
    
    // Advisor Section
    html += `
        <div style="background: #f0fdf4; border-left: 4px solid #22c55e; padding: 1rem; margin: 1.5rem 0; border-radius: 8px;">
            <h4 style="margin: 0 0 1rem 0; color: #15803d;">💡 Recommendation Advisor</h4>
            <div class="detail-item">
                <span class="detail-label">Fit Status:</span>
                <span class="detail-value" style="color: ${getStatusColor(advisor.fit_status)};">
                    ${advisor.fit_status.toUpperCase()}
                </span>
            </div>
            <div class="detail-item">
                <span class="detail-label">Fit Score:</span>
                <span class="detail-value">${advisor.fit_score}/100</span>
            </div>
            <div class="detail-item">
                <span class="detail-label">Confidence:</span>
                <span class="detail-value">${advisor.confidence.toUpperCase()}</span>
            </div>
    `;
    
    // Selected Product
    if (advisor.selected_product) {
        html += `
            <div style="background: white; padding: 1rem; border-radius: 8px; margin-top: 1rem; border: 2px solid #22c55e;">
                <h5 style="margin: 0 0 0.5rem 0; color: #22c55e;">🏆 Recommended Product</h5>
                <div class="detail-item">
                    <span class="detail-label">Name:</span>
                    <span class="detail-value">${advisor.selected_product.name || 'N/A'}</span>
                </div>
                ${advisor.selected_product.price ? `
                <div class="detail-item">
                    <span class="detail-label">Price:</span>
                    <span class="detail-value">₹${advisor.selected_product.price.toLocaleString()}</span>
                </div>` : ''}
                ${advisor.selected_product.rating ? `
                <div class="detail-item">
                    <span class="detail-label">Rating:</span>
                    <span class="detail-value">⭐ ${advisor.selected_product.rating}/5</span>
                </div>` : ''}
            </div>
        `;
    }
    
    // Why Selected
    if (advisor.why_selected && advisor.why_selected.length > 0) {
        html += `
            <div style="margin-top: 1rem;">
                <strong style="color: #15803d;">Why Selected:</strong>
                <ul style="margin: 0.5rem 0 0 1.5rem; color: #4b5563;">
                    ${advisor.why_selected.map(reason => `<li>${reason}</li>`).join('')}
                </ul>
            </div>
        `;
    }
    
    html += '</div>';
    
    // Mismatches
    if (advisor.mismatches && advisor.mismatches.length > 0) {
        html += `
            <div style="background: #fef2f2; border-left: 4px solid #ef4444; padding: 1rem; margin: 1.5rem 0; border-radius: 8px;">
                <strong style="color: #7f1d1d;">⚠️ Mismatches:</strong>
                <ul style="margin: 0.5rem 0 0 1.5rem; color: #4b5563; font-size: 0.9rem;">
                    ${advisor.mismatches.map(m => `
                        <li>${m.field}: Required <strong>${m.required}</strong>, Got <strong>${m.actual}</strong></li>
                    `).join('')}
                </ul>
            </div>
        `;
    }
    
    // Alternatives
    if (advisor.alternatives && advisor.alternatives.length > 0) {
        html += `
            <div style="background: #fef3c7; border-left: 4px solid #f59e0b; padding: 1rem; margin: 1.5rem 0; border-radius: 8px;">
                <strong style="color: #92400e;">💼 Alternative Options:</strong>
                <ul style="margin: 0.5rem 0 0 1.5rem; color: #4b5563; font-size: 0.9rem;">
                    ${advisor.alternatives.map(alt => `
                        <li><strong>${alt.name}</strong> - ₹${alt.price.toLocaleString()} | ${alt.reason}</li>
                    `).join('')}
                </ul>
            </div>
        `;
    }
    
    // Improvement Suggestions
    if (advisor.improvement_suggestions && advisor.improvement_suggestions.length > 0) {
        html += `
            <div style="background: #f0f9ff; border-left: 4px solid #0284c7; padding: 1rem; margin: 1.5rem 0; border-radius: 8px;">
                <strong style="color: #0c4a6e;">💡 Improvement Suggestions:</strong>
                <ul style="margin: 0.5rem 0 0 1.5rem; color: #4b5563; font-size: 0.9rem;">
                    ${advisor.improvement_suggestions.map(s => `<li>${s}</li>`).join('')}
                </ul>
            </div>
        `;
    }
    
    // Usage Tips
    if (advisor.usage_tips && advisor.usage_tips.length > 0) {
        html += `
            <div style="background: #f5f3ff; border-left: 4px solid #a855f7; padding: 1rem; margin: 1.5rem 0; border-radius: 8px;">
                <strong style="color: #6b21a8;">📖 Usage Tips:</strong>
                <ul style="margin: 0.5rem 0 0 1.5rem; color: #4b5563; font-size: 0.9rem;">
                    ${advisor.usage_tips.map(tip => `<li>${tip}</li>`).join('')}
                </ul>
            </div>
        `;
    }
    
    // Filtered Candidates
    if (filter_agent.candidates && filter_agent.candidates.length > 0) {
        html += `
            <div style="margin: 1.5rem 0;">
                <h4 style="color: #1f2937; margin-bottom: 1rem;">🏪 Filtered Candidates (${filter_agent.candidates.length})</h4>
                <div class="products-grid">
                    ${filter_agent.candidates.map(product => `
                        <div class="product-card">
                            <div class="product-name">${product.name}</div>
                            ${product.price ? `<div class="product-price">₹${product.price.toLocaleString()}</div>` : ''}
                            <div class="product-specs">
                                ${product.CPU ? `<div>CPU: ${product.CPU}</div>` : ''}
                                ${product.RAM ? `<div>RAM: ${product.RAM}</div>` : ''}
                                ${product.Storage ? `<div>Storage: ${product.Storage}</div>` : ''}
                                ${product.GPU ? `<div>GPU: ${product.GPU}</div>` : ''}
                                ${product.category ? `<div>Category: ${product.category}</div>` : ''}
                            </div>
                            ${product.rating ? `<div class="product-rating">⭐ ${product.rating}/5</div>` : ''}
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
    }
    
    modalBody.innerHTML = html;
    responseModal.classList.add('active');
}

/**
 * Format filter mode for display
 */
function formatMode(mode) {
    const modes = {
        'exact_filter': '✓ Exact Match',
        'near_match': '◐ Near Match',
        'no_match': '✗ No Match'
    };
    return modes[mode] || mode;
}

/**
 * Get color for fit status
 */
function getStatusColor(status) {
    const colors = {
        'perfect_fit': '#059669',
        'strong_fit': '#2563eb',
        'acceptable': '#f59e0b',
        'no_fit': '#dc2626'
    };
    return colors[status] || '#666';
}

/**
 * Add loading message
 */
function addLoadingMessage() {
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message assistant';
    messageDiv.id = 'loadingMessage';
    
    const avatar = document.createElement('div');
    avatar.className = 'message-avatar';
    avatar.textContent = '🤖';
    
    const content = document.createElement('div');
    content.className = 'message-content';
    
    const loadingDiv = document.createElement('div');
    loadingDiv.className = 'loading';
    loadingDiv.innerHTML = '<div class="loading-dot"></div><div class="loading-dot"></div><div class="loading-dot"></div><span>Analyzing...</span>';
    
    content.appendChild(loadingDiv);
    messageDiv.appendChild(avatar);
    messageDiv.appendChild(content);
    
    messagesContainer.appendChild(messageDiv);
    scrollToBottom();
}

/**
 * Remove loading message
 */
function removeLoadingMessage() {
    const loadingMsg = document.getElementById('loadingMessage');
    if (loadingMsg) {
        loadingMsg.remove();
    }
}

/**
 * Close modal
 */
function closeModal() {
    responseModal.classList.remove('active');
}

/**
 * Set example query
 */
function setExample(text) {
    messageInput.value = text;
    messageInput.focus();
}

/**
 * Scroll to bottom of messages
 */
function scrollToBottom() {
    setTimeout(() => {
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }, 0);
}

/**
 * Close modal when clicking outside
 */
responseModal.addEventListener('click', (e) => {
    if (e.target === responseModal) {
        closeModal();
    }
});

/**
 * Keyboard shortcut: Ctrl+Enter to send
 */
messageInput.addEventListener('keydown', (e) => {
    if (e.ctrlKey && e.key === 'Enter') {
        sendMessage(new Event('submit'));
    }
});

// Auto-focus input on load
window.addEventListener('load', () => {
    messageInput.focus();
    loadHistory();
});

/* ============ HISTORY TAB FUNCTIONALITY ============ */

let historyData = [];

/**
 * Switch between Chat and History tabs
 */
function switchTab(tabName) {
    // Update tab buttons
    const buttons = document.querySelectorAll('.tab-btn');
    buttons.forEach(btn => {
        if ((tabName === 'chat' && btn.textContent.includes('Chat')) ||
            (tabName === 'history' && btn.textContent.includes('History'))) {
            btn.classList.add('active');
        } else {
            btn.classList.remove('active');
        }
    });
    
    // Hide/Show tab content
    const chatTab = document.getElementById('chat-tab');
    const historyTab = document.getElementById('history-tab');
    
    if (tabName === 'chat') {
        chatTab.classList.remove('hidden');
        historyTab.classList.add('hidden');
        messageInput.focus();
    } else {
        chatTab.classList.add('hidden');
        historyTab.classList.remove('hidden');
    }
}

/**
 * Load history from backend
 */
async function loadHistory() {
    try {
        const response = await fetch('/api/history');
        const data = await response.json();
        
        if (data.status === 'success') {
            historyData = data.history || [];
            displayHistory(historyData);
            updateHistoryCount(data.total_searches);
        }
    } catch (error) {
        console.error('Error loading history:', error);
        const historyList = document.getElementById('historyList');
        if (historyList) {
            historyList.innerHTML = '<p class="history-empty"><div class="history-empty-icon">📋</div><p>Failed to load history</p></p>';
        }
    }
}

/**
 * Update history count display
 */
function updateHistoryCount(count) {
    const countElement = document.getElementById('historyCount');
    if (countElement) {
        countElement.textContent = count === 0 
            ? 'No searches yet' 
            : `${count} search${count !== 1 ? 'es' : ''}`;
    }
}

/**
 * Display history items
 */
function displayHistory(items) {
    const historyList = document.getElementById('historyList');
    
    if (!historyList) return;
    
    if (items.length === 0) {
        historyList.innerHTML = `
            <div class="history-empty">
                <div class="history-empty-icon">📋</div>
                <p><strong>No search history yet</strong></p>
                <p>Start searching to see your history here</p>
            </div>
        `;
        return;
    }
    
    historyList.innerHTML = items.map((item, index) => {
        const output = item.output || {};
        const budgetType = item.budgetType || 'unknown';
        const specs = [];
        
        if (output.CPU) specs.push(`CPU: ${output.CPU}`);
        if (output.RAM) specs.push(`RAM: ${output.RAM}`);
        if (output.Storage) specs.push(`Storage: ${output.Storage}`);
        if (output.GPU) specs.push(`GPU: ${output.GPU}`);
        
        return `
            <div class="history-item" onclick="setExample('${item.input.replace(/'/g, "\\'")}')">
                <div class="history-item-input">${item.input}</div>
                <div class="history-item-meta">
                    <span class="history-badge ${budgetType}">💰 ${budgetType.charAt(0).toUpperCase() + budgetType.slice(1)}</span>
                    ${output.category ? `<span class="history-badge">📱 ${output.category}</span>` : ''}
                    ${output.product && output.product !== 'unknown' ? `<span class="history-badge">🏢 ${output.product}</span>` : ''}
                </div>
                ${specs.length > 0 ? `
                <div class="history-specs">
                    ${specs.map(spec => `<span class="spec-tag">${spec}</span>`).join('')}
                </div>` : ''}
            </div>
        `;
    }).join('');
}

/**
 * Filter history by search query and budget
 */
function filterHistory() {
    const searchInput = document.getElementById('historySearch');
    const budgetFilter = document.getElementById('budgetFilter');
    
    const searchQuery = searchInput.value.toLowerCase();
    const budgetType = budgetFilter.value;
    
    const filtered = historyData.filter(item => {
        const matchesSearch = item.input.toLowerCase().includes(searchQuery);
        const matchesBudget = !budgetType || item.budgetType === budgetType;
        return matchesSearch && matchesBudget;
    });
    
    displayHistory(filtered);
    updateHistoryCount(filtered.length);
}

