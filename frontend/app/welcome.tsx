"use client";

import { Button } from "@/components/ui/button";
import { useCallback, useRef, useState } from "react";

interface UploadedFile {
  file: File;
  status: 'uploading' | 'completed' | 'error';
  progress: number;
  content?: string;
}

interface WelcomePageProps {
  onFilesUploaded: () => void;
}

export default function WelcomePage({ onFilesUploaded }: WelcomePageProps) {
  const [uploadedFiles, setUploadedFiles] = useState<UploadedFile[]>([]);
  const [isDragActive, setIsDragActive] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // 处理文件上传
  const processFiles = useCallback(async (files: FileList | File[]) => {
    const fileArray = Array.from(files);
    
    // 创建上传文件状态
    const newUploadedFiles: UploadedFile[] = fileArray.map(file => ({
      file,
      status: 'uploading',
      progress: 0,
    }));

    setUploadedFiles(prev => [...prev, ...newUploadedFiles]);

    // 实际上传文件到后端
    
    for (let i = 0; i < newUploadedFiles.length; i++) {
      const uploadedFile = newUploadedFiles[i];
      try {
        console.log(`🚀 Starting upload for file "${uploadedFile.file.name}"`);
        
        // 创建 FormData
        const formData = new FormData();
        formData.append('file', uploadedFile.file);

        // 上传到后端
        const response = await fetch('http://127.0.0.1:8000/artifacts/upload', {
          method: 'POST',
          body: formData,
        });

        if (!response.ok) {
          throw new Error(`Upload failed: ${response.statusText}`);
        }

        const artifact = await response.json();
        console.log(`✅ File "${uploadedFile.file.name}" uploaded successfully, artifact ID: ${artifact.id}`);
        
        // 更新进度到100%
        setUploadedFiles(prev => 
          prev.map((f, index) => 
            index === prev.length - newUploadedFiles.length + i
              ? { ...f, progress: 100 }
              : f
          )
        );

        // 更新为完成状态，同时保存内容
        setUploadedFiles(prev => 
          prev.map((f, index) => 
            index === prev.length - newUploadedFiles.length + i
              ? { ...f, status: 'completed' as const }
              : f
          )
        );
      } catch (error) {
        console.error('Upload error:', error);
        // 更新为错误状态
        setUploadedFiles(prev => 
          prev.map((f, index) => 
            index === prev.length - newUploadedFiles.length + i
              ? { ...f, status: 'error' as const }
              : f
          )
        );
      }
    }

    // 延迟一下再上报成功处理的文件
    setTimeout(() => {
      onFilesUploaded();
    }, 500);

  }, [onFilesUploaded]);

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

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragActive(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      processFiles(e.dataTransfer.files);
    }
  }, [processFiles]);

  // 处理文件选择
  const handleFileSelect = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      processFiles(e.target.files);
    }
  }, [processFiles]);

  const handleSelectFiles = () => {
    fileInputRef.current?.click();
  };

  const allFilesCompleted = uploadedFiles.length > 0 && uploadedFiles.every(f => f.status === 'completed');

  return (
    <div className="min-h-screen bg-background p-6">
      <div className="max-w-3xl mx-auto h-full flex flex-col">
        {/* 标题区域 */}
        <div className="text-center py-20">
          <h1 className="text-3xl font-bold text-foreground mb-4">
            Synphora
          </h1>
          <p className="text-muted-foreground text-base">
            你的文章分析和润色助手
          </p>
        </div>

        {/* 上传区域 */}
        <div className="flex-1 flex flex-col">
          <div
            className={`
              flex flex-col items-center justify-center border-1 border-dashed rounded-lg p-8 text-center transition-all duration-200 bg-gray-50 mb-6
              ${isDragActive 
                ? 'border-foreground bg-muted/50' 
                : 'border-muted-foreground/30 hover:border-muted-foreground/50'
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
              {isDragActive ? '释放文件以上传' : '上传你的文章'}
            </h3>
            <p className="text-muted-foreground text-sm mb-6">
              拖拽文件或点击选择，支持 .txt 和 .md 文件
            </p>

            <div className="flex gap-2">
              <Button
                onClick={handleSelectFiles}
                variant="outline"
                className="font-medium"
              >
                选择文件
              </Button>

              <Button
                variant="outline"
                className="font-medium text-foreground bg-gradient-to-r from-blue-100 via-purple-100 to-pink-100 bg-clip-border border-1 border-transparent bg-origin-border  relative overflow-hidden"
              >
                <span className="text-foreground">
                  AI 生成示例文章
                </span>
              </Button>
            </div>
            
            <input
              ref={fileInputRef}
              type="file"
              multiple
              accept=".txt,.md"
              onChange={handleFileSelect}
              className="hidden"
            />
          </div>

          {/* 上传进度 */}
          {uploadedFiles.length > 0 && (
            <div className="bg-card border border-border rounded-lg p-6">
              <h3 className="text-base font-medium text-foreground mb-4">
                文件处理中
              </h3>
              <div className="space-y-4">
                {uploadedFiles.map((uploadedFile, index) => (
                  <div key={`${uploadedFile.file.name}-${index}`} className="space-y-2">
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-foreground truncate pr-4">
                        {uploadedFile.file.name}
                      </span>
                      <span className="text-sm text-muted-foreground flex-shrink-0">
                        {uploadedFile.status === 'completed' ? '完成' : 
                         uploadedFile.status === 'error' ? '错误' : 
                         `${uploadedFile.progress}%`}
                      </span>
                    </div>
                    <div className="w-full bg-muted rounded-full h-1.5">
                      <div
                        className={`h-1.5 rounded-full transition-all duration-300 ${
                          uploadedFile.status === 'completed' ? 'bg-foreground' :
                          uploadedFile.status === 'error' ? 'bg-destructive' :
                          'bg-muted-foreground'
                        }`}
                        style={{ width: `${uploadedFile.progress}%` }}
                      />
                    </div>
                  </div>
                ))}
              </div>
              
              {allFilesCompleted && (
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
