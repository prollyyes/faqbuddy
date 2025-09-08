'use client'
import React from 'react'
import { IoSendSharp } from "react-icons/io5";
import Link from 'next/link';
import { motion } from 'framer-motion';
import axios from 'axios';
import ReactMarkdown from 'react-markdown';

const HOST = process.env.NEXT_PUBLIC_HOST;

// Thinking Section Component (ChatGPT-like)
const ThinkingSection = ({ thinking }) => {
    const [isExpanded, setIsExpanded] = React.useState(false);
    
    return (
        <div className="mt-4 border-t border-gray-200 pt-3">
            <button
                onClick={() => setIsExpanded(!isExpanded)}
                className="flex items-center text-sm text-gray-600 hover:text-gray-800 transition-colors group"
            >
                <span className="mr-2 text-lg">🤔</span>
                <span className="font-medium">Thinking</span>
                <span className="ml-2 transform transition-transform duration-200 group-hover:scale-110">
                    {isExpanded ? '▼' : '▶'}
                </span>
            </button>
            
            {isExpanded && (
                <motion.div
                    initial={{ opacity: 0, height: 0 }}
                    animate={{ opacity: 1, height: 'auto' }}
                    exit={{ opacity: 0, height: 0 }}
                    transition={{ duration: 0.3 }}
                    className="mt-3 text-sm text-gray-700 bg-gray-50 p-4 rounded-lg border border-gray-200"
                >
                    <ReactMarkdown
                        components={{
                            p: ({node, ...props}) => <p className="mb-2 last:mb-0 leading-relaxed" {...props} />,
                            ul: ({node, ...props}) => <ul className="list-disc list-inside mb-2 space-y-1" {...props} />,
                            ol: ({node, ...props}) => <ol className="list-decimal list-inside mb-2 space-y-1" {...props} />,
                            li: ({node, ...props}) => <li className="leading-relaxed" {...props} />,
                            strong: ({node, ...props}) => <strong className="font-semibold text-gray-900" {...props} />,
                            em: ({node, ...props}) => <em className="italic text-gray-600" {...props} />,
                            h1: ({node, ...props}) => <h1 className="text-base font-bold mb-2 text-gray-900" {...props} />,
                            h2: ({node, ...props}) => <h2 className="text-sm font-semibold mb-1 text-gray-900" {...props} />,
                            h3: ({node, ...props}) => <h3 className="text-sm font-medium mb-1 text-gray-900" {...props} />,
                        }}
                    >
                        {thinking}
                    </ReactMarkdown>
                </motion.div>
            )}
        </div>
    );
};

// Reference Button Component (ChatGPT-like)
const ReferenceButton = ({ fragmentId, onClick }) => {
    return (
        <button
            onClick={() => onClick(fragmentId)}
            className="inline-flex items-center px-2 py-1 text-xs bg-blue-50 text-blue-700 border border-blue-200 rounded-md hover:bg-blue-100 hover:border-blue-300 transition-all duration-200 ml-1 font-medium"
        >
            <span className="mr-1">📄</span>
            {fragmentId}
        </button>
    );
};

const Chat = () => {
    const [chatExpanded, setChatExpanded] = React.useState(false);
    const [message, setMessage] = React.useState('');
    const [messages, setMessages] = React.useState([]);
    const [isLoading, setIsLoading] = React.useState(false);
    const [selectedFragment, setSelectedFragment] = React.useState(null);
    const [conversationId, setConversationId] = React.useState(null);

    const handleFragmentClick = (fragmentId) => {
        setSelectedFragment(fragmentId);
        // Here you could show a modal or expand a section to show the fragment content
        console.log('Clicked fragment:', fragmentId);
    };

    const sendMessage = async () => {
        if (!message.trim()) return;

        // Expand chat when first message is sent
        if (!chatExpanded) {
            setChatExpanded(true);
        }

        const userMessage = { text: message, sender: 'user', timestamp: new Date() };
        setMessages(prev => [...prev, userMessage]);
        const currentMessage = message;
        setMessage('');
        setIsLoading(true);

        // Create a placeholder for the streaming response
        const streamingMessageIndex = messages.length + 1;
        setMessages(prev => [...prev, {
            text: '',
            sender: 'bot',
            timestamp: new Date(),
            isStreaming: true,
            metadata: {}
        }]);

        try {
            // Try streaming first, fallback to regular if it fails
            await sendMessageStreaming(currentMessage, streamingMessageIndex);
        } catch (error) {
            console.error('Streaming failed, falling back to regular API:', error);
            await sendMessageRegular(currentMessage, streamingMessageIndex);
        } finally {
            setIsLoading(false);
        }
    };

    const sendMessageStreaming = async (question, messageIndex) => {
        try {
            const response = await fetch(`${HOST}/chat?streaming=true`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Accept': 'text/event-stream',
                },
                body: JSON.stringify({ 
                    question,
                    conversation_id: conversationId 
                }),
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let accumulatedText = '';
            let sseBuffer = '';

            while (true) {
                const { done, value } = await reader.read();
                if (done) break;

                sseBuffer += decoder.decode(value, { stream: true });
                let boundaryIndex;
                while ((boundaryIndex = sseBuffer.indexOf('\n\n')) !== -1) {
                    const eventChunk = sseBuffer.slice(0, boundaryIndex);
                    sseBuffer = sseBuffer.slice(boundaryIndex + 2);

                    const lines = eventChunk.split('\n');
                    for (const line of lines) {
                        if (!line.startsWith('data: ')) continue;
                        try {
                            const data = JSON.parse(line.slice(6));
                            if (data.type === 'token') {
                                accumulatedText += data.token;
                                setMessages(prev => {
                                    const newMessages = [...prev];
                                    newMessages[messageIndex] = {
                                        ...newMessages[messageIndex],
                                        text: accumulatedText,
                                        isStreaming: true
                                    };
                                    return newMessages;
                                });
                            } else if (data.type === 'metadata') {
                                // Final metadata from RAG streaming
                                setMessages(prev => {
                                    const newMessages = [...prev];
                                    newMessages[messageIndex] = {
                                        ...newMessages[messageIndex],
                                        isStreaming: false,
                                        thinking: data.thinking || '',
                                        metadata: {
                                            chosen: 'RAG',
                                            streaming: true,
                                            confidence: data.confidence,
                                            verified: data.verified
                                        }
                                    };
                                    return newMessages;
                                });
                                return;
                            } else if (data.type === 'complete') {
                                // Update conversation_id if provided
                                if (data.conversation_id) {
                                    setConversationId(data.conversation_id);
                                }
                                
                                setMessages(prev => {
                                    const newMessages = [...prev];
                                    newMessages[messageIndex] = {
                                        ...newMessages[messageIndex],
                                        isStreaming: false,
                                        thinking: data.thinking || '',
                                        metadata: {
                                            chosen: data.chosen || 'RAG',
                                            streaming: true
                                        }
                                    };
                                    return newMessages;
                                });
                                return;
                            } else if (data.type === 'error') {
                                throw new Error(data.message);
                            }
                        } catch (parseError) {
                            console.error('Error parsing streaming data:', parseError);
                        }
                    }
                }
            }
        } catch (error) {
            console.error('Streaming error:', error);
            throw error;
        }
    };

    const sendMessageRegular = async (question, messageIndex) => {
        try {
            const response = await axios.post(`${HOST}/chat`, {
                question: question,
                conversation_id: conversationId
            });

            console.log('Backend response:', response.data);

            // Update conversation_id if provided
            if (response.data.conversation_id) {
                setConversationId(response.data.conversation_id);
            }

            const botMessage = {
                text: response.data.natural_response || response.data.result || response.data.response,
                thinking: response.data.thinking,
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
                                                : 'bg-gray-100 text-black'
                                    }`}>
                                        <div className={`text-sm max-w-none ${msg.sender === 'user' ? 'text-white' : ''}`}>
                                            {/* Main Answer */}
                                            <ReactMarkdown
                                                components={{
                                                    h1: ({node, ...props}) => <h1 className={`text-xl font-bold mb-4 mt-6 first:mt-0 leading-tight ${msg.sender === 'user' ? 'text-white' : 'text-gray-900'}`} {...props} />,
                                                    h2: ({node, ...props}) => <h2 className={`text-lg font-semibold mb-3 mt-5 first:mt-0 leading-tight ${msg.sender === 'user' ? 'text-white' : 'text-gray-900'}`} {...props} />,
                                                    h3: ({node, ...props}) => <h3 className={`text-base font-semibold mb-2 mt-4 first:mt-0 leading-tight ${msg.sender === 'user' ? 'text-white' : 'text-gray-900'}`} {...props} />,
                                                    p: ({node, ...props}) => <p className={`mb-4 last:mb-0 leading-7 text-base ${msg.sender === 'user' ? 'text-white' : 'text-gray-800'}`} {...props} />,
                                                    ul: ({node, ...props}) => <ul className="list-disc list-inside mb-4 space-y-2 ml-4" {...props} />,
                                                    ol: ({node, ...props}) => <ol className="list-decimal list-inside mb-4 space-y-2 ml-4" {...props} />,
                                                    li: ({node, ...props}) => <li className={`leading-7 text-base ${msg.sender === 'user' ? 'text-white' : 'text-gray-800'}`} {...props} />,
                                                    strong: ({node, ...props}) => <strong className={`font-semibold ${msg.sender === 'user' ? 'text-white' : 'text-gray-900'}`} {...props} />,
                                                    em: ({node, ...props}) => <em className={`italic ${msg.sender === 'user' ? 'text-white' : 'text-gray-700'}`} {...props} />,
                                                    a: ({node, ...props}) => <a className={`underline transition-colors font-medium ${msg.sender === 'user' ? 'text-blue-300 hover:text-blue-200' : 'text-blue-600 hover:text-blue-800'}`} {...props} />,
                                                    code: ({node, ...props}) => <code className={`px-2 py-1 rounded text-sm font-mono border ${msg.sender === 'user' ? 'bg-gray-700 text-gray-200 border-gray-600' : 'bg-gray-100 text-gray-800 border-gray-300'}`} {...props} />,
                                                    pre: ({node, ...props}) => <pre className={`p-4 rounded-lg text-sm font-mono overflow-x-auto mb-4 border ${msg.sender === 'user' ? 'bg-gray-800 text-gray-200 border-gray-600' : 'bg-gray-900 text-gray-100 border-gray-700'}`} {...props} />,
                                                    blockquote: ({node, ...props}) => <blockquote className={`border-l-4 pl-4 italic mb-4 py-3 rounded-r-lg ${msg.sender === 'user' ? 'border-blue-300 text-gray-200 bg-blue-900/20' : 'border-blue-400 text-gray-700 bg-blue-50'}`} {...props} />,
                                                    // Custom component for fragment references
                                                    text: ({node, ...props}) => {
                                                        const text = props.children;
                                                        if (typeof text === 'string' && text.includes('secondo il frammento analizzato')) {
                                                            const parts = text.split('secondo il frammento analizzato');
                                                            return (
                                                                <span>
                                                                    {parts[0]}
                                                                    secondo il frammento analizzato
                                                                    <ReferenceButton fragmentId="1" onClick={handleFragmentClick} />
                                                                    {parts[1]}
                                                                </span>
                                                            );
                                                        }
                                                        return <span {...props} />;
                                                    }
                                                }}
                                            >
                                                {msg.text}
                                            </ReactMarkdown>
                                            
                                            {/* Thinking Section (Collapsible) */}
                                            {msg.thinking && (
                                                <ThinkingSection thinking={msg.thinking} />
                                            )}
                                        </div>
                                        {/* Disabled "Scrivendo..." indicator to avoid conflicts with streaming */}
                                        {false && msg.isStreaming && (
                                            <div className="flex items-center mt-2">
                                                <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse mr-2"></div>
                                                <span className="text-xs text-gray-500">Scrivendo...</span>
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
                            {/* {isLoading && (
                                <motion.div
                                    initial={{ opacity: 0 }}
                                    animate={{ opacity: 1 }}
                                    className="flex justify-start"
                                >
                                    <div className="bg-gray-100 p-3 rounded-lg">
                                        <div className="flex space-x-1">
                                            <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                                            <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{animationDelay: '0.1s'}}></div>
                                            <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{animationDelay: '0.2s'}}></div>
                                        </div>
                                    </div>
                                </motion.div>
                            )} */}
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
        </div>
    );
};

export default Chat;
