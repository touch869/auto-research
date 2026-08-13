#!/usr/bin/env python3
"""autoresearch · arXiv PDF 下载 + 全文提取

deep 模式读论文原文用。arXiv 网页 WebFetch 常被拦,但 PDF 端点通常可下。

用法:
    # 下载 + 提取( 一步 )
    python pdf_extract.py 2608.10402 --out tmp/papers/tiderl.json
    # → 同时存 tiderl.pdf 和 tiderl.json( 每页文本 )

    # 已有 PDF,只提取
    python pdf_extract.py --pdf tmp/pdfs/tiderl.pdf --out tmp/papers/tiderl.json

输出 JSON: {arxiv_id, pages:[{page, text}], full_text, n_pages}
依赖:PyMuPDF( fitz )。若缺失,提示安装:pip install PyMuPDF
"""
import argparse
import json
import sys
import urllib.request
from pathlib import Path


def download_pdf(arxiv_id, dest):
    """下载 arXiv PDF。id 可带版本( 2608.10402 或 2608.10402v1 )。"""
    base = arxiv_id.split("v")[0]  # 去版本号,pdf 端点用基础 id
    url = f"https://arxiv.org/pdf/{base}"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 autoresearch/0.1"})
    with urllib.request.urlopen(req, timeout=90) as resp:
        data = resp.read()
    dest.write_bytes(data)
    if not data[:5] == b"%PDF-":
        raise ValueError(f"下载内容不是 PDF( 可能是错误页 ),前 20 字节: {data[:20]}")
    return len(data)


def extract_text(pdf_path):
    """用 PyMuPDF 提取每页文本。返回 [{page, text}],页码从 1 开始。"""
    try:
        import fitz  # PyMuPDF
    except ImportError:
        print("ERROR: 缺少 PyMuPDF。安装:pip install PyMuPDF", file=sys.stderr)
        sys.exit(2)
    doc = fitz.open(str(pdf_path))
    pages = []
    for i, page in enumerate(doc, 1):
        pages.append({"page": i, "text": page.get_text()})
    n = len(doc)
    doc.close()
    return pages, n


def main():
    ap = argparse.ArgumentParser(description="autoresearch arXiv PDF 下载+提取")
    ap.add_argument("arxiv_id", nargs="?", help="arXiv id( 如 2608.10402 );与 --pdf 二选一")
    ap.add_argument("--pdf", help="已有 PDF 路径,跳过下载直接提取")
    ap.add_argument("--out", required=True, help="输出 JSON 路径")
    ap.add_argument("--keep-pdf", action="store_true", default=True, help="保留下载的 PDF( 默认保留 )")
    args = ap.parse_args()

    if not args.arxiv_id and not args.pdf:
        ap.error("需要 arxiv_id 或 --pdf")

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)

    if args.pdf:
        pdf_path = Path(args.pdf)
        arxiv_id = ""
    else:
        pdf_dir = out.parent / "pdfs"
        pdf_dir.mkdir(exist_ok=True)
        pdf_path = pdf_dir / f"{out.stem}.pdf"
        try:
            size = download_pdf(args.arxiv_id, pdf_path)
            print(f"[pdf] 下载 {args.arxiv_id} → {pdf_path} ({size//1024}KB)", file=sys.stderr)
        except Exception as e:
            print(f"ERROR: PDF 下载失败: {e}", file=sys.stderr)
            sys.exit(1)
        arxiv_id = args.arxiv_id

    try:
        pages, n = extract_text(pdf_path)
    except Exception as e:
        print(f"ERROR: PDF 提取失败: {e}", file=sys.stderr)
        sys.exit(1)

    payload = {
        "arxiv_id": arxiv_id,
        "pdf_path": str(pdf_path),
        "n_pages": n,
        "pages": pages,
        "full_text": "\n".join(p["text"] for p in pages),
    }
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[pdf] 提取 {n} 页 → {out}", file=sys.stderr)


if __name__ == "__main__":
    main()
