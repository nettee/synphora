import json
import os
import shutil
import tempfile
import uuid
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from synphora.models import ArtifactData, ArtifactRole, ArtifactType

load_dotenv()

class FileStorage:
    def __init__(self, storage_path: str = "tests/data/store"):
        self.original_storage_path = Path(storage_path)
        # 创建临时目录副本
        self.storage_path = self._create_temp_copy()
        self.metadata_file = self.storage_path / "metadata.json"
        self._ensure_storage_directory()
        self._metadata: dict[str, dict] = self._load_metadata()

    def _create_temp_copy(self) -> Path:
        """创建原始存储目录的临时副本"""
        # 在 /tmp 下创建唯一的临时目录
        temp_dir = Path(tempfile.mkdtemp(prefix="synphora_storage_"))

        # 如果原始目录存在，且 NEXT_PUBLIC_SKIP_WELCOME 为 true，复制其内容
        skip_welcome = os.getenv('NEXT_PUBLIC_SKIP_WELCOME') == 'true'
        print(f"📁 skip_welcome: {skip_welcome}")
        if skip_welcome and self.original_storage_path.exists():
            shutil.copytree(self.original_storage_path, temp_dir, dirs_exist_ok=True)

        print(f"📁 Created temporary storage copy at: {temp_dir}")
        return temp_dir

    def _ensure_storage_directory(self):
        """确保存储目录存在"""
        self.storage_path.mkdir(parents=True, exist_ok=True)

    def _load_metadata(self) -> dict[str, dict]:
        """从metadata.json加载元数据"""
        if self.metadata_file.exists():
            try:
                with open(self.metadata_file, encoding='utf-8') as f:
                    return json.load(f)
            except (OSError, json.JSONDecodeError):
                return {}
        return {}

    def _save_metadata(self):
        """保存元数据到metadata.json"""
        with open(self.metadata_file, 'w', encoding='utf-8') as f:
            json.dump(self._metadata, f, indent=2, ensure_ascii=False)

    def _get_data_file_path(self, artifact_id: str) -> Path:
        """获取数据文件路径"""
        return self.storage_path / f"{artifact_id}.txt"

    def generate_artifact_id(self) -> str:
        """生成 artifact ID"""
        return str(uuid.uuid4())

    def create_artifact(
        self,
        title: str,
        content: str,
        artifact_type: ArtifactType = ArtifactType.ORIGINAL,
        role: ArtifactRole = ArtifactRole.USER,
        description: str | None = None,
    ) -> ArtifactData:
        """创建新的 artifact"""
        artifact_id = self.generate_artifact_id()
        return self.create_artifact_with_id(
            artifact_id, title, content, artifact_type, role, description
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
            "updated_at": now,
        }

        self._metadata[artifact_id] = metadata
        self._save_metadata()

        return ArtifactData(content=content, **metadata)

    def get_artifact(self, artifact_id: str) -> ArtifactData | None:
        """根据 ID 获取 artifact"""
        metadata = self._metadata.get(artifact_id)
        if not metadata:
            return None

        # 读取内容文件
        data_file = self._get_data_file_path(artifact_id)
        if not data_file.exists():
            return None

        try:
            with open(data_file, encoding='utf-8') as f:
                content = f.read()

            return ArtifactData(content=content, **metadata)
        except OSError:
            return None

    def list_artifacts(self) -> list[ArtifactData]:
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
        title: str | None = None,
        content: str | None = None,
        description: str | None = None,
    ) -> ArtifactData | None:
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

    def cleanup_temp_storage(self):
        """清理临时存储目录（可选）"""
        if self.storage_path.exists() and str(self.storage_path).startswith("/tmp"):
            shutil.rmtree(self.storage_path)
            print(f"🗑️ Cleaned up temporary storage: {self.storage_path}")
