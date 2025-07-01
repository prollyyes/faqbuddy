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

            while (true) {
                const { done, value } = await reader.read();
                if (done) break;

                const chunk = decoder.decode(value);
                const lines = chunk.split('\n');

                for (const line of lines) {
                    if (line.startsWith('data: ')) {
                        try {
                            const data = JSON.parse(line.slice(6));
                            console.log('Streaming data:', data);
                            
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
                            } else if (data.type === 'complete') {
                                setMessages(prev => {
                                    const newMessages = [...prev];
                                    newMessages[messageIndex] = {
                                        ...newMessages[messageIndex],
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
                                        <div className="text-sm prose prose-sm max-w-none">
                                            <ReactMarkdown
                                                components={{
                                                    h1: ({node, ...props}) => <h1 className="text-lg font-bold mb-2" {...props} />,
                                                    h2: ({node, ...props}) => <h2 className="text-base font-semibold mb-2" {...props} />,
                                                    h3: ({node, ...props}) => <h3 className="text-sm font-semibold mb-1" {...props} />,
                                                    p: ({node, ...props}) => <p className="mb-2" {...props} />,
                                                    ul: ({node, ...props}) => <ul className="list-disc list-inside mb-2" {...props} />,
                                                    ol: ({node, ...props}) => <ol className="list-decimal list-inside mb-2" {...props} />,
                                                    li: ({node, ...props}) => <li className="mb-1" {...props} />,
                                                    strong: ({node, ...props}) => <strong className="font-bold" {...props} />,
                                                    em: ({node, ...props}) => <em className="italic" {...props} />,
                                                    a: ({node, ...props}) => <a className="text-blue-600 underline hover:text-blue-800" {...props} />,
                                                }}
                                            >
                                                {msg.text}
                                            </ReactMarkdown>
                                        </div>
                                        {msg.isStreaming && (
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
