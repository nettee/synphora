import os
from typing import List, Optional

from synphora.models import ArtifactData, ArtifactType
from synphora.file_storage import FileStorage


class ArtifactManager:
    def __init__(self):
        # 从环境变量获取存储路径，默认为 tests/data/store
        storage_path = os.getenv('SYNPHORA_STORAGE_PATH', 'tests/data/store')
        self._storage = FileStorage(storage_path)
    
    def create_artifact(
        self, 
        title: str, 
        content: str, 
        artifact_type: ArtifactType = ArtifactType.ORIGINAL,
        role: str = "user",
        description: Optional[str] = None
    ) -> ArtifactData:
        """创建新的 artifact"""
        return self._storage.create_artifact(
            title=title,
            content=content,
            artifact_type=artifact_type,
            role=role,
            description=description
        )
    
    def get_artifact(self, artifact_id: str) -> Optional[ArtifactData]:
        """根据 ID 获取 artifact"""
        return self._storage.get_artifact(artifact_id)
    
    def list_artifacts(self) -> List[ArtifactData]:
        """获取所有 artifacts"""
        return self._storage.list_artifacts()
    
    def update_artifact(
        self, 
        artifact_id: str, 
        title: Optional[str] = None,
        content: Optional[str] = None,
        description: Optional[str] = None
    ) -> Optional[ArtifactData]:
        """更新 artifact"""
        return self._storage.update_artifact(
            artifact_id=artifact_id,
            title=title,
            content=content,
            description=description
        )
    
    def delete_artifact(self, artifact_id: str) -> bool:
        """删除 artifact"""
        return self._storage.delete_artifact(artifact_id)
    
    def clear_all(self):
        """清空所有 artifacts（主要用于测试）"""
        self._storage.clear_all()


# 创建全局单例实例
artifact_manager = ArtifactManager()