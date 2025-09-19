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

const articleContent = `
# 如何在 Cursor 与 Claude Code 之间选择？ 

## 选择依据

1. 你会编程吗？ 

- No -> Claude Code 
- Yes -> 2 

2. 你希望代码 100% 由 AI 来写吗？ 

- Yes -> Claude Code 
- No -> 3 

3. 你是写新功能还是维护已有代码？ 

- 新功能 -> Claude Code 
- 维护已有代码 -> Cursor 

## 一些说明

+ 这主要体现的是 Cursor 和 Claude Code 产品哲学的不同。Cursor 关注的还是人机交互循环，即人和 AI 各写一部分代码，Claude Code 则是全自动化编程，希望你所有代码都交给 AI 来写 
+ 对于不会编程的人，或者希望代码全部由 AI 来写的人，那你就是纯粹的 Vibe Coding。在这种情况下，Cursor 的 IDE 功能和代码 review 功能都发挥不出作用，所以使用 Claude Code 是最顺畅的。 
+ Claude Code 在写新功能上水平非常高，但是维护已有代码的效果不尽如人意。这时候使用 Cursor 是最合适的，无论是读懂代码还是修改代码，都可以在 Cursor 中精确控制给 AI 的上下文。 
+ 大部分路径的结果是 Claude Code，并不代表 Cursor 的水平不行，只是在这些场景下 Claude Code 更方便使用而已。用一个比喻：Cursor 是一台有各种精细按钮的专业相机，而 Claude Code 是一台全自动相机。如果你是专业人员，那么用 Cursor 的上限会更高，但是简单的场景，你会更喜欢用 Claude Code 的。
`;

export const testArtifacts: ArtifactData[] = [
  {
    id: '1',
    role: MessageRole.USER,
    type: ArtifactType.ORIGINAL,
    title: '如何在 Cursor 与 Claude Code 之间选择.md',
    content: articleContent,
  },
  // {
  //   id: '2',
  //   role: MessageRole.ASSISTANT,
  //   type: ArtifactType.COMMENT,
  //   title: 'React Component Example',
  //   content: 'import React from "react";\n\nfunction Example() {\n  return <div>Hello World</div>;\n}\n\nexport default Example;',
  // },
  // {
  //   id: '3',
  //   role: MessageRole.ASSISTANT,
  //   type: ArtifactType.COMMENT,
  //   title: 'API Response Schema',
  //   content: '{\n  "status": "success",\n  "data": {\n    "message": "Hello from API"\n  }\n}',
  // },
];