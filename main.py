from seleniumwire import webdriver
# from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.keys import Keys
from seleniumwire.utils import decode
import requests
import json
from datetime import datetime
import yaml
import re
import os
import threading
import queue
import unicodedata
import logging
import time

# 更换自己的账号密码
user = "修改自己的账号"
passwd = "修改自己的密码"

notes_url = "https://yun.smartisan.com/#/notes"
login_url = "https://account.smartisan.com/#/v2/login?return_url=https:%2F%2Fcloud.smartisan.com%2F%23%2Fnotes"
image_url = "https://yun.smartisan.com/apps/note/notesimage/"

# 工作目录
if not os.path.exists("downloads"):
    os.mkdir("downloads")
work_dir = os.path.join("downloads", str(int(datetime.now().timestamp())))
print("当前工作目录为 " + work_dir)
if not os.path.exists(work_dir):
    os.mkdir(work_dir)

logger = logging.getLogger()
fileHandler = logging.FileHandler(os.path.join(work_dir, "debug.log"), encoding="utf-8")
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
fileHandler.setFormatter(formatter)
logger.addHandler(fileHandler)
logger.setLevel(logging.WARNING)


# 登录和下载便签JSON


def wait_load_complete(driver):
    WebDriverWait(driver, 10).until(
        lambda d: d.execute_script("return document.readyState") == "complete"
    )


chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument("--incognito")


options = webdriver.ChromeOptions()
# 忽略证书错误
options.add_argument('--ignore-certificate-errors')
# 如需后台执行，不弹出UI界面开启下面参数
# options.add_argument('--headless')
driver = webdriver.Chrome(chrome_options=options)

driver.get(login_url)
wait_load_complete(driver)

# 点击普通登录
driver.find_element(By.XPATH, "//a[@ng-click='switchModel()']").click()

# 定位并输入用户名和密码字段
username_field = driver.find_element(By.XPATH, "//input[@ng-model='user.username']")
password_field = driver.find_element(By.XPATH, "//input[@ng-model='user.password']")
username_field.send_keys(user)
password_field.send_keys(passwd)
# 点击登录
driver.find_element(By.CLASS_NAME, "btn-wrapper").click()
time.sleep(2)
# 等待页面加载完成

cookies = driver.get_cookies()
user_agent = driver.execute_script("return navigator.userAgent;")


driver.get(notes_url)
request = driver.wait_for_request(r"index.php\?r=v2.*", timeout=30)
web_response = decode(
    request.response.body,
    request.response.headers.get("Content-Encoding", "identity"),
).decode("utf-8")

print("便签获取完成，关闭浏览器。")
driver.quit()

# 解析和保存便签JSON
web_response_dict = json.loads(web_response)

note_total = int(web_response_dict["data"]["note"]["total"])
note_list = web_response_dict["data"]["note"]["list"]

with open(os.path.join(work_dir, "web_response.json"), "w", encoding="utf-8") as f:
    f.write(web_response)


# 下载队列和多线程下载

THREAD_NUM = 4
image_queue = queue.Queue()
thread_list = []


def downloader():
    s = requests.Session()
    for cookie in cookies:
        s.cookies.set(cookie["name"], cookie["value"])

    while True:
        task = image_queue.get()
        if task is None:
            image_queue.task_done()
            break

        url, filepath = task
        res = s.get(url, headers={"user-agent": user_agent})
        with open(filepath, "wb") as f:
            f.write(res.content)

        logger.debug("OK  " + url + filepath)
        logger.debug("QUEUE SIZE " + str(image_queue.qsize()))
        image_queue.task_done()


for _ in range(THREAD_NUM):
    t = threading.Thread(target=downloader)
    t.start()
    thread_list.append(t)


# 验证文件名
def slugify(value, allow_unicode=False):
    """
    Taken from https://github.com/django/django/blob/master/django/utils/text.py
    Convert to ASCII if 'allow_unicode' is False. Convert spaces or repeated
    dashes to single dashes. Remove characters that aren't alphanumerics,
    underscores, or hyphens. Convert to lowercase. Also strip leading and
    trailing whitespace, dashes, and underscores.
    """
    value = str(value)
    if allow_unicode:
        value = unicodedata.normalize("NFKC", value)
    else:
        value = (
            unicodedata.normalize("NFKD", value)
            .encode("ascii", "ignore")
            .decode("ascii")
        )
    value = re.sub(r"[^\w\s-]", "", value.lower())
    return re.sub(r"[-\s]+", "-", value).strip("-_")


# 图片标签转为HTML格式，下载链接添加至image_queue
def image_tag_handler(matchobj):

    global subdir

    file_name = matchobj.group(4)
    image_queue.put(
        (
            "https://yun.smartisan.com/apps/note/notesimage/" + file_name,
            os.path.join(subdir, file_name),
        )
    )
    logger.debug(
        "ADD "
        + "https://yun.smartisan.com/apps/note/notesimage/"
        + file_name
        + os.path.join(subdir, file_name)
    )
    logger.debug("QUEUE SIZE " + str(image_queue.qsize()))

    return '\n<img src="{}" alt="{}" width="{}" height="{}">'.format(
        *matchobj.group(4, 3, 1, 2)
    )


# 逐个保存便签为Markdown格式

DATETIME_FORMAT = "%Y%m%d"

IMAGE_PATTERN = r"<image w=([0-9]+) h=([0-9]+) describe=(.*) name=(.+)>"
IMAGE_REPL = r'<img src="\\4" alt="\\3" width="\\1" height="\\2">'

for note_item in note_list:

    # 解析元数据
    content = note_item.pop("detail")
    modify_time = datetime.fromtimestamp(
        note_item["modify_time"] / 1000
    )  # millisecond to second
    note_item["modify_time_r"] = str(modify_time)  # readable time

    # 每个便签单独创建文件夹
    '''
   
    filename = (
        modify_time.strftime(DATETIME_FORMAT)
        + "_"
        + slugify(note_item["title"], allow_unicode=True)
        + ".md"
    )
    '''
    filename = (
            modify_time.strftime(DATETIME_FORMAT)
            + "_"
            + slugify(note_item["title"], allow_unicode=True)[:10] # 文件名取10个字符，否则太长会导致错误
            + ".md"
    )

    subdir = os.path.join(work_dir, filename)
    if not os.path.exists(subdir):
        os.mkdir(subdir)

    # 写入Markdown
    with open(os.path.join(subdir, filename), "w", encoding="utf-8") as f:
        f.write("---\n")
        f.write(str(yaml.dump(note_item, allow_unicode=True)))  # 写入元数据
        f.write("---\n")
        f.write("\n")
        f.write(re.sub(IMAGE_PATTERN, image_tag_handler, content))  # 写入替换图片标签后的正文

# image_tag_handler()已将图片下载链接入队完毕。添加downloader结束信号。
for _ in range(THREAD_NUM):
    image_queue.put(None)

# 等待线程结束
for t in thread_list:
    t.join()

# 等待队列清空
image_queue.join()
