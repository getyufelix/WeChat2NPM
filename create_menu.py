import requests
import json

# 企业微信的corpid和corpsecret
corpid = "your_corpid"
corpsecret = "your_corpsecret"

# 企业微信的agentid
agent_id = "your_agentid"

# 获取access_token的函数
def get_access_token(corpid, corpsecret):
    url = f"https://qyapi.weixin.qq.com/cgi-bin/gettoken?corpid={corpid}&corpsecret={corpsecret}"
    response = requests.get(url)
    if response.status_code == 200:
        result = response.json()
        if result.get("errcode") == 0:
            return result.get("access_token")
        else:
            raise Exception(f"Failed to get access_token: {result.get('errmsg')}")
    else:
        raise Exception(f"Failed to get access_token: {response.status_code}")

# 获取access_token
access_token = get_access_token(corpid, corpsecret)

# 构造自定义菜单的JSON数据
menu_data = {
    "button": [
        {
            "name": "FRP",
            "sub_button": [
                {
                    "type": "click",
                    "name": "Enable",
                    "key": "frp.enable"
                },
                {
                    "type": "click",
                    "name": "Disable",
                    "key": "frp.disable"
                }
            ]
        }
    ]
}

# 将JSON数据转换为字符串
menu_data_str = json.dumps(menu_data, ensure_ascii=False).encode('utf-8')

# 构造请求URL
url = f"https://qyapi.weixin.qq.com/cgi-bin/menu/create?access_token={access_token}&agentid={agent_id}"

# 发送POST请求
response = requests.post(url, data=menu_data_str)

print("Response Status Code:", response.status_code)
print("Response Content:", response.json())