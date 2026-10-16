---
name: get-ugate-token
description: 获取并缓存 ugate token，供其他 skill 依赖使用进行API调用（多用户版本，永久有效）。支持管理 ugate/邮箱授权开关。
---

# get-ugate-token Skill

## 功能描述
该 skill 用于获取并缓存 ugate token，供其他 skill 依赖使用进行API调用。支持多用户独立缓存，每个用户有独立的缓存文件。

**核心特性：**
- 所有 token 都是永久有效的
- 支持用户手动输入 token
- **支持 ugate/邮箱授权开关管理**

## 文件结构

```
get-ugate-token/
├── SKILL.md           # 技能说明文档
└── getUgateToken.py   # Python 主脚本
```

## 功能列表

### 1. Token 管理

#### 手动输入 Token

**当用户发送格式为 `ugate token: xxxx` 或 `ugate token：xxxx`（中文冒号）的消息时：**

1. **提取 token** - 从用户消息中提取 token 内容
2. **保存到缓存** - 将 token 保存到用户的缓存文件
3. **返回成功消息** - 输出 `TOKEN_SAVED:Token 已保存`

**示例：**

```bash
# 用户发送消息：ugate token: eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
USER_MESSAGE="ugate token: eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..." python3 getUgateToken.py chenshouqin 2>&1
TOKEN_SAVED:Token 已保存
eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
```

#### 检查缓存的 token

- 检查文件 `~/.config/uuap/.eac_ugate_token_{username}` 是否存在
- 如果文件存在，直接返回缓存的 token（永久有效）

#### 需要手动获取 token

如果缓存不存在：

1. **返回提示消息** - 输出到 stderr，格式为 `NEED_MANUAL_TOKEN:请点击 https://uuap.baidu.com/agent/token 获取token，然后复制内容发送给我`
2. **退出码为 2** - 表示需要手动获取 token（区别于错误退出码 1）

用户需要：
- 访问 https://uuap.baidu.com/agent/token
- 复制页面内容
- 将内容发送给技能调用者

### 2. 授权开关管理

通过 `aigate-cli policy` 命令管理 ugate 和邮箱授权开关。

#### 开启 Ugate 用户授权

**触发关键词：**
- 开启ugate / 开启 ugate / 打开ugate / 打开 ugate
- 开启我的ugate / 开启我的 ugate
- 开启ugate授权 / 开启 ugate 授权
- 开启用户授权 / 打开用户授权
- 身份授权开启 / 开启身份授权 / 打开身份授权

**执行命令：** `aigate-cli policy -c=on -n=ugate`

**示例：**
```bash
USER_MESSAGE="开启我的ugate授权" python3 getUgateToken.py chenshouqin
# 输出: POLICY_RESULT:✅ Ugate 用户授权已开启
```

#### 关闭 Ugate 用户授权

**触发关键词：**
- 关闭ugate / 关闭 ugate / 取消ugate / 取消 ugate
- 关闭我的ugate / 关闭我的 ugate
- 关闭ugate授权 / 关闭 ugate 授权
- 关闭用户授权 / 取消用户授权
- 身份授权取消 / 取消身份授权 / 关闭身份授权

**执行命令：** `aigate-cli policy -c=off -n=ugate`

**示例：**
```bash
USER_MESSAGE="关闭ugate授权" python3 getUgateToken.py chenshouqin
# 输出: POLICY_RESULT:✅ Ugate 用户授权已关闭
```

#### 开启邮箱授权

**触发关键词：**
- 开启邮箱 / 打开邮箱 / 开启邮箱授权
- 开启我的邮箱 / 打开我的邮箱授权
- 邮箱授权开启 / 邮箱开启

**执行命令：** `aigate-cli policy -c=on -n=mail`

**示例：**
```bash
USER_MESSAGE="开启邮箱授权" python3 getUgateToken.py chenshouqin
# 输出: POLICY_RESULT:✅ 邮箱授权已开启
```

#### 关闭邮箱授权

**触发关键词：**
- 关闭邮箱 / 取消邮箱 / 关闭邮箱授权
- 关闭我的邮箱 / 取消我的邮箱授权
- 邮箱授权关闭 / 邮箱关闭

**执行命令：** `aigate-cli policy -c=off -n=mail`

**示例：**
```bash
USER_MESSAGE="关闭邮箱授权" python3 getUgateToken.py chenshouqin
# 输出: POLICY_RESULT:✅ 邮箱授权已关闭
```

## 使用方法

```bash
# 获取 ugate token（需要传入用户名）
python3 /home/gem/.openclaw/skills/get-ugate-token/getUgateToken.py <username>

# 手动输入 token（通过 USER_MESSAGE 环境变量）
USER_MESSAGE="ugate token: eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..." python3 /home/gem/.openclaw/skills/get-ugate-token/getUgateToken.py <username>

# 开启 ugate 授权
USER_MESSAGE="开启ugate授权" python3 /home/gem/.openclaw/skills/get-ugate-token/getUgateToken.py <username>

# 关闭邮箱授权
USER_MESSAGE="关闭邮箱授权" python3 /home/gem/.openclaw/skills/get-ugate-token/getUgateToken.py <username>
```

## 输出格式

### 成功场景（缓存有效）

```bash
$ python3 getUgateToken.py chenshouqin
eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
```

### 手动输入 token 场景

```bash
$ USER_MESSAGE="ugate token: eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..." python3 getUgateToken.py chenshouqin 2>&1
TOKEN_SAVED:Token 已保存
eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
```

### 需要手动获取场景（缓存无效）

脚本会输出到 stderr 并以退出码 2 退出：

```bash
$ python3 getUgateToken.py chenshouqin 2>&1
NEED_MANUAL_TOKEN:请点击 https://uuap.baidu.com/agent/token 获取token，然后复制内容发送给我
```

### Policy 操作场景

```bash
$ USER_MESSAGE="开启ugate授权" python3 getUgateToken.py chenshouqin
POLICY_RESULT:✅ Ugate 用户授权已开启
```

## 强制刷新

当用户消息中包含以下关键词时，会忽略缓存：

- 重新生成ugate
- 刷新ugate
- 重新生成 ugate
- 刷新 ugate
- 强制刷新
- 重新获取
- 重新生成token
- 刷新token
- 重新生成 token
- 刷新 token
- 强制刷新token
- 忽略缓存

**使用方式：** 在调用脚本时设置环境变量 `USER_MESSAGE`，例如：

```bash
USER_MESSAGE="刷新ugate" python3 /home/gem/.openclaw/skills/get-ugate-token/getUgateToken.py <username>
```

## 环境变量依赖

- `USER_MESSAGE` - 用户原始消息（可选，用于判断操作意图）

## 缓存机制

- **缓存文件:** `~/.config/uuap/.eac_ugate_token_{username}`（多用户独立缓存）
- **缓存格式:** JSON
  ```json
  {
    "token": "xxx",
    "permanent": true
  }
  ```
- **缓存时长:** 永久有效

## 多用户支持

每个用户有独立的缓存文件，文件名格式为 `.eac_ugate_token_{username}`，例如：

- 用户 `chenshouqin` → `~/.config/uuap/.eac_ugate_token_chenshouqin`
- 用户 `zhangjianxing` → `~/.config/uuap/.eac_ugate_token_zhangjianxing`

这样可以避免不同用户的 token 相互干扰。

## 退出码说明

- **0**: 成功（token 返回或 policy 操作成功）
- **1**: 错误（参数缺失、policy 操作失败等）
- **2**: 需要手动获取 token（缓存无效，请提示用户访问 https://uuap.baidu.com/agent/token）

## 注意事项

- token 会缓存到本地文件中，避免重复获取
- 每个用户有独立的缓存文件，互不干扰
- 所有 token 都是永久有效的
- **手动输入 token 格式：** `ugate token: <token内容>` 或 `ugate token：<token内容>`（中文冒号）
- **Policy 操作依赖：** 需要系统已安装 `aigate-cli` 命令行工具
