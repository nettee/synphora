import json
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
import uuid

from synphora.models import ArtifactData, ArtifactType


class FileStorage:
    def __init__(self, storage_path: str = "tests/data/store"):
        self.storage_path = Path(storage_path)
        self.metadata_file = self.storage_path / "metadata.json"
        self._ensure_storage_directory()
        self._metadata: Dict[str, dict] = self._load_metadata()
    
    def _ensure_storage_directory(self):
        """确保存储目录存在"""
        self.storage_path.mkdir(parents=True, exist_ok=True)
    
    def _load_metadata(self) -> Dict[str, dict]:
        """从metadata.json加载元数据"""
        if self.metadata_file.exists():
            try:
                with open(self.metadata_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                return {}
        return {}
    
    def _save_metadata(self):
        """保存元数据到metadata.json"""
        with open(self.metadata_file, 'w', encoding='utf-8') as f:
            json.dump(self._metadata, f, indent=2, ensure_ascii=False)
    
    def _get_data_file_path(self, artifact_id: str) -> Path:
        """获取数据文件路径"""
        return self.storage_path / f"{artifact_id}.txt"
    
    def create_artifact(
        self, 
        title: str, 
        content: str, 
        artifact_type: ArtifactType = ArtifactType.ORIGINAL,
        role: str = "user",
        description: Optional[str] = None
    ) -> ArtifactData:
        """创建新的 artifact"""
        artifact_id = str(uuid.uuid4())
        now = datetime.now().isoformat()
        
        # 保存内容到数据文件
        data_file = self._get_data_file_path(artifact_id)
        with open(data_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        # 保存元数据
        metadata = {
            "id": artifact_id,
            "role": role,
            "type": artifact_type.value,
            "title": title,
            "description": description,
            "created_at": now,
            "updated_at": now
        }
        
        self._metadata[artifact_id] = metadata
        self._save_metadata()
        
        return ArtifactData(content=content, **metadata)
    
    def get_artifact(self, artifact_id: str) -> Optional[ArtifactData]:
        """根据 ID 获取 artifact"""
        metadata = self._metadata.get(artifact_id)
        if not metadata:
            return None
        
        # 读取内容文件
        data_file = self._get_data_file_path(artifact_id)
        if not data_file.exists():
            return None
        
        try:
            with open(data_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            return ArtifactData(content=content, **metadata)
        except IOError:
            return None
    
    def list_artifacts(self) -> List[ArtifactData]:
        """获取所有 artifacts"""
        artifacts = []
        for artifact_id in self._metadata:
            artifact = self.get_artifact(artifact_id)
            if artifact:
                artifacts.append(artifact)
        return artifacts
    
    def update_artifact(
        self, 
        artifact_id: str, 
        title: Optional[str] = None,
        content: Optional[str] = None,
        description: Optional[str] = None
    ) -> Optional[ArtifactData]:
        """更新 artifact"""
        metadata = self._metadata.get(artifact_id)
        if not metadata:
            return None
        
        now = datetime.now().isoformat()
        
        # 更新元数据
        if title is not None:
            metadata['title'] = title
        if description is not None:
            metadata['description'] = description
        metadata['updated_at'] = now
        
        # 更新内容文件
        if content is not None:
            data_file = self._get_data_file_path(artifact_id)
            with open(data_file, 'w', encoding='utf-8') as f:
                f.write(content)
        
        self._metadata[artifact_id] = metadata
        self._save_metadata()
        
        return self.get_artifact(artifact_id)
    
    def delete_artifact(self, artifact_id: str) -> bool:
        """删除 artifact"""
        if artifact_id not in self._metadata:
            return False
        
        # 删除数据文件
        data_file = self._get_data_file_path(artifact_id)
        if data_file.exists():
            data_file.unlink()
        
        # 删除元数据
        del self._metadata[artifact_id]
        self._save_metadata()
        
        return True
    
    def clear_all(self):
        """清空所有 artifacts（主要用于测试）"""
        # 删除所有数据文件
        for artifact_id in self._metadata:
            data_file = self._get_data_file_path(artifact_id)
            if data_file.exists():
                data_file.unlink()
        
        # 清空元数据
        self._metadata.clear()
        self._save_metadata()