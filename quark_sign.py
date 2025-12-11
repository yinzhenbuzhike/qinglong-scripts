'''
夸克网盘自动签到 - 美化版

Author: BNDou
LastEditTime: 2025-11-18 03:49:26
Description: 夸克网盘自动签到，支持多账户
'''

import os
import re
import sys
import requests
from datetime import datetime

# ==================== 美化输出类 ====================
class Logger:
    @staticmethod
    def info(msg):
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"ℹ️ [{timestamp}] {msg}")
    
    @staticmethod
    def success(msg):
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"✅ [{timestamp}] {msg}")
    
    @staticmethod
    def warning(msg):
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"⚠️ [{timestamp}] {msg}")
    
    @staticmethod
    def error(msg):
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"❌ [{timestamp}] {msg}")
    
    @staticmethod
    def title(msg):
        print("\n" + "=" * 60)
        print(f"🌟 {msg}")
        print("=" * 60)

# ==================== 通知模块 ====================
try:
    from utils.notify import send
    NOTIFY_AVAILABLE = True
except Exception as err:
    Logger.warning(f"加载通知服务失败: {err}")
    NOTIFY_AVAILABLE = False

# ==================== 获取环境变量 ====================
def get_env():
    if "COOKIE_QUARK" in os.environ:
        cookie_list = re.split(r'\n|&&', os.environ.get('COOKIE_QUARK'))
        return cookie_list
    else:
        Logger.error("未添加COOKIE_QUARK变量")
        if NOTIFY_AVAILABLE:
            send('夸克自动签到', '❌未添加COOKIE_QUARK变量')
        sys.exit(1)

# ==================== 夸克签到类 ====================
class Quark:
    def __init__(self, user_data):
        self.param = user_data
    
    def convert_bytes(self, b):
        '''字节单位转换'''
        units = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
        i = 0
        while b >= 1024 and i < len(units) - 1:
            b /= 1024
            i += 1
        return f"{b:.2f} {units[i]}"
    
    def get_growth_info(self):
        '''获取成长信息'''
        url = "https://drive-m.quark.cn/1/clouddrive/capacity/growth/info"
        querystring = {
            "pr": "ucpro",
            "fr": "android",
            "kps": self.param.get('kps'),
            "sign": self.param.get('sign'),
            "vcode": self.param.get('vcode')
        }
        try:
            response = requests.get(url=url, params=querystring, timeout=10).json()
            if response.get("data"):
                return response["data"]
            return False
        except Exception as e:
            Logger.error(f"获取成长信息失败: {e}")
            return False
    
    def get_growth_sign(self):
        '''执行签到'''
        url = "https://drive-m.quark.cn/1/clouddrive/capacity/growth/sign"
        querystring = {
            "pr": "ucpro",
            "fr": "android",
            "kps": self.param.get('kps'),
            "sign": self.param.get('sign'),
            "vcode": self.param.get('vcode')
        }
        data = {"sign_cyclic": True}
        try:
            response = requests.post(url=url, json=data, params=querystring, timeout=10).json()
            if response.get("data"):
                return True, response["data"]["sign_daily_reward"]
            return False, response.get("message", "签到失败")
        except Exception as e:
            return False, f"请求异常: {e}"
    
    def do_sign(self):
        '''执行签到任务'''
        log_lines = []
        
        # 获取成长信息
        growth_info = self.get_growth_info()
        if not growth_info:
            log_lines.append("❌ 获取成长信息失败")
            return "\n".join(log_lines)
        
        # 用户信息
        username = self.param.get('user', '未知用户')
        is_vip = "⭐ VIP用户" if growth_info.get('88VIP') else "👤 普通用户"
        log_lines.append(f"{is_vip} {username}")
        
        # 容量信息
        total_cap = self.convert_bytes(growth_info['total_capacity'])
        log_lines.append(f"💾 总容量: {total_cap}")
        
        # 签到累计容量
        sign_reward = growth_info['cap_composition'].get('sign_reward', 0)
        log_lines.append(f"📈 签到累计: {self.convert_bytes(sign_reward)}")
        
        # 签到状态
        cap_sign = growth_info['cap_sign']
        if cap_sign["sign_daily"]:
            daily_reward = self.convert_bytes(cap_sign['sign_daily_reward'])
            log_lines.append(f"✅ 今日已签到: +{daily_reward}")
            log_lines.append(f"📊 连签进度: {cap_sign['sign_progress']}/{cap_sign['sign_target']}")
        else:
            # 执行签到
            sign_result, sign_return = self.get_growth_sign()
            if sign_result:
                daily_reward = self.convert_bytes(sign_return)
                log_lines.append(f"🎉 签到成功: +{daily_reward}")
                log_lines.append(f"📊 连签进度: {cap_sign['sign_progress'] + 1}/{cap_sign['sign_target']}")
            else:
                log_lines.append(f"❌ 签到失败: {sign_return}")
        
        return "\n".join(log_lines)

# ==================== 工具函数 ====================
def extract_params(url):
    '''从URL提取参数'''
    query_start = url.find('?')
    if query_start == -1:
        return {}
    
    query_string = url[query_start + 1:]
    params = {}
    for param in query_string.split('&'):
        if '=' in param:
            key, value = param.split('=', 1)
            params[key] = value
    
    return {
        'kps': params.get('kps', ''),
        'sign': params.get('sign', ''),
        'vcode': params.get('vcode', '')
    }

# ==================== 主函数 ====================
def main():
    Logger.title("夸克网盘自动签到")
    
    # 获取账号列表
    accounts = get_env()
    Logger.success(f"检测到 {len(accounts)} 个夸克账号")
    
    all_results = []
    
    # 处理每个账号
    for idx, account in enumerate(accounts, 1):
        Logger.title(f"处理第 {idx} 个账号")
        
        # 解析账号信息
        user_data = {}
        for item in account.replace(" ", "").split(';'):
            if item and '=' in item:
                key, value = item.split('=', 1)
                user_data[key] = value
        
        # 从URL提取参数
        if 'url' in user_data:
            url_params = extract_params(user_data['url'])
            user_data.update(url_params)
        
        # 显示账号信息（脱敏）
        if 'user' in user_data:
            Logger.info(f"用户: {user_data['user']}")
        
        # 执行签到
        try:
            quark = Quark(user_data)
            result = quark.do_sign()
            print(result)
            all_results.append(f"账号{idx}:\n{result}")
        except Exception as e:
            error_msg = f"账号{idx} 处理异常: {e}"
            Logger.error(error_msg)
            all_results.append(error_msg)
        
        # 延迟防止请求过快
        if idx < len(accounts):
            import time
            time.sleep(1)
    
    # 汇总结果
    Logger.title("签到完成")
    summary = "\n\n".join(all_results)
    print(summary)
    
    # 发送通知
    if NOTIFY_AVAILABLE:
        try:
            send('📱 夸克网盘签到', summary)
            Logger.success("通知发送成功")
        except Exception as e:
            Logger.error(f"通知发送失败: {e}")
    
    return summary

# ==================== 脚本入口 ====================
if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        Logger.error("用户中断执行")
    except Exception as e:
        Logger.error(f"脚本执行异常: {e}")
    finally:
        Logger.title("执行结束")
