"use client";

import { ArtifactData, ArtifactType, MessageRole } from "@/lib/types";
import { useState } from "react";
import SynphoraPage from "./synphora";
import WelcomePage from "./welcome";
import { countMeaningfulWords } from "@/lib/markdown";
import { testArtifacts } from "@/lib/test-data";

interface FileContent {
  file: File;
  content: string;
}

enum CurrentPage {
  WELCOME = "welcome",
  MAIN = "main",
}

// 生成唯一ID
const generateId = () =>
  Date.now().toString() + Math.random().toString(36).substr(2, 9);

// 将文件转换为 artifacts
const convertFilesToArtifacts = (
  fileContents: FileContent[]
): ArtifactData[] => {
  return fileContents.map((fileContent) => ({
    id: generateId(),
    role: MessageRole.USER,
    type: ArtifactType.ORIGINAL,
    title: fileContent.file.name,
    description: `${countMeaningfulWords(fileContent.content)} 字`,
    content: fileContent.content,
  }));
};

export default function Home() {
  const [currentPage, setCurrentPage] = useState<CurrentPage>(
    CurrentPage.WELCOME
  );
  const [uploadedArtifacts, setUploadedArtifacts] = useState<ArtifactData[]>(
    []
  );

  // 如果需要跳过欢迎页面，则定义环境变量 NEXT_PUBLIC_SKIP_WELCOME 为 true
  const skipWelcome = process.env.NEXT_PUBLIC_SKIP_WELCOME === "true";
  if (skipWelcome) {
    return <SynphoraPage initialArtifacts={testArtifacts} />;
  }

  const handleFilesUploaded = (fileContents: FileContent[]) => {
    const artifacts = convertFilesToArtifacts(fileContents);
    setUploadedArtifacts(artifacts);
    setCurrentPage(CurrentPage.MAIN);
  };

  if (currentPage === CurrentPage.WELCOME) {
    return <WelcomePage onFilesUploaded={handleFilesUploaded} />;
  } else if (currentPage === CurrentPage.MAIN) {
    return <SynphoraPage initialArtifacts={uploadedArtifacts} />;
  } else {
    throw new Error("Invalid current page");
  }
}
