import os


from synphora.file_storage import FileStorage
from synphora.models import ArtifactData, ArtifactRole, ArtifactType




class ArtifactManager:
    def __init__(self):
        # 从环境变量获取存储路径，默认为 tests/data/store
        storage_path = os.getenv('SYNPHORA_STORAGE_PATH', 'tests/data/store')
        self._storage = FileStorage(storage_path)

    def generate_artifact_id(self) -> str:
        """生成 artifact ID"""
        return self._storage.generate_artifact_id()

    def create_artifact(
        self,
        title: str,
        content: str,
        artifact_type: ArtifactType = ArtifactType.ORIGINAL,
        role: ArtifactRole = ArtifactRole.USER,
        description: str | None = None,
    ) -> ArtifactData:
        """创建新的 artifact"""
        return self._storage.create_artifact(
            title=title,
            content=content,
            artifact_type=artifact_type,
            role=role,
            description=description,
        )

    def create_artifact_with_id(
        self,
        artifact_id: str,
        title: str,
        content: str,
        artifact_type: ArtifactType = ArtifactType.ORIGINAL,
        role: ArtifactRole = ArtifactRole.USER,
        description: str | None = None,
    ) -> ArtifactData:
        """用户指定 ID 创建新的 artifact"""
        return self._storage.create_artifact_with_id(
            artifact_id, title, content, artifact_type, role, description
        )

    def get_artifact(self, artifact_id: str) -> ArtifactData | None:
        """根据 ID 获取 artifact"""
        return self._storage.get_artifact(artifact_id)

    def list_artifacts(self) -> list[ArtifactData]:
        """获取所有 artifacts"""
        return self._storage.list_artifacts()

    def get_original_artifact(self) -> ArtifactData:
        artifacts = self.list_artifacts()
        for artifact in artifacts:
            if artifact.type == ArtifactType.ORIGINAL:
                return artifact
        raise ValueError("No original artifact found")

    def update_artifact(
        self,
        artifact_id: str,
        title: str | None = None,
        content: str | None = None,
        description: str | None = None,
    ) -> ArtifactData | None:
        """更新 artifact"""
        return self._storage.update_artifact(
            artifact_id=artifact_id,
            title=title,
            content=content,
            description=description,
        )

    def delete_artifact(self, artifact_id: str) -> bool:
        """删除 artifact"""
        return self._storage.delete_artifact(artifact_id)

    def clear_all(self):
        """清空所有 artifacts（主要用于测试）"""
        self._storage.clear_all()


# 创建全局单例实例
artifact_manager = ArtifactManager()
