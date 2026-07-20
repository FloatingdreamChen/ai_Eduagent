# scripts/build_knowledge_base.py（完整版）

import asyncio
import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from langchain_core.documents import Document

from backend.core.knowledge_base import BGEMEmbedder, KnowledgeBaseClient, DocumentChunk, generate_chunk_id
from backend.core.llm_factory import get_llm

# ── 常量 ─────────────────────────────────────────────────────

MAX_CONTEXT_CONCURRENCY = 5    # Contextual 上下文生成的最大并发 LLM 请求数

CONTEXTUAL_CHUNK_PROMPT = """\
<document>
{document_text}
</document>

以下是需要在整个文档中定位的 chunk：
<chunk>
{chunk_content}
</chunk>

请用一句简洁的中文，描述这段内容在整个文档中的位置和作用，以便改善检索效果。
只输出这一句描述，不要加任何前缀或标签。"""


# ── Step 1：读取文档（5.2 已实现）──────────────────────────
# load_document(file_path: str) -> list[Document]
# 在此文件内定义，参见 5.2 节完整代码


# ── Step 2：智能分块（5.3 已实现）──────────────────────────
# split_documents(docs: list[Document], file_path: str) -> list[Document]
# 在此文件内定义，参见 5.3 节完整代码


# ── Step 3：BGE-M3 嵌入（5.4 已实现）───────────────────────
# embed_chunks(chunks, course_id, document_id, ...) -> list[DocumentChunk]
# 在此文件内定义，参见 5.4 节完整代码


# ── Step 2.5：Contextual RAG 上下文增强 ─────────────────────

async def generate_chunk_context(
    llm,
    document_text: str,
    chunk_content: str,
    semaphore: asyncio.Semaphore,
) -> str:
    """
    用 LLM 为单个 chunk 生成一句定位描述。

    失败时返回空字符串，调用方保留原始 chunk 文本（降级处理）。

    Args:
        llm:           DeepSeek LLM 实例（via get_llm）
        document_text: 整篇文档全文（截断至 8000 字）
        chunk_content: 当前 chunk 的原始文本
        semaphore:     并发限流（最多 MAX_CONTEXT_CONCURRENCY 个 LLM 请求同时进行）
    """
    async with semaphore:
        try:
            from langchain_core.messages import HumanMessage
            prompt = CONTEXTUAL_CHUNK_PROMPT.format(
                document_text=document_text,
                chunk_content=chunk_content,
            )
            resp = await llm.ainvoke([HumanMessage(content=prompt)])
            ctx = (
                resp.text
                if hasattr(resp, "text") and not callable(resp.text)
                else str(resp.content)
            ).strip()
            return ctx
        except Exception as e:
            print(f"   [warning] 上下文生成失败，保留原始 chunk：{e}")
            return ""


async def add_context(
    chunks: list[Document],
    docs: list[Document],
    concurrency: int = MAX_CONTEXT_CONCURRENCY,
) -> list[Document]:
    """
    Contextual RAG：并发为所有 chunk 生成上下文描述，拼接到 chunk 文本前方。

    拼接后格式：
        "<上下文描述一句话>\\n\\n<原始 chunk 文本>"

    拼接后再做嵌入（embed_chunks），向量同时编码"在哪里"和"说了什么"两层信息。

    Args:
        chunks:      split_documents() 输出的 list[Document]
        docs:        load_document() 输出的原始 list[Document]（用于构建全文参考）
        concurrency: 最大并发 LLM 请求数（默认 5，防止触发 API 限流）

    Returns:
        page_content 已被就地修改（拼接上下文）的 list[Document]
    """
    # 拼接全文供 LLM 参考（截断 8000 字，避免超出模型 context 长度）
    full_doc_text = "\n\n".join(d.page_content for d in docs)[:8000]

    llm       = get_llm("qa", temperature=0)
    semaphore = asyncio.Semaphore(concurrency)

    # 并发调用 LLM，为每个 chunk 生成上下文描述
    contexts = await asyncio.gather(*[
        generate_chunk_context(llm, full_doc_text, c.page_content, semaphore)
        for c in chunks
    ])

    enriched = 0
    for chunk, ctx in zip(chunks, contexts):
        if ctx:
            chunk.page_content = f"{ctx}\n\n{chunk.page_content}"
            enriched += 1

    print(f"  上下文增强完成：{enriched}/{len(chunks)} 个 chunk 已添加描述")
    return chunks


# ── Step 4：写入 Milvus ────────────────────────────────────────

def write_to_milvus(doc_chunks: list[DocumentChunk]) -> None:
    """
    将 embed_chunks() 产出的 DocumentChunk 列表写入 Milvus。

    先按 document_id 删除同文档旧版本 chunk，再批量 upsert，
    保证文档更新时不残留旧数据。
    """
    if not doc_chunks:
        print("  ⚠️  无 chunk 可写入，跳过")
        return

    kb          = KnowledgeBaseClient()
    document_id = doc_chunks[0].document_id

    print(f"  🗑️  删除旧版本 chunk（document_id={document_id[:8]}…）")
    kb.delete_document_chunks(document_id)

    written = kb.upsert_chunks(doc_chunks)
    print(f"  ✅ 写入完成：{written} 个 chunk → knowledge_domain")


# ── 主流水线 ─────────────────────────────────────────────────

async def build_pipeline(
    file_path:   str,
    course_id:   str,
    document_id: str,
    tenant_id:   str = "tenant_default",
    version:     str = "1.0",
    use_context: bool = True,
) -> None:
    """
    知识库建库完整流水线（五步）：

      Step 1   读取文档（PyPDFLoader / TextLoader）
      Step 2   智能分块（MarkdownHeaderTextSplitter / RecursiveCharacterTextSplitter）
      Step 2.5 Contextual RAG 上下文增强（LLM 并发，可跳过）
      Step 3   BGE-M3 嵌入（dense + sparse 双向量）
      Step 4   写入 Milvus（MilvusClient upsert）
    """
    print(f"\n{'='*55}")
    print(f" EduAgent 知识库构建")
    print(f" 文件      ：{file_path}")
    print(f" 课程      ：{course_id}")
    print(f" 文档 ID   ：{document_id}")
    print(f" 租户      ：{tenant_id}")
    print(f" Contextual RAG：{'启用' if use_context else '跳过（--no-context）'}")
    print(f"{'='*55}\n")

    # Step 1：读取
    print("📖 Step 1/4  读取文档…")
    docs = load_document(file_path)

    # Step 2：分块
    print("\n✂️  Step 2/4  智能分块…")
    chunks = split_documents(docs, file_path)

    # Step 2.5：Contextual RAG（可选）
    if use_context and chunks:
        print(f"\n🧠 Step 2.5  Contextual RAG 上下文增强"
              f"（并发={MAX_CONTEXT_CONCURRENCY}）…")
        chunks = await add_context(chunks, docs)

    # Step 3：嵌入
    print("\n🔢 Step 3/4  BGE-M3 嵌入…")
    doc_chunks = embed_chunks(
        chunks,
        course_id=course_id,
        document_id=document_id,
        tenant_id=tenant_id,
        version=version,
    )

    # Step 4：写入
    print("\n💾 Step 4/4  写入 Milvus…")
    write_to_milvus(doc_chunks)

    print(f"\n🎉 完成！共处理 {len(doc_chunks)} 个 chunk")
    print(f"   document_id = {document_id}")
    print(f"   ⚠️  更新此文档时请保留此 document_id")


# ── CLI 入口 ─────────────────────────────────────────────────
# 直接修改下方变量值，然后运行：python scripts/build_knowledge_base.py

if __name__ == "__main__":
    FILE_PATH   = "./samples/sample2.md"
    COURSE_ID   = "3e76aeed-5e01-4aa7-be8d-2055d12b9ea7"   # 替换为实际课程 UUID
    DOCUMENT_ID = None          # None = 自动生成；更新同一文档时填入上次输出的 ID
    TENANT_ID   = "tenant_default"
    VERSION     = "1.0"
    USE_CONTEXT = True          # False = 跳过 Contextual RAG（快速调试，不消耗 API 配额）

    doc_id = DOCUMENT_ID or str(uuid.uuid4())

    asyncio.run(build_pipeline(
        file_path=FILE_PATH,
        course_id=COURSE_ID,
        document_id=doc_id,
        tenant_id=TENANT_ID,
        version=VERSION,
        use_context=USE_CONTEXT,
    ))
