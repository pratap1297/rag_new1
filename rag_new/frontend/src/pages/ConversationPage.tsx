import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

interface Message {
  id: string;
  text: string;
  sender: 'user' | 'bot';
  timestamp: Date;
  isStreaming?: boolean;
  sources?: any[];
  suggestions?: string[];
  hasTable?: boolean;
}

interface Thread {
  id: string;
  name: string;
  timestamp: Date;
  messageCount: number;
  messages?: Message[];
  createdAt?: Date;
  lastUpdated?: Date;
}

const ConversationPage: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [threadId, setThreadId] = useState<string | null>(null);
  const [enableStreaming, setEnableStreaming] = useState<boolean>(true);
  const [showSources, setShowSources] = useState<boolean>(true);
  const [showSuggestions, setShowSuggestions] = useState<boolean>(true);
  const [showTableView, setShowTableView] = useState<boolean>(false);
  const [threads, setThreads] = useState<Thread[]>([]);
  const [showThreadHistory, setShowThreadHistory] = useState<boolean>(false);
  const [currentThreadName, setCurrentThreadName] = useState<string>('');
  const [showHelpPanel, setShowHelpPanel] = useState<boolean>(false);
  const messagesEndRef = useRef<null | HTMLDivElement>(null);
  const eventSourceRef = useRef<EventSource | null>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
    
    // Auto-update thread when messages change
    if (threadId && messages.length > 0) {
      const existingThreads = JSON.parse(localStorage.getItem('conversation-threads') || '[]');
      const threadIndex = existingThreads.findIndex((t: Thread) => t.id === threadId);
      
      if (threadIndex !== -1) {
        existingThreads[threadIndex] = {
          ...existingThreads[threadIndex],
          messageCount: messages.length,
          lastUpdated: new Date()
        };
        localStorage.setItem('conversation-threads', JSON.stringify(existingThreads));
        localStorage.setItem(`thread-${threadId}`, JSON.stringify(messages));
        setThreads(existingThreads);
      }
    }
  }, [messages, threadId]);

  // Load threads from localStorage
  useEffect(() => {
    const savedThreads = localStorage.getItem('conversation-threads');
    if (savedThreads) {
      const parsedThreads = JSON.parse(savedThreads).map((thread: any) => ({
        ...thread,
        timestamp: new Date(thread.timestamp)
      }));
      setThreads(parsedThreads);
    }
  }, []);

  // Save current thread
  const saveCurrentThread = () => {
    if (!threadId || messages.length === 0) return;
    
    const threadName = currentThreadName || `Thread ${new Date().toLocaleDateString()}`;
    const newThread: Thread = {
      id: threadId,
      name: threadName,
      timestamp: new Date(),
      messageCount: messages.length
    };
    
    const updatedThreads = threads.filter(t => t.id !== threadId);
    updatedThreads.unshift(newThread);
    
    setThreads(updatedThreads);
    localStorage.setItem('conversation-threads', JSON.stringify(updatedThreads));
    localStorage.setItem(`thread-${threadId}`, JSON.stringify(messages));
    setCurrentThreadName(threadName);
  };

  // Load thread from history
  const loadThread = (thread: Thread) => {
    const savedMessages = localStorage.getItem(`thread-${thread.id}`);
    if (savedMessages) {
      const parsedMessages = JSON.parse(savedMessages).map((msg: any) => ({
        ...msg,
        timestamp: new Date(msg.timestamp)
      }));
      setMessages(parsedMessages);
      setThreadId(thread.id);
      setCurrentThreadName(thread.name);
      setShowThreadHistory(false);
    }
  };

  // Start new thread
  const startNewThread = async () => {
    setIsLoading(true);
    try {
      const response = await axios.post('http://localhost:8000/api/conversation/start');
      const newThreadId = response.data.thread_id;
      setThreadId(newThreadId);
      
      // Generate default thread name with timestamp
      const now = new Date();
      const defaultName = `Conversation ${now.toLocaleDateString()} ${now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}`;
      setCurrentThreadName(defaultName);
      
      const welcomeMessage: Message = {
        id: Date.now().toString() + '-bot',
        text: '# 🤖 Welcome to AI Force Intelligent Support Agent\n\nHello! I\'m ready to help you with your questions. Use the controls above to customize your experience, or click the ℹ️ button for more details about my capabilities.',
        sender: 'bot',
        timestamp: new Date(),
      };
      setMessages([welcomeMessage]);

      // Auto-save the new thread
      const newThread: Thread = {
        id: newThreadId,
        name: defaultName,
        timestamp: now,
        messageCount: 1,
        messages: [welcomeMessage],
        createdAt: now,
        lastUpdated: now
      };

      const existingThreads = JSON.parse(localStorage.getItem('conversation-threads') || '[]');
      const updatedThreads = [newThread, ...existingThreads];
      localStorage.setItem('conversation-threads', JSON.stringify(updatedThreads));
      localStorage.setItem(`thread-${newThreadId}`, JSON.stringify([welcomeMessage]));
      setThreads(updatedThreads);

    } catch (error) {
      console.error('Error starting conversation:', error);
      const errorMessage: Message = {
        id: Date.now().toString() + '-error',
        text: '⚠️ Failed to start new thread. Please ensure the backend server is running.',
        sender: 'bot',
        timestamp: new Date(),
      };
      setMessages([errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  // Function to start a conversation
  const startConversation = async () => {
    if (!threadId) {
      await startNewThread();
    }
  };

  useEffect(() => {
    startConversation();
    
    return () => {
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
      }
    };
  }, []);

  const sendMessageStreaming = (userMessage: Message) => {
    if (!threadId) return;
    
    const botPlaceholder: Message = {
      id: Date.now().toString() + '-bot-streaming',
      text: '',
      sender: 'bot',
      timestamp: new Date(),
      isStreaming: true,
    };
    
    setMessages(prev => [...prev, botPlaceholder]);
    
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
    }
    
    fetch('http://localhost:8000/api/conversation/message/stream', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'text/event-stream',
      },
      body: JSON.stringify({
        thread_id: threadId,
        message: userMessage.text,
      }),
    })
    .then(response => {
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const reader = response.body?.getReader();
      const decoder = new TextDecoder();
      
      if (!reader) {
        throw new Error('No response body reader available');
      }
      
      let streamedText = '';
      let sources: any[] = [];
      let suggestions: string[] = [];
      let hasTable = false;
      
      const readStream = async () => {
        try {
          while (true) {
            const { done, value } = await reader.read();
            
            if (done) {
              break;
            }
            
            const chunk = decoder.decode(value);
            const lines = chunk.split('\n');
            
            for (const line of lines) {
              if (line.startsWith('data: ')) {
                try {
                  const data = JSON.parse(line.slice(6));
                  
                  if (data.type === 'status') {
                    console.log('Status:', data.message);
                  } else if (data.type === 'metadata') {
                    console.log('Metadata:', data);
                  } else if (data.type === 'content') {
                    streamedText += data.chunk;
                    
                    // Check for table content
                    if (streamedText.includes('|') && streamedText.includes('---')) {
                      hasTable = true;
                    }
                    
                    setMessages(prevMessages => {
                      const updatedMessages = [...prevMessages];
                      const streamingMessageIndex = updatedMessages.findIndex(
                        msg => msg.id === botPlaceholder.id
                      );
                      
                      if (streamingMessageIndex !== -1) {
                        updatedMessages[streamingMessageIndex] = {
                          ...updatedMessages[streamingMessageIndex],
                          text: streamedText,
                          hasTable: hasTable,
                        };
                      }
                      
                      return updatedMessages;
                    });
                  } else if (data.type === 'suggestions') {
                    suggestions = data.suggested_questions || [];
                  } else if (data.type === 'sources') {
                    sources = data.sources || [];
                  } else if (data.type === 'complete') {
                    setMessages(prevMessages => {
                      const updatedMessages = [...prevMessages];
                      const streamingMessageIndex = updatedMessages.findIndex(
                        msg => msg.id === botPlaceholder.id
                      );
                      
                      if (streamingMessageIndex !== -1) {
                        updatedMessages[streamingMessageIndex] = {
                          ...updatedMessages[streamingMessageIndex],
                          text: streamedText,
                          sources: sources,
                          suggestions: suggestions,
                          isStreaming: false,
                          hasTable: hasTable,
                        };
                      }
                      
                      return updatedMessages;
                    });
                    break;
                  }
                } catch (parseError) {
                  console.error('Error parsing SSE data:', parseError);
                }
              }
            }
          }
        } catch (streamError) {
          console.error('Error reading stream:', streamError);
          throw streamError;
        }
      };
      
      return readStream();
    })
    .catch(error => {
      console.error('Streaming error, falling back to regular API:', error);
      
      setMessages(prevMessages => 
        prevMessages.filter(msg => msg.id !== botPlaceholder.id)
      );
      
      sendMessageRegular(userMessage);
    });
  };

  const sendMessageRegular = async (userMessage: Message) => {
    if (!threadId) return;
    
    setIsLoading(true);
    
    try {
      const response = await axios.post('http://localhost:8000/api/conversation/message', {
        thread_id: threadId,
        message: userMessage.text,
      });
      
      let responseText = 'No response from server';
      let sources: any[] = [];
      let suggestions: string[] = [];
      let hasTable = false;
      
      if (response.data) {
        if (typeof response.data === 'string') {
          responseText = response.data;
        } else if (response.data.response) {
          responseText = response.data.response;
          sources = response.data.sources || [];
          suggestions = response.data.suggested_questions || [];
        } else if (response.data.text) {
          responseText = response.data.text;
          sources = response.data.sources || [];
          suggestions = response.data.suggested_questions || [];
        } else if (response.data.message) {
          responseText = response.data.message;
          sources = response.data.sources || [];
          suggestions = response.data.suggested_questions || [];
        } else {
          responseText = JSON.stringify(response.data);
        }
        
        // Check for table content
        if (responseText.includes('|') && responseText.includes('---')) {
          hasTable = true;
        }
      }

      const botMessage: Message = {
        id: Date.now().toString() + '-bot',
        text: responseText,
        sender: 'bot',
        timestamp: new Date(),
        sources,
        suggestions,
        hasTable,
      };
      
      setMessages(prev => [...prev, botMessage]);
    } catch (error) {
      console.error('Error sending message:', error);
      const errorMessage: Message = {
        id: Date.now().toString() + '-error',
        text: '❌ Sorry, I encountered an error. Please try again.',
        sender: 'bot',
        timestamp: new Date(),
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const sendMessage = async () => {
    if (input.trim() === '' || !threadId) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      text: input,
      sender: 'user',
      timestamp: new Date(),
    };
    
    setMessages(prev => [...prev, userMessage]);
    setInput('');
    
    if (enableStreaming) {
      sendMessageStreaming(userMessage);
    } else {
      sendMessageRegular(userMessage);
    }
  };

  const handleKeyPress = (event: React.KeyboardEvent<HTMLInputElement>) => {
    if (event.key === 'Enter' && !isLoading) {
      sendMessage();
    }
  };

  const handleSuggestionClick = (suggestion: string) => {
    setInput(suggestion);
  };

  // Render table content
  const renderTableContent = (text: string) => {
    if (!showTableView || !text.includes('|')) {
      return <ReactMarkdown remarkPlugins={[remarkGfm]}>{text}</ReactMarkdown>;
    }

    const lines = text.split('\n');
    const tableLines = [];
    const nonTableLines = [];
    let inTable = false;

    for (const line of lines) {
      if (line.includes('|') && (line.includes('---') || inTable)) {
        inTable = true;
        tableLines.push(line);
      } else if (inTable && line.trim() === '') {
        inTable = false;
        nonTableLines.push(line);
      } else if (inTable) {
        tableLines.push(line);
      } else {
        nonTableLines.push(line);
      }
    }

    if (tableLines.length === 0) {
      return <ReactMarkdown remarkPlugins={[remarkGfm]}>{text}</ReactMarkdown>;
    }

    const tableText = tableLines.join('\n');
    const otherText = nonTableLines.join('\n');

    return (
      <div>
        {otherText && <ReactMarkdown remarkPlugins={[remarkGfm]}>{otherText}</ReactMarkdown>}
        <div style={styles.tableContainer}>
          <ReactMarkdown remarkPlugins={[remarkGfm]}>{tableText}</ReactMarkdown>
        </div>
      </div>
    );
  };

  return (
    <div style={styles.container}>
      {/* Header */}
      <header style={styles.header}>
        <div style={styles.headerContent}>
          <div style={styles.headerLeft}>
            <div style={styles.avatar}>
              <span style={styles.avatarIcon}>🤖</span>
            </div>
            <div>
              <h1 style={styles.title}>AI Force Intelligent Support Agent</h1>
              <p style={styles.subtitle}>
                {currentThreadName || 'Advanced RAG Technology'} 
                {threadId && <span style={styles.threadId}>• {threadId.slice(-8)}</span>}
              </p>
            </div>
          </div>
          
          <div style={styles.controlsContainer}>
            <div style={styles.control}>
              <label style={styles.controlLabel}>
                <input
                  type="checkbox"
                  checked={enableStreaming}
                  onChange={(e) => setEnableStreaming(e.target.checked)}
                  style={styles.checkbox}
                />
                <span style={styles.controlIcon}>🌊</span>
                <span style={styles.controlText}>Stream</span>
              </label>
            </div>
            <div style={styles.control}>
              <label style={styles.controlLabel}>
                <input
                  type="checkbox"
                  checked={showSources}
                  onChange={(e) => setShowSources(e.target.checked)}
                  style={styles.checkbox}
                />
                <span style={styles.controlIcon}>📚</span>
                <span style={styles.controlText}>Sources</span>
              </label>
            </div>
            <div style={styles.control}>
              <label style={styles.controlLabel}>
                <input
                  type="checkbox"
                  checked={showSuggestions}
                  onChange={(e) => setShowSuggestions(e.target.checked)}
                  style={styles.checkbox}
                />
                <span style={styles.controlIcon}>💡</span>
                <span style={styles.controlText}>Suggest</span>
              </label>
            </div>
            <div style={styles.control}>
              <label style={styles.controlLabel}>
                <input
                  type="checkbox"
                  checked={showTableView}
                  onChange={(e) => setShowTableView(e.target.checked)}
                  style={styles.checkbox}
                />
                <span style={styles.controlIcon}>📊</span>
                <span style={styles.controlText}>Tables</span>
              </label>
            </div>
            <div style={styles.helpControl}>
              <button onClick={() => setShowHelpPanel(!showHelpPanel)} style={styles.helpButton}>
                <span style={styles.helpIcon}>ℹ️</span>
                <span style={styles.helpText}>Help</span>
              </button>
            </div>
          </div>
        </div>
        
        {/* Thread Management Bar */}
        <div style={styles.threadBar}>
          <div style={styles.threadBarContent}>
            <div style={styles.threadActions}>
              <button onClick={startNewThread} style={styles.threadButton} disabled={isLoading}>
                <span style={styles.threadButtonIcon}>🆕</span>
                <span style={styles.threadButtonText}>New Thread</span>
              </button>
              <button onClick={saveCurrentThread} style={styles.threadButton} disabled={!threadId || messages.length === 0}>
                <span style={styles.threadButtonIcon}>💾</span>
                <span style={styles.threadButtonText}>Save</span>
              </button>
              <button onClick={() => setShowThreadHistory(!showThreadHistory)} style={styles.threadButton}>
                <span style={styles.threadButtonIcon}>📜</span>
                <span style={styles.threadButtonText}>History</span>
              </button>
            </div>
            
            {currentThreadName && (
              <input
                type="text"
                value={currentThreadName}
                onChange={(e) => setCurrentThreadName(e.target.value)}
                placeholder="Thread name..."
                style={styles.threadNameInput}
              />
            )}
          </div>
        </div>
      </header>

      {/* Help Panel */}
      {showHelpPanel && (
        <div style={styles.helpPanel}>
          <div style={styles.helpContent}>
            <div style={styles.helpHeader}>
              <span style={styles.helpTitle}>🤖 Advanced AI Conversation</span>
              <button onClick={() => setShowHelpPanel(false)} style={styles.closeButton}>✕</button>
            </div>
            <div style={styles.helpBody}>
              <p style={styles.helpDescription}>I'm your intelligent assistant with enhanced capabilities:</p>
              <div style={styles.featureList}>
                <div style={styles.featureItem}>
                  <span style={styles.featureIcon}>📚</span>
                  <div style={styles.featureText}>
                    <strong>Knowledge Search</strong> - Access your document database
                  </div>
                </div>
                <div style={styles.featureItem}>
                  <span style={styles.featureIcon}>🔍</span>
                  <div style={styles.featureText}>
                    <strong>Deep Analysis</strong> - Detailed insights with sources
                  </div>
                </div>
                <div style={styles.featureItem}>
                  <span style={styles.featureIcon}>📊</span>
                  <div style={styles.featureText}>
                    <strong>Table Display</strong> - Structured data visualization
                  </div>
                </div>
                <div style={styles.featureItem}>
                  <span style={styles.featureIcon}>💾</span>
                  <div style={styles.featureText}>
                    <strong>Thread Management</strong> - Save and organize conversations
                  </div>
                </div>
                <div style={styles.featureItem}>
                  <span style={styles.featureIcon}>⚡</span>
                  <div style={styles.featureText}>
                    <strong>Real-time Streaming</strong> - Live response generation
                  </div>
                </div>
              </div>
              <p style={styles.helpFooter}>Use the controls to customize your experience. How can I assist you?</p>
            </div>
          </div>
        </div>
      )}

      {/* Thread History Panel */}
      {showThreadHistory && (
        <div style={styles.threadHistoryPanel}>
          <div style={styles.threadHistoryContent}>
            <div style={styles.threadHistoryHeader}>
              <span style={styles.threadHistoryTitle}>Thread History</span>
              <button onClick={() => setShowThreadHistory(false)} style={styles.closeButton}>✕</button>
            </div>
            <div style={styles.threadList}>
              {threads.length === 0 ? (
                <div style={styles.emptyThreads}>No saved threads yet</div>
              ) : (
                threads.map((thread) => (
                  <div key={thread.id} style={styles.threadItem} onClick={() => loadThread(thread)}>
                    <div style={styles.threadItemHeader}>
                      <span style={styles.threadItemName}>{thread.name}</span>
                      <span style={styles.threadItemTime}>{thread.timestamp.toLocaleDateString()}</span>
                    </div>
                    <div style={styles.threadItemInfo}>
                      <span style={styles.threadItemMessages}>{thread.messageCount} messages</span>
                      <span style={styles.threadItemId}>ID: {thread.id.slice(-8)}</span>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      )}

      {/* Messages Area */}
      <main style={styles.messagesArea}>
        <div style={styles.messagesContainer}>
          {messages.map((msg) => (
            <div key={msg.id} style={styles.messageWrapper}>
              <div style={{
                ...styles.messageRow,
                ...(msg.sender === 'user' ? styles.userRow : styles.botRow)
              }}>
                {msg.sender === 'bot' && (
                  <div style={styles.messageAvatar}>
                    <div style={styles.botAvatar}>🤖</div>
                  </div>
                )}
                
                <div style={{
                  ...styles.messageCard,
                  ...(msg.sender === 'user' ? styles.userCard : styles.botCard)
                }}>
                  <div style={styles.messageContent}>
                    {msg.hasTable && showTableView ? renderTableContent(msg.text) : (
                      <ReactMarkdown remarkPlugins={[remarkGfm]}>{msg.text}</ReactMarkdown>
                    )}
                    {msg.isStreaming && (
                      <div style={styles.streamingIndicator}>
                        <div style={styles.streamingDots}>
                          <span>●</span>
                          <span>●</span>
                          <span>●</span>
                        </div>
                        <span style={styles.streamingText}>Streaming response...</span>
                      </div>
                    )}
                  </div>
                  <div style={styles.messageTime}>
                    {msg.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                    {msg.hasTable && <span style={styles.tableIndicator}>📊</span>}
                  </div>
                </div>
                
                {msg.sender === 'user' && (
                  <div style={styles.messageAvatar}>
                    <div style={styles.userAvatar}>👤</div>
                  </div>
                )}
              </div>
              
              {/* Suggestions */}
              {showSuggestions && msg.suggestions && msg.suggestions.length > 0 && (
                <div style={styles.suggestionsWrapper}>
                  <div style={styles.suggestionsCard}>
                    <div style={styles.suggestionsHeader}>
                      <span style={styles.suggestionsIcon}>💡</span>
                      <span style={styles.suggestionsTitle}>Suggested Questions</span>
                    </div>
                    <div style={styles.suggestionsGrid}>
                      {msg.suggestions.map((suggestion, index) => (
                        <button
                          key={index}
                          onClick={() => handleSuggestionClick(suggestion)}
                          style={styles.suggestionButton}
                          disabled={isLoading}
                        >
                          <span style={styles.suggestionIcon}>❓</span>
                          <span style={styles.suggestionText}>{suggestion}</span>
                        </button>
                      ))}
                    </div>
                  </div>
                </div>
              )}
              
              {/* Sources */}
              {showSources && msg.sources && msg.sources.length > 0 && (
                <div style={styles.sourcesWrapper}>
                  <div style={styles.sourcesCard}>
                    <div style={styles.sourcesHeader}>
                      <span style={styles.sourcesIcon}>📚</span>
                      <span style={styles.sourcesTitle}>Sources ({msg.sources.length})</span>
                    </div>
                    <div style={styles.sourcesGrid}>
                      {msg.sources.slice(0, 3).map((source, index) => (
                        <div key={index} style={styles.sourceItem}>
                          <div style={styles.sourceHeader}>
                            <span style={styles.sourceIcon}>📄</span>
                            <span style={styles.sourceName}>
                              {source.source || source.title || `Source ${index + 1}`}
                            </span>
                          </div>
                          {source.score && (
                            <div style={styles.sourceScore}>
                              <div style={styles.scoreBar}>
                                <div 
                                  style={{
                                    ...styles.scoreBarFill,
                                    width: `${source.score * 100}%`
                                  }}
                                />
                              </div>
                              <span style={styles.scoreText}>
                                {(source.score * 100).toFixed(0)}% match
                              </span>
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              )}
            </div>
          ))}
          
          {isLoading && (
            <div style={styles.messageWrapper}>
              <div style={styles.botRow}>
                <div style={styles.messageAvatar}>
                  <div style={styles.botAvatar}>🤖</div>
                </div>
                <div style={styles.loadingCard}>
                  <div style={styles.loadingContent}>
                    <div style={styles.loadingDots}>
                      <span>●</span>
                      <span>●</span>
                      <span>●</span>
                    </div>
                    <span style={styles.loadingText}>Thinking...</span>
                  </div>
                </div>
              </div>
            </div>
          )}
          
          <div ref={messagesEndRef} />
        </div>
      </main>

      {/* Input Area */}
      <footer style={styles.inputArea}>
        <div style={styles.inputContainer}>
          <div style={styles.inputWrapper}>
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="What is artificial intelligence?"
              style={styles.inputField}
              disabled={isLoading || !threadId}
            />
            <button 
              onClick={sendMessage} 
              style={{
                ...styles.sendButton,
                ...(isLoading || !threadId || !input.trim() ? styles.sendButtonDisabled : {})
              }}
              disabled={isLoading || !threadId || !input.trim()}
            >
              <span style={styles.sendIcon}>🚀</span>
            </button>
          </div>
          <p style={styles.disclaimer}>
            AI-generated responses may contain inaccuracies. Please verify important information.
          </p>
        </div>
      </footer>
    </div>
  );
};

const styles: { [key: string]: React.CSSProperties } = {
  container: {
    display: 'flex',
    flexDirection: 'column',
    height: '100vh',
    background: '#ffffff',
    fontFamily: "'Segoe UI', Tahoma, Geneva, Verdana, sans-serif",
  },
  header: {
    background: 'rgba(248, 249, 250, 0.95)',
    backdropFilter: 'blur(10px)',
    borderBottom: '1px solid #e9ecef',
    boxShadow: '0 2px 10px rgba(0, 0, 0, 0.05)',
  },
  headerContent: {
    maxWidth: '1200px',
    margin: '0 auto',
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    flexWrap: 'wrap',
    gap: '12px',
    padding: '10px 14px',
  },
  headerLeft: {
    display: 'flex',
    alignItems: 'center',
    gap: '10px',
  },
  avatar: {
    width: '36px',
    height: '36px',
    borderRadius: '50%',
    background: 'linear-gradient(135deg, #007bff 0%, #0056b3 100%)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    boxShadow: '0 4px 15px rgba(0, 123, 255, 0.3)',
  },
  avatarIcon: {
    fontSize: '18px',
  },
  title: {
    margin: 0,
    fontSize: '18px',
    fontWeight: '700',
    color: '#212529',
  },
  subtitle: {
    margin: 0,
    fontSize: '11px',
    color: '#6c757d',
    fontWeight: '500',
  },
  threadId: {
    color: '#adb5bd',
    fontSize: '10px',
  },
  controlsContainer: {
    display: 'flex',
    gap: '8px',
    flexWrap: 'wrap',
    alignItems: 'center',
  },
  control: {
    background: '#ffffff',
    borderRadius: '16px',
    padding: '4px 8px',
    border: '1px solid #dee2e6',
    boxShadow: '0 2px 8px rgba(0, 0, 0, 0.05)',
  },
  controlLabel: {
    display: 'flex',
    alignItems: 'center',
    gap: '4px',
    cursor: 'pointer',
    fontSize: '10px',
    fontWeight: '500',
  },
  checkbox: {
    margin: 0,
    cursor: 'pointer',
    transform: 'scale(0.8)',
  },
  controlIcon: {
    fontSize: '12px',
  },
  controlText: {
    color: '#495057',
    whiteSpace: 'nowrap',
  },
  helpControl: {
    background: '#ffffff',
    borderRadius: '16px',
    padding: '4px 8px',
    border: '1px solid #dee2e6',
    boxShadow: '0 2px 8px rgba(0, 0, 0, 0.05)',
  },
  helpButton: {
    display: 'flex',
    alignItems: 'center',
    gap: '4px',
    background: 'none',
    border: 'none',
    cursor: 'pointer',
    fontSize: '10px',
    fontWeight: '500',
    color: '#495057',
  },
  helpIcon: {
    fontSize: '12px',
  },
  helpText: {
    whiteSpace: 'nowrap',
  },
  threadBar: {
    background: 'rgba(248, 249, 250, 0.9)',
    borderTop: '1px solid #dee2e6',
    padding: '8px 14px',
  },
  threadBarContent: {
    maxWidth: '1200px',
    margin: '0 auto',
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    gap: '12px',
  },
  threadActions: {
    display: 'flex',
    gap: '6px',
  },
  threadButton: {
    display: 'flex',
    alignItems: 'center',
    gap: '4px',
    padding: '4px 8px',
    background: '#ffffff',
    border: '1px solid #dee2e6',
    borderRadius: '12px',
    cursor: 'pointer',
    fontSize: '10px',
    fontWeight: '500',
    transition: 'all 0.2s ease',
    color: '#495057',
  },
  threadButtonIcon: {
    fontSize: '12px',
  },
  threadButtonText: {
    color: '#495057',
  },
  threadNameInput: {
    padding: '4px 8px',
    borderRadius: '8px',
    border: '1px solid #dee2e6',
    fontSize: '11px',
    background: '#ffffff',
    outline: 'none',
    width: '150px',
    color: '#495057',
  },
  helpPanel: {
    background: '#ffffff',
    borderBottom: '1px solid #dee2e6',
    boxShadow: '0 2px 10px rgba(0, 0, 0, 0.05)',
  },
  helpContent: {
    maxWidth: '1200px',
    margin: '0 auto',
    padding: '16px 14px',
  },
  helpHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '12px',
  },
  helpTitle: {
    fontSize: '14px',
    fontWeight: '700',
    color: '#212529',
  },
  closeButton: {
    background: 'none',
    border: 'none',
    fontSize: '16px',
    cursor: 'pointer',
    color: '#6c757d',
    padding: '4px',
  },
  helpBody: {
    color: '#495057',
  },
  helpDescription: {
    fontSize: '12px',
    marginBottom: '12px',
    color: '#495057',
  },
  featureList: {
    display: 'flex',
    flexDirection: 'column',
    gap: '8px',
    marginBottom: '12px',
  },
  featureItem: {
    display: 'flex',
    alignItems: 'flex-start',
    gap: '8px',
  },
  featureIcon: {
    fontSize: '14px',
    marginTop: '1px',
  },
  featureText: {
    fontSize: '11px',
    lineHeight: '1.4',
    color: '#495057',
  },
  helpFooter: {
    fontSize: '11px',
    color: '#6c757d',
    fontStyle: 'italic',
  },
  threadHistoryPanel: {
    background: '#ffffff',
    borderBottom: '1px solid #dee2e6',
    boxShadow: '0 2px 10px rgba(0, 0, 0, 0.05)',
  },
  threadHistoryContent: {
    maxWidth: '1200px',
    margin: '0 auto',
    padding: '12px 14px',
  },
  threadHistoryHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '8px',
  },
  threadHistoryTitle: {
    fontSize: '12px',
    fontWeight: '600',
    color: '#212529',
  },
  threadList: {
    display: 'flex',
    flexDirection: 'column',
    gap: '4px',
    maxHeight: '150px',
    overflowY: 'auto',
  },
  emptyThreads: {
    fontSize: '11px',
    color: '#6c757d',
    textAlign: 'center',
    padding: '20px',
  },
  threadItem: {
    padding: '6px 8px',
    background: '#f8f9fa',
    borderRadius: '8px',
    border: '1px solid #dee2e6',
    cursor: 'pointer',
    transition: 'all 0.2s ease',
  },
  threadItemHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '2px',
  },
  threadItemName: {
    fontSize: '11px',
    fontWeight: '600',
    color: '#212529',
  },
  threadItemTime: {
    fontSize: '9px',
    color: '#6c757d',
  },
  threadItemInfo: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  threadItemMessages: {
    fontSize: '9px',
    color: '#6c757d',
  },
  threadItemId: {
    fontSize: '8px',
    color: '#adb5bd',
  },
  messagesArea: {
    flex: 1,
    overflow: 'hidden',
    padding: '10px 14px',
    background: '#ffffff',
  },
  messagesContainer: {
    maxWidth: '1200px',
    margin: '0 auto',
    height: '100%',
    overflowY: 'auto',
    display: 'flex',
    flexDirection: 'column',
    gap: '10px',
  },
  messageWrapper: {
    display: 'flex',
    flexDirection: 'column',
    gap: '4px',
  },
  messageRow: {
    display: 'flex',
    gap: '8px',
    alignItems: 'flex-start',
  },
  userRow: {
    justifyContent: 'flex-end',
  },
  botRow: {
    justifyContent: 'flex-start',
  },
  messageAvatar: {
    flexShrink: 0,
  },
  botAvatar: {
    width: '28px',
    height: '28px',
    borderRadius: '50%',
    background: 'linear-gradient(135deg, #007bff 0%, #0056b3 100%)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    fontSize: '14px',
    boxShadow: '0 4px 15px rgba(0, 123, 255, 0.3)',
  },
  userAvatar: {
    width: '28px',
    height: '28px',
    borderRadius: '50%',
    background: 'linear-gradient(135deg, #28a745 0%, #20c997 100%)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    fontSize: '14px',
    boxShadow: '0 4px 15px rgba(40, 167, 69, 0.3)',
  },
  messageCard: {
    maxWidth: '75%',
    borderRadius: '14px',
    padding: '10px 12px',
    boxShadow: '0 2px 8px rgba(0, 0, 0, 0.08)',
    border: '1px solid #e9ecef',
  },
  userCard: {
    background: 'linear-gradient(135deg, #007bff 0%, #0056b3 100%)',
    color: 'white',
    border: 'none',
  },
  botCard: {
    background: '#ffffff',
    color: '#212529',
  },
  messageContent: {
    fontSize: '13px',
    lineHeight: '1.4',
  },
  messageTime: {
    fontSize: '9px',
    opacity: 0.7,
    marginTop: '4px',
    textAlign: 'right',
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  tableIndicator: {
    fontSize: '10px',
  },
  tableContainer: {
    marginTop: '8px',
    overflowX: 'auto',
    background: '#f8f9fa',
    borderRadius: '8px',
    padding: '8px',
    border: '1px solid #dee2e6',
  },
  streamingIndicator: {
    display: 'flex',
    alignItems: 'center',
    gap: '6px',
    marginTop: '6px',
    padding: '6px',
    background: 'rgba(0, 123, 255, 0.1)',
    borderRadius: '6px',
    border: '1px solid rgba(0, 123, 255, 0.2)',
  },
  streamingDots: {
    display: 'flex',
    gap: '2px',
  },
  streamingText: {
    fontSize: '10px',
    color: '#007bff',
    fontStyle: 'italic',
  },
  suggestionsWrapper: {
    marginLeft: '36px',
    marginTop: '4px',
  },
  suggestionsCard: {
    background: '#ffffff',
    borderRadius: '10px',
    padding: '8px',
    boxShadow: '0 2px 8px rgba(0, 0, 0, 0.08)',
    border: '1px solid #e9ecef',
  },
  suggestionsHeader: {
    display: 'flex',
    alignItems: 'center',
    gap: '4px',
    marginBottom: '6px',
  },
  suggestionsIcon: {
    fontSize: '12px',
  },
  suggestionsTitle: {
    fontSize: '11px',
    fontWeight: '600',
    color: '#212529',
  },
  suggestionsGrid: {
    display: 'flex',
    flexDirection: 'column',
    gap: '4px',
  },
  suggestionButton: {
    display: 'flex',
    alignItems: 'center',
    gap: '6px',
    padding: '6px 8px',
    background: '#f8f9fa',
    border: '1px solid #dee2e6',
    borderRadius: '8px',
    cursor: 'pointer',
    transition: 'all 0.3s ease',
    textAlign: 'left',
    fontSize: '10px',
    color: '#495057',
  },
  suggestionIcon: {
    fontSize: '10px',
    opacity: 0.7,
  },
  suggestionText: {
    flex: 1,
    lineHeight: '1.2',
  },
  sourcesWrapper: {
    marginLeft: '36px',
    marginTop: '4px',
  },
  sourcesCard: {
    background: '#ffffff',
    borderRadius: '10px',
    padding: '8px',
    boxShadow: '0 2px 8px rgba(0, 0, 0, 0.08)',
    border: '1px solid #e9ecef',
  },
  sourcesHeader: {
    display: 'flex',
    alignItems: 'center',
    gap: '4px',
    marginBottom: '6px',
  },
  sourcesIcon: {
    fontSize: '12px',
  },
  sourcesTitle: {
    fontSize: '11px',
    fontWeight: '600',
    color: '#212529',
  },
  sourcesGrid: {
    display: 'flex',
    flexDirection: 'column',
    gap: '6px',
  },
  sourceItem: {
    padding: '6px',
    background: '#f8f9fa',
    borderRadius: '6px',
    border: '1px solid #dee2e6',
  },
  sourceHeader: {
    display: 'flex',
    alignItems: 'center',
    gap: '4px',
    marginBottom: '4px',
  },
  sourceIcon: {
    fontSize: '10px',
    opacity: 0.7,
  },
  sourceName: {
    fontSize: '10px',
    fontWeight: '600',
    color: '#212529',
  },
  sourceScore: {
    display: 'flex',
    alignItems: 'center',
    gap: '6px',
  },
  scoreBar: {
    flex: 1,
    height: '3px',
    background: '#e9ecef',
    borderRadius: '2px',
    overflow: 'hidden',
  },
  scoreBarFill: {
    height: '100%',
    background: 'linear-gradient(135deg, #28a745 0%, #20c997 100%)',
    borderRadius: '2px',
    transition: 'width 0.3s ease',
  },
  scoreText: {
    fontSize: '9px',
    color: '#6c757d',
    fontWeight: '500',
  },
  loadingCard: {
    maxWidth: '160px',
    borderRadius: '14px',
    padding: '10px 12px',
    background: '#ffffff',
    boxShadow: '0 2px 8px rgba(0, 0, 0, 0.08)',
    border: '1px solid #e9ecef',
  },
  loadingContent: {
    display: 'flex',
    alignItems: 'center',
    gap: '6px',
  },
  loadingDots: {
    display: 'flex',
    gap: '2px',
  },
  loadingText: {
    fontSize: '10px',
    color: '#007bff',
    fontStyle: 'italic',
  },
  inputArea: {
    background: 'rgba(248, 249, 250, 0.95)',
    backdropFilter: 'blur(10px)',
    borderTop: '1px solid #dee2e6',
    padding: '10px 14px',
  },
  inputContainer: {
    maxWidth: '1200px',
    margin: '0 auto',
  },
  inputWrapper: {
    display: 'flex',
    gap: '8px',
    alignItems: 'center',
    marginBottom: '4px',
  },
  inputField: {
    flex: 1,
    padding: '10px 14px',
    borderRadius: '18px',
    border: '1px solid #dee2e6',
    background: '#ffffff',
    fontSize: '13px',
    outline: 'none',
    boxShadow: '0 2px 8px rgba(0, 0, 0, 0.05)',
    transition: 'all 0.3s ease',
    color: '#495057',
  },
  sendButton: {
    width: '40px',
    height: '40px',
    borderRadius: '50%',
    border: 'none',
    background: 'linear-gradient(135deg, #007bff 0%, #0056b3 100%)',
    color: 'white',
    cursor: 'pointer',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    boxShadow: '0 4px 15px rgba(0, 123, 255, 0.3)',
    transition: 'all 0.3s ease',
  },
  sendButtonDisabled: {
    opacity: 0.5,
    cursor: 'not-allowed',
  },
  sendIcon: {
    fontSize: '14px',
  },
  disclaimer: {
    fontSize: '9px',
    color: '#6c757d',
    textAlign: 'center',
    margin: 0,
  },
};

export default ConversationPage;
