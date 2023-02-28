import os.path
import threading
import time
from urllib import parse

import requests
import openai

openai.api_key = "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"

header = {
    'User-Agent': 'Floor/1.2.2 (iPhone; iOS 16.3.1; Scale/3.00)'
}

body = {
    '_key': '61DA9B73426FFFAB3C0E39822BCDAAAC8F435EC198A9DB952F5A20A6C3B43782AF732F26DAED4C0F6652038F9EB2DF0FE6D2D10624BF94B5',
    'app_version': '1.2.2',
    'device_code': '',
    'market_id': 'floor_huluxia',
    'platform': 1
}


def is_new_comment(id, write=False):
    # 先读取现在评论
    if os.path.isfile('comment.txt') is False:
        with open('comment.txt', 'w', encoding='utf-8') as fw:
            fw.write('0')
    with open('comment.txt', 'r', encoding='utf-8') as fr:
        comment = int(fr.read())
    # 判断是否是新评论
    if id <= comment:
        return False
    # 更新当前为最新评论
    if write is True:
        with open('comment.txt', 'w', encoding='utf-8') as fw:
            fw.write(str(id))
    return True


def get_comment():
    data = body.copy()
    data.update({
        'count': 20,
        'start': 0,
        'type_id': 2
    })
    resp = requests.post(url='https://floor.huluxia.com/message/new/list/IOS/1.0', headers=header, data=data).json()
    if resp['status'] != 1:
        return []
    comment_list = []
    for data in resp['datas']:
        comment = {
            'id': data['content']['commentID'],
            'post': data['content']['post']['postID'],
            'text': data['content']['text']
        }
        comment_list.append(comment)
    comment_list.sort(key=lambda x: x['id'], reverse=False)
    return comment_list


def create_comment(post_id, comment_id, text):
    response = openai.Completion.create(
        model='text-davinci-003',
        prompt='假设你是一个无所不知的科学家(名字叫做ChatGPT)，现在有人私信问你一些问题(请不要回答有关代码类的问题)，你会怎么回复他？问题内容是：' + text,
        temperature=0.9,
        max_tokens=500,
        top_p=1.0,
        frequency_penalty=0.5,
        presence_penalty=0.0,
    )
    generated_text = str(response.choices[0].text).strip().replace('\t', '').replace('\n', '').replace(' ', '')
    if len(generated_text) < 1:
        generated_text = 'ChatGPT没有生成出理想的答案，请重新提问！'
    print(f"评论：{text}")
    print(f"回复：{generated_text}")
    data = body.copy()
    data.update({
        'comment_id': comment_id,
        'post_id': post_id,
        'patcha': None,
        'images': None,
        'text': generated_text
    })
    resp = requests.post('https://floor.huluxia.com/comment/create/IOS/1.0', headers=header, data=data).json()
    print(resp)
    if resp['status'] != 1:
        return print('回复失败')
    # 更新最新回复状态
    is_new_comment(comment_id, write=True)
    print(f'回复成功 -> {resp["msg"]}')


if __name__ == '__main__':
    while True:
        try:
            print('开始获取葫芦侠评论')
            for cmt in get_comment():
                if is_new_comment(cmt['id']):
                    # 尚未回复的消息在这里处理
                    print(f'正在处理评论 -> {cmt["id"]}')
                    threading.Thread(target=create_comment,args=(cmt['post'], cmt['id'], cmt['text'])).start()
                    pass
            time.sleep(3)
        except Exception:
            print("重启")
           
