import { useState, useRef, useEffect } from 'react';
import axios from 'axios';
import ReactMarkdown from 'react-markdown';
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card } from "@/components/ui/card";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Bot, User, Send, LoaderCircle } from 'lucide-react';

interface Message {
  sender: 'user' | 'bot';
  text: string;
  sources?: any[];
}

function RagPage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    // Welcome message
    setMessages([
      {
        sender: 'bot',
        text: 'Welcome to the AI Force Intelligent Support Agent! How can I help you today?',
      }
    ]);
  }, []);

  useEffect(scrollToBottom, [messages]);

  const sendMessage = async () => {
    if (input.trim() === '' || isLoading) return;

    const userMessage: Message = { sender: 'user', text: input };
    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);

    try {
      // NOTE: This URL assumes your backend is running on localhost:8000
      // and has a /api/query endpoint.
      const response = await axios.post('http://localhost:8000/query', {
        query: input,
      });

      const botMessage: Message = {
        sender: 'bot',
        text: response.data.success && response.data.data 
          ? response.data.data.answer || response.data.data.response || 'No response generated'
          : response.data.response || response.data.answer || 'No response generated',
        sources: response.data.success && response.data.data 
          ? response.data.data.sources
          : response.data.sources,
      };
      setMessages(prev => [...prev, botMessage]);
    } catch (error) {
      console.error("Error fetching response:", error);
      const errorMessage: Message = {
        sender: 'bot',
        text: 'Sorry, I encountered an error connecting to the backend. Please ensure it is running on http://localhost:8000.',
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-screen bg-secondary/50 font-sans">
      <header className="bg-card border-b p-4 shadow-sm flex items-center justify-between">
        <div className="flex items-center">
            <img src="/logo.svg" alt="Logo" className="h-8 w-8 mr-3 text-primary" />
            <h1 className="text-xl font-bold text-foreground">AI Force Intelligent Support Agent</h1>
        </div>
      </header>

      <main className="flex-1 overflow-y-auto p-4 sm:p-6">
        <div className="max-w-4xl mx-auto space-y-8">
          {messages.map((msg, index) => (
            <div key={index} className={`flex items-start gap-4 ${msg.sender === 'user' ? 'justify-end' : ''}`}>
              {msg.sender === 'bot' && (
                <Avatar className="w-10 h-10 border-2 border-primary">
                  <AvatarFallback className="bg-primary/20"><Bot className="text-primary" /></AvatarFallback>
                </Avatar>
              )}
              <div className={`max-w-xl rounded-xl p-4 shadow-md ${msg.sender === 'user' ? 'bg-primary text-primary-foreground' : 'bg-card text-card-foreground'}`}>
                <ReactMarkdown className="prose prose-sm sm:prose-base dark:prose-invert max-w-none">{msg.text}</ReactMarkdown>
                {msg.sender === 'bot' && msg.sources && msg.sources.length > 0 && (
                  <div className="mt-4 border-t pt-3">
                    <h3 className="text-xs font-semibold mb-2 uppercase tracking-wider">Sources</h3>
                    <div className="space-y-2">
                      {msg.sources.map((source, i) => (
                        <Card key={i} className="bg-secondary/50 p-3 text-xs text-muted-foreground">
                          <p className="font-semibold text-foreground truncate"><strong>Source {i + 1}:</strong> {source.metadata?.file_name || 'Unknown'}</p>
                          <p className="truncate mt-1">{source.text}</p>
                        </Card>
                      ))}
                    </div>
                  </div>
                )}
              </div>
              {msg.sender === 'user' && (
                <Avatar className="w-10 h-10 border-2 border-muted">
                  <AvatarFallback><User /></AvatarFallback>
                </Avatar>
              )}
            </div>
          ))}
          {isLoading && (
            <div className="flex items-start gap-4">
              <Avatar className="w-10 h-10 border-2 border-primary">
                <AvatarFallback className="bg-primary/20"><Bot className="text-primary" /></AvatarFallback>
              </Avatar>
              <div className="max-w-lg rounded-xl p-4 bg-card text-card-foreground shadow-md flex items-center space-x-3">
                <LoaderCircle className="animate-spin h-5 w-5 text-primary" />
                <span className="text-sm">Thinking...</span>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>
      </main>

      <footer className="bg-card/95 backdrop-blur-sm p-4 border-t">
        <div className="max-w-4xl mx-auto">
          <div className="relative">
            <Input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && sendMessage()}
              placeholder="What is artificial intelligence?"
              className="pr-12 h-12 text-base rounded-full"
              disabled={isLoading}
            />
            <Button
              type="submit"
              size="icon"
              className="absolute top-1/2 right-2 -translate-y-1/2 rounded-full"
              onClick={sendMessage}
              disabled={isLoading || input.trim() === ''}
            >
              <Send className="h-5 w-5" />
            </Button>
          </div>
          <p className="text-xs text-center text-muted-foreground mt-2">
            AI-generated content may be inaccurate. Verify important information.
          </p>
        </div>
      </footer>
    </div>
  );
}

export default RagPage;
