import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';

interface Message {
  id: string;
  text: string;
  sender: 'user' | 'bot';
  timestamp: Date;
}

const ChatPage: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<null | HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const sendMessage = async () => {
    if (input.trim() === '') return;

    const userMessage: Message = {
      id: Date.now().toString(),
      text: input,
      sender: 'user',
      timestamp: new Date(),
    };
    setMessages((prevMessages) => [...prevMessages, userMessage]);
    setInput('');
    setIsLoading(true);

    try {
      // Replace with your actual API endpoint for chat
      const response = await axios.post('http://localhost:8000/chat', { // Assuming a new /chat endpoint
        message: input,
        history: messages.filter(m => m.sender === 'bot').map(m => ({ role: 'assistant', content: m.text })),
        // You might need to send conversation history or other context
      });

      const botMessage: Message = {
        id: Date.now().toString() + '-bot',
        text: response.data.reply, // Adjust based on your API response structure
        sender: 'bot',
        timestamp: new Date(),
      };
      setMessages((prevMessages) => [...prevMessages, botMessage]);
    } catch (error) {
      console.error('Error fetching bot response:', error);
      const errorMessage: Message = {
        id: Date.now().toString() + '-error',
        text: 'Sorry, I encountered an error. Please try again.',
        sender: 'bot',
        timestamp: new Date(),
      };
      setMessages((prevMessages) => [...prevMessages, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (event: React.KeyboardEvent<HTMLInputElement>) => {
    if (event.key === 'Enter' && !isLoading) {
      sendMessage();
    }
  };

  return (
    <div style={styles.chatContainer}>
      <div style={styles.header}>
        <h2>AI Force Intelligent Support Agent</h2>
      </div>
      <div style={styles.messagesArea}>
        {messages.map((msg) => (
          <div
            key={msg.id}
            style={{
              ...styles.messageBubble,
              ...(msg.sender === 'user' ? styles.userMessage : styles.botMessage),
            }}
          >
            <p style={styles.messageText}>{msg.text}</p>
            <span style={styles.timestamp}>
              {msg.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
            </span>
          </div>
        ))}
        <div ref={messagesEndRef} />
      </div>
      <div style={styles.inputArea}>
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyPress={handleKeyPress}
          placeholder="What is artificial intelligence?"
          style={styles.inputField}
          disabled={isLoading}
        />
        <button onClick={sendMessage} style={styles.sendButton} disabled={isLoading}>
          {isLoading ? 'Sending...' : 'Send'}
        </button>
      </div>
    </div>
  );
};

const styles: { [key: string]: React.CSSProperties } = {
  chatContainer: {
    display: 'flex',
    flexDirection: 'column',
    height: '100vh',
    maxWidth: '800px',
    margin: '0 auto',
    border: '1px solid #ccc',
    borderRadius: '8px',
    boxShadow: '0 2px 10px rgba(0,0,0,0.1)',
    fontFamily: 'Arial, sans-serif',
    overflow: 'hidden',
    backgroundColor: '#f9f9f9',
  },
  header: {
    padding: '15px',
    backgroundColor: '#007bff',
    color: 'white',
    textAlign: 'center',
    borderBottom: '1px solid #0056b3',
  },
  messagesArea: {
    flexGrow: 1,
    padding: '20px',
    overflowY: 'auto',
    display: 'flex',
    flexDirection: 'column',
    gap: '10px',
    backgroundColor: '#fff',
  },
  messageBubble: {
    maxWidth: '70%',
    padding: '10px 15px',
    borderRadius: '18px',
    wordWrap: 'break-word',
    position: 'relative',
  },
  userMessage: {
    backgroundColor: '#007bff',
    color: 'white',
    alignSelf: 'flex-end',
    borderBottomRightRadius: '4px',
  },
  botMessage: {
    backgroundColor: '#e9ecef',
    color: '#333',
    alignSelf: 'flex-start',
    borderBottomLeftRadius: '4px',
  },
  messageText: {
    margin: 0,
    fontSize: '1rem',
  },
  timestamp: {
    display: 'block',
    fontSize: '0.75rem',
    color: 'rgba(0,0,0,0.5)',
    textAlign: 'right',
    marginTop: '5px',
  },
  inputArea: {
    display: 'flex',
    padding: '15px',
    borderTop: '1px solid #ccc',
    backgroundColor: '#f1f1f1',
  },
  inputField: {
    flexGrow: 1,
    padding: '10px 15px',
    border: '1px solid #ccc',
    borderRadius: '20px',
    fontSize: '1rem',
    marginRight: '10px',
  },
  sendButton: {
    padding: '10px 20px',
    backgroundColor: '#007bff',
    color: 'white',
    border: 'none',
    borderRadius: '20px',
    cursor: 'pointer',
    fontSize: '1rem',
  },
};

export default ChatPage;
