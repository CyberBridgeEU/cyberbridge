import { useRef, useEffect, useState } from 'react';
import { Drawer, Button, Input, Space, Typography, message } from 'antd';
import { SendOutlined, StopOutlined, DeleteOutlined, RobotOutlined, UserOutlined } from '@ant-design/icons';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import useChatStore from '../store/useChatStore';

const { Text } = Typography;
const { TextArea } = Input;

const MAX_INPUT_LENGTH = 2000;

const STARTER_QUESTIONS = [
    'What is CyberBridge and how can it help with compliance?',
    'How do I run a security scan?',
    'What frameworks does CyberBridge support?',
    'How does risk management work?',
];

interface ChatbotDrawerProps {
    open: boolean;
    onClose: () => void;
}

export default function ChatbotDrawer({ open, onClose }: ChatbotDrawerProps) {
    const { messages, isStreaming, error, sendMessage, cancelStream, clearChat } = useChatStore();
    const [input, setInput] = useState('');
    const messagesEndRef = useRef<HTMLDivElement>(null);
    const inputRef = useRef<HTMLTextAreaElement>(null);

    // Auto-scroll to bottom when messages update
    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages]);

    // Focus input when drawer opens
    useEffect(() => {
        if (open) {
            setTimeout(() => inputRef.current?.focus(), 300);
        }
    }, [open]);

    // Show error as message notification
    useEffect(() => {
        if (error) {
            message.error(error);
        }
    }, [error]);

    const handleClose = () => {
        if (isStreaming) cancelStream();
        onClose();
    };

    const handleSend = () => {
        const trimmed = input.trim();
        if (!trimmed || isStreaming) return;
        setInput('');
        sendMessage(trimmed);
    };

    const handleKeyDown = (e: React.KeyboardEvent) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSend();
        }
    };

    const handleStarterClick = (question: string) => {
        sendMessage(question);
    };

    const isEmpty = messages.length === 0;

    return (
        <Drawer
            title={
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                    <Space>
                        <RobotOutlined style={{ fontSize: '18px', color: '#0f386a' }} />
                        <span>AI Assistant</span>
                    </Space>
                    {messages.length > 0 && (
                        <Button
                            type="text"
                            size="small"
                            icon={<DeleteOutlined />}
                            onClick={clearChat}
                            disabled={isStreaming}
                            style={{ color: 'rgba(0, 0, 0, 0.45)' }}
                        >
                            Clear
                        </Button>
                    )}
                </div>
            }
            placement="right"
            width={400}
            open={open}
            onClose={handleClose}
            destroyOnClose={false}
            styles={{
                body: {
                    display: 'flex',
                    flexDirection: 'column',
                    padding: 0,
                    height: '100%',
                    overflow: 'hidden',
                }
            }}
        >
            {/* Messages Area */}
            <div style={{
                flex: 1,
                overflowY: 'auto',
                padding: '16px',
                display: 'flex',
                flexDirection: 'column',
                gap: '12px'
            }}>
                {isEmpty ? (
                    <div style={{
                        flex: 1,
                        display: 'flex',
                        flexDirection: 'column',
                        alignItems: 'center',
                        justifyContent: 'center',
                        gap: '24px',
                        padding: '20px'
                    }}>
                        <div style={{ textAlign: 'center' }}>
                            <RobotOutlined style={{ fontSize: '48px', color: '#0f386a', marginBottom: '12px' }} />
                            <div>
                                <Text strong style={{ fontSize: '16px', display: 'block', marginBottom: '4px' }}>
                                    CyberBridge AI Assistant
                                </Text>
                                <Text type="secondary" style={{ fontSize: '13px' }}>
                                    Ask me anything about the platform
                                </Text>
                            </div>
                        </div>
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', width: '100%' }}>
                            {STARTER_QUESTIONS.map((q) => (
                                <Button
                                    key={q}
                                    type="default"
                                    block
                                    style={{
                                        textAlign: 'left',
                                        height: 'auto',
                                        padding: '10px 14px',
                                        whiteSpace: 'normal',
                                        lineHeight: '1.4',
                                        borderColor: '#d9d9d9',
                                    }}
                                    onClick={() => handleStarterClick(q)}
                                >
                                    {q}
                                </Button>
                            ))}
                        </div>
                    </div>
                ) : (
                    <>
                        {messages.map((msg, idx) => (
                            <div
                                key={idx}
                                style={{
                                    display: 'flex',
                                    justifyContent: msg.role === 'user' ? 'flex-end' : 'flex-start',
                                    gap: '8px',
                                    alignItems: 'flex-start'
                                }}
                            >
                                {msg.role === 'assistant' && (
                                    <div style={{
                                        width: '28px',
                                        height: '28px',
                                        borderRadius: '50%',
                                        backgroundColor: '#0f386a',
                                        display: 'flex',
                                        alignItems: 'center',
                                        justifyContent: 'center',
                                        flexShrink: 0,
                                        marginTop: '2px'
                                    }}>
                                        <RobotOutlined style={{ color: '#fff', fontSize: '14px' }} />
                                    </div>
                                )}
                                <div style={{
                                    maxWidth: '80%',
                                    padding: '10px 14px',
                                    borderRadius: msg.role === 'user' ? '16px 16px 4px 16px' : '16px 16px 16px 4px',
                                    backgroundColor: msg.role === 'user' ? '#0f386a' : '#f0f0f0',
                                    color: msg.role === 'user' ? '#fff' : 'inherit',
                                    wordBreak: 'break-word'
                                }}>
                                    {msg.role === 'assistant' ? (
                                        <div className="chatbot-markdown" style={{ fontSize: '13px', lineHeight: '1.5' }}>
                                            {msg.content ? (
                                                <ReactMarkdown remarkPlugins={[remarkGfm]}>
                                                    {msg.content}
                                                </ReactMarkdown>
                                            ) : isStreaming && idx === messages.length - 1 ? (
                                                <span style={{ opacity: 0.6 }}>Thinking...</span>
                                            ) : null}
                                        </div>
                                    ) : (
                                        <div style={{ fontSize: '13px', lineHeight: '1.5', whiteSpace: 'pre-wrap' }}>
                                            {msg.content}
                                        </div>
                                    )}
                                </div>
                                {msg.role === 'user' && (
                                    <div style={{
                                        width: '28px',
                                        height: '28px',
                                        borderRadius: '50%',
                                        backgroundColor: '#8c8c8c',
                                        display: 'flex',
                                        alignItems: 'center',
                                        justifyContent: 'center',
                                        flexShrink: 0,
                                        marginTop: '2px'
                                    }}>
                                        <UserOutlined style={{ color: '#fff', fontSize: '14px' }} />
                                    </div>
                                )}
                            </div>
                        ))}
                        <div ref={messagesEndRef} />
                    </>
                )}
            </div>

            {/* Input Area */}
            <div style={{
                borderTop: '1px solid #f0f0f0',
                padding: '12px 16px',
                backgroundColor: '#fff'
            }}>
                <div style={{ display: 'flex', gap: '8px', alignItems: 'flex-end' }}>
                    <TextArea
                        ref={inputRef as React.Ref<any>}
                        value={input}
                        onChange={(e) => setInput(e.target.value.slice(0, MAX_INPUT_LENGTH))}
                        onKeyDown={handleKeyDown}
                        placeholder="Ask about CyberBridge..."
                        autoSize={{ minRows: 1, maxRows: 4 }}
                        disabled={isStreaming}
                        style={{ resize: 'none' }}
                    />
                    {isStreaming ? (
                        <Button
                            type="default"
                            danger
                            icon={<StopOutlined />}
                            onClick={cancelStream}
                            style={{ flexShrink: 0 }}
                        />
                    ) : (
                        <Button
                            type="primary"
                            icon={<SendOutlined />}
                            onClick={handleSend}
                            disabled={!input.trim()}
                            style={{ flexShrink: 0, backgroundColor: '#0f386a', borderColor: '#0f386a' }}
                        />
                    )}
                </div>
                {input.length > MAX_INPUT_LENGTH * 0.9 && (
                    <Text type="secondary" style={{ fontSize: '11px', marginTop: '4px', display: 'block' }}>
                        {input.length}/{MAX_INPUT_LENGTH}
                    </Text>
                )}
            </div>
        </Drawer>
    );
}
