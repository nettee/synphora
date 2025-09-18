"use client";

import { ArtifactData, ArtifactType, MessageRole } from "@/lib/types";
import { useState } from "react";
import SynphoraPage from "./synphora";
import WelcomePage from "./welcome";
import { countMeaningfulWords } from "@/lib/markdown";

interface FileContent {
  file: File;
  content: string;
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
  const [currentPage, setCurrentPage] = useState<"welcome" | "main">("welcome");
  const [uploadedArtifacts, setUploadedArtifacts] = useState<ArtifactData[]>(
    []
  );

  const handleFilesUploaded = (fileContents: FileContent[]) => {
    const artifacts = convertFilesToArtifacts(fileContents);
    setUploadedArtifacts(artifacts);
    setCurrentPage("main");
  };

  if (currentPage === "welcome") {
    return <WelcomePage onFilesUploaded={handleFilesUploaded} />;
  }

  return <SynphoraPage initialArtifacts={uploadedArtifacts} />;
}
