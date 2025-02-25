# -*- coding: utf-8 -*-
import datetime
import logging
import os
import requests
import threading
import time
import xml.etree.ElementTree as ET

from flask import Flask, jsonify, make_response, request
from WXBizMsgCrypt3 import WXBizMsgCrypt
from telegram import Update, Bot
from telegram.ext import Dispatcher, CommandHandler, MessageHandler, Filters

# 定义日志级别字典
LOG_LEVELS = {
    'DEBUG': logging.DEBUG,
    'INFO': logging.INFO,
    'WARNING': logging.WARNING,
    'ERROR': logging.ERROR,
    'CRITICAL': logging.CRITICAL,
}

# 时间转换字典
TIME_DICT = {
    1: '一',
    2: '两',
    3: '三',
    4: '四',
    5: '五',
    6: '六',
    7: '七',
    8: '八',
    9: '九',
    10: '十',
    11: '十一',
    12: '十二'
}

# 配置日志输出到控制台，并设置日志格式
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')  # 默认设置为 INFO 级别
logging.basicConfig(level=LOG_LEVELS.get(LOG_LEVEL, logging.INFO),
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)

# 企业微信配置
token = os.getenv('WECHAT_TOKEN')
encoding_aes_key = os.getenv('WECHAT_ENCODING_AES_KEY')
corp_id = os.getenv('WECHAT_CORP_ID')
corp_secret = os.getenv('WECHAT_CORP_SECRET')
api_token = os.getenv('WECHAT_API_TOKEN')

# Nginx Proxy Manager API 配置
npm_url = os.getenv('NPM_URL')
npm_item_id = os.getenv('NPM_ITEM_ID')
npm_identity = os.environ.get('NPM_IDENTITY')
npm_secret = os.environ.get('NPM_SECRET')

# 图片URL
pic_url_open = os.getenv('PIC_URL_OPEN', 'https://img.yufelix.xyz/project/open.png')
pic_url_closed = os.getenv('PIC_URL_CLOSED', 'https://img.yufelix.xyz/project/closed.png')

# Telegram Bot 配置
telegram_token = os.getenv('TELEGRAM_TOKEN')
telegram_chat_id = os.getenv('TELEGRAM_CHAT_ID')

# 对应接受消息回调模式中的token，EncodingAESKey，企业id
if token and encoding_aes_key and corp_id:
    qy_api = WXBizMsgCrypt(token, encoding_aes_key, corp_id)
    logger.info("WeChat initialized successfully")
else:
    logger.error("WeChat initialization failed: Missing required environment variables")

# 全局变量来存储当前的线程和事件
current_timer = None
current_thread_wait_time = int(os.getenv('CURRENT_THREAD_WAIT_TIME', '7200'))  # 默认2h

# 初始化 Telegram Bot
if telegram_token:
    bot = Bot(token=telegram_token)
    dispatcher = Dispatcher(bot, None, workers=1)  # 设置至少一个工作线程
    logger.info("Telegram Bot initialized successfully")
else:
    bot = None
    dispatcher = None
    logger.warning("Telegram initialization failed: Missing required environment variables")

def build_news_message(from_user, to_user, create_time, title, pic_url):
    """构建微信图文消息"""
    return f"""
    <xml>
        <ToUserName><![CDATA[{to_user}]]></ToUserName>
        <FromUserName><![CDATA[{from_user}]]></FromUserName>
        <CreateTime>{create_time}</CreateTime>
        <MsgType><![CDATA[news]]></MsgType>
        <ArticleCount>1</ArticleCount>
        <Articles>
            <item>
                <Title><![CDATA[{title}]]></Title>
                <PicUrl><![CDATA[{pic_url}]]></PicUrl>
            </item>
        </Articles>
    </xml>
    """

def get_token():
    """获取NPM API的token"""
    url = f'{npm_url}/api/tokens'
    data = {
        "identity": npm_identity,
        "secret": npm_secret
    }

    try:
        response = requests.post(url, json=data)
        response.raise_for_status()
        return response.json().get('token')
    except requests.exceptions.RequestException as e:
        logger.error('Failed to get NPM token: %s', e)
        return None

def update_stream_status(npm_stream_status):
    """更新NPM流状态"""
    npm_token = get_token()
    if npm_token is None:
        return '-1'

    url = f'{npm_url}/api/nginx/streams/{npm_item_id}/{npm_stream_status}'
    headers = {
        'Authorization': f'Bearer {npm_token}',
        'Content-Type': 'application/json'
    }

    try:
        response = requests.post(url, headers=headers)
        response.raise_for_status()
        logger.info('NPM stream status %s', npm_stream_status)
        return '0'
    except requests.exceptions.HTTPError as e:
        response_json = response.json()
        error_message = response_json.get('error', {}).get('message')
        if error_message == "Host is already disabled":
            logger.info('NPM update stream status response: %s', response_json)
            return '1'
        elif error_message == "Host is already enabled":
            logger.info('NPM update stream status response: %s', response_json)
            return '2'
        else:
            logger.error('NPM update stream status failed: %s', e)
            return '-1'
    except requests.exceptions.RequestException as e:
        logger.error('NPM update stream status failed: %s', e)
        return '-1'

def handle_stream_status_change(npm_stream_status, xml_tree=None, chat_id=None):
    """处理流状态变更"""
    global current_timer

    if npm_stream_status == 'enable':
        time = current_thread_wait_time / 60 / 60
        title = f'回家模式已激活，有效期{TIME_DICT.get(int(time), str(time))}小时'
        pic_url = pic_url_open

        # 取消之前的定时器
        if current_timer:
            current_timer.cancel()

        # 创建新的定时器
        current_timer = threading.Timer(current_thread_wait_time, update_stream_status, args=('disable',))
        current_timer.start()
        logger.debug('Timer started for %s seconds.', current_thread_wait_time)

    elif npm_stream_status == 'disable':
        title = '回家模式已停用'
        pic_url = pic_url_closed

        # 取消定时器
        if current_timer:
            current_timer.cancel()
            current_timer = None
            logger.debug('Timer cancelled.')

    npm_status = update_stream_status(npm_stream_status)
    if npm_status in ['0', '1']:
        if xml_tree:
            return build_news_message(xml_tree.find('ToUserName').text, xml_tree.find('FromUserName').text,
                                     xml_tree.find('CreateTime').text, title, pic_url)
        elif chat_id:
            bot.send_message(chat_id=chat_id, text=title)
    elif npm_status == '2':
        title = f'有效期已延长{TIME_DICT.get(int(time), str(time))}小时'
        if xml_tree:
            return build_news_message(xml_tree.find('ToUserName').text, xml_tree.find('FromUserName').text,
                                     xml_tree.find('CreateTime').text, title, pic_url_open)
        elif chat_id:
            bot.send_message(chat_id=chat_id, text=title)
    else:
        logger.error('NPM request failed')
        return "failed"

@app.route('/api/v1/message/', methods=['GET', 'POST'])
def message():
    """处理微信消息"""
    # 获取请求中的 token 参数
    token = request.args.get('token')

    # 检查 token
    if token != api_token:
        return jsonify({"error": "Invalid token"}), 401

    if request.method == 'GET':
        return signature(request)
    elif request.method == 'POST':
        msg_signature = request.args.get('msg_signature', '')
        timestamp = request.args.get('timestamp', '')
        nonce = request.args.get('nonce', '')
        data_str = request.data.decode('utf-8')

        ret, msg = qy_api.DecryptMsg(data_str, msg_signature, timestamp, nonce)
        if ret != 0:
            logger.error('ERR: DecryptMsg ret: %s', ret)
            return make_response("failed", 500)

        # 解析XML数据
        xml_tree = ET.fromstring(msg)
        msg_type = xml_tree.find('MsgType').text
        event = xml_tree.find('Event').text
        event_key = xml_tree.find('EventKey').text if event == 'click' else None

        # 处理点击事件
        if msg_type == 'event' and event == 'click':
            response = handle_stream_status_change(event_key.split('.')[-1], xml_tree)
        else:
            logger.error('未知消息类型或事件 event: %s', event)
            response = "未知消息类型或事件"

        # 加密响应消息
        ret, encrypted_msg = qy_api.EncryptMsg(response, nonce, timestamp)
        if ret != 0:
            logger.error('ERR: EncryptMsg ret: %s', ret)
            return make_response("failed", 500)

        return encrypted_msg

def signature(request):
    """验证URL签名"""
    msg_signature = request.args.get('msg_signature', '')
    timestamp = request.args.get('timestamp', '')
    nonce = request.args.get('nonce', '')
    echo_str = request.args.get('echostr', '')
    ret, sEchoStr = qy_api.VerifyURL(msg_signature, timestamp, nonce, echo_str)
    if ret != 0:
        logger.error('ERR: VerifyURL ret: %s', ret)
        return "failed"
    else:
        return sEchoStr

# Telegram Bot 处理逻辑
def handle_telegram_message(update: Update, context):
    """处理 Telegram 消息"""
    logger.debug('Received Telegram message: %s', update.message.text)
    text = update.message.text
    chat_id = update.message.chat_id

    # 校验 chat_id
    if str(chat_id) != telegram_chat_id:
        logger.warning(f"Unauthorized chat_id: {chat_id}")
        bot.send_message(chat_id=chat_id, text="Unauthorized access.")
        return

    if text == '/start':
        bot.send_message(chat_id=chat_id, text="欢迎使用！请输入命令。")
    elif text in ['/enable', '/disable']:
        handle_stream_status_change(text.split('/')[-1], chat_id=chat_id)

# 设置 Telegram Bot 的处理器
if dispatcher:
    dispatcher.add_handler(CommandHandler("start", handle_telegram_message))
    dispatcher.add_handler(CommandHandler("enable", handle_telegram_message))
    dispatcher.add_handler(CommandHandler("disable", handle_telegram_message))
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_telegram_message))

@app.route('/telegram', methods=['POST'])
def telegram_webhook():
    """Telegram Webhook 入口"""
    logger.debug('Received Telegram message: %s', request.get_json(force=True))
    if bot:
        update = Update.de_json(request.get_json(force=True), bot)
        dispatcher.process_update(update)
    return 'ok'

# Flask服务端口，可自定义
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
    logger.info("Flask application started on port 8080")
