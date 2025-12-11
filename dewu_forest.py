#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
得物森林 - iPhone完整优化版 v1.3.0
青龙面板专用版

cron: 0 9,18 * * *
new Env('得物森林');
"""

import os
import re
import sys
import time
import hashlib
import random
import json
import requests
from datetime import datetime
try:
    from sendNotify import send
except:
    send = None

# 版本信息
__version__ = '1.3.0'

def myprint(*args, sep=' ', end='\n', **kwargs):
    print(*args, sep=sep, end=end, **kwargs)

def get_env():
    """从青龙环境变量获取配置"""
    ck_list = []
    sk_list = []
    user_agent_list = []
    
    # 从环境变量获取
    env_str = os.getenv("dewu_x_auth_token")
    if env_str:
        # 支持多种分隔符
        if '&' in env_str:
            ck_list = env_str.split('&')
        elif '@' in env_str:
            ck_list = env_str.split('@')
        else:
            ck_list = [env_str]
    
    env_str = os.getenv("dewu_sk")
    if env_str:
        if '&' in env_str:
            sk_list = env_str.split('&')
        elif '@' in env_str:
            sk_list = env_str.split('@')
        else:
            sk_list = [env_str]
    
    env_str = os.getenv("dewu_user_agent")
    if env_str:
        if '&' in env_str:
            user_agent_list = env_str.split('&')
        elif '@' in env_str:
            user_agent_list = env_str.split('@')
        else:
            user_agent_list = [env_str]
    
    # 如果只有一个User-Agent但多个账号，重复使用
    if len(user_agent_list) == 1 and len(ck_list) > 1:
        user_agent_list = user_agent_list * len(ck_list)
    
    # 如果只有一个SK但多个账号，重复使用
    if len(sk_list) == 1 and len(ck_list) > 1:
        sk_list = sk_list * len(ck_list)
    
    return ck_list, sk_list, user_agent_list

class DeWu:
    def __init__(self, x_auth_token, sk, user_agent, index):
        self.index = index
        self.session = requests.Session()
        
        # 提取版本号
        pattern = r'duapp/([0-9]+\.[0-9]+\.[0-9]+)'
        match = re.search(pattern, user_agent)
        app_version = match.group(1) if match else '5.81.1'
        
        # iPhone headers
        self.headers = {
            'Host': 'app.dewu.com',
            'Connection': 'keep-alive',
            'Accept': '*/*',
            'User-Agent': user_agent,
            'x-auth-token': x_auth_token,
            'SK': sk,
            'appVersion': app_version,
            'appid': 'h5',
            'platform': 'h5',
            'Content-Type': 'application/json',
            'Origin': 'https://cdn-m.dewu.com',
            'X-Requested-With': 'com.shizhuang.duapp',
            'Referer': 'https://cdn-m.dewu.com/',
            'Accept-Encoding': 'gzip, deflate',
            'Accept-Language': 'zh-Hans-HK;q=1.0, en-US;q=0.9',
            'device_model': 'iPhone 14 Pro',
            'deviceTrait': 'iPhone',
            'networktype': 'WIFI',
            'countryCode': 'HK',
            'channel': 'App Store',
            'isProxy': '0',
            'emu': '0',
        }
    
    def random_delay(self, min_seconds=1, max_seconds=3):
        """随机延迟，避免请求过快"""
        delay = random.uniform(min_seconds, max_seconds)
        time.sleep(delay)
    
    def safe_request(self, method, url, **kwargs):
        """安全的请求方法"""
        try:
            self.random_delay(0.5, 1.5)
            
            if method.upper() == 'GET':
                response = self.session.get(url, headers=self.headers, **kwargs)
            elif method.upper() == 'POST':
                if 'headers' not in kwargs:
                    kwargs['headers'] = self.headers
                response = self.session.post(url, **kwargs)
            else:
                return None
            
            if response.status_code == 200:
                try:
                    return response.json()
                except:
                    return None
            return None
                
        except Exception as e:
            return None
    
    def get_droplet(self):
        """获取当前水滴"""
        url = 'https://app.dewu.com/hacking-tree/v1/user/init'
        data = {"keyword": ""}
        
        result = self.safe_request('POST', url, json=data)
        if result and result.get('data'):
            return result.get('data').get('droplet', 0)
        return 0
    
    def tree_info(self):
        """获取树信息"""
        url = 'https://app.dewu.com/hacking-tree/v1/user/target/info'
        
        result = self.safe_request('GET', url)
        if result and result.get('code') == 200:
            data = result.get('data', {})
            name = data.get('name', '')
            level = data.get('level', 0)
            return name, level
        return '', 0
    
    def tree_water(self):
        """浇水功能"""
        myprint("💧 正在尝试浇水...")
        
        water_url = 'https://app.dewu.com/hacking-tree/v1/tree/watering'
        water_result = self.safe_request('POST', water_url, json={})
        
        if not water_result:
            return 0, 0
            
        code = water_result.get('code')
        
        if code == 200:
            data = water_result.get('data', {})
            if data and data.get('userWateringDroplet'):
                current_water = data.get('userWateringDroplet', 0)
                need_water = data.get('currentLevelNeedWateringDroplet', 0)
                watering_cost = data.get('wateringCost', 30)
                myprint(f"✅ 浇水成功！进度: {current_water}/{need_water}，消耗{watering_cost}g")
                
                if data and data.get('nextWateringTimes') == 0:
                    myprint("🎁 有浇水奖励可领取")
                    reward = self.receive_watering_reward()
                    if reward > 0:
                        return watering_cost, reward
                
                return watering_cost, 0
            else:
                myprint(f"✅ 浇水成功！")
                return 30, 0
                
        elif code == 711110015:
            myprint("📝 今日浇水已达上限")
            return 0, 0
        elif code == 711110002:
            myprint("💧 水滴不足，无法浇水")
            return 0, 0
        elif code == 1001:
            myprint("📝 今日浇水任务已完成")
            return 0, 0
        else:
            msg = water_result.get('msg', '未知错误')
            myprint(f"❌ 浇水失败: {msg} (code: {code})")
            return 0, 0
    
    def receive_watering_reward(self):
        """领取浇水奖励"""
        url = 'https://app.dewu.com/hacking-tree/v1/tree/get_watering_reward'
        
        result = self.safe_request('POST', url, json={"promote": ""})
        if result and result.get('code') == 200:
            data_info = result.get('data', {})
            current_reward = data_info.get('currentWateringReward', {})
            reward_num = current_reward.get('rewardNum', 0)
            myprint(f"🎁 领取浇水奖励成功，获得{reward_num}g水滴")
            return reward_num
        return 0
    
    def receive_bubble_droplet(self):
        """领取气泡水滴"""
        myprint("💦 检查气泡水滴...")
        
        info_url = 'https://app.dewu.com/hacking-tree/v1/droplet-extra/info'
        result = self.safe_request('GET', info_url)
        
        if not result or result.get('code') != 200:
            myprint("📭 暂无气泡水滴信息")
            return 0
        
        data = result.get('data', {})
        receivable = data.get('receivable', False)
        
        if receivable:
            receive_url = 'https://app.dewu.com/hacking-tree/v1/droplet-extra/receive'
            receive_result = self.safe_request('POST', receive_url)
            
            if not receive_result:
                myprint("❌ 领取气泡水滴失败")
                return 0
            
            if receive_result.get('code') == 200:
                total_droplet = receive_result.get('data', {}).get('totalDroplet', 0)
                myprint(f"🎯 领取气泡水滴成功，获得{total_droplet}g水滴")
                return total_droplet
            elif receive_result.get('code') == 1001:
                myprint("📝 气泡水滴已领取")
                return 0
        else:
            daily_extra = data.get('dailyExtra', {})
            if daily_extra:
                total_droplet = daily_extra.get('totalDroplet', 0)
                pop_title = daily_extra.get('popTitle', '气泡水滴')
                myprint(f"💧 {pop_title}，已经积攒{total_droplet}g水滴!")
        
        return 0
    
    def receive_bucket_droplet(self):
        """领取木桶水滴"""
        myprint("🪣 检查木桶水滴...")
        
        info_url = 'https://app.dewu.com/hacking-tree/v1/droplet/generate_info'
        result = self.safe_request('GET', info_url)
        
        if not result or result.get('code') != 200:
            myprint("❌ 获取木桶信息失败")
            return 0
        
        data = result.get('data', {})
        current_droplet = data.get('currentDroplet', 0)
        get_times = data.get('getTimes', 0)
        
        myprint(f"🪣 木桶状态: {current_droplet}/100，今天已领取{get_times}次")
        
        if current_droplet == 100:
            receive_url = 'https://app.dewu.com/hacking-tree/v1/droplet/get_generate_droplet'
            receive_result = self.safe_request('POST', receive_url)
            
            if not receive_result:
                myprint("❌ 领取木桶水滴失败")
                return 0
            
            if receive_result.get('code') == 200:
                droplet = receive_result.get('data', {}).get('droplet', 0)
                myprint(f"✅ 领取木桶水滴成功，获得{droplet}g水滴")
                return droplet
        else:
            myprint(f"⏳ 木桶: {current_droplet}/100，未满")
        
        return 0
    
    def game_center_check_in(self):
        """领潮金币签到"""
        myprint("🪙 领潮金币签到...")
        url = 'https://app.dewu.com/hacking-game-center/v1/sign/sign'
        
        result = self.safe_request('POST', url)
        if not result:
            return 0
        
        if result.get('code') == 200:
            myprint("✅ 领潮金币签到成功")
            return 1
        elif result.get('code') == 1001:
            myprint("📝 领潮金币已签到")
            return 0
        return 0
    
    def droplet_check_in(self):
        """水滴7天签到"""
        myprint("📅 水滴签到...")
        
        sign_url = 'https://app.dewu.com/hacking-tree/v1/sign/sign_in'
        result = self.safe_request('POST', sign_url, json={})
        
        if not result:
            return 0
            
        code = result.get('code')
        
        if code == 200:
            num = result.get('data', {}).get('Num', 0)
            myprint(f"✅ 水滴签到成功，获得{num}g水滴")
            return num
        elif code == 711110001 or code == 1001:
            myprint("📝 水滴已签到")
            return 0
        return 0
    
    def receive_task_rewards(self):
        """领取任务奖励"""
        url = 'https://app.dewu.com/hacking-tree/v1/task/list'
        result = self.safe_request('GET', url)
        
        if not result or result.get('code') != 200:
            return 0
        
        tasks = result.get('data', {}).get('taskList', [])
        total_reward = 0
        
        for task in tasks:
            if task.get('isComplete') and not task.get('isReceiveReward'):
                task_id = task.get('taskId')
                classify = task.get('classify')
                task_name = task.get('taskName', '未知任务')
                
                myprint(f"  正在领取: {task_name}")
                
                receive_url = 'https://app.dewu.com/hacking-tree/v1/task/receive'
                data = {'classify': classify, 'taskId': task_id}
                
                result2 = self.safe_request('POST', receive_url, json=data)
                
                if not result2:
                    continue
                
                if result2.get('code') == 200:
                    reward = result2.get('data', {}).get('num', 0)
                    total_reward += reward
                    myprint(f"    ✅ 获得{reward}g水滴")
                elif result2.get('code') == 1001:
                    myprint(f"    📝 {task_name}已领取")
        
        return total_reward
    
    def get_level_reward(self):
        """领取等级奖励"""
        myprint("🏆 检查等级奖励...")
        url = 'https://app.dewu.com/hacking-tree/v1/tree/get_level_reward'
        
        result = self.safe_request('POST', url, json={"promote": ""})
        if result and result.get('code') == 200:
            data_info = result.get('data', {})
            current_reward = data_info.get('currentLevelReward', {})
            reward_num = current_reward.get('rewardNum', 0)
            level_reward = data_info.get('levelReward', {})
            show_level = level_reward.get('showLevel', 0)
            
            if reward_num > 0:
                myprint(f"🎁 领取{show_level-1}级奖励成功，获得{reward_num}g水滴")
                return reward_num
        elif result and result.get('code') == 1001:
            myprint("📝 等级奖励已领取")
        
        return 0
    
    def main(self):
        myprint(f"\n{'='*40}")
        myprint(f"👤 账号 {self.index + 1}")
        myprint(f"{'='*40}")
        
        # 获取树信息
        name, level = self.tree_info()
        
        # 获取当前水滴
        start_droplet = self.get_droplet()
        myprint(f"💧 开始水滴: {start_droplet}g")
        
        if name:
            myprint(f"🌳 目标: {name}")
        if level:
            myprint(f"📊 等级: {level}")
        
        total_income = 0
        
        # 签到
        myprint(f"\n📝 签到检查...")
        total_income += self.game_center_check_in()
        total_income += self.droplet_check_in()
        
        # 领取气泡水滴
        bubble_income = self.receive_bubble_droplet()
        total_income += bubble_income
        
        # 领取木桶水滴
        bucket_income = self.receive_bucket_droplet()
        total_income += bucket_income
        
        # 领取任务奖励
        myprint(f"\n🎁 领取任务奖励...")
        reward_income = self.receive_task_rewards()
        total_income += reward_income
        
        # 检查等级奖励
        level_income = self.get_level_reward()
        total_income += level_income
        
        # 智能浇水（只浇1次完成任务）
        myprint(f"\n💧 智能浇水...")
        water_cost, water_reward = 0, 0
        
        # 只浇1次水完成任务
        cost, reward = self.tree_water()
        if cost > 0:
            water_cost = cost
            water_reward = reward
        
        water_net = water_reward - water_cost
        total_income += water_net
        
        if water_cost > 0:
            myprint(f"💧 浇水1次完成任务，消耗{water_cost}g，获得奖励{water_reward}g，净收益{water_net:+}g")
        
        # 最终水滴
        end_droplet = self.get_droplet()
        myprint(f"\n💰 最终水滴: {end_droplet}g")
        
        actual_change = end_droplet - start_droplet
        myprint(f"📊 水滴变化: {actual_change:+}g")
        
        myprint(f"{'='*40}")
        
        return {
            'start': start_droplet,
            'end': end_droplet,
            'change': actual_change,
            'income': total_income,
            'name': name,
            'level': level
        }

def main():
    # 获取环境变量
    ck_list, sk_list, user_agent_list = get_env()
    
    # 检查配置
    if not ck_list:
        myprint("❌ 未找到账号，请设置dewu_x_auth_token环境变量")
        if send:
            send('得物森林', '❌ 未找到账号配置')
        return
    
    if len(ck_list) > len(sk_list):
        myprint("⚠️  SK数量不足，将使用第一个SK")
        sk_list = sk_list * len(ck_list)
    
    if len(ck_list) > len(user_agent_list):
        myprint("⚠️  User-Agent数量不足，将使用第一个User-Agent")
        user_agent_list = user_agent_list * len(ck_list)
    
    myprint(f"📱 找到 {len(ck_list)} 个账号")
    myprint(f"🎯 版本: {__version__}")
    myprint(f"⏰ 开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    results = []
    total_change = 0
    
    # 执行每个账号
    for i in range(len(ck_list)):
        ck = ck_list[i]
        sk = sk_list[i] if i < len(sk_list) else sk_list[0]
        ua = user_agent_list[i] if i < len(user_agent_list) else user_agent_list[0]
        
        dewu = DeWu(ck, sk, ua, i)
        result = dewu.main()
        results.append(result)
        total_change += result['change']
        
        # 账号间延迟
        if i < len(ck_list) - 1:
            delay = random.uniform(3, 6)
            time.sleep(delay)
    
    # 发送通知
    myprint(f"\n📊 总结: 总水滴变化 {total_change:+}g")
    myprint(f"⏰ 结束时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 构建通知消息
    message = f"得物森林任务完成\n\n"
    message += f"账号数量: {len(results)}个\n"
    message += f"总水滴变化: {total_change:+}g\n\n"
    
    for i, result in enumerate(results):
        message += f"账号{i+1}:\n"
        message += f"目标: {result['name']} (Lv{result['level']})\n"
        message += f"水滴: {result['start']}g → {result['end']}g ({result['change']:+}g)\n"
        message += f"计算收益: {result['income']:+}g\n"
        if i < len(results) - 1:
            message += "---\n"
    
    if send:
        try:
            send('得物森林', message)
            myprint("📢 通知发送成功")
        except Exception as e:
            myprint(f"📢 通知发送失败: {e}")
    else:
        myprint("📢 未配置通知，跳过发送")

if __name__ == '__main__':
    main()
