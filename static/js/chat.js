// 聊天应用主逻辑
class ChatApp {
    constructor() {
        this.apiUrl = window.location.origin;
        this.messageInput = document.getElementById('messageInput');
        this.sendButton = document.getElementById('sendButton');
        this.clearButton = document.getElementById('clearButton');
        this.chatMessages = document.getElementById('chatMessages');
        this.statusElement = document.getElementById('status');
        this.errorToast = document.getElementById('errorToast');
        this.errorMessage = document.getElementById('errorMessage');
        this.fileInput = document.getElementById('fileInput');
        this.inputWrapper = document.getElementById('inputWrapper');

        this.conversationHistory = [];
        this.isLoading = false;
        this.draggedFile = null;
        this.sessionId = this.generateSessionId();

        this.init();
    }

    generateSessionId() {
        // 生成一个简单的会话ID，如果localStorage中有则使用，否则生成新的
        let sessionId = localStorage.getItem('chatSessionId');
        if (!sessionId) {
            sessionId = 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
            localStorage.setItem('chatSessionId', sessionId);
        }
        return sessionId;
    }

    init() {
        this.bindEvents();
        this.checkServerStatus();
        this.loadConversationHistory();
    }

    bindEvents() {
        // 发送消息事件
        this.sendButton.addEventListener('click', () => this.sendMessage());
        this.messageInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });

        // 清空对话事件
        this.clearButton.addEventListener('click', () => this.clearConversation());

        // 输入框变化事件
        this.messageInput.addEventListener('input', () => {
            this.updateSendButton();
        });

        // 拖拽事件
        this.inputWrapper.addEventListener('dragover', (e) => this.handleDragOver(e));
        this.inputWrapper.addEventListener('dragleave', (e) => this.handleDragLeave(e));
        this.inputWrapper.addEventListener('drop', (e) => this.handleDrop(e));

        // 文件输入变化
        this.fileInput.addEventListener('change', (e) => this.handleFileSelect(e));
    }

    async checkServerStatus() {
        console.log('Checking server status at:', this.apiUrl);
        try {
            const response = await fetch(`${this.apiUrl}/`, {
                method: 'GET',
                mode: 'cors',
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
        const hasContent = message || this.draggedFile;
        this.sendButton.disabled = !hasContent || this.isLoading;
    }

    handleDragOver(e) {
        e.preventDefault();
        e.stopPropagation();
        this.inputWrapper.classList.add('drag-over');
    }

    handleDragLeave(e) {
        e.preventDefault();
        e.stopPropagation();
        this.inputWrapper.classList.remove('drag-over');
    }

    handleDrop(e) {
        e.preventDefault();
        e.stopPropagation();
        this.inputWrapper.classList.remove('drag-over');

        const files = e.dataTransfer.files;
        if (files.length > 0) {
            const file = files[0];
            if (this.isValidFile(file)) {
                this.draggedFile = file;
                this.messageInput.placeholder = `已选择文件: ${file.name} (拖拽或点击发送)`;
                this.updateSendButton();
            } else {
                this.showError('仅支持 PDF 或 Word (.docx) 文件');
            }
        }
    }

    handleFileSelect(e) {
        const file = e.target.files[0];
        if (file && this.isValidFile(file)) {
            this.draggedFile = file;
            this.messageInput.placeholder = `已选择文件: ${file.name} (拖拽或点击发送)`;
            this.updateSendButton();
        }
    }

    isValidFile(file) {
        const allowedExtensions = ['.pdf', '.docx'];
        const filename = file.name.toLowerCase();
        return allowedExtensions.some(ext => filename.endsWith(ext));
    }

    displayAnalysisResult(result) {
        if (!result || !result.analysis) {
            this.addMessage('简历解析结果无效，请稍后重试。', 'ai');
            return;
        }

        const analysis = result.analysis;
        let summary = '📄 **简历分析结果**\n\n';
        summary += `👤 **姓名：** ${analysis.basic_info?.name || '未提及'}\n`;
        summary += `📞 **电话：** ${analysis.basic_info?.phone || '未提及'}\n`;
        summary += `📧 **邮箱：** ${analysis.basic_info?.email || '未提及'}\n`;
        summary += `🎓 **学历：** ${analysis.basic_info?.education || '未提及'}\n`;
        summary += `💼 **工作经验：** ${analysis.basic_info?.experience || '未提及'}\n`;
        summary += `🏢 **当前职位：** ${analysis.basic_info?.current_position || '未提及'}\n\n`;

        if (Array.isArray(analysis.refinements) && analysis.refinements.length > 0) {
            summary += '✨ **亮点提炼：**\n';
            analysis.refinements.forEach((item, index) => {
                summary += `${index + 1}. ${item}\n`;
            });
        }

        this.addMessage(summary, 'ai');
    }

    async sendMessage() {
        const message = this.messageInput.value.trim();
        const hasFile = this.draggedFile !== null;
        const hasMessage = message.length > 0;

        if ((!hasMessage && !hasFile) || this.isLoading) return;

        // 添加用户消息或文件到界面
        if (hasFile) {
            this.addMessage(`📎 上传简历: ${this.draggedFile.name}`, 'user');
        } else {
            this.addMessage(message, 'user');
        }

        // 重置输入
        this.messageInput.value = '';
        this.messageInput.placeholder = '输入您的问题，或拖拽简历文件到此处...';
        const fileToSend = this.draggedFile;
        this.draggedFile = null;
        this.updateSendButton();

        // 显示加载状态
        this.setLoading(true);

        try {
            let response;
            if (hasFile) {
                // 发送文件到 /chat
                const formData = new FormData();
                formData.append('file', fileToSend);
                formData.append('session_id', this.sessionId);

                response = await fetch(`${this.apiUrl}/chat`, {
                    method: 'POST',
                    body: formData,
                });

                if (!response.ok) {
                    const errorText = await response.text();
                    throw new Error(`上传失败: ${response.status} ${response.statusText} ${errorText}`);
                }

                const result = await response.json();
                this.displayAnalysisResult(result);
            } else {
                // 发送消息到 /stream_chat
                response = await fetch(`${this.apiUrl}/stream_chat`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ message: message, session_id: this.sessionId })
                });

                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }

                // 处理Server-Sent Events
                const reader = response.body.getReader();
                const decoder = new TextDecoder();
                let traceId = null;
                let aiMessage = '';
                let aiMessageElement = null;

                while (true) {
                    const { done, value } = await reader.read();
                    if (done) break;

                    const text = decoder.decode(value, { stream: true });
                    const lines = text.split('\n');

                    for (const line of lines) {
                        if (line.startsWith('data: ')) {
                            try {
                                const data = JSON.parse(line.slice(6));
                                
                                if (data.type === 'trace_id') {
                                    traceId = data.data;
                                } else if (data.type === 'chunk') {
                                    // 首次创建消息元素
                                    if (!aiMessageElement) {
                                        const messageDiv = document.createElement('div');
                                        messageDiv.className = 'message ai-message';
                                        
                                        const avatarDiv = document.createElement('div');
                                        avatarDiv.className = 'message-avatar';
                                        const avatarIcon = document.createElement('i');
                                        avatarIcon.className = 'fas fa-robot';
                                        avatarDiv.appendChild(avatarIcon);
                                        
                                        const contentDiv = document.createElement('div');
                                        contentDiv.className = 'message-content';
                                        
                                        const textDiv = document.createElement('div');
                                        textDiv.className = 'message-text';
                                        
                                        const timeDiv = document.createElement('div');
                                        timeDiv.className = 'message-time';
                                        
                                        contentDiv.appendChild(textDiv);
                                        contentDiv.appendChild(timeDiv);
                                        messageDiv.appendChild(avatarDiv);
                                        messageDiv.appendChild(contentDiv);
                                        
                                        this.chatMessages.appendChild(messageDiv);
                                        aiMessageElement = textDiv;
                                        
                                        // 添加打字机指示器
                                        this.addTypingIndicator(textDiv);
                                    }
                                    
                                    // 添加文本块
                                    aiMessage += data.data;
                                    aiMessageElement.textContent = aiMessage;
                                    this.scrollToBottom();
                                } else if (data.type === 'done') {
                                    // 消息完成，更新时间戳
                                    if (aiMessageElement) {
                                        const timeDiv = aiMessageElement.parentElement.querySelector('.message-time');
                                        timeDiv.textContent = this.formatTime(new Date());
                                        if (traceId) {
                                            timeDiv.textContent += ` | ID: ${traceId}`;
                                        }
                                    }
                                    // 保存到历史
                                    this.saveToHistory(message, aiMessage, traceId);
                                } else if (data.type === 'error') {
                                    console.error('流式处理错误:', data.data);
                                    this.showError('处理消息出错：' + data.data);
                                }
                            } catch (e) {
                                console.error('解析SSE数据失败:', e);
                            }
                        }
                    }
                }
            }
        } catch (error) {
            console.error('发送失败:', error);
            this.showError(hasFile ? '简历上传失败，请检查服务器是否已启动' : '发送消息失败，请稍后重试');
            // 如果是消息失败，重新添加输入框内容
            if (!hasFile) {
                this.messageInput.value = message;
            }
        } finally {
            this.setLoading(false);
            this.updateSendButton();
        }
    }

    addMessage(content, type, traceId = null) {
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
        this.sendButton.disabled = loading;
    }

    addTypingIndicator(textElement) {
        // 创建打字机指示器
        const typingContainer = document.createElement('div');
        typingContainer.className = 'typing-container';
        typingContainer.style.display = 'inline-block';
        typingContainer.style.marginLeft = '0.25rem';
        
        for (let i = 0; i < 3; i++) {
            const dot = document.createElement('span');
            dot.className = 'typing-indicator';
            typingContainer.appendChild(dot);
        }
        
        textElement.appendChild(typingContainer);
        
        // 1秒后移除打字机指示器
        setTimeout(() => {
            if (typingContainer.parentNode) {
                typingContainer.remove();
            }
        }, 1000);
    }

    clearConversation() {
        if (confirm('确定要清空所有对话记录吗？')) {
            this.chatMessages.innerHTML = '';
            this.conversationHistory = [];
            localStorage.removeItem('chatHistory');
            // 生成新的会话ID
            this.sessionId = this.generateSessionId();
            localStorage.setItem('chatSessionId', this.sessionId);

            // 重新添加欢迎消息
            this.addMessage('对话已清空！我是基于DeepSeek-R1-Distill-Qwen-7B模型的AI助手。', 'ai');
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
    new ChatApp();
});