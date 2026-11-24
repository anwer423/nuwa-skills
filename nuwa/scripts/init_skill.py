#!/usr/bin/env python3
"""生成一个符合规范的 Skill 骨架。

用法：
    python init_skill.py <skill-name> --path <目标目录> [--scripts] [--references] [--assets] [--force]

示例：
    python init_skill.py invoice-ocr --path D:/skills --scripts --references
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

NAME_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")

SKILL_TEMPLATE = """---
name: {name}
description: 写清这个技能做什么、解决哪类问题，并把用户真实会说的触发词都放进来。当用户需要【替换为具体场景，例如：把发票批量转成结构化表格】时使用。
---

# {title}

## 流程

1. 写清第一步要拿到的输入，缺什么就问什么，不要凭空补。
2. 写清中间判据：什么算成功，什么算失败，失败怎么退。
3. 写清产出：文件放哪里、叫什么名字、什么格式。

## 附带资源

{resources}
"""


def title_of(name: str) -> str:
    return " ".join(word.capitalize() for word in name.split("-"))


def main() -> int:
    parser = argparse.ArgumentParser(description="生成 Skill 骨架")
    parser.add_argument("name", help="技能名，kebab-case")
    parser.add_argument("--path", required=True, help="输出目录（技能文件夹会建在其下）")
    parser.add_argument("--scripts", action="store_true", help="同时创建 scripts/")
    parser.add_argument("--references", action="store_true", help="同时创建 references/")
    parser.add_argument("--assets", action="store_true", help="同时创建 assets/")
    parser.add_argument("--force", action="store_true", help="目录已存在时覆盖 SKILL.md")
    args = parser.parse_args()

    if not NAME_RE.match(args.name):
        print("error: name 必须是 kebab-case（小写字母/数字/单个连字符），例如 invoice-ocr")
        return 1

    root = Path(args.path).expanduser().resolve()
    if not root.is_dir():
        print(f"error: 输出目录不存在 -> {root}")
        return 1

    skill_dir = root / args.name
    skill_md = skill_dir / "SKILL.md"
    if skill_md.exists() and not args.force:
        print(f"error: {skill_md} 已存在，覆盖请加 --force")
        return 1

    skill_dir.mkdir(parents=True, exist_ok=True)

    resources = []
    if args.scripts:
        (skill_dir / "scripts").mkdir(exist_ok=True)
        resources.append("- `scripts/` — 放可执行脚本，写完必须真跑一遍")
    if args.references:
        (skill_dir / "references").mkdir(exist_ok=True)
        resources.append("- `references/` — 放口径、规范、长案例，按需加载")
    if args.assets:
        (skill_dir / "assets").mkdir(exist_ok=True)
        resources.append("- `assets/` — 放要进产出的模板与素材")
    if not resources:
        resources.append("- 暂无附带资源；需要脚本或长材料时再建目录")

    skill_md.write_text(
        SKILL_TEMPLATE.format(name=args.name, title=title_of(args.name), resources="\n".join(resources)),
        encoding="utf-8",
    )
    print(f"已创建: {skill_md}")
    print("下一步: 补全 description 和流程，删掉不适用的段落，然后跑 validate_skill.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
