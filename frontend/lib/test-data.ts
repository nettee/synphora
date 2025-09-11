import { ArtifactData, ArtifactType, ChatMessage, MessageRole } from "./types";

export const testMessages: ChatMessage[] = [
  {
    id: '1',
    role: MessageRole.USER,
    parts: [{ type: 'text', text: '你好' }],
  },
  {
    id: '2',
    role: MessageRole.ASSISTANT,
    parts: [{ type: 'text', text: '你好，我是你的助手。' }],
  },
  {
    id: '3',
    role: MessageRole.USER,
    parts: [{ type: 'text', text: '你叫什么名字？' }],
  },
  {
    id: '4',
    role: MessageRole.ASSISTANT,
    parts: [{ type: 'text', text: '我叫小助手。' }],
  },
];

export const testArtifact: ArtifactData = {
  id: '1',
  role: MessageRole.USER,
  type: ArtifactType.ORIGINAL,
  title: 'Dijkstra\'s Algorithm Implementation',
  description: '文章原文',
  content: 'This is the artifact content.',
};
