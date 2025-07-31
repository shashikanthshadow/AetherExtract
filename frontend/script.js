document.addEventListener('DOMContentLoaded', () => {
    const pdfUpload = document.getElementById('pdfUpload'); 
    const uploadBtn = document.getElementById('uploadBtn'); 
    const resetBtn = document.getElementById('resetBtn');
    const uploadStatus = document.getElementById('uploadStatus');
    const questionInput = document.getElementById('questionInput');
    const sendBtn = document.getElementById('sendBtn');
    const chatDisplay = document.getElementById('chatDisplay');
    const initialMessage = document.getElementById('initialMessage');

    const BACKEND_URL = ''; 

    function addMessage(text, senderClass) {
        const messageDiv = document.createElement('div');
        messageDiv.classList.add('message', senderClass);

        if (senderClass === 'bot-message') {
            const answerParagraph = document.createElement('p');
            let sourcesContent = '';

            const sourceDelimiter = "\n\nSource(s):\n- ";
            const sourceIndex = text.indexOf(sourceDelimiter);

            if (sourceIndex !== -1) {
                let answerPart = text.substring(0, sourceIndex).trim();
                sourcesContent = text.substring(sourceIndex).trim();

                const answerPrefixMatch = answerPart.match(/^Answer:\s*(.*)/is);
                if (answerPrefixMatch && answerPrefixMatch[1]) {
                    answerParagraph.innerHTML = `<strong>Answer:</strong> ${answerPrefixMatch[1].trim()}`;
                } else {
                    answerParagraph.textContent = answerPart;
                }
            } else {
                const answerPrefixMatch = text.match(/^Answer:\s*(.*)/is);
                if (answerPrefixMatch && answerPrefixMatch[1]) {
                    answerParagraph.innerHTML = `<strong>Answer:</strong> ${answerPrefixMatch[1].trim()}`;
                } else {
                    answerParagraph.textContent = text;
                }
            }
            
            messageDiv.appendChild(answerParagraph);

            if (sourcesContent) {
                const sourcesText = document.createElement('pre');
                sourcesText.textContent = sourcesContent;
                messageDiv.appendChild(sourcesText);
            }

        } else {
            messageDiv.textContent = text;
        }
        
        chatDisplay.appendChild(messageDiv);
        chatDisplay.scrollTop = chatDisplay.scrollHeight;
    }

    function setChatEnabled(enabled) {
        questionInput.disabled = !enabled;
        sendBtn.disabled = !enabled;
    }

    function resetFrontendState() {
        chatDisplay.innerHTML = '';
        addMessage(`Welcome! Upload a document (PDF, DOCX, TXT) to begin asking questions about its content.`, 'system-message');
        uploadStatus.textContent = '';
        pdfUpload.value = '';
        questionInput.value = '';
        setChatEnabled(false);
    }

    setChatEnabled(false);

    pdfUpload.addEventListener('change', async (event) => {
        const file = event.target.files[0];
        if (!file) {
            uploadStatus.textContent = 'No file selected.';
            uploadStatus.className = 'status-message error';
            return;
        }

        uploadStatus.textContent = `Processing "${file.name}"...`;
        uploadStatus.className = 'status-message';
        sendBtn.disabled = true;
        questionInput.disabled = true;
        resetBtn.disabled = true;

        const formData = new FormData();
        formData.append('file', file);

        try {
            // MODIFIED: Use the new endpoint name /upload-document/
            const response = await fetch(`${BACKEND_URL}/upload-document/`, { 
                method: 'POST',
                body: formData,
            });

            const data = await response.json();

            if (response.ok) {
                uploadStatus.textContent = `"${file.name}" processed successfully!`;
                uploadStatus.className = 'status-message success';
                setChatEnabled(true);
                chatDisplay.innerHTML = '';
                addMessage(`Document "${file.name}" processed. You can now ask questions!`, 'system-message');
            } else {
                uploadStatus.textContent = `Error: ${data.detail || 'Unknown error'}`;
                uploadStatus.className = 'status-message error';
                setChatEnabled(false);
                addMessage(`Error processing document: ${data.detail || 'Please try again.'}`, 'system-message');
            }
        } catch (error) {
            uploadStatus.textContent = `Network error: ${error.message}. Is backend running?`;
            uploadStatus.className = 'status-message error';
            setChatEnabled(false);
            addMessage(`A network error occurred: ${error.message}. Ensure backend is running.`, 'system-message');
        } finally {
            sendBtn.disabled = false;
            questionInput.disabled = false;
            resetBtn.disabled = false;
        }
    });

    resetBtn.addEventListener('click', async () => {
        if (!confirm('Are you sure you want to reset the chatbot? This will clear the conversation and remove the loaded document from memory.')) {
            return;
        }

        uploadStatus.textContent = 'Resetting...';
        uploadStatus.className = 'status-message';
        sendBtn.disabled = true;
        questionInput.disabled = true;
        resetBtn.disabled = true;

        try {
            const response = await fetch(`${BACKEND_URL}/reset-chatbot/`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({})
            });

            const data = await response.json();

            if (response.ok) {
                uploadStatus.textContent = `Chatbot reset successfully.`;
                uploadStatus.className = 'status-message success';
                resetFrontendState();
            } else {
                uploadStatus.textContent = `Error: ${data.detail || 'Unknown error'}`;
                uploadStatus.className = 'status-message error';
                addMessage(`Error resetting chatbot: ${data.detail || 'Please try again.'}`, 'system-message');
            }
        } catch (error) {
            uploadStatus.textContent = `Network error during reset: ${error.message}.`;
            uploadStatus.className = 'status-message error';
            addMessage(`A network error occurred during reset: ${error.message}.`, 'system-message');
        } finally {
            sendBtn.disabled = false;
            questionInput.disabled = false;
            resetBtn.disabled = false;
        }
    });

    sendBtn.addEventListener('click', async () => {
        const question = questionInput.value.trim();
        if (!question) {
            alert('Please enter a question.');
            return;
        }

        addMessage(question, 'user-message');
        questionInput.value = '';
        sendBtn.disabled = true;
        questionInput.disabled = true;
        resetBtn.disabled = true;

        try {
            const response = await fetch(`${BACKEND_URL}/chat/`, { 
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ query: question }),
            });

            const data = await response.json();

            if (response.ok) {
                let botMessage = data.answer;
                if (data.sources && data.sources.length > 0) {
                    botMessage += "\n\nSource(s):\n- " + data.sources[0].trim(); 
                }
                addMessage(botMessage, 'bot-message');
            } else {
                addMessage(`Error: ${data.detail || 'Unknown error'}. Please try your question again or re-upload the document.`, 'system-message');
            }
        } catch (error) {
            addMessage(`Network error during chat: ${error.message}. Is the backend server running?`, 'system-message');
        } finally {
            sendBtn.disabled = false;
            questionInput.disabled = false;
            resetBtn.disabled = false;
        }
    });

    questionInput.addEventListener('keypress', (event) => {
        if (event.key === 'Enter' && !sendBtn.disabled) {
            sendBtn.click();
        }
    });
});