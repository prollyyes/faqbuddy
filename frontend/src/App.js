import React, { useState, useRef, useEffect } from 'react';
import styled from 'styled-components';
import axios from 'axios';

const Container = styled.div`
  max-width: 800px;
  margin: 0 auto;
  padding: 20px;
  height: 100vh;
  display: flex;
  flex-direction: column;
`;

const Header = styled.header`
  text-align: center;
  padding: 20px;
  background: #802433;
  color: white;
  border-radius: 10px 10px 0 0;
`;

const ChatContainer = styled.div`
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  background: #f5f5f5;
  border-left: 1px solid #ddd;
  border-right: 1px solid #ddd;
`;

const MessageBubble = styled.div`
  max-width: 70%;
  padding: 10px 15px;
  border-radius: 20px;
  margin: 10px;
  ${props => props.isUser ? `
    background-color: #007AFF;
    color: white;
    margin-left: auto;
  ` : `
    background-color: #802433;
    color: white;
    margin-right: auto;
  `}
`;

const InputContainer = styled.div`
  display: flex;
  padding: 20px;
  background: white;
  border: 1px solid #ddd;
  border-radius: 0 0 10px 10px;
`;

const Input = styled.input`
  flex: 1;
  padding: 10px;
  border: 1px solid #ddd;
  border-radius: 20px;
  margin-right: 10px;
  font-size: 16px;
`;

const SendButton = styled.button`
  background: #802433;
  color: white;
  border: none;
  padding: 10px 20px;
  border-radius: 20px;
  cursor: pointer;
  font-size: 16px;
  
  &:hover {
    background: #6b1f2b;
  }
  
  &:disabled {
    background: #ccc;
    cursor: not-allowed;
  }
`;

const LoadingDots = styled.div`
  display: inline-block;
  
  &::after {
    content: '.';
    animation: dots 1.5s steps(5, end) infinite;
  }
  
  @keyframes dots {
    0%, 20% { content: '.'; }
    40% { content: '..'; }
    60% { content: '...'; }
    80%, 100% { content: ''; }
  }
`;

function App() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;

    const userMessage = input.trim();
    setInput('');
    setMessages(prev => [...prev, { text: userMessage, isUser: true }]);
    setIsLoading(true);

    try {
      const response = await axios.post('http://localhost:8000/api/chat', {
        message: userMessage
      });

      setMessages(prev => [...prev, { 
        text: response.data.response,
        isUser: false,
        metadata: {
          retrieval_time: response.data.retrieval_time,
          generation_time: response.data.generation_time,
          total_time: response.data.total_time
        }
      }]);
    } catch (error) {
      console.error('Error:', error);
      setMessages(prev => [...prev, { 
        text: 'Sorry, I encountered an error while processing your request.',
        isUser: false 
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Container>
      <Header>
        <h1>FAQ Buddy</h1>
      </Header>
      <ChatContainer>
        {messages.map((message, index) => (
          <MessageBubble key={index} isUser={message.isUser}>
            {message.text}
            {message.metadata && !message.isUser && (
              <div style={{ fontSize: '0.8em', marginTop: '5px', opacity: 0.8 }}>
                Response time: {message.metadata.total_time.toFixed(2)}s
              </div>
            )}
          </MessageBubble>
        ))}
        {isLoading && (
          <MessageBubble isUser={false}>
            <LoadingDots />
          </MessageBubble>
        )}
        <div ref={messagesEndRef} />
      </ChatContainer>
      <form onSubmit={handleSubmit}>
        <InputContainer>
          <Input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Type your message..."
            disabled={isLoading}
          />
          <SendButton type="submit" disabled={!input.trim() || isLoading}>
            Send
          </SendButton>
        </InputContainer>
      </form>
    </Container>
  );
}

export default App; 