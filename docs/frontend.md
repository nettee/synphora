# Frontend 文档

## 应用架构

应用采用多页面架构，通过主页面 (`frontend/app/page.tsx`) 管理页面状态和路由：

1. **欢迎页面** (`WelcomePage`): 应用启动时的文件上传界面
2. **主应用页面** (`SynphoraPage`): 核心的聊天和构件管理界面

## `WelcomePage` 组件 (`frontend/components/welcome-page.tsx`)

`WelcomePage` 是应用的入口页面，提供文件上传功能，让用户可以导入文件作为分析的起点。

### 主要功能

1. **文件上传**:
   * 支持点击选择文件和拖拽上传两种方式

2. **文件处理**:
   * 读取文件内容并转换为 `ArtifactData` 格式
   * 完成上传后自动跳转到主应用页面

## `SynphoraPage` 组件 (`frontend/app/synphora.tsx`)

`SynphoraPage` 是应用的核心 UI 页面组件。它负责管理一个双栏布局，该布局由一个聊天机器人（`Chatbot`）和一个"构件"（Artifact）管理区域组成。

### 主要功能

1. **动态布局管理**:
   * 组件的主要职责是控制聊天机器人和构件区域之间的空间分配。
   * 它使用一个内部状态 `artifactStatus` (拥有 `COLLAPSED` 或 `EXPANDED` 两种状态) 来动态调整两个区域的宽度。

2. **两种视图状态**:
   * **折叠状态 (`COLLAPSED`)**: 在这种默认状态下，构件区域会显示为一个固定宽度的侧边栏，其中包含 `ArtifactList` 组件，用于列出所有可用的构件。此时，聊天机器人区域占据剩余的主要空间。
   * **展开状态 (`EXPANDED`)**: 当用户从列表中选择一个构件时，构件区域会展开以显示该构件的详细信息（使用 `ArtifactDetail` 组件），并占据大部分屏幕宽度。此时，聊天机器人区域的宽度会相应收缩。

3. **状态与交互逻辑**:
   * 组件通过自定义 Hook `useArtifacts` 来封装和管理与构件相关的状态逻辑。
   * 这些状态包括完整的构件列表、当前的视图状态（折叠/展开）以及当前选中的构件 ID。
   * 提供了 `openArtifact` 和 `closeArtifact` 方法来处理用户交互，切换构件区域的折叠和展开状态。

4. **外部数据支持**:
   * 支持通过 `artifacts` 属性接收外部传入的构件数据
   * 如果没有传入数据，则使用默认的测试数据

### 接口

```typescript
interface SynphoraPageProps {
  artifacts?: ArtifactData[];
}
```

### 子组件依赖

* `Chatbot`: 独立的聊天机器人界面。
* `ArtifactList`: 在折叠状态下，负责显示所有构件的摘要列表。
* `ArtifactDetail`: 在展开状态下，负责显示单个构件的完整内容。

## 数据流

1. 用户在 `WelcomePage` 上传文件
2. 文件被转换为 `ArtifactData[]` 格式
3. 主页面接收数据并切换到 `SynphoraPage`
4. `SynphoraPage` 使用上传的文件作为初始构件数据
5. 用户可以在构件列表和详情之间切换浏览上传的文件