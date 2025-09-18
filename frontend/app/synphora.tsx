"use client";

import { useState } from "react";

import { ArtifactDetail, ArtifactList } from "@/components/artifact";
import { Chatbot } from "@/components/chatbot";
import { testArtifacts, testMessages } from "@/lib/test-data";
import { ArtifactData } from "@/lib/types";

enum ArtifactStatus {
  COLLAPSED = "collapsed",
  EXPANDED = "expanded",
}

const useArtifacts = (
  initialStatus: ArtifactStatus = ArtifactStatus.COLLAPSED,
  initialArtifacts: ArtifactData[],
  initialArtifactId: string
) => {
  const [artifacts, setArtifacts] = useState<ArtifactData[]>(initialArtifacts);
  const [artifactStatus, setArtifactStatus] =
    useState<ArtifactStatus>(initialStatus);
  const [currentArtifactId, setCurrentArtifactId] =
    useState<string>(initialArtifactId);

  const currentArtifact = artifacts.find((artifact) => artifact.id === currentArtifactId) || artifacts[0];

  const collapseArtifact = () => {
    setArtifactStatus(ArtifactStatus.COLLAPSED);
  };

  const expandArtifact = () => {
    setArtifactStatus(ArtifactStatus.EXPANDED);
  };

  return {
    artifacts,
    artifactStatus,
    currentArtifact,
    collapseArtifact,
    expandArtifact,
    setCurrentArtifactId,
  };
};

const SynphoraPage = () => {
  const {
    artifacts,
    artifactStatus,
    currentArtifact,
    collapseArtifact,
    expandArtifact,
    setCurrentArtifactId,
  } = useArtifacts(
    ArtifactStatus.COLLAPSED,
    testArtifacts,
    testArtifacts[0].id
  );

  const openArtifact = (artifactId: string) => {
    expandArtifact();
    setCurrentArtifactId(artifactId);
  };

  const closeArtifact = () => {
    collapseArtifact();
  };

  return (
    <div className="w-full h-screen mx-auto p-6">
      <div className="w-full h-full flex gap-4">
        {/* 
          根据 artifactStatus 灵活布局
          当 artifact 部分收起时，artifact 部分固定占据 w-96 宽度，chatbot 部分占据剩余宽度
          当 artifact 部分展开时，artifact 部分占据 2/3 宽度，chatbot 部分占据 1/3 宽度
        */}
        <div
          data-role="chatbot-container"
          className={`flex flex-col h-full ${
            artifactStatus === ArtifactStatus.COLLAPSED ? "flex-1" : "w-1/3"
          }`}
        >
          <Chatbot initialMessages={testMessages} />
        </div>
        <div
          data-role="artifact-container"
          className={`h-full transition-all duration-300 ${
            artifactStatus === ArtifactStatus.COLLAPSED ? "w-96" : "w-2/3"
          }`}
        >
          {artifactStatus === ArtifactStatus.COLLAPSED ? (
            <ArtifactList
              artifacts={artifacts}
              onOpenArtifact={openArtifact}
            />
          ) : (
            <ArtifactDetail
              artifact={currentArtifact}
              onCloseArtifact={closeArtifact}
            />
          )}
        </div>
      </div>
    </div>
  );
};

export default SynphoraPage;
