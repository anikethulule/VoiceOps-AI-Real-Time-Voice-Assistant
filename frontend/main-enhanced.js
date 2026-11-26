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
  
  const payload = JSON.stringify({ type: 'text', text: text });
  if (ws && ws.readyState === WebSocket.OPEN) {
    ws.send(payload);
  } else {
    connect();
    ws.addEventListener('open', function() { ws.send(payload); }, { once: true });
  }
}

// Audio: Gemini returns 24 kHz 16-bit mono PCM
let playCtx = null;
let playTime = 0;
let activeSources = [];

function playPcm(buffer) {
  if (!playCtx) playCtx = new AudioContext({ sampleRate: 24000 });
  const int16 = new Int16Array(buffer);
  const audioBuf = playCtx.createBuffer(1, int16.length, 24000);
  const ch = audioBuf.getChannelData(0);
  for (let i = 0; i < int16.length; i++) ch[i] = int16[i] / 32768;
  const src = playCtx.createBufferSource();
  src.buffer = audioBuf;
  src.connect(playCtx.destination);
  playTime = Math.max(playTime, playCtx.currentTime);
  src.start(playTime);
  playTime += audioBuf.duration;
  activeSources.push(src);
  src.onended = () => { activeSources = activeSources.filter(s => s !== src); };
}

function stopPlayback() {
  activeSources.forEach(s => { try { s.stop(); } catch (e) {} });
  activeSources = [];
  playTime = 0;
}

// Microphone capture -> 16 kHz PCM over WebSocket
let micCtx = null;
let micStream = null;

async function startMic() {
  micStream = await navigator.mediaDevices.getUserMedia({
    audio: { echoCancellation: true, noiseSuppression: true }
  });
  micCtx = new AudioContext();
  await micCtx.audioWorklet.addModule('pcm-processor.js');
  const source = micCtx.createMediaStreamSource(micStream);
  const node = new AudioWorkletNode(micCtx, 'pcm-processor');
  node.port.onmessage = (e) => {
    if (ws && ws.readyState === WebSocket.OPEN) ws.send(e.data.pcm);
  };
  source.connect(node);
  if (playCtx && playCtx.state === 'suspended') playCtx.resume();
}

function stopMic() {
  if (micStream) micStream.getTracks().forEach(t => t.stop());
  if (micCtx) micCtx.close();
  micStream = null;
  micCtx = null;
}

// Connect to WebSocket
function connect() {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  const url = protocol + '//' + window.location.host + '/ws';
  
  console.log('[WS] Connecting to', url);
  
  ws = new WebSocket(url);
  ws.binaryType = 'arraybuffer';
  
  ws.onopen = function() {
    console.log('[WS] Connected');
    if (statusEl) statusEl.textContent = 'Connected';
  };
  
  ws.onmessage = function(event) {
    if (event.data instanceof ArrayBuffer) {
      playPcm(event.data);
      return;
    }
    console.log('[WS] Message:', event.data);
    
    try {
      const data = JSON.parse(event.data);
      
      if (data.type === 'text') {
        addMessage('assistant', data.text);
        sendBtn.disabled = chatInput.value.trim().length === 0;
      } else if (data.type === 'user') {
        addMessage('user', data.text);
      } else if (data.type === 'tool' && data.event) {
        addMessage('assistant', '🔧 ' + data.event.title + ': ' + data.event.summary);
      } else if (data.type === 'interrupted') {
        stopPlayback();
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
    if (micStream) {
      stopMic();
      talkBtn.classList.remove('active');
      return;
    }
    if (!ws || ws.readyState !== WebSocket.OPEN) {
      connect();
    }
    startMic().then(function() {
      talkBtn.classList.add('active');
    }).catch(function(err) {
      console.error('[MIC] Error:', err);
      addMessage('error', 'Microphone unavailable: ' + err.message);
    });
  });
  
  document.querySelectorAll('.chip[data-prompt]').forEach(function(chip) {
    chip.addEventListener('click', function() {
      chatInput.value = chip.dataset.prompt;
      sendTextMessage();
    });
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
