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

export const testArtifacts: ArtifactData[] = [
  {
    id: '1',
    role: MessageRole.USER,
    type: ArtifactType.ORIGINAL,
    title: 'Dijkstra\'s Algorithm Implementation',
    content: 'This is the artifact content.',
  },
  {
    id: '2',
    role: MessageRole.ASSISTANT,
    type: ArtifactType.COMMENT,
    title: 'React Component Example',
    content: 'import React from "react";\n\nfunction Example() {\n  return <div>Hello World</div>;\n}\n\nexport default Example;',
  },
  {
    id: '3',
    role: MessageRole.ASSISTANT,
    type: ArtifactType.COMMENT,
    title: 'API Response Schema',
    content: '{\n  "status": "success",\n  "data": {\n    "message": "Hello from API"\n  }\n}',
  },
];