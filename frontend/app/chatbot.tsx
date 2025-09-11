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
import {
  Artifact,
  ArtifactAction,
  ArtifactActions,
  ArtifactContent,
  ArtifactDescription,
  ArtifactHeader,
  ArtifactTitle,
} from '@/components/ai-elements/artifact';
import { useState, Fragment, useRef } from 'react';
import { fetchEventSource } from '@microsoft/fetch-event-source';
import { Response } from '@/components/ai-elements/response';
import { GlobeIcon, RefreshCcwIcon, CopyIcon, ChevronRightIcon, ChevronLeftIcon, XIcon } from 'lucide-react';
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
import { Suggestion, Suggestions } from '@/components/ai-elements/suggestion';

import { MessagePart, ChatMessage, ChatStatus, MessageRole, ArtifactData, ArtifactType } from '@/lib/types';
import { testMessages, testArtifacts } from '@/lib/test-data';
import { Streamdown } from 'streamdown';

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

const suggestions = [
  {
    value: "评价这篇文章",
  },
  {
    value: "分析文章定位",
  },
  {
    value: "撰写候选标题",
  },
];

const ChatBotDemo = () => {
  const [input, setInput] = useState('');
  const [model, setModel] = useState<string>(models[0].value);
  const [messages, setMessages] = useState<ChatMessage[]>(testMessages);
  const [status, setStatus] = useState<ChatStatus>('ready');
  const abortControllerRef = useRef<AbortController | null>(null);

  const [isArtifactCollapsed, setIsArtifactCollapsed] = useState(false);
  const [artifacts, setArtifacts] = useState<ArtifactData[]>(testArtifacts);
  const [currentArtifactId, setCurrentArtifactId] = useState<string>(testArtifacts[0].id);

  // 获取当前工件
  const currentArtifact = artifacts.find(artifact => artifact.id === currentArtifactId) || artifacts[0];

  // 处理工件选择
  const handleArtifactSelect = (artifactId: string) => {
    setCurrentArtifactId(artifactId);
    setIsArtifactCollapsed(false); // 选择工件后自动展开
  };

  // 工件列表组件
  const ArtifactList = () => {
    const userArtifacts = artifacts.filter(artifact => artifact.role === MessageRole.USER);
    const assistantArtifacts = artifacts.filter(artifact => artifact.role === MessageRole.ASSISTANT);

    const renderArtifactItem = (artifact: ArtifactData) => (
      <div
        key={artifact.id}
        onClick={() => handleArtifactSelect(artifact.id)}
        className="p-3 rounded-lg border border-gray-200 cursor-pointer transition-all duration-200 hover:shadow-sm hover:border-gray-300 hover:bg-gray-50"
      >
        <div className="flex items-start justify-between gap-2">
          <div className="flex-1 min-w-0">
            <div className="text-sm font-medium text-gray-900 truncate">
              {artifact.title}
            </div>
            {artifact.description && (
              <div className="text-xs text-gray-600 mt-1 line-clamp-2">
                {artifact.description}
              </div>
            )}
          </div>
          <div className={`text-xs px-2 py-1 rounded-full flex-shrink-0 ${
            artifact.type === ArtifactType.ORIGINAL 
              ? 'bg-green-100 text-green-700' 
              : 'bg-blue-100 text-blue-700'
          }`}>
            {artifact.type === ArtifactType.ORIGINAL ? '原文' : '评论'}
          </div>
        </div>
      </div>
    );

    return (
      <div className="h-full flex flex-col bg-white border border-gray-200 rounded-lg">
        <div className="p-4 border-b border-gray-200 bg-gray-50 rounded-t-lg">
          <h3 className="text-sm font-medium text-gray-900">所有文件</h3>
        </div>
        <div className="flex-1 overflow-y-auto">
          {/* 用户添加的部分 */}
          {userArtifacts.length > 0 && (
            <div className="p-3 pb-0">
              <div className="flex items-center gap-2 mb-3">
                <div className="text-xs font-medium text-gray-600 uppercase tracking-wide">
                  你添加的
                </div>
              </div>
              <div className="space-y-2">
                {userArtifacts.map(renderArtifactItem)}
              </div>
            </div>
          )}
          
          {/* AI生成的部分 */}
          {assistantArtifacts.length > 0 && (
            <div className="p-3">
              <div className="flex items-center gap-2 mb-3">
                <div className="text-xs font-medium text-gray-600 uppercase tracking-wide">
                  生成的
                </div>
              </div>
              <div className="space-y-2">
                {assistantArtifacts.map(renderArtifactItem)}
              </div>
            </div>
          )}
          
          {/* 空状态 */}
          {artifacts.length === 0 && (
            <div className="flex-1 flex items-center justify-center p-6">
              <div className="text-center text-gray-500">
                <div className="text-sm">暂无文件</div>
                <div className="text-xs mt-1">开始对话来创建文件</div>
              </div>
            </div>
          )}
        </div>
      </div>
    );
  };

  const addUserMessage = (text: string) => {
    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      role: MessageRole.USER,
      parts: [{ type: 'text', text }]
    };
    setMessages(prev => [...prev, userMessage]);
  };

  // 发送消息函数
  const sendMessage = async (text: string) => {
    // 中止之前的请求
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    
    const controller = new AbortController();
    abortControllerRef.current = controller;

    // 添加用户消息
    addUserMessage(text);
    
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
                      role: MessageRole.ASSISTANT,
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
      if (lastUserMessage.role === MessageRole.USER) {
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
    <div className="w-full h-screen mx-auto p-6">
      <div className="w-full h-full flex gap-4">
        <div 
          data-role="chatbot-container" 
          className={`flex flex-col h-full ${ isArtifactCollapsed ? 'flex-1' : 'w-1/3' }`}
        >
          <div className="w-full max-w-3xl h-full mx-auto flex flex-col">
            <Conversation className="h-full">
              <ConversationContent>
                {messages.map((message) => (
                  <div key={message.id}>
                    {message.role === MessageRole.ASSISTANT && message.parts.filter((part) => part.type === 'source-url').length > 0 && (
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
                              {message.role === MessageRole.ASSISTANT && i === message.parts.length - 1 && message.id === messages.at(-1)?.id && (
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

            <Suggestions>
              {suggestions.map((suggestion) => (
                <Suggestion key={suggestion.value}
                  onClick={() => {
                    sendMessage(suggestion.value);
                  }}
                  suggestion={suggestion.value}
                />
              ))}
            </Suggestions>

            <PromptInput onSubmit={handleSubmit} className="mt-4">
              <PromptInputTextarea
                onChange={(e) => setInput(e.target.value)}
                value={input}
              />
              <PromptInputToolbar>
              <PromptInputTools>
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
        <div 
          data-role="artifact-container" 
          className={`h-full transition-all duration-300 ${ isArtifactCollapsed ? 'w-96' : 'w-2/3' }`}
        >
          {isArtifactCollapsed ? (
            <ArtifactList />
          ) : (
            <Artifact className="h-full">
              <ArtifactHeader>
                <div>
                  <ArtifactTitle>{currentArtifact.title}</ArtifactTitle>
                  <ArtifactDescription>{currentArtifact.description}</ArtifactDescription>
                </div>
                <ArtifactActions>
                  <ArtifactAction 
                    icon={XIcon} 
                    label="关闭" 
                    tooltip="关闭面板"
                    onClick={() => setIsArtifactCollapsed(true)}
                  />
                </ArtifactActions>
              </ArtifactHeader>
              <ArtifactContent className="h-full">
                {/* 定义 classname 为 streamdown，这样 globals.css 中的样式会生效 */}
                <Streamdown className="streamdown">{currentArtifact.content}</Streamdown>
              </ArtifactContent>
            </Artifact>
          )}
        </div>
      </div>
    </div>
  );
};

export default ChatBotDemo;