'use client';

import { useState } from 'react';

import { ArtifactDetail, ArtifactList } from '@/components/artifact';
import { Chatbot } from '@/components/conversation';
import { testArtifacts } from '@/lib/test-data';
import { ArtifactData } from '@/lib/types';



const ChatBotDemo = () => {
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

  return (
    <div className="w-full h-screen mx-auto p-6">
      <div className="w-full h-full flex gap-4">
        <div 
          data-role="chatbot-container" 
          className={`flex flex-col h-full ${ isArtifactCollapsed ? 'flex-1' : 'w-1/3' }`}
        >
          <Chatbot />
        </div>
        <div 
          data-role="artifact-container" 
          className={`h-full transition-all duration-300 ${ isArtifactCollapsed ? 'w-96' : 'w-2/3' }`}
        >
          {isArtifactCollapsed ? (
            <ArtifactList artifacts={artifacts} onOpenArtifact={handleArtifactSelect} />
          ) : (
            <ArtifactDetail artifact={currentArtifact} onCloseArtifact={() => setIsArtifactCollapsed(true)} />
          )}
        </div>
      </div>
    </div>
  );
};

export default ChatBotDemo;