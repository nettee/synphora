from typing import Dict, List, Optional
from datetime import datetime
import uuid

from synphora.models import ArtifactData, ArtifactType


class ArtifactManager:
    def __init__(self):
        self._artifacts: Dict[str, ArtifactData] = {}
    
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
        
        artifact = ArtifactData(
            id=artifact_id,
            role=role,
            type=artifact_type,
            title=title,
            description=description,
            content=content,
            created_at=now,
            updated_at=now
        )
        
        self._artifacts[artifact_id] = artifact
        return artifact
    
    def get_artifact(self, artifact_id: str) -> Optional[ArtifactData]:
        """根据 ID 获取 artifact"""
        return self._artifacts.get(artifact_id)
    
    def list_artifacts(self) -> List[ArtifactData]:
        """获取所有 artifacts"""
        return list(self._artifacts.values())
    
    def update_artifact(
        self, 
        artifact_id: str, 
        title: Optional[str] = None,
        content: Optional[str] = None,
        description: Optional[str] = None
    ) -> Optional[ArtifactData]:
        """更新 artifact"""
        artifact = self._artifacts.get(artifact_id)
        if not artifact:
            return None
        
        now = datetime.now().isoformat()
        
        # 创建更新的数据字典
        update_data = artifact.model_dump()
        if title is not None:
            update_data['title'] = title
        if content is not None:
            update_data['content'] = content
        if description is not None:
            update_data['description'] = description
        update_data['updated_at'] = now
        
        # 创建新的 artifact 实例
        updated_artifact = ArtifactData(**update_data)
        self._artifacts[artifact_id] = updated_artifact
        return updated_artifact
    
    def delete_artifact(self, artifact_id: str) -> bool:
        """删除 artifact"""
        if artifact_id in self._artifacts:
            del self._artifacts[artifact_id]
            return True
        return False
    
    def clear_all(self):
        """清空所有 artifacts（主要用于测试）"""
        self._artifacts.clear()


# 创建全局单例实例
artifact_manager = ArtifactManager()