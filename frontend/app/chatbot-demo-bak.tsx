'use client';

import {
  Conversation,
  ConversationContent,
  ConversationScrollButton,
} from '@/components/ai-elements/conversation';
import { Message, MessageContent } from '@/components/ai-elements/message';
import {
  PromptInput,
  PromptInputButton,
  PromptInputModelSelect,
  PromptInputModelSelectContent,
  PromptInputModelSelectItem,
  PromptInputModelSelectTrigger,
  PromptInputModelSelectValue,
  PromptInputSubmit,
  PromptInputTextarea,
  PromptInputToolbar,
  PromptInputTools,
} from '@/components/ai-elements/prompt-input';
import {
  Actions,
  Action,
} from '@/components/ai-elements/actions';
import { useState, Fragment, useRef } from 'react';
import { fetchEventSource } from '@microsoft/fetch-event-source';
import { Response } from '@/components/ai-elements/response';
import { GlobeIcon, RefreshCcwIcon, CopyIcon } from 'lucide-react';
import {
  Source,
  Sources,
  SourcesContent,
  SourcesTrigger,
} from '@/components/ai-elements/sources';
import {
  Reasoning,
  ReasoningContent,
  ReasoningTrigger,
} from '@/components/ai-elements/reasoning';
import { Loader } from '@/components/ai-elements/loader';

// 定义消息类型
interface MessagePart {
  type: 'text' | 'reasoning' | 'source-url';
  text: string;
  url?: string;
}

interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  parts: MessagePart[];
}

type ChatStatus = 'submitted' | 'streaming' | 'ready' | 'error';

const models = [
  {
    name: 'GPT 4o',
    value: 'openai/gpt-4o',
  },
  {
    name: 'Deepseek R1',
    value: 'deepseek/deepseek-r1',
  },
];

const ChatBotDemo = () => {
  const [input, setInput] = useState('');
  const [model, setModel] = useState<string>(models[0].value);
  const [webSearch, setWebSearch] = useState(false);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [status, setStatus] = useState<ChatStatus>('ready');
  const abortControllerRef = useRef<AbortController | null>(null);

  // 发送消息函数
  const sendMessage = async (text: string) => {
    // 中止之前的请求
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    
    const controller = new AbortController();
    abortControllerRef.current = controller;

    // 添加用户消息
    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      role: 'user',
      parts: [{ type: 'text', text }]
    };
    
    setMessages(prev => [...prev, userMessage]);
    setStatus('submitted');

    let currentMessageId = '';
    let currentContent = '';

    try {
      await fetchEventSource('http://127.0.0.1:8000/agent', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          text,
        }),
        signal: controller.signal,
        async onopen(response) {
          if (response.ok && response.headers.get('content-type')?.includes('text/event-stream')) {
            setStatus('streaming');
            console.log('SSE connection opened');
          } else if (response.status >= 400 && response.status < 500) {
            // 客户端错误
            throw new Error(`HTTP error! status: ${response.status}`);
          } else {
            // 其他错误
            throw new Error(`HTTP error! status: ${response.status}`);
          }
        },
        onmessage(msg) {
          try {
            if (msg.data && msg.data.trim() !== '') {
              const eventData = JSON.parse(msg.data);
              
              switch (eventData.type) {
                case 'RUN_STARTED':
                  // 开始新的助手消息
                  currentMessageId = '';
                  currentContent = '';
                  break;
                  
                case 'TEXT_MESSAGE':
                  const { message_id, content } = eventData.data;
                  
                  if (message_id !== currentMessageId) {
                    // 新消息开始
                    currentMessageId = message_id;
                    currentContent = content;
                    
                    const assistantMessage: ChatMessage = {
                      id: message_id,
                      role: 'assistant',
                      parts: [{ type: 'text', text: content }]
                    };
                    
                    setMessages(prev => [...prev, assistantMessage]);
                  } else {
                    // 继续当前消息
                    currentContent += content;
                    
                    setMessages(prev => prev.map(msg => 
                      msg.id === message_id 
                        ? {
                            ...msg,
                            parts: msg.parts.map(part => 
                              part.type === 'text' 
                                ? { ...part, text: currentContent }
                                : part
                            )
                          }
                        : msg
                    ));
                  }
                  break;
                  
                case 'RUN_FINISHED':
                  setStatus('ready');
                  break;
              }
            }
          } catch (error) {
            console.error('Error parsing SSE data:', error);
          }
        },
        onclose() {
          console.log('SSE connection closed');
          setStatus('ready');
        },
        onerror(err) {
          console.error('SSE error:', err);
          setStatus('error');
          throw err; // 重新抛出错误以触发重连机制
        },
      });
    } catch (error) {
      if (error instanceof Error && error.name === 'AbortError') {
        console.log('Request was aborted');
      } else {
        console.error('Error sending message:', error);
        setStatus('error');
      }
    }
  };

  // 重新生成最后一条消息
  const regenerate = () => {
    if (messages.length >= 2) {
      const lastUserMessage = messages[messages.length - 2];
      if (lastUserMessage.role === 'user') {
        // 移除最后一条助手消息
        setMessages(prev => prev.slice(0, -1));
        // 重新发送用户消息
        sendMessage(lastUserMessage.parts[0].text);
      }
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (input.trim()) {
      sendMessage(input);
      setInput('');
    }
  };

  return (
    <div className="max-w-4xl mx-auto p-6 relative size-full h-screen">
      <div className="flex flex-col h-full">
        <Conversation className="h-full">
          <ConversationContent>
            {messages.map((message) => (
              <div key={message.id}>
                {message.role === 'assistant' && message.parts.filter((part) => part.type === 'source-url').length > 0 && (
                  <Sources>
                    <SourcesTrigger
                      count={
                        message.parts.filter(
                          (part) => part.type === 'source-url',
                        ).length
                      }
                    />
                    {message.parts.filter((part) => part.type === 'source-url').map((part, i) => (
                      <SourcesContent key={`${message.id}-${i}`}>
                        <Source
                          key={`${message.id}-${i}`}
                          href={part.url}
                          title={part.url}
                        />
                      </SourcesContent>
                    ))}
                  </Sources>
                )}
                {message.parts.map((part, i) => {
                  switch (part.type) {
                    case 'text':
                      return (
                        <Fragment key={`${message.id}-${i}`}>
                          <Message from={message.role}>
                            <MessageContent>
                              <Response>
                                {part.text}
                              </Response>
                            </MessageContent>
                          </Message>
                          {message.role === 'assistant' && i === message.parts.length - 1 && message.id === messages.at(-1)?.id && (
                            <Actions className="mt-2">
                              <Action
                                onClick={() => regenerate()}
                                label="Retry"
                              >
                                <RefreshCcwIcon className="size-3" />
                              </Action>
                              <Action
                                onClick={() =>
                                  navigator.clipboard.writeText(part.text)
                                }
                                label="Copy"
                              >
                                <CopyIcon className="size-3" />
                              </Action>
                            </Actions>
                          )}
                        </Fragment>
                      );
                    case 'reasoning':
                      return (
                        <Reasoning
                          key={`${message.id}-${i}`}
                          className="w-full"
                          isStreaming={status === 'streaming' && i === message.parts.length - 1 && message.id === messages.at(-1)?.id}
                        >
                          <ReasoningTrigger />
                          <ReasoningContent>{part.text}</ReasoningContent>
                        </Reasoning>
                      );
                    default:
                      return null;
                  }
                })}
              </div>
            ))}
            {status === 'submitted' && <Loader />}
          </ConversationContent>
          <ConversationScrollButton />
        </Conversation>

        <PromptInput onSubmit={handleSubmit} className="mt-4">
          <PromptInputTextarea
            onChange={(e) => setInput(e.target.value)}
            value={input}
          />
          <PromptInputToolbar>
            <PromptInputTools>
              <PromptInputButton
                variant={webSearch ? 'default' : 'ghost'}
                onClick={() => setWebSearch(!webSearch)}
              >
                <GlobeIcon size={16} />
                <span>Search</span>
              </PromptInputButton>
              <PromptInputModelSelect
                onValueChange={(value) => {
                  setModel(value);
                }}
                value={model}
              >
                <PromptInputModelSelectTrigger>
                  <PromptInputModelSelectValue />
                </PromptInputModelSelectTrigger>
                <PromptInputModelSelectContent>
                  {models.map((model) => (
                    <PromptInputModelSelectItem key={model.value} value={model.value}>
                      {model.name}
                    </PromptInputModelSelectItem>
                  ))}
                </PromptInputModelSelectContent>
              </PromptInputModelSelect>
            </PromptInputTools>
            <PromptInputSubmit disabled={!input} status={status} />
          </PromptInputToolbar>
        </PromptInput>
      </div>
    </div>
  );
};

export default ChatBotDemo;