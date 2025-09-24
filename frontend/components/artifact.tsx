import { ArtifactData, ArtifactType, MessageRole } from "@/lib/types";
import {
  Artifact,
  ArtifactAction,
  ArtifactActions,
  ArtifactContent,
  ArtifactDescription,
  ArtifactHeader,
  ArtifactTitle,
} from "./ai-elements/artifact";
import { Streamdown } from "streamdown";
import { XIcon, Loader2 } from "lucide-react";

// Artifact 详情组件
export const ArtifactDetail = ({
  artifact,
  onCloseArtifact,
}: {
  artifact: ArtifactData;
  onCloseArtifact: () => void;
}) => {
  const showDebugInfo = process.env.NEXT_PUBLIC_SHOW_DEBUG_INFO === "true";

  return (
    <Artifact data-role="artifact-detail" className="h-full">
      <ArtifactHeader>
        <div>
          <ArtifactTitle className="flex items-center gap-2">
            {artifact.title}
            {artifact.isStreaming && (
              <Loader2 className="h-4 w-4 animate-spin text-blue-500" />
            )}
            {showDebugInfo && (
              <span className="text-xs text-gray-500">{artifact.id}</span>
            )}
          </ArtifactTitle>
          {artifact.description && (
            <ArtifactDescription>{artifact.description}</ArtifactDescription>
          )}
        </div>
        <ArtifactActions>
          <ArtifactAction
            icon={XIcon}
            label="关闭"
            tooltip="关闭面板"
            onClick={() => onCloseArtifact()}
          />
        </ArtifactActions>
      </ArtifactHeader>
      <ArtifactContent className="h-full">
        {/* 定义 classname 为 streamdown，这样 globals.css 中的样式会生效 */}
        <Streamdown className="streamdown">{artifact.content}</Streamdown>
        {artifact.isStreaming && (
          <div className="mt-2 text-sm text-gray-500 flex items-center gap-1">
            <Loader2 className="h-3 w-3 animate-spin" />
            正在生成中...
          </div>
        )}
      </ArtifactContent>
    </Artifact>
  );
};

// Artifact 列表组件
export const ArtifactList = ({
  artifacts,
  onOpenArtifact,
}: {
  artifacts: ArtifactData[];
  onOpenArtifact: (artifactId: string) => void;
}) => {
  const showDebugInfo = process.env.NEXT_PUBLIC_SHOW_DEBUG_INFO === "true";

  const userArtifacts = artifacts.filter(
    (artifact) => artifact.role === MessageRole.USER
  );
  const assistantArtifacts = artifacts.filter(
    (artifact) => artifact.role === MessageRole.ASSISTANT
  );

  const renderArtifactItem = (artifact: ArtifactData) => (
    <div
      key={artifact.id}
      onClick={() => onOpenArtifact(artifact.id)}
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
          {showDebugInfo && (
            <div className="text-xs text-gray-500 mt-1">{artifact.id}</div>
          )}
        </div>
        <div
          className={`text-xs px-2 py-1 rounded-full flex-shrink-0 ${
            artifact.type === ArtifactType.ORIGINAL
              ? "bg-green-100 text-green-700"
              : "bg-blue-100 text-blue-700"
          }`}
        >
          {artifact.type === ArtifactType.ORIGINAL ? "原文" : "评论"}
        </div>
      </div>
    </div>
  );

  return (
    <div
      data-role="artifact-list"
      className="h-full flex flex-col bg-white border border-gray-200 rounded-lg"
    >
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
