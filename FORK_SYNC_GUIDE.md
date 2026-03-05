# Fork 项目同步主项目指南

本文档介绍如何将 Fork 项目与主项目保持同步的完整步骤。

## 📋 目录

- [概述](#概述)
- [前置条件](#前置条件)
- [同步步骤](#同步步骤)
- [冲突解决](#冲突解决)
- [常见问题](#常见问题)
- [最佳实践](#最佳实践)

---

## 概述

当你 Fork 了一个项目后，原项目（upstream）会继续更新。本指南帮助你定期同步最新的主项目代码到你的 Fork。

**同步流程示意：**
```
Primary Project (upstream/main)
           ↓
        fetch
           ↓
   Local Repository
           ↓
        merge
           ↓
   Your Fork (origin/main)
           ↓
        push
           ↓
  Remote Fork on GitHub
```

---

## 前置条件

- 已克隆你的 Fork 仓库到本地
- 有 Git 命令行环境
- 对 Git 基本操作有了解

**验证环境：**
```bash
git --version  # 确保已安装Git
cd your-fork-repo
git remote -v  # 查看当前远程仓库配置
```

---

## 同步步骤

### 第 1 步：保存本地更改（如有）

如果有未提交的本地修改，先保存它们：

```bash
# 查看当前状态
git status

# 如果有未提交的更改，执行 stash
git stash
```

**说明：** `git stash` 会临时保存你的修改，清空工作区。稍后可以恢复。

### 第 2 步：添加上游远程仓库

检查是否已添加主项目为远程仓库：

```bash
git remote -v
```

**如果没有 upstream：**
```bash
git remote add upstream <primary-project-url>
```

**示例：**
```bash
git remote add upstream https://github.com/mujocolab/mjlab.git
```

**验证：**
```bash
git remote -v
# 应该显示：
# origin    https://github.com/your-username/mjlab.git (fetch)
# origin    https://github.com/your-username/mjlab.git (push)
# upstream  https://github.com/mujocolab/mjlab.git (fetch)
# upstream  https://github.com/mujocolab/mjlab.git (push)
```

### 第 3 步：从主项目获取最新代码

```bash
git fetch upstream
```

**输出示例：**
```
remote: Enumerating objects: 6596, done.
remote: Counting objects: 100% (2277/2277), done.
...
 * [新分支]  main  -> upstream/main
```

**说明：** 这一步下载主项目的最新代码到本地，但不修改你的工作区。

### 第 4 步：合并主项目更改

```bash
git merge upstream/main
```

**三种可能的结果：**

#### ✅ 情况 1：自动合并成功
```
自动合并成功，本地代码已更新
```

**处理：** 直接跳到第 5 步推送。

#### ⚠️ 情况 2：产生冲突
```
自动合并失败，修正冲突然后提交修正的结果。
冲突（内容）：合并冲突于 file1.py
冲突（内容）：合并冲突于 file2.py
```

**处理：** 参考下面的 [冲突解决](#冲突解决) 部分。

#### ❌ 情况 3：合并冲突过多（建议中止）
```bash
# 中止合并，回到合并前状态
git merge --abort
```

---

## 冲突解决

### 查看冲突文件

```bash
# 列出所有有冲突的文件
git status

# 或者
git diff --name-only --diff-filter=U
```

### 解决方案选择

有三种解决冲突的策略：

#### 方案 A：保留上游版本（推荐同步时使用）

如果你想完全同步主项目，使用上游版本解决所有冲突：

```bash
# 对所有冲突文件使用upstream版本
git checkout --theirs <file1> <file2> ...

# 示例
git checkout --theirs README.md src/config.py

# 标记为已解决
git add <file1> <file2> ...
```

#### 方案 B：保留本地版本

如果有重要的本地定制需要保留：

```bash
# 对冲突文件使用本地版本
git checkout --ours <file1> <file2> ...

# 标记为已解决
git add <file1> <file2> ...
```

#### 方案 C：手动解决指定冲突

对于需要精细调整的文件，手动编辑：

```bash
# 编辑冲突文件
vim <conflict-file>
```

在文件中找到冲突标记：
```
<<<<<<< HEAD
本地版本的内容
=======
upstream版本的内容
>>>>>>> upstream/main
```

手动保留需要的部分，删除冲突标记。

保存后标记为已解决：
```bash
git add <conflict-file>
```

### 完成合并

解决所有冲突后：

```bash
# 创建合并提交
git commit -m "Sync with upstream/main: merge latest changes from primary project"
```

---

## 第 5 步：推送到远程 Fork

```bash
git push origin main
```

**验证成功：**
```
To https://github.com/your-username/mjlab.git
   old-hash..new-hash  main -> main
```

---

## 第 6 步：恢复本地更改（可选）

如果第 1 步中执行了 `git stash`，现在可以恢复本地修改：

```bash
# 查看 stash 列表
git stash list

# 恢复最新的 stash
git stash pop

# 或恢复特定的 stash（例如 stash@{0}）
git stash pop stash@{0}
```

**注意：** 恢复时可能产生新的冲突。按照同样的方法解决即可。

---

## 常见问题

### Q1: 我应该多久同步一次主项目？

**A:** 建议：
- **活跃项目**（频繁更新）: 每周一次
- **稳定项目**（月度更新）: 每月一次
- **发布前**：必须同步一次
- **发现 bug**：检查是否主项目已修复

### Q2: 冲突太多，无法快速解决怎么办？

**A:** 中止合并并寻求帮助：
```bash
# 中止合并
git merge --abort

# 查看详细冲突信息
git diff upstream/main

# 如果需要，可以创建新分支逐步合并
git checkout -b sync-upstream
git merge upstream/main
```

### Q3: 已经 push 到 origin 后发现有问题怎么办？

**A:** 如果只是本地分支，可以使用 rebase：
```bash
# 中止之前的合并（如果还在进行）
git merge --abort

# 重新开始
git reset --hard origin/main
git fetch upstream
git merge upstream/main
```

### Q4: 如何只同步特定的文件而不是整个分支？

**A:** 使用 cherry-pick：
```bash
# 获取特定提交的哈希
git log upstream/main

# 应用特定提交
git cherry-pick <commit-hash>
```

### Q5: upstream 分支名不是 main 怎么办？

**A:** 查看上游分支名：
```bash
git branch -r  # 查看所有远程分支

# 使用正确的分支名，例如 master
git merge upstream/master
```

---

## 最佳实践

### ✅ DO（推荐）

1. **定期同步** - 避免过多相怪问题堆积
2. **同步前提交** - 确保本地工作已保存
3. **查看上游变更** - 合并前了解做了什么改动
4. **保留合并历史** - 便于追踪问题来源
5. **在功能分支上工作** - main 分支只用于同步

### ❌ DON'T（避免）

1. ❌ **在 main 上做大量自定义** - 增加同步难度
2. ❌ **force push 到公共分支** - 可能丢失历史和他人工作
3. ❌ **忽视合并冲突** - 自动解决可能破坏代码
4. ❌ **不测试合并结果** - 验证同步后代码可用
5. ❌ **同时修改和同步** - 先完成本地工作，再同步

### 🔍 检查清单

同步前：
- [ ] 提交所有本地修改或 stash
- [ ] 确认当前分支是 main
- [ ] 运行测试验证当前代码可用

合并后：
- [ ] 查看合并摘要 `git log --oneline -5`
- [ ] 检查关键文件是否符合预期
- [ ] 运行测试验证合并结果
- [ ] 查看是否有 Breaking Changes

推送前：
- [ ] 再次验证本地改动正确
- [ ] 检查网络连接
- [ ] 准备好处理权限问题

---

## 快速参考（一行命令）

### 标准同步流程

```bash
# 完整命令序列（逐行执行）
git status                          # 检查状态
git stash                           # 保存本地修改（如需要）
git fetch upstream                  # 获取上游
git merge upstream/main             # 合并上游
# 如有冲突，手动解决
git commit -m "Sync with upstream"  # 创建合并提交
git push origin main                # 推送到你的fork
git stash pop                       # 恢复本地修改（如有）
```

### 查看同步前后的差异

```bash
# 查看上游与本地的差异
git diff main upstream/main

# 查看上游新增的提交
git log main..upstream/main

# 查看完整日志
git log --oneline upstream/main -20
```

---

## 故障排除

### 问题：无法连接到 upstream

```bash
# 检查网络和 URL
git remote -v

# 测试连接
git fetch upstream

# 如果 URL 错误，修改它
git remote set-url upstream <correct-url>
```

### 问题：本地分支落后太多

```bash
# 查看落后多少个提交
git log --oneline main..upstream/main | wc -l

# 如果很多，考虑重新 checkout（仅限本地代码无重要定制）
git checkout main
git reset --hard upstream/main
```

### 问题：合并后代码无法运行

```bash
# 检查是否有 Breaking Changes
git diff HEAD~1 HEAD

# 查看相关提交信息
git log upstream/main -p --follow -- <problem-file>

# 回退合并（如果很严重）
git reset --hard HEAD~1
```

---

## 相关资源

- [Git 官方文档 - 同步 Fork](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/working-with-forks/syncing-a-fork)
- [Atlassian Git 教程](https://www.atlassian.com/git/tutorials/merging-vs-rebasing)
- [GitHub Sync Upstream 指南](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/working-with-forks/syncing-a-fork)

---

## 脚本：自动化同步

如果需要频繁同步，可以创建一个自动化脚本：

```bash
#!/bin/bash
# 文件名：sync-fork.sh

set -e

echo "🔄 开始同步 Fork 项目..."

# 检查是否有未提交的更改
if ! git diff-index --quiet HEAD --; then
    echo "⚠️  有未提交的更改，正在 stash..."
    git stash
    HAS_STASH=1
fi

# 获取主项目最新代码
echo "📥 从 upstream 获取代码..."
git fetch upstream

# 合并主项目
echo "🔀 合并 upstream/main..."
git merge upstream/main

# 推送到 fork
echo "📤 推送到 origin..."
git push origin main

# 恢复本地修改
if [ "$HAS_STASH" = "1" ]; then
    echo "♻️  恢复本地修改..."
    git stash pop
fi

echo "✅ 同步完成！"
```

使用方式：
```bash
chmod +x sync-fork.sh
./sync-fork.sh
```

---

**最后更新**: 2026年2月6日  
**版本**: 1.0
