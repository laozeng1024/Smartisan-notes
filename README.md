# 锤子便签批量导出markdown

基于https://github.com/wintertee/Smartisan-notes-downloader 项目，并做了以下优化：

- 解决目录/文件名过长，程序异常终止。如便签没有标题，默认会把长长的内容当文件名，导致执行错误。
- 解决自动化登陆。程序中提前填入自己的用户名及密码，可在chrome模拟登陆，以便实现定期自动（配合任务计划程序或crontab）功能。

## 使用方法

- 1. 安装 Python3 （略）
- 2. 安装 Chrome（略）
- 3. 下载ChromeDriver

以下以Windows系统为例

	- 查看chrome浏览器版本,如：121.0.6167.86，这里的大版本是121
	- 如版本号小于115,在这里找到对应的版本：https://chromedriver.chromium.org/downloads 。如114，进入下载chromedriver_win32.zip
	- 如版本号大于115，到这个页面找对应的版本：https://googlechromelabs.github.io/chrome-for-testing/ 。我的是121版本，下载win64版本：https://edgedl.me.gvt1.com/edgedl/chrome/chrome-for-testing/121.0.6167.85/win64/chromedriver-win64.zip 。必须要下载和浏览器一致的版本，否则运行报错。
	- 解压zip，把chromedriver.exe文件复制到本地main.py同目录下。

- 4. 安装依赖: `pip install -r requirements.txt`
- 5. 修改main.py文件19-20行，替换为自己的信息，即欢喜云登陆的邮箱和密码。
- 6. 运行程序：`python main.py`
- 7. 备份的标签在downloads目录，每个便签独立文件夹。
