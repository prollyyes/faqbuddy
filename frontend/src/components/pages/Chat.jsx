'use client'
import React from 'react'
import { IoSendSharp } from "react-icons/io5";
import Link from 'next/link';
import { motion } from 'framer-motion';
import axios from 'axios';
import ReactMarkdown from 'react-markdown';

const Chat = () => {
    const [chatExpanded, setChatExpanded] = React.useState(false);
    const [message, setMessage] = React.useState('');
    const [messages, setMessages] = React.useState([]);
    const [isLoading, setIsLoading] = React.useState(false);
    const [showNewChatButton, setShowNewChatButton] = React.useState(false);
    const [isResetting, setIsResetting] = React.useState(false);

    const sendMessage = async () => {
        if (!message.trim()) return;

        // Expand chat when first message is sent
        if (!chatExpanded) {
            setChatExpanded(true);
        }

        const userMessage = { text: message, sender: 'user', timestamp: new Date() };
        const currentMessage = message;
        setMessage('');
        setIsLoading(true);

        // Add user message and bot placeholder in one update
        setMessages(prev => {
            const newMessages = [...prev, userMessage, {
                text: '',
                sender: 'bot',
                timestamp: new Date(),
                isStreaming: true,
                metadata: {}
            }];
            
            // The bot message index is the last message in the array
            const botMessageIndex = newMessages.length - 1;
            
            // Start streaming with the correct index
            sendMessageStreaming(currentMessage, botMessageIndex);
            
            return newMessages;
        });

        try {
            // The streaming is handled inside the setMessages callback
        } catch (error) {
            console.error('Streaming failed, falling back to regular API:', error);
            // Fallback will be handled in sendMessageStreaming
        } finally {
            setIsLoading(false);
        }
    };

    const sendMessageStreaming = async (question, messageIndex) => {
        try {
            console.log('🔄 Starting streaming request for:', question);
            const response = await fetch('http://127.0.0.1:8000/chat?streaming=true', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ question }),
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let accumulatedText = '';

            console.log('📡 Streaming response started');

            while (true) {
                const { done, value } = await reader.read();
                if (done) {
                    console.log('✅ Streaming completed');
                    break;
                }

                const chunk = decoder.decode(value);
                const lines = chunk.split('\n');

                for (const line of lines) {
                    if (line.startsWith('data: ')) {
                        try {
                            const data = JSON.parse(line.slice(6));
                            console.log('📦 Received streaming data:', data);
                            
                            if (data.type === 'token') {
                                accumulatedText += data.token;
                                console.log('🔄 Streaming token:', data.token, 'Total length:', accumulatedText.length);
                                
                                // Force immediate update for streaming
                                setMessages(prev => {
                                    const newMessages = [...prev];
                                    newMessages[messageIndex] = {
                                        ...newMessages[messageIndex],
                                        text: accumulatedText,
                                        isStreaming: true
                                    };
                                    return newMessages;
                                });
                            } else if (data.type === 'complete') {
                                console.log('✅ Streaming complete signal received');
                                setMessages(prev => {
                                    const newMessages = [...prev];
                                    newMessages[messageIndex] = {
                                        ...newMessages[messageIndex],
                                        text: accumulatedText,
                                        isStreaming: false,
                                        metadata: {
                                            chosen: data.chosen || 'RAG',
                                            streaming: true
                                        }
                                    };
                                    return newMessages;
                                });
                                return;
                            } else if (data.type === 'error') {
                                // Handle error type directly without throwing
                                console.error('❌ Received error from backend:', data.message);
                                
                                // Check if it's a context window error
                                if (data.message && (data.message.includes('exceed context window') || data.message.includes('Requested tokens'))) {
                                    setShowNewChatButton(true);
                                    const errorMessage = {
                                        text: 'La conversazione è diventata troppo lunga. Clicca il pulsante "+" per iniziare una nuova chat.',
                                        sender: 'bot',
                                        timestamp: new Date(),
                                        isError: true,
                                        isStreaming: false
                                    };
                                    setMessages(prev => {
                                        const newMessages = [...prev];
                                        newMessages[messageIndex] = errorMessage;
                                        return newMessages;
                                    });
                                    return;
                                } else {
                                    // Handle other errors
                                    const errorMessage = {
                                        text: data.message || 'Si è verificato un errore. Riprova più tardi.',
                                        sender: 'bot',
                                        timestamp: new Date(),
                                        isError: true,
                                        isStreaming: false
                                    };
                                    setMessages(prev => {
                                        const newMessages = [...prev];
                                        newMessages[messageIndex] = errorMessage;
                                        return newMessages;
                                    });
                                    return;
                                }
                            }
                        } catch (parseError) {
                            console.error('❌ Error parsing streaming data:', parseError);
                        }
                    }
                }
            }
        } catch (error) {
            console.error('❌ Streaming error:', error);
            // Check if it's a context window error
            if (error.message && (error.message.includes('exceed context window') || error.message.includes('Requested tokens'))) {
                setShowNewChatButton(true);
                const errorMessage = {
                    text: 'La conversazione è diventata troppo lunga. Clicca il pulsante "+" per iniziare una nuova chat.',
                    sender: 'bot',
                    timestamp: new Date(),
                    isError: true,
                    isStreaming: false
                };
                setMessages(prev => {
                    const newMessages = [...prev];
                    newMessages[messageIndex] = errorMessage;
                    return newMessages;
                });
                return;
            }
            
            // Fallback to regular API
            console.log('🔄 Streaming failed, falling back to regular API');
            try {
                await sendMessageRegular(question, messageIndex);
            } catch (fallbackError) {
                console.error('❌ Fallback also failed:', fallbackError);
                const errorMessage = {
                    text: 'Si è verificato un errore. Riprova più tardi.',
                    sender: 'bot',
                    timestamp: new Date(),
                    isError: true,
                    isStreaming: false
                };
                setMessages(prev => {
                    const newMessages = [...prev];
                    newMessages[messageIndex] = errorMessage;
                    return newMessages;
                });
            }
        }
    };

    const sendMessageRegular = async (question, messageIndex) => {
        try {
            const response = await axios.post('http://127.0.0.1:8000/chat', {
                question: question
            });

            console.log('Backend response:', response.data);

            const botMessage = {
                text: response.data.natural_response || response.data.result,
                sender: 'bot',
                timestamp: new Date(),
                isStreaming: false,
                metadata: {
                    chosen: response.data.chosen,
                    ml_confidence: response.data.ml_confidence,
                    query: response.data.query
                }
            };

            setMessages(prev => {
                const newMessages = [...prev];
                newMessages[messageIndex] = botMessage;
                return newMessages;
            });
        } catch (error) {
            console.error('Error sending message:', error);
            // Check if it's a context window error
            if (error.message && (error.message.includes('exceed context window') || error.message.includes('Requested tokens'))) {
                setShowNewChatButton(true);
                const errorMessage = {
                    text: 'La conversazione è diventata troppo lunga. Clicca il pulsante "+" per iniziare una nuova chat.',
                    sender: 'bot',
                    timestamp: new Date(),
                    isError: true,
                    isStreaming: false
                };
                setMessages(prev => {
                    const newMessages = [...prev];
                    newMessages[messageIndex] = errorMessage;
                    return newMessages;
                });
                return;
            }
            const errorMessage = {
                text: 'Mi dispiace, si è verificato un errore. Riprova più tardi.',
                sender: 'bot',
                timestamp: new Date(),
                isError: true,
                isStreaming: false
            };
            setMessages(prev => {
                const newMessages = [...prev];
                newMessages[messageIndex] = errorMessage;
                return newMessages;
            });
        }
    };

    const handleKeyPress = (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    };

    const startNewChat = async () => {
        setIsResetting(true);
        
        // Clear frontend state
        setMessages([]);
        setMessage('');
        setShowNewChatButton(false);
        setIsLoading(false);

        // Reset backend context
        try {
            const response = await fetch('http://127.0.0.1:8000/reset_context', { method: 'POST' });
            const result = await response.json();
            if (result.status === 'ok') {
                console.log('✅ Backend context reset successfully');
            } else {
                console.warn('⚠️ Backend context reset failed:', result.message);
            }
        } catch (err) {
            console.warn('⚠️ Failed to reset backend context:', err);
        } finally {
            setIsResetting(false);
        }
    };

    return (
        <div className="bg-white text-black min-h-screen">
            <motion.div
              initial={{ opacity: 0, x: -50 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.5 }}
            >
                <motion.div
                    initial={{ height: 'auto' }}
                    animate={{ height: chatExpanded ? '100vh' : 'auto' }}
                    transition={{ duration: 0.5, ease: 'easeInOut' }}
                    className={`overflow-hidden transition-all duration-500 ease-in-out ${
                        chatExpanded ? 'fixed inset-x-0 top-0 z-40 bg-white pt-16 pb-24' : 'w-full max-w-md mx-auto mt-4 p-4 rounded-lg'
                    }`}
                >
                    {!chatExpanded && (
                        <motion.div
                            key="collapsed-chat"
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            className="flex flex-col mt-27 items-center justify-center p-6"
                        >
                            <motion.p
                                initial={{ opacity: 0, y: 20 }}
                                animate={{ opacity: 1, y: 0 }}
                                transition={{ duration: 0.5 }}
                                className="text-lg font-semibold text-[#822433] mb-2"
                            >
                                Fai una domanda al tuo <span className="italic">FAQbuddy</span>!
                            </motion.p>
                        </motion.div>
                    )}

                    {chatExpanded && (
                        <div className="flex-1 overflow-y-auto p-4 space-y-4 max-h-[calc(100vh-200px)] pt-10">
                            {messages.map((msg, index) => (
                                <motion.div
                                    key={index}
                                    initial={{ opacity: 0, y: 20 }}
                                    animate={{ opacity: 1, y: 0 }}
                                    className={`flex ${msg.sender === 'user' ? 'justify-end' : 'justify-start'}`}
                                >
                                    <div className={`max-w-[80%] p-3 rounded-lg ${
                                        msg.sender === 'user' 
                                            ? 'bg-[#822433] text-white' 
                                            : msg.isError 
                                                ? 'bg-red-100 text-red-800' 
                                                : 'bg-white text-black border border-gray-200'
                                    }`}>
                                        <div className="text-sm max-w-none">
                                            {msg.sender === 'user' ? (
                                                <div className="text-white">{msg.text}</div>
                                            ) : (
                                                <ReactMarkdown
                                                    components={{
                                                        h1: ({node, ...props}) => (
                                                            <h1 style={{fontSize: '1.5rem', fontWeight: '600', marginBottom: '0.75rem', color: '#374151'}} {...props} />
                                                        ),
                                                        h2: ({node, ...props}) => (
                                                            <h2 style={{fontSize: '1.25rem', fontWeight: '500', marginTop: '1rem', marginBottom: '0.5rem', color: '#374151'}} {...props} />
                                                        ),
                                                        h3: ({node, ...props}) => (
                                                            <h3 style={{fontSize: '1rem', fontWeight: '500', marginTop: '0.75rem', marginBottom: '0.5rem', color: '#374151'}} {...props} />
                                                        ),
                                                        p: ({node, ...props}) => (
                                                            <p style={{marginBottom: '0.75rem', lineHeight: '1.6', color: '#6b7280'}} {...props} />
                                                        ),
                                                        ul: ({node, ...props}) => (
                                                            <ul style={{marginBottom: '0.75rem', paddingLeft: '1.5rem', color: '#6b7280'}} {...props} />
                                                        ),
                                                        ol: ({node, ...props}) => (
                                                            <ol style={{marginBottom: '0.75rem', paddingLeft: '1.5rem', color: '#6b7280'}} {...props} />
                                                        ),
                                                        li: ({node, ...props}) => (
                                                            <li style={{marginBottom: '0.5rem', color: '#6b7280', lineHeight: '1.5'}} {...props} />
                                                        ),
                                                        strong: ({node, ...props}) => (
                                                            <strong style={{fontWeight: '600', color: '#111827'}} {...props} />
                                                        ),
                                                        em: ({node, ...props}) => (
                                                            <em style={{fontStyle: 'italic', color: '#6b7280'}} {...props} />
                                                        ),
                                                        a: ({node, children, href, ...props}) => {
                                                            // Prevent nested links by checking if we're already inside a link
                                                            const isInsideLink = node?.parent?.tagName === 'a';
                                                            if (isInsideLink) {
                                                                return <span style={{color: '#3b82f6', textDecoration: 'underline'}}>{children}</span>;
                                                            }
                                                            return (
                                                                <a 
                                                                    href={href} 
                                                                    target="_blank" 
                                                                    rel="noopener noreferrer"
                                                                    style={{color: '#3b82f6', textDecoration: 'underline'}} 
                                                                    {...props}
                                                                >
                                                                    {children}
                                                                </a>
                                                            );
                                                        },
                                                        code: ({node, ...props}) => (
                                                            <code style={{backgroundColor: '#f3f4f6', padding: '0.125rem 0.25rem', borderRadius: '0.25rem', fontSize: '0.875rem', fontFamily: 'monospace', color: '#111827'}} {...props} />
                                                        ),
                                                        pre: ({node, ...props}) => (
                                                            <pre style={{backgroundColor: '#f3f4f6', padding: '0.75rem', borderRadius: '0.5rem', fontSize: '0.875rem', fontFamily: 'monospace', overflowX: 'auto', border: '1px solid #e5e7eb', marginBottom: '0.75rem'}} {...props} />
                                                        ),
                                                        blockquote: ({node, ...props}) => (
                                                            <blockquote style={{borderLeft: '3px solid #e5e7eb', paddingLeft: '0.75rem', fontStyle: 'italic', color: '#6b7280', marginTop: '0.75rem', marginBottom: '0.75rem'}} {...props} />
                                                        ),
                                                    }}
                                                >
                                                    {msg.text}
                                                </ReactMarkdown>
                                            )}
                                        </div>
                                        {msg.isStreaming && (
                                            <div className="flex items-center mt-2">
                                                <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse mr-2"></div>
                                                <span className="text-xs text-gray-500">Sta scrivendo...</span>
                                            </div>
                                        )}
                                        {msg.metadata && !msg.isStreaming && (
                                            <div className="text-xs mt-2 opacity-70">
                                                <p>Metodo: {msg.metadata.chosen}</p>
                                                {msg.metadata.ml_confidence && (
                                                    <p>Confidenza: {(msg.metadata.ml_confidence * 100).toFixed(1)}%</p>
                                                )}
                                                {msg.metadata.streaming && (
                                                    <p>Streaming: Attivato</p>
                                                )}
                                            </div>
                                        )}
                                    </div>
                                </motion.div>
                            ))}
                            
                        </div>
                    )}
                </motion.div>

                <motion.div
                  layout
                  transition={{ type: "spring", stiffness: 200, damping: 20 }}
                  className={`${
                    chatExpanded
                      ? "fixed bottom-18 left-0 w-full px-4 pb-4 z-40 bg-white"
                      : "w-full max-w-md mx-auto mt-2 px-4"
                  }`}
                >
                  <div className="flex items-center w-full gap-2">
                    <input
                      type="text"
                      placeholder="Scrivi un messaggio..."
                      value={message}
                      onChange={(e) => setMessage(e.target.value)}
                      onKeyPress={handleKeyPress}
                      disabled={isLoading}
                      className="flex-1 border border-gray-300 rounded-full px-4 py-2 shadow-sm focus:outline-none focus:ring-2 focus:ring-[#822433] transition duration-200 hover:shadow-md disabled:opacity-50"
                    />
                    <button
                      className="group bg-white text-[#822433] hover:bg-[#822433] p-2 rounded-full transition-all duration-200 disabled:opacity-50"
                      onClick={sendMessage}
                      disabled={isLoading || !message.trim()}
                    >
                      <IoSendSharp className="text-[1.65rem] group-hover:text-white" />
                    </button>
                  </div>
                </motion.div>
            </motion.div>

            {/* Floating New Chat Button */}
            {showNewChatButton && (
                <motion.button
                    initial={{ opacity: 0, scale: 0.8 }}
                    animate={{ opacity: 1, scale: 1 }}
                    transition={{ duration: 0.3, ease: "easeOut" }}
                    onClick={startNewChat}
                    disabled={isResetting}
                    className={`fixed top-20 right-4 z-50 w-12 h-12 bg-[#822433] text-white rounded-full shadow-lg hover:shadow-xl transition-all duration-200 flex items-center justify-center hover:scale-110 ${
                        isResetting ? 'opacity-50 cursor-not-allowed' : ''
                    }`}
                    title={isResetting ? "Ripristino in corso..." : "Inizia una nuova chat"}
                >
                    {isResetting ? (
                        <div className="w-6 h-6 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                    ) : (
                        <svg 
                            className="w-6 h-6" 
                            fill="none" 
                            stroke="currentColor" 
                            viewBox="0 0 24 24"
                        >
                            <path 
                                strokeLinecap="round" 
                                strokeLinejoin="round" 
                                strokeWidth={2} 
                                d="M12 4v16m8-8H4" 
                            />
                        </svg>
                    )}
                </motion.button>
            )}
        </div>
    );
};

export default Chat;