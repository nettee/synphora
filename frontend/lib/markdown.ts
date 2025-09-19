// 计算markdown文件中有意义的字数
export const countMeaningfulWords = (content: string): number => {
  // 移除markdown语法标记
  const text = content
    // 移除代码块
    .replace(/```[\s\S]*?```/g, '')
    // 移除行内代码
    .replace(/`[^`]*`/g, '')
    // 移除链接 [text](url)，保留text部分
    .replace(/\[([^\]]*)\]\([^)]*\)/g, '$1')
    // 移除图片 ![alt](url)
    .replace(/!\[[^\]]*\]\([^)]*\)/g, '')
    // 移除标题标记
    .replace(/^#{1,6}\s+/gm, '')
    // 移除引用标记
    .replace(/^>\s*/gm, '')
    // 移除列表标记
    .replace(/^[\s]*[-*+]\s+/gm, '')
    .replace(/^[\s]*\d+\.\s+/gm, '')
    // 移除水平分割线
    .replace(/^[-*_]{3,}$/gm, '')
    // 移除粗体和斜体标记
    .replace(/\*\*([^*]*)\*\*/g, '$1')
    .replace(/\*([^*]*)\*/g, '$1')
    .replace(/__([^_]*)__/g, '$1')
    .replace(/_([^_]*)_/g, '$1')
    // 移除删除线
    .replace(/~~([^~]*)~~/g, '$1')
    // 移除多余的空白字符
    .replace(/\s+/g, ' ')
    .trim();

  // 计算中文字符数和英文单词数
  const chineseChars = (text.match(/[\u4e00-\u9fa5]/g) || []).length;
  const englishWords = (text.match(/[a-zA-Z]+/g) || []).length;
  
  return chineseChars + englishWords;
};