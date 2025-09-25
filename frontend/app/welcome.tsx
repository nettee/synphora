"use client";

import { Button } from "@/components/ui/button";
import { useCallback, useRef, useState } from "react";

interface UploadedFile {
  file: File;
  status: "uploading" | "completed" | "error";
  progress: number;
  content?: string;
}

interface WelcomePageProps {
  onWelcomeComplete: () => void;
}

export default function WelcomePage({ onWelcomeComplete }: WelcomePageProps) {
  const [uploadedFile, setUploadedFile] = useState<UploadedFile | null>(null);
  const [isDragActive, setIsDragActive] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // 处理文件上传
  const processFile = useCallback(
    async (file: File) => {
      // 创建上传文件状态
      const newUploadedFile: UploadedFile = {
        file,
        status: "uploading",
        progress: 0,
      };

      setUploadedFile(newUploadedFile);

      try {
        console.log(`🚀 Starting upload for file "${file.name}"`);

        // 创建 FormData
        const formData = new FormData();
        formData.append("file", file);

        // 上传到后端
        const response = await fetch("http://127.0.0.1:8000/artifacts/upload", {
          method: "POST",
          body: formData,
        });

        if (!response.ok) {
          throw new Error(`Upload failed: ${response.statusText}`);
        }

        const artifact = await response.json();
        console.log(
          `✅ File "${file.name}" uploaded successfully, artifact ID: ${artifact.id}`
        );

        // 更新进度到100%
        setUploadedFile((prev) => (prev ? { ...prev, progress: 100 } : prev));

        // 更新为完成状态
        setUploadedFile((prev) =>
          prev ? { ...prev, status: "completed" as const } : prev
        );

        // 延迟一下再上报成功处理的文件
        setTimeout(() => {
          onWelcomeComplete();
        }, 500);
      } catch (error) {
        console.error("Upload error:", error);
        // 更新为错误状态
        setUploadedFile((prev) =>
          prev ? { ...prev, status: "error" as const } : prev
        );
      }
    },
    [onWelcomeComplete]
  );

  // 处理拖拽
  const handleDrag = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
  }, []);

  const handleDragIn = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragActive(true);
  }, []);

  const handleDragOut = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragActive(false);
  }, []);

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      e.stopPropagation();
      setIsDragActive(false);

      if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
        processFile(e.dataTransfer.files[0]);
      }
    },
    [processFile]
  );

  // 处理文件选择
  const handleFileSelect = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      if (e.target.files && e.target.files.length > 0) {
        processFile(e.target.files[0]);
      }
    },
    [processFile]
  );

  const handleSelectFiles = () => {
    fileInputRef.current?.click();
  };

  const handleGenerateSampleArticle = async () => {
    try {
      console.log("🤖 Generating sample article...");
      setIsGenerating(true);

      // 添加生成进度显示
      const generatingFile: UploadedFile = {
        file: new File([""], "示例文章.md", { type: "text/markdown" }),
        status: "uploading",
        progress: 0,
      };

      setUploadedFile(generatingFile);

      // 模拟进度增长
      const progressInterval = setInterval(() => {
        setUploadedFile((prev) =>
          prev && prev.status === "uploading"
            ? {
                ...prev,
                progress: Math.min(prev.progress + Math.random() * 5, 98),
              }
            : prev
        );
      }, 800);

      const response = await fetch(
        "http://127.0.0.1:8000/artifacts/generate-sample",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            topic: null, // 使用默认主题
          }),
        }
      );

      // 清除进度更新
      clearInterval(progressInterval);

      if (!response.ok) {
        throw new Error(`Failed to generate article: ${response.statusText}`);
      }

      const artifact = await response.json();
      console.log(
        `✅ Sample article generated successfully, artifact ID: ${artifact.id}`
      );

      // 更新进度到100%并标记完成
      setUploadedFile((prev) =>
        prev ? { ...prev, progress: 100, status: "completed" as const } : prev
      );

      // 延迟一下再通知完成
      setTimeout(() => {
        onWelcomeComplete();
      }, 500);
    } catch (error) {
      console.error("Error generating sample article:", error);

      // 更新为错误状态
      setUploadedFile((prev) =>
        prev ? { ...prev, status: "error" as const } : prev
      );

      alert("生成示例文章失败，请稍后重试");
    } finally {
      setIsGenerating(false);
    }
  };

  return (
    <div className="min-h-screen bg-background p-6">
      <div className="max-w-3xl mx-auto h-full flex flex-col">
        {/* 标题区域 */}
        <div className="text-center py-20">
          <h1 className="text-3xl font-bold text-foreground mb-4">Synphora</h1>
          <p className="text-muted-foreground text-base">
            你的文章分析和润色助手
          </p>
        </div>

        {/* 上传区域 */}
        <div className="flex-1 flex flex-col">
          <div
            className={`
              flex flex-col items-center justify-center border-1 border-dashed rounded-lg p-8 text-center transition-all duration-200 bg-gray-50 mb-6
              ${
                isDragActive
                  ? "border-foreground bg-muted/50"
                  : "border-muted-foreground/30 hover:border-muted-foreground/50"
              }
            `}
            onDragEnter={handleDragIn}
            onDragLeave={handleDragOut}
            onDragOver={handleDrag}
            onDrop={handleDrop}
          >
            <div className="mb-6">
              <svg
                className="mx-auto h-12 w-12 text-muted-foreground"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={1.5}
                  d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
                />
              </svg>
            </div>

            <h3 className="text-lg font-medium text-foreground mb-2">
              {isDragActive ? "释放文件以上传" : "上传你的文章"}
            </h3>
            <p className="text-muted-foreground text-sm mb-6">
              拖拽文件或点击选择，支持 .txt 和 .md 文件
            </p>

            <div className="flex gap-2">
              <Button
                onClick={handleSelectFiles}
                disabled={isGenerating}
                variant="outline"
                className="font-medium"
              >
                选择文件
              </Button>

              <Button
                onClick={handleGenerateSampleArticle}
                disabled={isGenerating}
                variant="outline"
                className="font-medium text-foreground bg-gradient-to-r from-blue-100 via-purple-100 to-pink-100 bg-clip-border border-1 border-transparent bg-origin-border  relative overflow-hidden disabled:opacity-50"
              >
                <span className="text-foreground">
                  {isGenerating ? "AI 生成中..." : "AI 生成示例文章"}
                </span>
              </Button>
            </div>

            <input
              ref={fileInputRef}
              type="file"
              accept=".txt,.md"
              onChange={handleFileSelect}
              className="hidden"
            />
          </div>

          {/* 上传进度 */}
          {uploadedFile && (
            <div className="bg-card border border-border rounded-lg p-6">
              <h3 className="text-base font-medium text-foreground mb-4">
                文章生成中
              </h3>
              <div className="space-y-4">
                <div className="space-y-2">
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-foreground truncate pr-4">
                      {uploadedFile.file.name}
                    </span>
                  </div>
                  {/* 进度条 */}
                  <div className="w-full bg-muted rounded-full h-1.5">
                    <div
                      className={`h-1.5 rounded-full transition-all duration-300 ${
                        uploadedFile.status === "completed"
                          ? "bg-foreground"
                          : uploadedFile.status === "error"
                          ? "bg-destructive"
                          : "bg-muted-foreground"
                      }`}
                      style={{ width: `${uploadedFile.progress}%` }}
                    />
                  </div>
                </div>
              </div>

              {uploadedFile.status === "completed" && (
                <div className="mt-6 pt-4 border-t border-border text-center">
                  <p className="text-foreground text-sm font-medium">
                    文件处理完成，正在进入主界面...
                  </p>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
