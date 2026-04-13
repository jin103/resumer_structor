// 简化版聊天应用 - 先测试基本功能
class ChatApp {
    constructor() {
        this.apiUrl = window.location.origin;
        this.messageInput = document.getElementById('messageInput');
        this.sendButton = document.getElementById('sendButton');
        this.clearButton = document.getElementById('clearButton');
        this.chatMessages = document.getElementById('chatMessages');
        this.statusElement = document.getElementById('status');
        this.loadingOverlay = document.getElementById('loadingOverlay');
        this.errorToast = document.getElementById('errorToast');
        this.errorMessage = document.getElementById('errorMessage');

        this.conversationHistory = [];
        this.isLoading = false;

        console.log('ChatApp initialized');
        this.init();
    }

    init() {
        console.log('Initializing...');
        this.bindEvents();
        this.checkServerStatus();
        this.loadConversationHistory();
    }

    bindEvents() {
        console.log('Binding events...');
        // 发送消息事件
        this.sendButton.addEventListener('click', () => {
            console.log('Send button clicked');
            this.sendMessage();
        });

        this.messageInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                console.log('Enter pressed');
                this.sendMessage();
            }
        });

        // 清空对话事件
        this.clearButton.addEventListener('click', () => this.clearConversation());

        // 输入框变化事件
        this.messageInput.addEventListener('input', () => {
            this.updateSendButton();
        });
    }

    async checkServerStatus() {
        console.log('Checking server status at:', this.apiUrl);
        try {
            const response = await fetch(`${this.apiUrl}/`, {
                method: 'GET',
                mode: 'cors', // 明确指定CORS模式
                cache: 'no-cache'
            });
            console.log('Server response status:', response.status);
            console.log('Server response ok:', response.ok);

            if (response.ok) {
                this.statusElement.textContent = '在线';
                this.statusElement.style.background = '#28a745';
                console.log('Server is online');
            } else {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
        } catch (error) {
            console.error('Server check failed:', error);
            this.statusElement.textContent = '离线';
            this.statusElement.style.background = '#dc3545';
            this.showError(`无法连接到服务器: ${error.message}`);
        }
    }

    updateSendButton() {
        const message = this.messageInput.value.trim();
        this.sendButton.disabled = !message || this.isLoading;
    }

    async sendMessage() {
        const message = this.messageInput.value.trim();
        if (!message || this.isLoading) {
            console.log('Message empty or loading, skipping');
            return;
        }

        console.log('Sending message:', message);

        // 添加用户消息到界面
        this.addMessage(message, 'user');
        this.messageInput.value = '';
        this.updateSendButton();

        // 显示加载状态
        this.setLoading(true);

        try {
            // 使用普通API
            console.log('Making API request...');
            const response = await fetch(`${this.apiUrl}/chat`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ message: message })
            });

            console.log('API response status:', response.status);

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const data = await response.json();
            console.log('API response data:', data);

            // 添加AI回复到界面
            this.addMessage(data.response, 'ai', data.trace_id);

            // 保存到本地历史
            this.saveToHistory(message, data.response, data.trace_id);

        } catch (error) {
            console.error('发送消息失败:', error);
            this.showError('发送消息失败，请稍后重试');
            // 重新添加输入框内容
            this.messageInput.value = message;
        } finally {
            this.setLoading(false);
            this.updateSendButton();
        }
    }

    addMessage(content, type, traceId = null) {
        console.log('Adding message:', type, content.substring(0, 50) + '...');

        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${type}-message`;

        const avatarDiv = document.createElement('div');
        avatarDiv.className = 'message-avatar';

        const avatarIcon = document.createElement('i');
        avatarIcon.className = type === 'user' ? 'fas fa-user' : 'fas fa-robot';
        avatarDiv.appendChild(avatarIcon);

        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';

        const textDiv = document.createElement('div');
        textDiv.className = 'message-text';
        textDiv.textContent = content;

        const timeDiv = document.createElement('div');
        timeDiv.className = 'message-time';
        timeDiv.textContent = this.formatTime(new Date());

        if (traceId && type === 'ai') {
            timeDiv.textContent += ` | ID: ${traceId}`;
        }

        contentDiv.appendChild(textDiv);
        contentDiv.appendChild(timeDiv);

        messageDiv.appendChild(avatarDiv);
        messageDiv.appendChild(contentDiv);

        this.chatMessages.appendChild(messageDiv);
        this.scrollToBottom();
    }

    formatTime(date) {
        return date.toLocaleTimeString('zh-CN', {
            hour: '2-digit',
            minute: '2-digit'
        });
    }

    scrollToBottom() {
        this.chatMessages.scrollTop = this.chatMessages.scrollHeight;
    }

    setLoading(loading) {
        this.isLoading = loading;
        this.loadingOverlay.style.display = loading ? 'flex' : 'none';
        this.sendButton.disabled = loading;
    }

    showError(message) {
        this.errorMessage.textContent = message;
        this.errorToast.style.display = 'flex';

        setTimeout(() => {
            this.errorToast.style.display = 'none';
        }, 5000);
    }

    clearConversation() {
        if (confirm('确定要清空所有对话记录吗？')) {
            this.chatMessages.innerHTML = '';
            this.conversationHistory = [];
            localStorage.removeItem('chatHistory');

            // 重新添加欢迎消息
            this.addMessage('对话已清空！我是小YO。', 'ai');
        }
    }

    saveToHistory(userMessage, aiResponse, traceId) {
        const historyItem = {
            userMessage,
            aiResponse,
            traceId,
            timestamp: new Date().toISOString()
        };

        this.conversationHistory.push(historyItem);
        localStorage.setItem('chatHistory', JSON.stringify(this.conversationHistory));
    }

    loadConversationHistory() {
        const history = localStorage.getItem('chatHistory');
        if (history) {
            try {
                this.conversationHistory = JSON.parse(history);
                // 重新显示历史消息
                this.conversationHistory.forEach(item => {
                    this.addMessage(item.userMessage, 'user');
                    this.addMessage(item.aiResponse, 'ai', item.traceId);
                });
            } catch (error) {
                console.error('加载历史记录失败:', error);
                localStorage.removeItem('chatHistory');
            }
        }
    }
}

// 初始化应用
document.addEventListener('DOMContentLoaded', () => {
    console.log('DOM loaded, initializing ChatApp...');
    new ChatApp();
});