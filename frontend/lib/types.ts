// 定义消息类型
export interface MessagePart {
  type: 'text' | 'reasoning' | 'source-url';
  text: string;
  url?: string;
}

export enum MessageRole {
  USER = 'user',
  ASSISTANT = 'assistant',
}

export interface ChatMessage {
  id: string;
  role: MessageRole;
  parts: MessagePart[];
}

export type ChatStatus = 'submitted' | 'streaming' | 'ready' | 'error';

export enum ArtifactType {
  ORIGINAL = 'original',
  COMMENT = 'comment',
}

export interface ArtifactData {
  id: string;
  role: MessageRole;
  type: ArtifactType;
  title: string;
  description?: string;
  content: string;
  created_at?: string;
  updated_at?: string;
  isStreaming?: boolean; // 新增：流式状态标识
}