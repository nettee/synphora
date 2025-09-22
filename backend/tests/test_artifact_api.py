"""
简化的 Artifact API 接口测试脚本
测试所有 CRUD 操作的串联流程
"""
import pytest
import io
from fastapi.testclient import TestClient
from synphora.server import app


class TestArtifactCRUD:
    """Artifact CRUD 接口测试"""
    
    @pytest.fixture
    def client(self):
        """FastAPI 测试客户端"""
        return TestClient(app)
    
    def test_artifact_crud_flow(self, client):
        """测试完整的 CRUD 流程"""
        
        # 1. 初始状态 - 获取空列表
        response = client.get("/artifacts")
        assert response.status_code == 200
        data = response.json()
        assert "artifacts" in data
        assert data["artifacts"] == []
        print("✓ 1. 获取空列表成功")
        
        # 2. 创建第一个 artifact
        artifact1_data = {
            "title": "测试文档1",
            "content": "这是第一个测试文档的内容",
            "description": "第一个测试描述"
        }
        response = client.post("/artifacts", json=artifact1_data)
        assert response.status_code == 200
        artifact1 = response.json()
        assert artifact1["title"] == artifact1_data["title"]
        assert artifact1["content"] == artifact1_data["content"]
        assert "id" in artifact1
        artifact1_id = artifact1["id"]
        print(f"✓ 2. 创建第一个 artifact 成功，ID: {artifact1_id}")
        
        # 3. 创建第二个 artifact（最小字段）
        artifact2_data = {
            "title": "测试文档2", 
            "content": "第二个文档内容"
        }
        response = client.post("/artifacts", json=artifact2_data)
        assert response.status_code == 200
        artifact2 = response.json()
        artifact2_id = artifact2["id"]
        print(f"✓ 3. 创建第二个 artifact 成功，ID: {artifact2_id}")
        
        # 4. 上传文件创建第三个 artifact
        file_content = "这是上传文件的内容\n支持中文和换行"
        file_data = io.BytesIO(file_content.encode('utf-8'))
        response = client.post(
            "/artifacts/upload",
            files={"file": ("test.txt", file_data, "text/plain")}
        )
        assert response.status_code == 200
        artifact3 = response.json()
        assert artifact3["title"] == "test.txt"
        assert artifact3["content"] == file_content
        artifact3_id = artifact3["id"]
        print(f"✓ 4. 上传文件创建第三个 artifact 成功，ID: {artifact3_id}")
        
        # 5. 获取所有 artifacts，应该有3个
        response = client.get("/artifacts")
        assert response.status_code == 200
        artifacts = response.json()["artifacts"]
        assert len(artifacts) == 3
        ids = [a["id"] for a in artifacts]
        assert artifact1_id in ids
        assert artifact2_id in ids
        assert artifact3_id in ids
        print("✓ 5. 获取所有 artifacts 成功，共3个")
        
        # 6. 根据ID获取特定 artifact
        response = client.get(f"/artifacts/{artifact1_id}")
        assert response.status_code == 200
        artifact = response.json()
        assert artifact["id"] == artifact1_id
        assert artifact["title"] == artifact1_data["title"]
        print(f"✓ 6. 根据ID获取 artifact 成功")
        
        # 7. 获取不存在的 artifact
        response = client.get("/artifacts/nonexistent-id")
        assert response.status_code == 404
        print("✓ 7. 获取不存在的 artifact 返回404")
        
        # 8. 删除第二个 artifact
        response = client.delete(f"/artifacts/{artifact2_id}")
        assert response.status_code == 200
        assert "deleted successfully" in response.json()["message"]
        print(f"✓ 8. 删除 artifact {artifact2_id} 成功")
        
        # 9. 验证删除后只剩2个
        response = client.get("/artifacts")
        assert response.status_code == 200
        artifacts = response.json()["artifacts"]
        assert len(artifacts) == 2
        ids = [a["id"] for a in artifacts]
        assert artifact1_id in ids
        assert artifact3_id in ids
        assert artifact2_id not in ids
        print("✓ 9. 验证删除后剩余2个 artifacts")
        
        # 10. 确认被删除的 artifact 不能再获取
        response = client.get(f"/artifacts/{artifact2_id}")
        assert response.status_code == 404
        print("✓ 10. 确认被删除的 artifact 无法获取")
        
        # 11. 删除不存在的 artifact
        response = client.delete("/artifacts/nonexistent-id")
        assert response.status_code == 404
        print("✓ 11. 删除不存在的 artifact 返回404")
        
        # 12. 清理剩余的 artifacts
        response = client.delete(f"/artifacts/{artifact1_id}")
        assert response.status_code == 200
        response = client.delete(f"/artifacts/{artifact3_id}")
        assert response.status_code == 200
        print("✓ 12. 清理剩余 artifacts 完成")
        
        # 13. 最终验证列表为空
        response = client.get("/artifacts")
        assert response.status_code == 200
        assert len(response.json()["artifacts"]) == 0
        print("✓ 13. 最终验证列表为空")
        
        print("\n🎉 所有 CRUD 操作测试通过！")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])