'use client'
import React from 'react'
import { IoSendSharp, IoStop, IoRefresh } from "react-icons/io5";
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
    const [currentRequestId, setCurrentRequestId] = React.useState(null);

    const handleFragmentClick = (fragmentId) => {
        setSelectedFragment(fragmentId);
        console.log('Clicked fragment:', fragmentId);
    };

    const stopGeneration = async () => {
        if (!currentRequestId) {
            return;
        }
        
        try {
            const response = await fetch(`${HOST}/chat/stop`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ request_id: currentRequestId }),
            });
            
            const result = await response.json();
            
            if (result.success) {
                setIsLoading(false);
                setCurrentRequestId(null);
                
                // Update the last message to show it was stopped
                setMessages(prev => {
                    const newMessages = [...prev];
                    const lastMessage = newMessages[newMessages.length - 1];
                    if (lastMessage && lastMessage.isStreaming) {
                        newMessages[newMessages.length - 1] = {
                            ...lastMessage,
                            text: lastMessage.text + '\n\n*Generazione interrotta dall\'utente*',
                            isStreaming: false,
                            isStopped: true
                        };
                    }
                    return newMessages;
                });
            }
        } catch (error) {
            console.error('Error stopping generation:', error);
        }
    };

    const emergencyReset = async () => {
        try {
            const response = await fetch(`${HOST}/chat/reset`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                }
            });
            
            const result = await response.json();
            
            if (result.success) {
                setIsLoading(false);
                setCurrentRequestId(null);
                
                setMessages(prev => [...prev, {
                    text: '🔄 **Sistema ripristinato con successo!** Le risorse bloccate sono state liberate.',
                    sender: 'bot',
                    timestamp: new Date(),
                    isError: false,
                    isStreaming: false
                }]);
            } else {
                setMessages(prev => [...prev, {
                    text: '❌ **Errore durante il ripristino:** ' + (result.message || result.error),
                    sender: 'bot',
                    timestamp: new Date(),
                    isError: true,
                    isStreaming: false
                }]);
            }
        } catch (error) {
            setMessages(prev => [...prev, {
                text: '❌ **Errore durante il ripristino:** ' + error.message,
                sender: 'bot',
                timestamp: new Date(),
                isError: true,
                isStreaming: false
            }]);
        }
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
            // Use SIMPLE streaming approach that works with our fixed backend
            console.log('🚀 Starting SIMPLE streaming request...');
            const response = await fetch(`${HOST}/chat?streaming=true&include_metadata=true`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Accept': 'text/event-stream',
                },
                body: JSON.stringify({ question: currentMessage }),
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            // Simple line-by-line streaming reader
            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let buffer = '';
            let accumulatedText = '';

            while (true) {
                const { done, value } = await reader.read();
                if (done) break;

                buffer += decoder.decode(value, { stream: true });
                const lines = buffer.split('\n');
                buffer = lines.pop() || ''; // Keep incomplete line in buffer

                for (const line of lines) {
                    if (!line.startsWith('data: ')) continue;
                    
                    const jsonData = line.slice(6);
                    if (jsonData === '[DONE]') break;

                    try {
                        const data = JSON.parse(jsonData);
                        
                        if (data.type === 'token' && data.token) {
                            accumulatedText += data.token;
                            setMessages(prev => {
                                const newMessages = [...prev];
                                newMessages[streamingMessageIndex] = {
                                    ...newMessages[streamingMessageIndex],
                                    text: accumulatedText,
                                    isStreaming: true
                                };
                                return newMessages;
                            });
                        } else if (data.type === 'metadata' && data.finished) {
                            console.log('✅ Streaming completed');
                            break;
                        }
                    } catch (e) {
                        console.warn('Failed to parse SSE data:', e);
                    }
                }
            }

            // Finalize the message
            setMessages(prev => {
                const newMessages = [...prev];
                newMessages[streamingMessageIndex] = {
                    ...newMessages[streamingMessageIndex],
                    text: accumulatedText || 'No response received',
                    isStreaming: false,
                    isLoading: false
                };
                return newMessages;
            });
        } catch (error) {
            console.error('Streaming failed:', error);
            setMessages(prev => {
                const newMessages = [...prev];
                newMessages[streamingMessageIndex] = {
                    text: 'Si è verificato un errore durante la generazione della risposta. Riprova più tardi.',
                    sender: 'bot',
                    timestamp: new Date(),
                    isError: true,
                    isStreaming: false
                };
                return newMessages;
            });
        } finally {
            setIsLoading(false);
            setCurrentRequestId(null);
        }
    };

    const sendMessageStreaming = async (question, messageIndex) => {
        let reader = null;
        let abortController = new AbortController();
        
        try {
            const response = await fetch(`${HOST}/chat?streaming=true`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Accept': 'text/event-stream',
                },
                body: JSON.stringify({ question }),
                signal: abortController.signal,
            });

            if (!response.ok) {
                const errorText = await response.text();
                throw new Error(`HTTP error! status: ${response.status} - ${errorText}`);
            }

            if (!response.body) {
                throw new Error('Response body is null - streaming not supported by server');
            }
            
            reader = response.body.getReader();
            const decoder = new TextDecoder();
            let accumulatedText = '';
            let sseBuffer = '';
            let hasReceivedData = false;

            // Set a reasonable timeout for the stream
            const streamTimeout = setTimeout(() => {
                console.warn('Stream timeout - aborting connection');
                abortController.abort();
            }, 180000); // 3 minutes

            try {
                while (true) {
                    const { done, value } = await reader.read();
                    
                    if (done) {
                        break;
                    }

                    if (value) {
                        hasReceivedData = true;
                        const decodedChunk = decoder.decode(value, { stream: true });
                        sseBuffer += decodedChunk;
                    }

                    // Process complete SSE events
                    let boundaryIndex;
                    while ((boundaryIndex = sseBuffer.indexOf('\n\n')) !== -1) {
                        const eventChunk = sseBuffer.slice(0, boundaryIndex);
                        sseBuffer = sseBuffer.slice(boundaryIndex + 2);

                        const lines = eventChunk.split('\n');
                        for (const line of lines) {
                            if (!line.startsWith('data: ')) continue;
                            
                            const jsonString = line.slice(6);
                            if (jsonString === '[DONE]') {
                                // Stream completion signal
                                clearTimeout(streamTimeout);
                                return;
                            }
                            
                            try {
                                const data = JSON.parse(jsonString);
                                
                                if (data.type === 'request_id') {
                                    setCurrentRequestId(data.request_id);
                                } else if (data.type === 'thinking') {
                                    setMessages(prev => {
                                        const newMessages = [...prev];
                                        newMessages[messageIndex] = {
                                            ...newMessages[messageIndex],
                                            thinking: data.thinking || '',
                                        };
                                        return newMessages;
                                    });
                                } else if (data.type === 'token') {
                                    const token = String(data.token || '');
                                    if (token && token !== 'undefined' && token !== 'null' && token.length > 0) {
                                        accumulatedText += token;
                                    }
                                    setMessages(prev => {
                                        const newMessages = [...prev];
                                        newMessages[messageIndex] = {
                                            ...newMessages[messageIndex],
                                            text: accumulatedText,
                                            isStreaming: true
                                        };
                                        return newMessages;
                                    });
                                } else if (data.type === 'cancelled') {
                                    setMessages(prev => {
                                        const newMessages = [...prev];
                                        newMessages[messageIndex] = {
                                            ...newMessages[messageIndex],
                                            text: accumulatedText + '\n\n*Generazione interrotta dall\'utente*',
                                            isStreaming: false,
                                            isStopped: true
                                        };
                                        return newMessages;
                                    });
                                    clearTimeout(streamTimeout);
                                    return;
                                } else if (data.type === 'metadata') {
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
                                    clearTimeout(streamTimeout);
                                    return;
                                } else if (data.type === 'complete') {
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
                                    clearTimeout(streamTimeout);
                                    return;
                                } else if (data.type === 'error') {
                                    if (data.severity === 'warning' && data.fallback) {
                                        // Non-fatal error with fallback
                                        continue;
                                    } else {
                                        // Fatal error
                                        setMessages(prev => {
                                            const newMessages = [...prev];
                                            const currentMsg = newMessages[messageIndex] || {};
                                            newMessages[messageIndex] = {
                                                ...currentMsg,
                                                text: accumulatedText + `\n\n**Errore:** ${data.message}`,
                                                isStreaming: false,
                                                isError: true,
                                            };
                                            return newMessages;
                                        });
                                        clearTimeout(streamTimeout);
                                        return;
                                    }
                                }
                            } catch (parseError) {
                                console.warn('Error parsing SSE data:', parseError);
                                // Continue processing other events
                            }
                        }
                    }
                }
            } finally {
                clearTimeout(streamTimeout);
            }

            // If we get here without proper completion, finalize the message gracefully
            if (hasReceivedData && accumulatedText.length > 0) {
                setMessages(prev => {
                    const newMessages = [...prev];
                    newMessages[messageIndex] = {
                        ...newMessages[messageIndex],
                        text: accumulatedText,
                        isStreaming: false,
                        metadata: {
                            chosen: 'RAG',
                            streaming: true,
                            note: 'Stream ended without completion signal'
                        }
                    };
                    return newMessages;
                });
            }

        } catch (error) {
            // Handle different types of errors gracefully
            if (error.name === 'AbortError') {
                console.warn('Stream was aborted (timeout or manual cancellation)');
            } else if (error.message.includes('Error in input stream')) {
                console.warn('Browser detected input stream error - connection likely terminated');
            } else {
                console.error('Streaming error:', error);
                throw error; // Re-throw unexpected errors
            }
        } finally {
            // Clean up resources
            if (reader) {
                try {
                    reader.releaseLock();
                } catch (e) {
                    // Ignore lock release errors
                }
            }
            
            // Ensure we always finalize the streaming state
            setMessages(prev => {
                const newMessages = [...prev];
                if (newMessages[messageIndex] && newMessages[messageIndex].isStreaming) {
                    newMessages[messageIndex] = {
                        ...newMessages[messageIndex],
                        isStreaming: false
                    };
                }
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
                                        {msg.metadata && !msg.isStreaming && (
                                            <div className="text-xs mt-2 opacity-70">
                                                <p>Metodo: {msg.metadata.chosen}</p>
                                                {msg.metadata.ml_confidence && (
                                                    <p>Confidenza: {(msg.metadata.ml_confidence * 100).toFixed(1)}%</p>
                                                )}
                                                {msg.metadata.streaming && (
                                                    <p>Streaming: Attivato</p>
                                                )}
                                                {msg.metadata.note && (
                                                    <p className="text-yellow-600">Note: {msg.metadata.note}</p>
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
                      className="group p-2 rounded-full transition-all duration-200 bg-orange-500 text-white hover:bg-orange-600 disabled:opacity-50 mr-2"
                      onClick={emergencyReset}
                      title="Ripristina sistema (usa se bloccato)"
                    >
                      <IoRefresh className="text-[1.65rem]" />
                    </button>
                    <button
                      className={`group p-2 rounded-full transition-all duration-200 ${
                        isLoading 
                          ? "bg-red-500 text-white hover:bg-red-600" 
                          : "bg-white text-[#822433] hover:bg-[#822433]"
                      } disabled:opacity-50`}
                      onClick={isLoading ? stopGeneration : sendMessage}
                      disabled={!isLoading && !message.trim()}
                    >
                      {isLoading ? (
                        <IoStop className="text-[1.65rem] group-hover:text-white" />
                      ) : (
                        <IoSendSharp className="text-[1.65rem] group-hover:text-white" />
                      )}
                    </button>
                  </div>
                </motion.div>
            </motion.div>
        </div>
    );
};

export default Chat;
