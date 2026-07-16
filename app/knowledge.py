from __future__ import annotations

from pathlib import Path
from typing import Any


class KnowledgeBase:
    def __init__(self, directory: Path, *, max_upload_bytes: int = 2 * 1024 * 1024):
        self.directory = Path(directory)
        self.max_upload_bytes = max_upload_bytes
        self.directory.mkdir(parents=True, exist_ok=True)

    def list_files(self) -> list[dict[str, Any]]:
        files = []
        for path in sorted(self.directory.glob("*.txt"), key=lambda item: item.name):
            try:
                files.append({"name": path.name, "size": path.stat().st_size})
            except OSError:
                continue
        return files

    def save_upload(self, filename: str, content: bytes) -> str:
        safe_name = Path(filename).name
        if not safe_name or safe_name != filename or Path(safe_name).suffix.lower() != ".txt":
            raise ValueError("仅支持名称有效的 .txt 文件")
        if len(content) > self.max_upload_bytes:
            raise ValueError("单个文件不能超过 2 MB")
        try:
            content.decode("utf-8")
        except UnicodeDecodeError as error:
            raise ValueError("文件需使用 UTF-8 编码") from error

        target = self.directory / safe_name
        target.write_bytes(content)
        return safe_name

    def delete(self, filename: str) -> None:
        safe_name = Path(filename).name
        if safe_name != filename or Path(safe_name).suffix.lower() != ".txt":
            raise ValueError("文件名无效")
        target = self.directory / safe_name
        if target.exists():
            target.unlink()

    def load_content(self, *, max_chars: int) -> str:
        sections: list[str] = []
        used = 0
        for item in self.list_files():
            path = self.directory / item["name"]
            try:
                content = path.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError):
                continue
            remaining = max_chars - used
            if remaining <= 0:
                break
            excerpt = content[:remaining]
            sections.append(f"【{item['name']}】\n{excerpt}")
            used += len(excerpt)
        return "\n\n".join(sections) or "（知识库暂无内容）"
