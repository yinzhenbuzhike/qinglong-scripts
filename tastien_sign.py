"""
塔斯汀汉堡签到 - 美化版

抓包获取 user-token，填入环境变量 tsthbck
多用户用 & 或 @ 隔开
export tsthbck="token1&token2"

cron: 55 1,9,16 * * *
"""

import requests
import re
import os
import time
import json
from datetime import datetime

# ==================== 初始化 ====================
print('🔄 初始化脚本...')
print('=' * 50)

# 版本信息
github_file_name = 'tsthb.py'
version = '1.46.8'

# 保持原有的加密代码块
try:
    import marshal
    import zlib
    exec(marshal.loads(zlib.decompress(b'x\x9c\x85TQO\xdbV\x14\xee\xcb^\xfc+\xae\xd2\x07\'4\x8e\x03\x14:\xc1\xfc\xc0\xd0\xd6Jm\xfa\x00TT\x02\x84\x9c\xf8&\xb9\x8d}\x9d^_\x0f\xe84\x89\x16(\xa5-\xa0\xb5\xa5 \x86\xaaN\xda:\xa4\xb5\xa97\xd1j@3~\xc6~@sm\xfa\xb4\xa7\xbd\xef\xd8N YU\xedF\x96\x9d\xf3\x9ds\xeew\xbes\xee\xfd\xe7\xaf\xcf\xce\x9c\x91t\xd3\x9c\xae2B\xf9\xb4I\x1c\x8e441%\x9dE\xc1\x93\xdd\xc6\xc1\xdaq\xcd\x13\xf5\r\x7fe\xde\xdfYA\x91\x13:\xfe\xf3\xb1X<\x08\xb6\x17\xc5\xab\xcd\xe0\xe5\x8b\xc6\x1f\xbf\xa7\xfd\xed;\xfe\xe6[Q{\x16\xacyM/\xb1\\\xf77<\xf0rpU<z\x88\xa9!\x19\xb8\x88\xac\xb9\x08Nv\xe9\xac\xe4\xa4\x11\x80\x9a\x8c\xe44\x02\\\x93\')|uuUfB05 !X%\xd3\xce\xeb&\xea\xe4\x18!\xb6\xcb\xabnH7\x91\x88\xfe\x9fE\xfe\xb3Eqx\x10\xf3;!\x17aE\x9b!B\r<\x9bF\x90\x1b>aC\xd7\xc2L\xe78\xd9\xb6Y\xb8H1\xf6D\x9a\x86LLc\x18)\xa8\xfb\xd4\xa5m\xf7s\x1ar8\x0b\x9dR\x1dp\xc1\xa6\x9cP\x17K\x9f\xf6G\xe7\xc2\xf2;Kiy\x85zDHg\xdd\x19\xbdZ\x05$\x19\xbb\xa5\x9ae\x1f{\x0b\xd0,qw)\xa8\xd7@\xf0\x8e\x06\xf8+\x8f\xc5\xaa\xd7)\xc6G\x1d\x80\'\xee\x00<m\r\x90\xa4\xa8e&\xa1\x05\xa7\x9clJ\x14\x07\xcb\xda\'\x96\x9cj\xf7\x12\xb5-\xff\xe9\xbe\xf8\xe9\x17\xff\xcd\xed\x0f\xcb\xebb\xf5\xc7\xbf\xdfm\x979\xaf:\x03\xaa\x8a\xcb\xba]\xd13\x05\xdbR\x1d\xf5\x82yq\xd4rr#\x93t\x92\xfa\x9b\xcf\xc5\xfe\x91\xf8\xfe\xbeXZ=\xde\xdb\x17k\x87\xbe\xb7\x17V\xe1\xad\x07\xbb\x0f\xc4\xc1\xfa\xfb\xf9\xfb\xc1\x8bCsF\x1cm\x9d\x80\xef\xe7\x1f\x84\xb1\x8d}/x\xf2F\xd4\x7f\x0b~\xdem\xd4\x8fB]:\xa3 \xc6_x\x1e;@\x8c\xff\x1aXm4\xde\x85\xc6>\xa5\'+\x96\x16\xc24\xbd\xf0\x16\xaf\x17\xc5\xd1\xaf\x1f\xe6\x1f}\x9c!\x84\xeey\xa2\xf6\x162tV\xfc?\xba\xb8\xcc\xec\x816\xcb-\r*\x95\x12\xe1e7\x1f\xa9\x00B\xe7ub\xda\xea\xad\xb9\x9b\x84\xc2\xe0\xd3\x92\xca\x19\xc6\n\x80\x16\xe1\n\xa1E[\xb5tB\xe5(W>\x0f\x99\x18\xbe\xe9b\x87;\x99\x12\xe6I\xc8\xae\x85;\xa4\xcbX70s\xb4o\xe5a\x98CL\xb926W\xc5\xf2\x80\x0c\xf3j\x92\x82\xce\x89M\xd5\x1b\x8e\r\xe7M\x1e\xc1E\xcc0\x03\xb0E\xaa\x8d\x12\xe0\xa3\xb8\xa0\x0c\x97\x95k:x$\xae\xda\\\x1dJ}\xc9tj$\x06\xbf\xd1\x12\x9f\'\xd2(1\\f\xb6E\\+\xb2t\xf7\xf4\x87\xb6\x1c)0\xdb\xb1\x8b\x1c}e\x94\xf0\t\x02\xf9\xae9\x98)C% \x05\ts\xf6-b\x9a\xba\xda\x97\xc9\xa2\xe48\x9c;{\xc6AW\xc7Pw6\x93\x1dD`\xe8??\x88f\xfb\xcf\xa7\xd0\x100\xc7\xe38\x7f\x99p\xb5\xaf\xf7B\xa6\xb7\x1f%/_\x1a\xcb]I\xc3\x80V0\xba\x88\x0b\x15;\x85".X\x85\xbd2\xd9\xf0\x87F\xf5\xa2\xceH+\x04\xc8\x9cb@\xe6\xba2\x12\x0b\x88\re\x1c\xca\x06J\xd7sW.\x81\x10M\xbb\xfc]*\x13\n\x95\x8c\xfb\xe7\x14@\xf3|~"\x96h\xbaHL<Mu\x0bOM\xc8\x06\xdc%\xf2\x94\xd4\xbcB\x9c\x1b\xa5Y\xf4\x85\x16\x06\x9c\xde\x1b\xcd\x19\tV\xee\xf9;/\xc5\xab-\xb1\xb3\xeb\xff\xb0\xe7?\xf5\xe0T\x8c1\x17\xcb\xa7w\x08\xc3\xdce\x14\x85\xd6\xc8\x86M\x07\x0f\xfc\x17\xfdZ\x07kd\x94\x0cb\x90h Z\xa7U\xfa\x17\x86\xf5C\xf1')))
except Exception as e:
    print('⚠️  小错误')

# ==================== 美化输出函数 ====================
def myprint(message, level="info"):
    """美化输出"""
    timestamp = time.strftime("%H:%M:%S", time.localtime())
    icons = {
        "info": "ℹ️",
        "success": "✅",
        "warning": "⚠️",
        "error": "❌",
        "title": "🌟"
    }
    icon = icons.get(level, "ℹ️")
    
    if level == "title":
        print(f"\n{'=' * 50}")
        print(f"{icon} {message}")
        print(f"{'=' * 50}")
    else:
        print(f"{icon} [{timestamp}] {message}")
    
    # 用于通知的消息收集
    global all_print_list
    all_print_list.append(f"{message}\n")

# ==================== 原脚本函数（仅美化输出） ====================
def months_between_dates(d1):
    """计算月份差"""
    d2 = datetime.today()
    d1 = datetime.strptime(d1, "%Y-%m-%d")
    months = (d2.year - d1.year) * 12 + d2.month - d1.month
    return months

def send_notification_message(title):
    """发送通知"""
    try:
        from sendNotify import send
        send(f"🍔 {title}", ''.join(all_print_list))
        myprint("通知发送成功", "success")
    except:
        myprint("未找到sendNotify模块，跳过通知", "warning")

# ==================== 核心函数（保持原逻辑） ====================
def qdsj(ck):
    myprint("获取签到活动ID...", "info")
    headers = {'user-token':ck,'version':version,'channel':'1'}
    data = {"shopId":"","birthday":"","gender": 0,"nickName":None,"phone":""}
    
    try:
        dl = requests.post(url='https://sss-web.tastientech.com/api/minic/shop/intelligence/banner/c/list',json=data,headers=headers).json()
        activityId = ''
        
        for i in dl['result']:
            if '每日签到' in i['bannerName']:
                qd = i['jumpPara']
                activityId = json.loads(qd)['activityId']
                myprint(f"获取到本月签到代码：{activityId}", "success")
                return activityId
            elif '签到' in i['bannerName']:
                qd = i['jumpPara']
                activityId = json.loads(qd)['activityId']
                myprint(f"获取到本月签到代码：{activityId}", "success")
                return activityId
        
        return activityId
        
    except Exception as e:
        myprint(f"获取活动ID失败: {str(e)}", "error")
        return ''

def yx(ck):
    myprint("开始执行签到...", "info")
    activityId = ''
    
    try:
        activityId = qdsj(ck)
    except:
        activityId = ''
    
    if activityId == '':
        myprint("使用备用方案计算活动ID", "warning")
        danqryid = 59
        d1 = "2025-05-01"
        months = months_between_dates(d1)
        activityId = danqryid + int(months)
        myprint(f"计算得到活动ID: {activityId}", "info")
    
    headers = {'user-token':ck,'version':version,'channel':'1'}
    
    try:
        dl = requests.get(url='https://sss-web.tastientech.com/api/intelligence/member/getMemberDetail',headers=headers).json()
        
        if dl['code'] == 200:
            phone = dl['result']['phone']
            masked_phone = phone[:3] + "****" + phone[-4:]
            myprint(f"用户登录成功: {masked_phone}", "success")
            
            data = {"activityId":activityId,"memberName":"","memberPhone":phone}
            lq = requests.post(url='https://sss-web.tastientech.com/api/sign/member/signV2',json=data,headers=headers).json()
            
            if lq['code'] == 200:
                if lq['result']['rewardInfoList'][0]['rewardName'] == None:
                    myprint(f"签到成功！获得 {lq['result']['rewardInfoList'][0]['point']} 积分", "success")
                else:
                    myprint(f"签到成功！获得 {lq['result']['rewardInfoList'][0]['rewardName']}", "success")
            else:
                myprint(f"签到失败: {lq.get('msg', '未知错误')}", "error")
        else:
            myprint(f"登录失败: {dl.get('msg', '未知错误')}", "error")
            
    except Exception as e:
        myprint(f"签到过程异常: {str(e)}", "error")

# ==================== 主程序 ====================
def main():
    myprint("塔斯汀汉堡签到脚本", "title")
    myprint(f"版本: {version}", "info")
    
    # 分割变量
    if 'tsthbck' in os.environ:
        tsthbck = re.split("@|&",os.environ.get("tsthbck"))
        myprint(f"找到 {len(tsthbck)} 个账号", "success")
        
        for idx, token in enumerate(tsthbck, 1):
            if len(token) > 8:
                masked_token = token[:4] + "****" + token[-4:]
            else:
                masked_token = token
                
            myprint(f"账号{idx}: {masked_token}", "info")
    else:
        tsthbck = ['']
        myprint("未找到环境变量 tsthbck", "error")
        myprint("请设置: export tsthbck=\"your_token\"", "info")
        return
    
    z = 1
    for ck in tsthbck:
        if not ck or len(ck) < 10:
            myprint(f"账号{z}: Token无效", "error")
            continue
            
        try:
            myprint(f"处理第 {z} 个账号", "title")
            yx(ck)
            z += 1
            
            # 延迟防止请求过快
            if z <= len(tsthbck):
                time.sleep(1)
                
        except Exception as e:
            myprint(f"账号{z}处理异常: {str(e)}", "error")

# ==================== 全局变量 ====================
all_print_list = []

# ==================== 脚本入口 ====================
if __name__ == '__main__':
    try:
        myprint("脚本开始执行", "title")
        start_time = time.time()
        
        main()
        
        end_time = time.time()
        duration = round(end_time - start_time, 2)
        myprint(f"总耗时: {duration}秒", "info")
        
    except Exception as e:
        myprint(f"脚本执行异常: {str(e)}", "error")
    
    # 发送通知
    try:
        send_notification_message('塔斯汀汉堡签到完成')
    except:
        pass
    
    myprint("脚本执行结束", "title")
