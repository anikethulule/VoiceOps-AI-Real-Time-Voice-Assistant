/**
 * VoiceOps AI - Main Application
 * Real-time voice assistant with text chat
 */

// Global state
let orb, statusEl, txEl, talkBtn, chatInput, sendBtn, newChatBtn, conversationsList, settingsBtn;
let conversations = [];
let currentConversationId = null;
let currentMessages = [];
let ws = null;
let started = false;

// Store key
const STORAGE_KEY = "voiceops_conversations";

// Generate unique ID
function generateId() {
  return 'msg-' + Date.now() + '-' + Math.random().toString(36).substr(2, 9);
}

// Save conversations to localStorage
function saveConversations() {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(conversations));
}

// Load conversations from localStorage
function loadConversations() {
  const stored = localStorage.getItem(STORAGE_KEY);
  conversations = stored ? JSON.parse(stored) : [];
  return conversations;
}

// Create new conversation
function createNewConversation() {
  const id = generateId();
  const conv = {
    id: id,
    messages: [],
    createdAt: new Date().toISOString()
  };
  conversations.unshift(conv);
  currentConversationId = id;
  currentMessages = [];
  clearMessages();
  renderConversationsList();
  saveConversations();
  chatInput.focus();
}

// Render conversations list
function renderConversationsList() {
  if (!conversationsList) return;
  
  conversationsList.innerHTML = '';
  
  if (conversations.length === 0) {
    conversationsList.innerHTML = '<div class="empty-state"><span class="icon">📝</span><span>No conversations yet</span></div>';
    return;
  }
  
  conversations.forEach(conv => {
    const div = document.createElement('div');
    div.className = 'conversation-item' + (conv.id === currentConversationId ? ' active' : '');
    const preview = conv.messages.length > 0 
      ? (conv.messages[0].text || 'Chat').substring(0, 50)
      : 'New conversation';
    div.textContent = preview;
    div.addEventListener('click', () => {
      currentConversationId = conv.id;
      currentMessages = conv.messages || [];
      clearMessages();
      renderConversationsList();
      renderMessages();
    });
    conversationsList.appendChild(div);
  });
}

// Clear messages display
function clearMessages() {
  if (txEl) txEl.innerHTML = '';
}

// Render messages
function renderMessages() {
  if (!txEl) return;
  
  txEl.innerHTML = '';
  
  currentMessages.forEach(msg => {
    const div = document.createElement('div');
    div.className = 'message ' + msg.type;
    
    if (msg.type === 'user') {
      div.innerHTML = '<div class="message-content">' + (msg.text || '') + '</div>';
    } else {
      div.innerHTML = '<div class="message-content">' + (msg.text || '') + '</div>';
    }
    
    txEl.appendChild(div);
  });
  
  // Scroll to bottom
  txEl.scrollTop = txEl.scrollHeight;
}

// Add message to current conversation
function addMessage(type, text) {
  if (!currentConversationId) {
    createNewConversation();
  }
  
  const msg = {
    id: generateId(),
    type: type,
    text: text,
    timestamp: new Date().toISOString()
  };
  
  currentMessages.push(msg);
  
  // Update in conversations
  const conv = conversations.find(c => c.id === currentConversationId);
  if (conv) {
    conv.messages = currentMessages;
  }
  
  renderMessages();
  saveConversations();
  
  return msg;
}

// Send text message
function sendTextMessage() {
  const text = chatInput.value.trim();
  if (!text) return;
  
  // Add user message
  addMessage('user', text);
  chatInput.value = '';
  sendBtn.disabled = true;
  
  // Connect WebSocket if not connected
  if (!ws || ws.readyState !== WebSocket.OPEN) {
    connect();
  }
  
  // Send to backend
  if (ws && ws.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify({
      type: 'text',
      text: text
    }));
  }
}

// Connect to WebSocket
function connect() {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  const url = protocol + '//' + window.location.host + '/ws';
  
  console.log('[WS] Connecting to', url);
  
  ws = new WebSocket(url);
  
  ws.onopen = function() {
    console.log('[WS] Connected');
    if (statusEl) statusEl.textContent = 'Connected';
  };
  
  ws.onmessage = function(event) {
    console.log('[WS] Message:', event.data);
    
    try {
      const data = JSON.parse(event.data);
      
      if (data.type === 'text') {
        addMessage('assistant', data.text);
      } else if (data.type === 'error') {
        addMessage('error', data.message);
      }
    } catch (e) {
      console.error('[WS] Parse error:', e);
    }
  };
  
  ws.onerror = function(error) {
    console.error('[WS] Error:', error);
    if (statusEl) statusEl.textContent = 'Connection error';
  };
  
  ws.onclose = function() {
    console.log('[WS] Disconnected');
    if (statusEl) statusEl.textContent = 'Disconnected';
  };
}

// Initialize
document.addEventListener('DOMContentLoaded', function() {
  console.log('[INIT] DOM loaded, initializing...');
  
  // Get elements
  orb = document.getElementById('orb');
  statusEl = document.getElementById('status');
  txEl = document.getElementById('transcript');
  talkBtn = document.getElementById('talk');
  chatInput = document.getElementById('chatInput');
  sendBtn = document.getElementById('sendBtn');
  newChatBtn = document.getElementById('newChatBtn');
  conversationsList = document.getElementById('conversationsList');
  settingsBtn = document.getElementById('settingsBtn');
  
  console.log('[INIT] Elements found');
  
  // Load conversations
  loadConversations();
  if (conversations.length === 0) {
    createNewConversation();
  } else {
    currentConversationId = conversations[0].id;
    currentMessages = conversations[0].messages || [];
  }
  renderConversationsList();
  renderMessages();
  
  // Event listeners
  newChatBtn.addEventListener('click', function() {
    console.log('[EVENT] New Chat clicked');
    createNewConversation();
  });
  
  settingsBtn.addEventListener('click', function() {
    console.log('[EVENT] Settings clicked');
    alert('Settings coming soon!');
  });
  
  talkBtn.addEventListener('click', function() {
    console.log('[EVENT] Talk button clicked');
    if (!ws || ws.readyState !== WebSocket.OPEN) {
      connect();
    }
  });
  
  sendBtn.addEventListener('click', function() {
    console.log('[EVENT] Send button clicked');
    sendTextMessage();
  });
  
  chatInput.addEventListener('keypress', function(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendTextMessage();
    }
  });
  
  chatInput.addEventListener('input', function() {
    const hasText = chatInput.value.trim().length > 0;
    sendBtn.disabled = !hasText;
    console.log('[INPUT] Text changed, disabled:', sendBtn.disabled);
  });
  
  console.log('[INIT] Initialization complete');
});
