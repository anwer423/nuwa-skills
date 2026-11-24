#!/usr/bin/env python3
"""校验一个 Skill 目录是否符合规范。

用法：
    python validate_skill.py <skill-dir>

退出码：0 无 error（可能有 warning）；1 存在 error。
"""

from __future__ import annotations

import ast
import re
import sys
from pathlib import Path

BODY_LINE_LIMIT = 500
DESC_MIN_CN = 40
NAME_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
FIELD_RE = re.compile(r"^([A-Za-z_-]+)\s*:\s*(.*)$")
LINK_RE = re.compile(r"\[[^\]]*\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")
BACKTICK_PATH_RE = re.compile(r"`((?:scripts|references|assets)/[\w./-]+)`")
PLACEHOLDER_RE = re.compile(r"(?:TODO|TBD|FIXME)(?=\s*[:：]|\s*$)|待补充说明|（待补充）", re.IGNORECASE)
FORBIDDEN_FILES = {
    "README.md",
    "readme.md",
    "INSTALL.md",
    "INSTALLATION_GUIDE.md",
    "QUICK_REFERENCE.md",
    "CHANGELOG.md",
}

errors: list[str] = []
warnings: list[str] = []


def err(msg: str) -> None:
    errors.append(msg)


def warn(msg: str) -> None:
    warnings.append(msg)


def split_frontmatter(text: str) -> tuple[dict[str, str], str]:
    """返回 (frontmatter 字典, 正文)。frontmatter 缺失时抛 ValueError。"""
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        raise ValueError("SKILL.md 必须以 '---' 开头的 frontmatter 起手")
    end = None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            end = i
            break
    if end is None:
        raise ValueError("frontmatter 没有闭合的 '---'")

    meta: dict[str, str] = {}
    for raw in lines[1:end]:
        if not raw.strip() or raw.strip().startswith("#"):
            continue
        m = FIELD_RE.match(raw.strip())
        if not m:
            warn(f"frontmatter 行无法解析，已跳过：{raw.strip()}")
            continue
        key, value = m.group(1), m.group(2).strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        meta[key] = value
    body = "\n".join(lines[end + 1 :])
    return meta, body


def check_frontmatter(skill_dir: Path, text: str) -> str:
    try:
        meta, body = split_frontmatter(text)
    except ValueError as exc:
        err(f"frontmatter: {exc}")
        return text

    extra = sorted(set(meta) - {"name", "description"})
    if extra:
        err(f"frontmatter 只允许 name / description，多出：{', '.join(extra)}")

    name = meta.get("name", "").strip()
    if not name:
        err("frontmatter 缺少 name")
    else:
        if not NAME_RE.match(name):
            err(f"name '{name}' 不符合 kebab-case（仅小写字母、数字、单个连字符）")
        if name != skill_dir.name:
            err(f"name '{name}' 与目录名 '{skill_dir.name}' 不一致")

    desc = meta.get("description", "").strip()
    if not desc:
        err("frontmatter 缺少 description（这是唯一的触发依据）")
    else:
        if len(desc) < DESC_MIN_CN:
            err(f"description 只有 {len(desc)} 字，太短会触发不准（建议 ≥{DESC_MIN_CN} 字）")
        if len(desc) > 1200:
            warn(f"description 有 {len(desc)} 字，偏长，会挤占上下文")
        if "使用" not in desc and "use" not in desc.lower() and "当" not in desc:
            warn("description 里没有明确的「什么时候用」表述，容易漏触发")

    body_lines = [ln for ln in body.splitlines() if ln.strip()]
    if len(body_lines) > BODY_LINE_LIMIT:
        err(f"SKILL.md 正文 {len(body_lines)} 行，超过 {BODY_LINE_LIMIT} 行上限，请拆分到 references/")
    if re.search(r"^\s*#+\s*(When to Use|何时使用)", body, re.IGNORECASE | re.MULTILINE):
        warn("正文里出现「何时使用」章节，这属于 description 的职责，建议删掉")
    return body


def check_tree(skill_dir: Path) -> None:
    for path in skill_dir.rglob("*"):
        if path.is_file() and path.name in FORBIDDEN_FILES:
            err(f"技能目录内不应有说明文档：{path.relative_to(skill_dir)}")
        if path.is_file() and path.suffix in {".pyc", ".pyo"}:
            warn(f"发现编译缓存：{path.relative_to(skill_dir)}")
        if path.is_dir() and not any(path.iterdir()) and path.name not in {"scripts", "references", "assets"}:
            warn(f"空目录：{path.relative_to(skill_dir)}")


def check_links(skill_dir: Path, body: str) -> None:
    targets = list(LINK_RE.findall(body)) + list(BACKTICK_PATH_RE.findall(body))
    for target in targets:
        if target.startswith(("http://", "https://", "mailto:", "#")):
            continue
        clean = target.split("#")[0].strip("`").strip()
        if not clean:
            continue
        resolved = (skill_dir / clean).resolve()
        if not resolved.exists():
            err(f"引用了不存在的文件：{clean}")


def check_placeholders(skill_dir: Path) -> None:
    for path in sorted(skill_dir.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in {".md", ".txt", ".sh", ".yaml", ".yml"}:
            continue
        try:
            content = path.read_text(encoding="utf-8", errors="ignore")
        except OSError as exc:
            warn(f"无法读取 {path.name}：{exc}")
            continue
        for lineno, line in enumerate(content.splitlines(), 1):
            if PLACEHOLDER_RE.search(line):
                err(f"{path.relative_to(skill_dir)}:{lineno} 残留占位符：{line.strip()[:60]}")


def check_scripts(skill_dir: Path) -> None:
    scripts_dir = skill_dir / "scripts"
    if not scripts_dir.exists():
        return
    py_files = sorted(scripts_dir.rglob("*.py"))
    if not py_files:
        warn("scripts/ 目录存在但没有 .py 脚本")
    for path in py_files:
        text = path.read_text(encoding="utf-8", errors="ignore")
        try:
            ast.parse(text, filename=str(path))
        except SyntaxError as exc:
            err(f"脚本语法错误 {path.relative_to(skill_dir)}:{exc.lineno} -> {exc.msg}")
        if "__name__" not in text and "def main" not in text:
            warn(f"{path.relative_to(skill_dir)} 看不出可执行入口，确认它能被直接运行")


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("用法: python validate_skill.py <skill-dir>")
        return 2
    skill_dir = Path(argv[1]).resolve()
    if not skill_dir.is_dir():
        print(f"error: 目录不存在 -> {skill_dir}")
        return 1

    skill_md = skill_dir / "SKILL.md"
    if not skill_md.is_file():
        print(f"error: 缺少必需文件 SKILL.md -> {skill_dir}")
        return 1

    text = skill_md.read_text(encoding="utf-8", errors="ignore")
    body = check_frontmatter(skill_dir, text)
    check_tree(skill_dir)
    check_links(skill_dir, body)
    check_placeholders(skill_dir)
    check_scripts(skill_dir)

    print(f"校验对象: {skill_dir}")
    for msg in errors:
        print(f"  ERROR   {msg}")
    for msg in warnings:
        print(f"  WARN    {msg}")
    print(f"结果: {len(errors)} error / {len(warnings)} warning")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
