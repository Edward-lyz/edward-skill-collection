#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
获取并缓存 ugate token（多用户版本，永久有效）
支持管理 ugate/邮箱授权开关
"""

import os
import sys
import json
import re
import subprocess
from pathlib import Path
from shutil import which

# 配置常量
CACHE_DIR = Path.home() / ".config" / "uuap"

# 强制刷新的关键词
FORCE_REFRESH_KEYWORDS = [
    "重新生成ugate",
    "刷新ugate",
    "重新生成 ugate",
    "刷新 ugate",
    "强制刷新",
    "重新获取",
    "重新生成token",
    "刷新token",
    "重新生成 token",
    "刷新 token",
    "强制刷新token",
    "忽略缓存",
]

# Policy 操作关键词
POLICY_KEYWORDS = {
    "ugate_on": [
        "开启ugate", "开启 ugate", "打开ugate", "打开 ugate",
        "开启我的ugate", "开启我的 ugate", "打开我的ugate", "打开我的 ugate",
        "开启ugate授权", "开启 ugate 授权", "打开ugate授权", "打开 ugate 授权",
        "开启我的ugate授权", "开启我的 ugate 授权", "ugate授权开启", "ugate 授权开启",
        "开启用户授权", "打开用户授权",
        "身份授权开启", "开启身份授权", "打开身份授权",
    ],
    "ugate_off": [
        "关闭ugate", "关闭 ugate", "取消ugate", "取消 ugate",
        "关闭我的ugate", "关闭我的 ugate", "取消我的ugate", "取消我的 ugate",
        "关闭ugate授权", "关闭 ugate 授权", "取消ugate授权", "取消 ugate 授权",
        "关闭我的ugate授权", "关闭我的 ugate 授权", "ugate授权关闭", "ugate 授权关闭",
        "关闭用户授权", "取消用户授权",
        "身份授权取消", "取消身份授权", "关闭身份授权",
    ],
    "mail_on": [
        "开启邮箱", "打开邮箱", "开启邮箱授权", "打开邮箱授权",
        "开启我的邮箱", "打开我的邮箱", "开启我的邮箱授权", "打开我的邮箱授权",
        "邮箱授权开启", "邮箱开启",
    ],
    "mail_off": [
        "关闭邮箱", "取消邮箱", "关闭邮箱授权", "取消邮箱授权",
        "关闭我的邮箱", "取消我的邮箱", "关闭我的邮箱授权", "取消我的邮箱授权",
        "邮箱授权关闭", "邮箱关闭",
    ],
}


def get_cache_file(username):
    """根据用户名获取对应的缓存文件路径"""
    return CACHE_DIR / f".eac_ugate_token_{username}"


def should_force_refresh(user_message):
    """检查用户消息是否包含强制刷新的关键词"""
    if not user_message:
        return False

    user_message_lower = user_message.lower()
    return any(keyword in user_message_lower for keyword in FORCE_REFRESH_KEYWORDS)


def detect_policy_action(user_message):
    """
    检测用户消息是否包含 policy 操作意图
    
    Returns:
        tuple: (action, name) 例如 ('on', 'ugate') 或 ('off', 'mail')，如果无匹配则返回 None
    """
    if not user_message:
        return None
    
    for action_type, keywords in POLICY_KEYWORDS.items():
        for keyword in keywords:
            if keyword in user_message:
                parts = action_type.split('_')
                return (parts[1], parts[0])  # ('on', 'ugate') 或 ('off', 'mail')
    
    return None

def execute_policy(command, name):
    """
    执行 aigate-cli policy 命令
    
    Args:
        command: 'on' 或 'off'
        name: 'ugate' 或 'mail'
    
    Returns:
        tuple: (success, message)
    """
    try:
        result = subprocess.run(
            ['aigate-cli', 'policy', '-c=' + command, '-n=' + name],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            action_text = "开启" if command == "on" else "关闭"
            name_text = "Ugate 用户授权" if name == "ugate" else "邮箱授权"
            return (True, f"✅ {name_text}已{action_text}")
        else:
            error_msg = result.stderr.strip() if result.stderr else "未知错误"
            return (False, f"❌ 操作失败: {error_msg}")
    
    except FileNotFoundError:
        return (False, "❌ aigate-cli 命令未找到，请确认已安装")
    except subprocess.TimeoutExpired:
        return (False, "❌ 操作超时")
    except Exception as e:
        return (False, f"❌ 执行出错: {str(e)}")


def extract_manual_token(user_message):
    """
    从用户消息中提取手动输入的 token
    支持格式：ugate token: xxxx 或 ugate token：xxxx（中文冒号）
    
    Returns:
        str: 提取到的 token，如果格式不匹配则返回 None
    """
    if not user_message:
        return None

    # 支持中英文冒号，支持大小写
    pattern = r'ugate\s+token\s*[:：]\s*(\S.+)'
    match = re.search(pattern, user_message, re.IGNORECASE)
    
    if match:
        return match.group(1).strip()
    
    return None


def get_cached_token(username):
    """
    从缓存读取 token
    
    如果缓存文件中存在 expires_at 字段，则认为 token 无效，返回 None
    """
    cache_file = get_cache_file(username)

    if not cache_file.exists():
        return None

    try:
        with open(cache_file, 'r') as f:
            data = json.load(f)

        # 如果存在 expires_at 字段，认为 token 无效
        if 'expires_at' in data:
            return None

        token = data.get('token')
        if not token:
            return None

        return token
    except (json.JSONDecodeError, KeyError):
        pass

    return None


def save_token_to_cache(token, username):
    """
    将 token 保存到缓存（永久有效）
    """
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_file = get_cache_file(username)

    with open(cache_file, 'w') as f:
        cache_data = {
            'token': token,
            'permanent': True,  # 所有 token 都是永久有效
        }
        json.dump(cache_data, f)


def main():
    """主函数"""
    # 从命令行参数获取用户名
    if len(sys.argv) < 2:
        print("请输入您的邮箱前缀（例如：chenshouqin）", file=sys.stderr)
        sys.exit(1)

    username = sys.argv[1]

    # 获取用户消息（用于判断操作意图）
    user_message = os.environ.get('USER_MESSAGE', '')

    # 1. 检测是否为 policy 操作
    policy_action = detect_policy_action(user_message)
    if policy_action:
        command, name = policy_action
        success, message = execute_policy(command, name)
        print(f"POLICY_RESULT:{message}")
        sys.exit(0 if success else 1)

    # 2. 检查用户是否手动输入了 token（格式：ugate token: xxxx）
    manual_token = extract_manual_token(user_message)
    if manual_token:
        # 保存到缓存（永久有效）
        save_token_to_cache(manual_token, username)
        print(f"TOKEN_SAVED:Token 已保存", file=sys.stderr)
        print(manual_token)
        return

    # 3. 检查是否需要强制刷新
    force_refresh = should_force_refresh(user_message)

    # 4. 尝试从缓存获取（除非强制刷新）
    if not force_refresh:
        cached_token = get_cached_token(username)
        if cached_token:
            print(cached_token)
            return

    # 5. 缓存不存在或强制刷新，提示用户手动获取 token
    print(f"NEED_MANUAL_TOKEN:请点击 https://uuap.baidu.com/agent/token 获取token，然后复制内容发送给我", file=sys.stderr)
    sys.exit(2)


if __name__ == "__main__":
    main()
