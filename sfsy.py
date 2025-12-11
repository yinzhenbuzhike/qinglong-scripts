#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
顺丰速运签到脚本 - 青龙面板版
功能：签到、领券、丰蜜任务、活动任务等
作者：呆呆呆呆（修改）
版本：2025.01.06
GitHub：https://github.com/你的用户名/你的仓库名
"""

import hashlib
import json
import os
import random
import time
import re
from datetime import datetime, timedelta
import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning
from urllib.parse import unquote, quote

# 禁用安全请求警告
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

# ========== 配置区域 ==========
APP_NAME = '顺丰速运'
ENV_NAME = 'sfsyUrl'
CK_NAME = 'url'
PROXY_API_URL = os.getenv('SF_PROXY_API_URL', '')  # 从环境变量获取代理API地址

# 邀请ID列表（可自定义）
inviteId = ['']

# 全局变量
send_msg = ''
one_msg = ''

def Log(cont=''):
    """日志记录函数"""
    global send_msg, one_msg
    print(cont)
    if cont:
        one_msg += f'{cont}\n'
        send_msg += f'{cont}\n'

def get_proxy():
    """
    从代理API获取代理
    返回格式：{'http': 'http://ip:port', 'https': 'http://ip:port'}
    """
    try:
        if not PROXY_API_URL:
            print('⚠️ 未配置代理API地址，将不使用代理')
            return None
            
        response = requests.get(PROXY_API_URL, timeout=10)
        if response.status_code == 200:
            proxy_text = response.text.strip()
            if ':' in proxy_text:
                proxy = f'http://{proxy_text}'
                return {
                    'http': proxy,
                    'https': proxy
                }
        print(f'❌ 获取代理失败: {response.text}')
        return None
    except Exception as e:
        print(f'❌ 获取代理异常: {str(e)}')
        return None

def get_quarter_end_date():
    """获取当前季度的最后一天"""
    current_date = datetime.now()
    current_month = current_date.month
    current_year = current_date.year

    # 计算当前季度最后一个月
    quarter_end_month = ((current_month - 1) // 3 + 1) * 3
    
    # 如果季度结束月份超过12月，则调整到下一年的3月
    if quarter_end_month > 12:
        quarter_end_month = 3
        current_year += 1
    
    # 计算下个月的第一天，然后减去一天得到本月的最后一天
    if quarter_end_month == 12:
        next_month_first_day = datetime(current_year + 1, 1, 1)
    else:
        next_month_first_day = datetime(current_year, quarter_end_month + 1, 1)
    
    quarter_end_date = next_month_first_day - timedelta(days=1)
    
    return quarter_end_date

def is_activity_end_date(end_date):
    """检查活动是否结束"""
    current_date = datetime.now().date()
    end_date = datetime.strptime(end_date, "%Y-%m-%d").date()
    return current_date == end_date

class SFExpress:
    """顺丰速运签到主类"""
    
    def __init__(self, info, index):
        global one_msg
        one_msg = ''
        
        # 解析账号信息
        split_info = info.split('@')
        url = split_info[0]
        len_split_info = len(split_info)
        last_info = split_info[len_split_info - 1]
        self.send_UID = None
        if len_split_info > 0 and "UID_" in last_info:
            self.send_UID = last_info
        self.index = index + 1
        self.user_id = ''
        self.phone = ''
        self.mobile = ''

        # 获取代理
        self.proxy = get_proxy()
        if self.proxy:
            print(f"✅ 成功获取代理: {self.proxy['http']}")
        
        # 初始化会话
        self.s = requests.session()
        self.s.verify = False
        if self.proxy:
            self.s.proxies = self.proxy
            
        # 请求头
        self.headers = {
            'Host': 'mcs-mimp-web.sf-express.com',
            'upgrade-insecure-requests': '1',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.102 Safari/537.36 NetType/WIFI MicroMessenger/7.0.20.1781(0x6700143B) WindowsWechat(0x63090551) XWEB/6945 Flue',
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'sec-fetch-site': 'none',
            'sec-fetch-mode': 'navigate',
            'sec-fetch-user': '?1',
            'sec-fetch-dest': 'document',
            'accept-language': 'zh-CN,zh',
            'platform': 'MINI_PROGRAM',
        }
        
        # 活动相关属性
        self.ifPassAllLevel = False
        self.surplusPushTime = 0
        self.lotteryNum = 0
        self.anniversary_black = False
        self.member_day_black = False
        self.member_day_red_packet_drew_today = False
        self.member_day_red_packet_map = {}
        
        # 任务相关属性
        self.taskId = ''
        self.taskCode = ''
        self.strategyId = ''
        self.title = ''
        self.taskType = ''
        
        # 初始化
        self.login_res = self.login(url)
        self.all_logs = []
        self.today = datetime.now().strftime('%Y-%m-%d')
        self.max_level = 8
        self.packet_threshold = 1 << (self.max_level - 1)

    # ========== 工具方法 ==========
    
    def get_deviceId(self, characters='abcdef0123456789'):
        """生成设备ID"""
        result = ''
        for char in 'xxxxxxxx-xxxx-xxxx':
            if char == 'x':
                result += random.choice(characters)
            elif char == 'X':
                result += random.choice(characters).upper()
            else:
                result += char
        return result

    def getSign(self):
        """生成签名"""
        timestamp = str(int(round(time.time() * 1000)))
        token = 'wwesldfs29aniversaryvdld29'
        sysCode = 'MCS-MIMP-CORE'
        data = f'token={token}&timestamp={timestamp}&sysCode={sysCode}'
        signature = hashlib.md5(data.encode()).hexdigest()
        data = {
            'sysCode': sysCode,
            'timestamp': timestamp,
            'signature': signature
        }
        self.headers.update(data)
        return data

    def do_request(self, url, data={}, req_type='post', max_retries=3):
        """执行HTTP请求"""
        self.getSign()
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                if req_type.lower() == 'get':
                    response = self.s.get(url, headers=self.headers, timeout=30)
                elif req_type.lower() == 'post':
                    response = self.s.post(url, headers=self.headers, json=data, timeout=30)
                else:
                    raise ValueError('Invalid req_type: %s' % req_type)
                    
                response.raise_for_status()
                
                try:
                    res = response.json()
                    return res
                except json.JSONDecodeError as e:
                    print(f'JSON解析失败: {str(e)}, 响应内容: {response.text[:200]}')
                    retry_count += 1
                    if retry_count < max_retries:
                        print(f'正在进行第{retry_count + 1}次重试...')
                        time.sleep(2)
                        continue
                    return None
                    
            except requests.exceptions.RequestException as e:
                retry_count += 1
                if retry_count < max_retries:
                    print(f'请求失败，正在切换代理重试 ({retry_count}/{max_retries}): {str(e)}')
                    self.proxy = get_proxy()
                    if self.proxy:
                        print(f"✅ 成功获取新代理: {self.proxy['http']}")
                        self.s.proxies = self.proxy
                    time.sleep(2)
                else:
                    print('请求最终失败:', e)
                    return None
                
        return None

    # ========== 登录相关 ==========
    
    def login(self, sfurl):
        """登录账号"""
        try:
            decoded_url = unquote(sfurl)
            ress = self.s.get(decoded_url, headers=self.headers)
            self.user_id = self.s.cookies.get_dict().get('_login_user_id_', '')
            self.phone = self.s.cookies.get_dict().get('_login_mobile_', '')
            self.mobile = self.phone[:3] + "*" * 4 + self.phone[7:] if self.phone else ''
            
            if self.phone:
                Log(f'👤 账号{self.index}:【{self.mobile}】登陆成功')
                return True
            else:
                Log(f'❌ 账号{self.index}获取用户信息失败')
                return False
        except Exception as e:
            Log(f'❌ 登录异常: {str(e)}')
            return False

    # ========== 签到任务 ==========
    
    def sign(self):
        """每日签到"""
        print(f'🎯 开始执行签到')
        json_data = {"comeFrom": "vioin", "channelFrom": "WEIXIN"}
        url = 'https://mcs-mimp-web.sf-express.com/mcs-mimp/commonPost/~memberNonactivity~integralTaskSignPlusService~automaticSignFetchPackage'
        response = self.do_request(url, data=json_data)
        if response.get('success') == True:
            count_day = response.get('obj', {}).get('countDay', 0)
            if response.get('obj') and response['obj'].get('integralTaskSignPackageVOList'):
                packet_name = response["obj"]["integralTaskSignPackageVOList"][0]["packetName"]
                Log(f'✨ 签到成功，获得【{packet_name}】，本周累计签到【{count_day + 1}】天')
            else:
                Log(f'📝 今日已签到，本周累计签到【{count_day + 1}】天')
        else:
            print(f'❌ 签到失败！原因：{response.get("errorMessage")}')

    def superWelfare_receiveRedPacket(self):
        """超值福利签到"""
        print(f'🎁 超值福利签到')
        json_data = {'channel': 'czflqdlhbxcx'}
        url = 'https://mcs-mimp-web.sf-express.com/mcs-mimp/commonPost/~memberActLengthy~redPacketActivityService~superWelfare~receiveRedPacket'
        response = self.do_request(url, data=json_data)
        if response.get('success') == True:
            gift_list = response.get('obj', {}).get('giftList', [])
            if response.get('obj', {}).get('extraGiftList', []):
                gift_list.extend(response['obj']['extraGiftList'])
            gift_names = ', '.join([gift['giftName'] for gift in gift_list])
            receive_status = response.get('obj', {}).get('receiveStatus')
            status_message = '领取成功' if receive_status == 1 else '已领取过'
            Log(f'🎉 超值福利签到[{status_message}]: {gift_names}')
        else:
            error_message = response.get('errorMessage') or json.dumps(response) or '无返回'
            print(f'❌ 超值福利签到失败: {error_message}')

    def get_SignTaskList(self, END=False):
        """获取签到任务列表"""
        if not END: 
            print(f'🎯 开始获取签到任务列表')
        json_data = {
            'channelType': '1',
            'deviceId': self.get_deviceId(),
        }
        url = 'https://mcs-mimp-web.sf-express.com/mcs-mimp/commonPost/~memberNonactivity~integralTaskStrategyService~queryPointTaskAndSignFromES'
        response = self.do_request(url, data=json_data)
        if response.get('success') == True and response.get('obj') != []:
            totalPoint = response["obj"]["totalPoint"]
            if END:
                Log(f'💰 当前积分：【{totalPoint}】')
                return
            Log(f'💰 执行前积分：【{totalPoint}】')
            for task in response["obj"]["taskTitleLevels"]:
                self.taskId = task["taskId"]
                self.taskCode = task["taskCode"]
                self.strategyId = task["strategyId"]
                self.title = task["title"]
                status = task["status"]
                skip_title = ['用行业模板寄件下单', '去新增一个收件偏好', '参与积分活动']
                if status == 3:
                    print(f'✨ {self.title}-已完成')
                    continue
                if self.title in skip_title:
                    print(f'⏭️ {self.title}-跳过')
                    continue
                else:
                    self.doTask()
                    time.sleep(3)
                self.receiveTask()

    def doTask(self):
        """执行任务"""
        print(f'🎯 开始去完成【{self.title}】任务')
        json_data = {'taskCode': self.taskCode}
        url = 'https://mcs-mimp-web.sf-express.com/mcs-mimp/commonRoutePost/memberEs/taskRecord/finishTask'
        response = self.do_request(url, data=json_data)
        if response.get('success') == True:
            print(f'✨ 【{self.title}】任务-已完成')
        else:
            print(f'❌ 【{self.title}】任务-{response.get("errorMessage")}')

    def receiveTask(self):
        """领取任务奖励"""
        print(f'🎁 开始领取【{self.title}】任务奖励')
        json_data = {
            "strategyId": self.strategyId,
            "taskId": self.taskId,
            "taskCode": self.taskCode,
            "deviceId": self.get_deviceId()
        }
        url = 'https://mcs-mimp-web.sf-express.com/mcs-mimp/commonPost/~memberNonactivity~integralTaskStrategyService~fetchIntegral'
        response = self.do_request(url, data=json_data)
        if response.get('success') == True:
            print(f'✨ 【{self.title}】任务奖励领取成功！')
        else:
            print(f'❌ 【{self.title}】任务-{response.get("errorMessage")}')

    # ========== 丰蜜任务 ==========
    
    def get_honeyTaskListStart(self):
        """获取丰蜜任务列表"""
        print('🍯 开始获取采蜜换大礼任务列表')
        json_data = {}
        self.headers['channel'] = 'wxwdsj'
        url = 'https://mcs-mimp-web.sf-express.com/mcs-mimp/commonPost/~memberNonactivity~receiveExchangeIndexService~taskDetail'

        response = self.do_request(url, data=json_data)
        if response.get('success') == True:
            for item in response["obj"]["list"]:
                self.taskType = item["taskType"]
                status = item["status"]
                if status == 3:
                    print(f'✨ 【{self.taskType}】-已完成')
                    continue
                if "taskCode" in item:
                    self.taskCode = item["taskCode"]
                    if self.taskType == 'DAILY_VIP_TASK_TYPE':
                        self.get_coupom_list()
                    else:
                        self.do_honeyTask()
                if self.taskType == 'BEES_GAME_TASK_TYPE':
                    self.honey_damaoxian()
                time.sleep(2)

    def do_honeyTask(self):
        """执行丰蜜任务"""
        json_data = {"taskCode": self.taskCode}
        url = 'https://mcs-mimp-web.sf-express.com/mcs-mimp/commonPost/~memberEs~taskRecord~finishTask'
        response = self.do_request(url, data=json_data)
        if response.get('success') == True:
            print(f'>【{self.taskType}】任务-已完成')
        else:
            print(f'>【{self.taskType}】任务-{response.get("errorMessage")}')

    def receive_honeyTask(self):
        """收取丰蜜"""
        print('>>>执行收取丰蜜任务')
        self.headers['syscode'] = 'MCS-MIMP-CORE'
        self.headers['channel'] = 'wxwdsj'
        self.headers['accept'] = 'application/json, text/plain, */*'
        self.headers['content-type'] = 'application/json;charset=UTF-8'
        self.headers['platform'] = 'MINI_PROGRAM'
        json_data = {"taskType": self.taskType}
        url = 'https://mcs-mimp-web.sf-express.com/mcs-mimp/commonPost/~memberNonactivity~receiveExchangeIndexService~receiveHoney'
        response = self.do_request(url, data=json_data)
        if response.get('success') == True:
            print(f'收取任务【{self.taskType}】成功！')
        else:
            print(f'收取任务【{self.taskType}】失败！原因：{response.get("errorMessage")}')

    def get_coupom(self, goods):
        """领取优惠券"""
        json_data = {
            "from": "Point_Mall",
            "orderSource": "POINT_MALL_EXCHANGE",
            "goodsNo": goods['goodsNo'],
            "quantity": 1,
            "taskCode": self.taskCode
        }
        url = 'https://mcs-mimp-web.sf-express.com/mcs-mimp/commonPost/~memberGoods~pointMallService~createOrder'
        response = self.do_request(url, data=json_data)
        return response.get('success') == True

    def get_coupom_list(self):
        """获取优惠券列表"""
        json_data = {
            "memGrade": 2,
            "categoryCode": "SHTQ",
            "showCode": "SHTQWNTJ"
        }
        url = 'https://mcs-mimp-web.sf-express.com/mcs-mimp/commonPost/~memberGoods~mallGoodsLifeService~list'
        response = self.do_request(url, data=json_data)
    
        if response.get('success') == True:
            all_goods = []
            for obj in response.get("obj", []):
                goods_list = obj.get("goodsList", [])
                all_goods.extend(goods_list)
               
            for goods in all_goods:
                exchange_times_limit = goods.get('exchangeTimesLimit', 0)
                if exchange_times_limit >= 1:
                    if self.get_coupom(goods):
                        print('✨ 成功领取券，任务结束！')
                        return
            print('📝 所有券尝试完成，没有可用的券或全部领取失败。')
        else:
            print(f'> 获取券列表失败！原因：{response.get("errorMessage")}')

    def honey_damaoxian(self):
        """丰蜜大冒险"""
        print('>>>执行大冒险任务')
        gameNum = 5
        for i in range(1, gameNum):
            json_data = {'gatherHoney': 20}
            if gameNum < 0: 
                break
            print(f'>>开始第{i}次大冒险')
            url = 'https://mcs-mimp-web.sf-express.com/mcs-mimp/commonPost/~memberNonactivity~receiveExchangeGameService~gameReport'
            response = self.do_request(url, data=json_data)
            stu = response.get('success')
            if stu:
                gameNum = response.get('obj')['gameNum']
                print(f'>大冒险成功！剩余次数【{gameNum}】')
                time.sleep(2)
                gameNum -= 1
            elif response.get("errorMessage") == '容量不足':
                print(f'> 需要扩容')
                self.honey_expand()
            else:
                print(f'>大冒险失败！【{response.get("errorMessage")}】')
                break

    def honey_expand(self):
        """丰蜜容器扩容"""
        print('>>>容器扩容')
        url = 'https://mcs-mimp-web.sf-express.com/mcs-mimp/commonPost/~memberNonactivity~receiveExchangeIndexService~expand'
        response = self.do_request(url, data={})
        stu = response.get('success', False)
        if stu:
            obj = response.get('obj')
            print(f'>成功扩容【{obj}】容量')
        else:
            print(f'>扩容失败！【{response.get("errorMessage")}】')

    def honey_indexData(self, END=False):
        """丰蜜数据"""
        if not END: 
            print('--------------------------------\n🍯 开始执行采蜜换大礼任务')
        random_invite = random.choice([invite for invite in inviteId if invite != self.user_id])
        self.headers['channel'] = 'wxwdsj'
        json_data = {"inviteUserId": random_invite}
        url = 'https://mcs-mimp-web.sf-express.com/mcs-mimp/commonPost/~memberNonactivity~receiveExchangeIndexService~indexData'
        response = self.do_request(url, data=json_data)
        if response.get('success') == True:
            usableHoney = response.get('obj').get('usableHoney')
            activityEndTime = response.get('obj').get('activityEndTime', '')

            if not END:
                print(f'📅 本期活动结束时间【{activityEndTime}】')
                Log(f'🍯 执行前丰蜜：【{usableHoney}】')
                taskDetail = response.get('obj').get('taskDetail')
                if taskDetail != []:
                    for task in taskDetail:
                        self.taskType = task['type']
                        self.receive_honeyTask()
                        time.sleep(2)
            else:
                Log(f'🍯 执行后丰蜜：【{usableHoney}】')
                return

    # ========== 活动任务 ==========
    
    def activityTaskService_taskList(self):
        """32周年活动任务"""
        print('🎭 开始32周年活动任务')
        json_data = {
            "activityCode": "DRAGONBOAT_2025",
            "channelType": "MINI_PROGRAM"
        }
        url = 'https://mcs-mimp-web.sf-express.com/mcs-mimp/commonPost/~memberNonactivity~activityTaskService~taskList'
        response = self.do_request(url, data=json_data)
        if response.get('success') == True:
            skip_task_types = [
                'PLAY_ACTIVITY_GAME', 'SEND_SUCCESS_RECALL', 'OPEN_SUPER_CARD',
                'CHARGE_NEW_EXPRESS_CARD', 'OPEN_NEW_EXPRESS_CARD', 'OPEN_FAMILY_CARD',
                'INTEGRAL_EXCHANGE'
            ]
            
            task_list = response.get('obj', [])
            task_list = [x for x in task_list if x.get('status') == 2 and x.get('taskType') not in skip_task_types]
            
            if not task_list:
                print('没有可执行的任务')
                return
                
            print(f'📝 获取到未完成任务: {len(task_list)}个')
            for task in task_list:
                print(f'📝 开始任务: {task.get("taskName")} [{task.get("taskType")}]')
                await_time = random.randint(1500, 3000) / 1000.0
                time.sleep(await_time)
                self.activityTaskService_finishTask(task)
                time.sleep(1.5)

    def activityTaskService_finishTask(self, task):
        """完成活动任务"""
        json_data = {"taskCode": task.get('taskCode')}
        url = 'https://mcs-mimp-web.sf-express.com/mcs-mimp/commonPost/~memberEs~taskRecord~finishTask'
        response = self.do_request(url, data=json_data)
        if response.get('success') == True:
            result_obj = response.get("obj", "")
            print(f'📝 完成任务[{task.get("taskName")}]: {result_obj}')
        else:
            error_code = response.get("errorCode", "未知错误码")
            error_msg = response.get("errorMessage", "未知错误")
            print(f'❌ 完成任务[{task.get("taskName")}]失败: {error_code} - {error_msg}')

    def activityTaskService_integralExchange(self):
        """积分兑换"""
        json_data = {
            "exchangeNum": 1,
            "activityCode": "DRAGONBOAT_2025"
        }
        url = 'https://mcs-mimp-web.sf-express.com/mcs-mimp/commonPost/~memberNonactivity~dragonBoat2025TaskService~integralExchange'
        response = self.do_request(url, data=json_data)
        if response.get('success') == True:
            print('✅ 积分兑换成功')
        else:
            error_msg = response.get("errorMessage", "未知错误")
            print(f'❌ 积分兑换失败: {error_msg}')

    # ========== 会员日任务 ==========
    
    def member_day_index(self):
        """会员日活动"""
        print('🎭 会员日活动')
        try:
            invite_user_id = random.choice([invite for invite in inviteId if invite != self.user_id])
            payload = {'inviteUserId': invite_user_id}
            url = 'https://mcs-mimp-web.sf-express.com/mcs-mimp/commonPost/~memberNonactivity~memberDayIndexService~index'

            response = self.do_request(url, data=payload)
            if response.get('success'):
                lottery_num = response.get('obj', {}).get('lotteryNum', 0)
                can_receive_invite_award = response.get('obj', {}).get('canReceiveInviteAward', False)
                if can_receive_invite_award:
                    self.member_day_receive_invite_award(invite_user_id)
                self.member_day_red_packet_status()
                Log(f'🎁 会员日可以抽奖{lottery_num}次')
                for _ in range(lottery_num):
                    self.member_day_lottery()
                if self.member_day_black:
                    return
                self.member_day_task_list()
                if self.member_day_black:
                    return
                self.member_day_red_packet_status()
            else:
                error_message = response.get('errorMessage', '无返回')
                Log(f'📝 查询会员日失败: {error_message}')
                if '没有资格参与活动' in error_message:
                    self.member_day_black = True
                    Log('📝 会员日任务风控')
        except Exception as e:
            print(e)

    def member_day_lottery(self):
        """会员日抽奖"""
        try:
            payload = {}
            url = 'https://mcs-mimp-web.sf-express.com/mcs-mimp/commonPost/~memberNonactivity~memberDayLotteryService~lottery'
            response = self.do_request(url, payload)
            if response.get('success'):
                product_name = response.get('obj', {}).get('productName', '空气')
                Log(f'🎁 会员日抽奖: {product_name}')
            else:
                error_message = response.get('errorMessage', '无返回')
                Log(f'📝 会员日抽奖失败: {error_message}')
                if '没有资格参与活动' in error_message:
                    self.member_day_black = True
                    Log('📝 会员日任务风控')
        except Exception as e:
            print(e)

    # ========== 主执行流程 ==========
    
    def main(self):
        """主执行函数"""
        global one_msg
        wait_time = random.randint(1000, 3000) / 1000.0  
        time.sleep(wait_time)  
        one_msg = ''
        
        if not self.login_res: 
            return False

        # 1. 执行签到任务
        Log('=' * 50)
        Log(f'📱 开始执行账号{self.index}任务')
        Log('=' * 50)
        
        self.sign()
        self.superWelfare_receiveRedPacket()
        self.get_SignTaskList()
        self.get_SignTaskList(True)

        # 2. 执行丰蜜任务
        self.get_honeyTaskListStart()
        self.honey_indexData()
        self.honey_indexData(True)

        # 3. 活动倒计时提醒
        activity_end_date = get_quarter_end_date()
        days_left = (activity_end_date - datetime.now()).days
        if days_left >= 0:
            message = f"⏰ 丰蜜活动截止兑换还有{days_left}天，请及时进行兑换！！"
            Log(message)

        # 4. 执行活动任务
        try:
            self.activityTaskService_taskList()
            self.activityTaskService_integralExchange()
        except Exception as e:
            print(f'活动任务执行异常: {str(e)}')

        # 5. 会员日任务
        current_date = datetime.now().day
        if 26 <= current_date <= 28:
            self.member_day_index()
        else:
            print('⏰ 未到指定时间不执行会员日任务')

        # 6. 任务完成统计
        Log('=' * 50)
        Log(f'✅ 账号{self.index}任务执行完成')
        Log('=' * 50)
        
        return True

def main():
    """主函数"""
    print(f"==================================")
    print(f"🚚 顺丰速运签到脚本")
    print(f"📅 版本：2025.01.06")
    print(f"👤 修改By：呆呆呆呆")
    print(f"==================================")
    
    # 获取环境变量
    tokens = re.split("\n", os.getenv(ENV_NAME, ""))
    
    if not tokens or not tokens[0]:
        print("❌ 未找到环境变量 sfsyUrl，请检查配置")
        return
    
    print(f"📱 共获取到 {len(tokens)} 个账号")
    print(f"==================================")
    
    success_count = 0
    for index, infos in enumerate(tokens):
        if not infos.strip():
            continue
            
        try:
            # URL编码处理
            encoded_info = quote(infos.strip())
            run_result = SFExpress(encoded_info, index).main()
            if run_result:
                success_count += 1
            print(f"\n")  # 账号间空行
        except Exception as e:
            print(f"❌ 账号{index+1}执行异常: {str(e)}")
    
    print(f"==================================")
    print(f"📊 执行完成：成功 {success_count}/{len(tokens)} 个账号")
    print(f"==================================")

if __name__ == '__main__':
    main()
