# 女娲 Skills · nuwa-skills

> 把跑通过的工作流固化成可复用的 Skill，而不是每次重写一遍。

女娲是一个「造技能」的技能：输入一段人类经验（一次成功任务的对话、一份 SOP、一套操作步骤），输出一个符合规范、能直接装进 `.skills` 目录被调用的 Skill 包。

女娲**面向**：已有经验的固化与沉淀。
女娲**不面向**：从零想象一个能力、批量分类管理技能、帮你运行别人写的技能。

## 目录结构

```
nuwa-skills/
├── README.md                 # 本文件（仓库文档）
├── LICENSE                   # MIT
└── nuwa/                     # 技能本体，整个文件夹即安装单元
    ├── SKILL.md              # 技能入口：触发条件 + 造技能六步流程
    ├── references/
    │   ├── skill-spec.md     # 规范：结构、frontmatter、渐进式披露、反模式
    │   └── quality-gates.md  # 交付前验收清单
    └── scripts/
        ├── init_skill.py     # 生成技能骨架
        └── validate_skill.py # 结构与规范校验
```

技能目录里刻意不放 README —— 说明文档留在仓库根，保持技能包只有「跑得起来的东西」。

## 安装

把 `nuwa/` 整个文件夹复制到当前环境的技能目录即可：

```bash
# 方式一：内置技能目录
cp -r nuwa-skills/nuwa <...>/workspace/.skills/nuwa

# 方式二：用户技能目录
cp -r nuwa-skills/nuwa <...>/workspace/.user_skills/nuwa
```

Windows PowerShell：

```powershell
Copy-Item -Recurse ".\nuwa-skills\nuwa" "C:\...\workspace\.skills\nuwa"
```

装好后新开会话，`nuwa` 会出现在可用技能列表里。

## 使用

直接说人话就能触发：

- 「把这个对账流程做成技能」
- 「上次那套日报模板沉淀一下，以后复用」
- 「女娲，帮我造个技能」

它会先判断这件事值不值得做成技能（会重复、步骤稳定、含 AI 自己想不到的知识），然后按「采 → 判 → 定自由度 → 拆三件套 → 写 SKILL.md → 校验」走完。

## 校验

任何 Skill 包都可以用这个校验器检查规范：

```bash
python nuwa/scripts/validate_skill.py nuwa
```

覆盖：frontmatter 字段与 kebab-case 命名、description 触发质量、正文 500 行上限、内部引用文件是否存在、脚本语法、TODO 残留、技能目录内的多余说明文档。

生成新技能骨架：

```bash
python nuwa/scripts/init_skill.py my-skill --path ./skills --scripts --references
```

## 设计要点

- **description 是唯一的触发器**：写清做什么 + 什么时候用，触发词全放这儿，正文不再写「何时使用」。
- **渐进式披露**：SKILL.md 只留流程与取舍，长材料进 `references/`，并按需加载。
- **能固化的就固化成脚本**：反复重写、要求确定性的逻辑放 `scripts/`，写完必须真跑一遍。
- **一个技能只干一件事**：两类事就拆两个技能。

## License

MIT
