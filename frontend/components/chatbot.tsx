import {
  Conversation,
  ConversationContent,
  ConversationScrollButton,
} from "@/components/ai-elements/conversation";
import {
  PromptInput,
  PromptInputModelSelect,
  PromptInputModelSelectContent,
  PromptInputModelSelectItem,
  PromptInputModelSelectTrigger,
  PromptInputModelSelectValue,
  PromptInputSubmit,
  PromptInputTextarea,
  PromptInputToolbar,
  PromptInputTools,
} from "@/components/ai-elements/prompt-input";
import {
  Reasoning,
  ReasoningContent,
  ReasoningTrigger,
} from "@/components/ai-elements/reasoning";
import { Response } from "@/components/ai-elements/response";
import {
  Source,
  Sources,
  SourcesContent,
  SourcesTrigger,
} from "@/components/ai-elements/sources";
import { Suggestion, Suggestions } from "@/components/ai-elements/suggestion";
import { fetchEventSource } from "@microsoft/fetch-event-source";
import { CopyIcon, RefreshCcwIcon } from "lucide-react";
import { Fragment, useRef, useState } from "react";
import { ChatMessage, ChatStatus, MessageRole } from "@/lib/types";
import { Message, MessageContent } from "@/components/ai-elements/message";
import { Actions, Action } from "@/components/ai-elements/actions";
import { Loader } from "@/components/ai-elements/loader";

const models = [
  {
    name: "Deepseek V3",
    value: "deepseek/deepseek-chat",
  },
  {
    name: "Deepseek R1",
    value: "deepseek/deepseek-reasoner",
  },
];

const suggestions = process.env.NEXT_PUBLIC_CHAT_SUGGESTIONS?.split(',').map(suggestion => ({
  value: suggestion.trim()
})) || [];

export const Chatbot = ({
  initialMessages = [],
  onArtifactContentStart,
  onArtifactContentChunk,
  onArtifactContentComplete,
  onArtifactListUpdated,
}: {
  initialMessages: ChatMessage[];
  onArtifactContentStart: (artifactId: string, title: string, description?: string) => void;
  onArtifactContentChunk: (artifactId: string, chunk: string) => void;
  onArtifactContentComplete: (artifactId: string) => void;
  onArtifactListUpdated: () => void;
}) => {
  const [input, setInput] = useState("");
  const [model, setModel] = useState<string>(models[0].value);
  const [messages, setMessages] = useState<ChatMessage[]>(initialMessages);
  const [status, setStatus] = useState<ChatStatus>("ready");
  const abortControllerRef = useRef<AbortController | null>(null);

  const addUserMessage = (text: string) => {
    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      role: MessageRole.USER,
      parts: [{ type: "text", text }],
    };
    setMessages((prev) => [...prev, userMessage]);
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

    setStatus("submitted");

    let currentMessageId = "";
    let currentContent = "";

    try {
      await fetchEventSource("http://127.0.0.1:8000/agent", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          message: text,
        }),
        signal: controller.signal,
        async onopen(response) {
          if (
            response.ok &&
            response.headers.get("content-type")?.includes("text/event-stream")
          ) {
            setStatus("streaming");
            console.log("SSE connection opened");
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
            if (msg.data && msg.data.trim() !== "") {
              const eventData = JSON.parse(msg.data);

              switch (eventData.type) {
                case "RUN_STARTED":
                  // 开始新的助手消息
                  currentMessageId = "";
                  currentContent = "";
                  break;

                case "TEXT_MESSAGE":
                  const { message_id, content } = eventData.data;

                  if (message_id !== currentMessageId) {
                    // 新消息开始
                    currentMessageId = message_id;
                    currentContent = content;

                    const assistantMessage: ChatMessage = {
                      id: message_id,
                      role: MessageRole.ASSISTANT,
                      parts: [{ type: "text", text: content }],
                    };

                    setMessages((prev) => [...prev, assistantMessage]);
                  } else {
                    // 继续当前消息
                    currentContent += content;

                    setMessages((prev) =>
                      prev.map((msg) =>
                        msg.id === message_id
                          ? {
                              ...msg,
                              parts: msg.parts.map((part) =>
                                part.type === "text"
                                  ? { ...part, text: currentContent }
                                  : part
                              ),
                            }
                          : msg
                      )
                    );
                  }
                  break;

                case "RUN_FINISHED":
                  setStatus("ready");
                  break;

                case "ARTIFACT_CONTENT_START":
                  const { artifact_id: startArtifactId, title, description } = eventData.data;
                  console.log("Artifact content start:", eventData.data);
                  onArtifactContentStart(startArtifactId, title, description);
                  break;

                case "ARTIFACT_CONTENT_CHUNK":
                  const { artifact_id: chunkArtifactId, content: chunkContent } = eventData.data;
                  // console.log("Artifact content chunk:", eventData.data);
                  onArtifactContentChunk(chunkArtifactId, chunkContent);
                  break;

                case "ARTIFACT_CONTENT_COMPLETE":
                  const { artifact_id: completeArtifactId } = eventData.data;
                  console.log("Artifact content complete:", eventData.data);
                  onArtifactContentComplete(completeArtifactId);
                  break;

                case "ARTIFACT_LIST_UPDATED":
                  console.log("Artifact list updated:", eventData.data);
                  onArtifactListUpdated();
                  break;
              }
            }
          } catch (error) {
            console.error("Error parsing SSE data:", error);
          }
        },
        onclose() {
          console.log("SSE connection closed");
          setStatus("ready");
        },
        onerror(err) {
          console.error("SSE error:", err);
          setStatus("error");
          throw err; // 重新抛出错误以触发重连机制
        },
      });
    } catch (error) {
      if (error instanceof Error && error.name === "AbortError") {
        console.log("Request was aborted");
      } else {
        console.error("Error sending message:", error);
        setStatus("error");
      }
    }
  };

  // 重新生成最后一条消息
  const regenerate = () => {
    if (messages.length >= 2) {
      const lastUserMessage = messages[messages.length - 2];
      if (lastUserMessage.role === MessageRole.USER) {
        // 移除最后一条助手消息
        setMessages((prev) => prev.slice(0, -1));
        // 重新发送用户消息
        sendMessage(lastUserMessage.parts[0].text);
      }
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (input.trim()) {
      sendMessage(input);
      setInput("");
    }
  };

  return (
    <div data-role="chatbot" className="w-full max-w-3xl h-full mx-auto flex flex-col">
      <Conversation className="h-full">
        <ConversationContent>
          {messages.map((message) => (
            <div key={message.id}>
              {message.role === MessageRole.ASSISTANT &&
                message.parts.filter((part) => part.type === "source-url")
                  .length > 0 && (
                  <Sources>
                    <SourcesTrigger
                      count={
                        message.parts.filter(
                          (part) => part.type === "source-url"
                        ).length
                      }
                    />
                    {message.parts
                      .filter((part) => part.type === "source-url")
                      .map((part, i) => (
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
                  case "text":
                    return (
                      <Fragment key={`${message.id}-${i}`}>
                        <Message from={message.role}>
                          <MessageContent>
                            <Response>{part.text}</Response>
                          </MessageContent>
                        </Message>
                        {message.role === MessageRole.ASSISTANT &&
                          i === message.parts.length - 1 &&
                          message.id === messages.at(-1)?.id && (
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
                  case "reasoning":
                    return (
                      <Reasoning
                        key={`${message.id}-${i}`}
                        className="w-full"
                        isStreaming={
                          status === "streaming" &&
                          i === message.parts.length - 1 &&
                          message.id === messages.at(-1)?.id
                        }
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
          {status === "submitted" && <Loader />}
        </ConversationContent>
        <ConversationScrollButton />
      </Conversation>

      <Suggestions>
        {suggestions.map((suggestion) => (
          <Suggestion
            key={suggestion.value}
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
                  <PromptInputModelSelectItem
                    key={model.value}
                    value={model.value}
                  >
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
  );
};
