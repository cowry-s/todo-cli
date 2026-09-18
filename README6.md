# Todo CLI

一个使用 JSON 文件存储的轻量级待办事项命令行工具。  
支持创建、完成、删除任务，并可按优先级、截止日期、关键词筛选和排序。

## ✨ 功能特性

- 创建任务：标题、优先级、截止日期
- 标记任务为已完成
- 删除任务
- 按优先级（low / medium / high）筛选
- 按截止日期范围筛选（`--due-before` / `--due-after`）
- 按标题关键词搜索
- 多种排序方式：创建时间、优先级、截止日期、标题
- 数据以 JSON 格式保存，可读、可编辑、可迁移
- 原子写入，避免数据损坏
- 支持完整 ID 或唯一 ID 前缀操作任务
- 完整的单元测试覆盖

## 📁 项目结构

```
todo_cli/
├── .gitignore              # Git 忽略规则
├── README.md               # 项目说明
├── main.py                 # 程序入口
├── todo/
│   ├── __init__.py         # 包入口，导出公共 API
│   ├── models.py           # Task / Priority 数据模型与序列化
│   ├── storage.py          # JSON 文件读写（持久化层）
│   ├── service.py          # 业务逻辑：增删改查、筛选、排序
│   └── cli.py              # 命令行参数解析与输出
└── tests/
    ├── __init__.py
    ├── test_models.py      # 模型层测试
    ├── test_storage.py     # 存储层测试
    ├── test_service.py     # 业务逻辑测试
    └── test_cli.py         # 命令行端到端测试
```

## 🚀 快速开始

### 环境要求

- Python 3.10 或更高版本
- 无需第三方依赖，仅使用标准库

### 运行方式

```bash
# 添加任务
python main.py add "写周报" -p high -d 2025-01-31
python main.py add "买菜"

# 查看任务（默认隐藏已完成）
python main.py list

# 按优先级筛选
python main.py list -p high

# 按截止日期筛选
python main.py list --due-before 2025-02-01

# 关键词搜索
python main.py list -k 周报

# 显示已完成任务
python main.py list --all

# 自定义排序（created / priority / due / title）
python main.py list --sort priority

# 标记完成（支持 ID 前缀）
python main.py done a1b2

# 删除任务
python main.py rm a1b2 c3d4
```

### 数据文件位置

默认保存在用户主目录下的 `.todo.json`：

- Linux / macOS：`~/.todo.json`
- Windows：`C:\Users\你的用户名\.todo.json`

可以通过以下方式自定义：

```bash
# 使用 --file 参数
python main.py --file ./my-todo.json list

# 或设置环境变量 TODO_FILE
export TODO_FILE=./my-todo.json
python main.py list
```

## 📖 命令详解

### `add` — 创建任务

```bash
python main.py add "任务标题" [-p PRIORITY] [-d YYYY-MM-DD]
```

- `-p, --priority`：优先级，可选 `low`、`medium`、`high`，默认 `medium`
- `-d, --due`：截止日期，格式 `YYYY-MM-DD`

### `list` — 列出与筛选

```bash
python main.py list [-p PRIORITY] [--due-before DATE] [--due-after DATE] [-a] [-k KEYWORD] [--sort KEY]
```

- `-p, --priority`：按优先级筛选
- `--due-before`：截止日期 ≤ 指定日期
- `--due-after`：截止日期 ≥ 指定日期
- `-a, --all`：包含已完成任务
- `-k, --keyword`：标题关键词（不区分大小写）
- `--sort`：排序方式，可选 `created`（默认）、`priority`、`due`、`title`

### `done` — 标记完成

```bash
python main.py done ID [ID ...]
```

支持完整 ID 或唯一前缀。

### `rm` — 删除任务

```bash
python main.py rm ID [ID ...]
```

支持完整 ID 或唯一前缀。

## 🧪 运行测试

```bash
python -m unittest discover -s tests -t .
```

测试覆盖：

- 模型序列化与反序列化
- 存储层的文件读写、损坏文件处理
- 业务逻辑的增删改查、筛选、排序
- CLI 端到端流程与错误码

## 🧠 学习目标

本项目适合作为 Python 模块化、JSON 序列化和单元测试的练习：

- **模块化**：模型、存储、业务、界面四层分离
- **序列化**：`Task.to_dict()` / `from_dict()`，日期与枚举处理
- **单元测试**：使用 `unittest`，测试替身（InMemoryStorage）隔离文件系统
- **健壮性**：原子写入、统一错误处理、退出码规范

## 📄 许可证

本项目仅供学习使用，可自由修改和分发。
