import re
import execjs
import json
import time
import logging
from PIL import Image
import logging.handlers
from request import Request
from classifier import Classifier
from yolo import YOLO


class Log(object):
    def __init__(self):
        self.logger = logging.getLogger('spider')  # 设置一个日志器
        self.logger.setLevel(logging.INFO)

        formatter = logging.Formatter('%(asctime)s [%(name)s] %(levelname)s: %(message)s')

        # fileHandler = logging.handlers.TimedRotatingFileHandler(filename="logs/log_file", when='D', interval=1, backupCount=0, encoding='utf8')
        # fileHandler.setFormatter(formatter)
        # self.logger.addHandler(fileHandler)

        handler = logging.StreamHandler()
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)


class Yidun(object):
    def __init__(self):
        self.id = None
        self.token = None
        self.image = None
        self.bg_path = 'picture/bg.jpg'

        with open('core.js', 'r', encoding='utf-8') as f:
            source = f.read()
        node = execjs.get('Node')
        self.core = node.compile(source)

        self.log = Log()
        self.req = Request(self.log)
        self.yolo = YOLO()
        self.classifier = Classifier()

    def start(self):
        self.id = self.captcha_sense()
        self.token = self.api_get_token()

        count = 0
        true_count = 0
        while True:
            try:
                front = self.generate_captcha()    # 生成新的验证码
                self.log.logger.info(str(front))
                if front:
                    pre_points = self.get_points()    # 汉字定位，获取坐标点
                    item = dict()
                    for key, point in enumerate(pre_points):
                        im = self.image.crop((point[0] - 20, point[1] - 20, point[0] + 20, point[1] + 20))
                        chinese = self.classifier.identify_image(im)    # 识别汉字图片
                        item[chinese] = (int(point[0]*300/320), int(point[1]*150/160), 10000)
                    self.log.logger.info(str(item))
                    result = self.api_check([item.get(i, (150, 75, 10000)) for i in front])    # 提交验证码
                    self.log.logger.info(str(result))
                    count += 1
                    if result is True:
                        true_count += 1
                    if count == 100:
                        break
            except:
                self.log.logger.exception('')
            time.sleep(1)

        self.log.logger.info('测试结束，验证码识别成功率：{:.1f}%'.format(true_count/count*100))
        self.yolo.close_session()
        self.classifier.close_session()

    def captcha_sense(self):
        url = 'http://dun.163.com/public/assets/pt_experience_captcha_sense.js'
        response = self.req.get(url=url)
        group = re.search(r'sense:"(\w+)",jigsaw:"(\w+)",point:"(\w+)"', response.text).groups()
        sense = group[0]
        jigsaw = group[1]
        point = group[2]
        return point

    def api_get_token(self):
        url = 'http://c.dun.163yun.com/api/v2/get'
        cb = self.core.call('get_cb')
        params = {
            'id': self.id,
            'fp': '',
            'https': 'false',
            'type': 'undefined',
            'width': '0',
            'version': '2.9.8',
            'dpr': '1',
            'dev': '1',
            'cb': cb,
            'ipv6': 'false',
            'referer': 'http://dun.163.com/trial/sense',
            'callback': '__JSONP'
        }
        response = self.req.get(url=url, params=params)
        token = json.loads(response.text[8: -2])['data']['token']
        return token

    def generate_captcha(self):
        url = 'http://c.dun.163yun.com/api/v2/get'
        cb = self.core.call('get_cb')
        params = {
            'id': self.id,
            'fp': '',
            'https': 'false',
            'type': 'undefined',
            'version': '2.9.8',
            'dpr': '1',
            'dev': '1',
            'cb': cb,
            'ipv6': 'false',
            'width': '0',
            'token': self.token,
            'referer': 'http://dun.163.com/trial/sense',
            'callback': '__JSONP'
        }
        response = self.req.get(url=url, params=params)
        data = json.loads(response.text[8: -2])['data']
        if data['type'] == 3:
            response2 = self.req.get(url=data['bg'][0])
            with open(self.bg_path, 'wb') as f:
                f.write(response2.content)
            return data['front']

    def api_check(self, points):
        url = 'http://c.dun.163yun.com/api/v2/check'
        cb = self.core.call('get_cb')
        data = self.core.call('get_data', self.token, points)
        params = {
            'id': self.id,
            'token': self.token,
            'acToken': '',
            'data': data,
            'width': '300',
            'type': '3',
            'version': '2.9.8',
            'cb': cb,
            'referer': 'http://dun.163.com/trial/sense',
            'callback': '__JSONP'
        }
        response = self.req.get(url=url, params=params)
        result = json.loads(response.text[8: -2])['data']['result']
        return result

    def get_points(self):
        self.image = Image.open(self.bg_path)
        out_boxes = self.yolo.detect_image(self.image)
        out_boxes = out_boxes.tolist()

        lis = list()
        for box in out_boxes:
            x = int((box[1] + box[3]) / 2)
            y = int((box[0] + box[2]) / 2)
            lis.append((x, y))
        return lis


if __name__ == '__main__':
    Yidun().start()
