"""
目标网站：红袖添香
目标网站：https://www.hongxiu.com/free
目标：所有免费小说
时间：2018年3月30日
作者：小易（yianxss）
"""
import math
import os
import re
from threading import Thread
import requests
from bs4 import BeautifulSoup
from lxml import etree

all_count = 0
class HongXiu:

    def __init__(self):
        self.host = 'www.hongxiu.com'
        self.headers = {
            'Host': self.host,
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.119 Safari/537.36'
        }
        self.s1_url = 'https://www.hongxiu.com/free/all?pageSize=10&gender=2&catId=-1&isFinish=-1&isVip=1&size=-1&updT=-1&orderBy=0&pageNum={}'
        self.main_url = 'https://www.hongxiu.com'
        self.savePath = r'F:\hongxiu_free'

    # get_html_code
    def getHtml(self, url):
        for tryCount in range(10):
            try:
                response = requests.get(url, headers=self.headers, timeout=20,allow_redirects=False)
                response.raise_for_status()
                response.encoding = 'UTF-8'
                return response.text
            except Exception as e:
                print("tryConnectionCount:{}\tfail:{}".format(tryCount, e))

        else:
            with open("Fail_log.txt", 'a+') as f:
                f.write(url + '\n')
            return

    # get_total_page_num
    def get_totalPage(self):
        url = 'https://www.hongxiu.com/free/all'
        r = self.getHtml(url)
        if r:
            max_page_max = int(re.findall('data-total="(\d+?)"', r)[0])
            return math.ceil(max_page_max/10)
        else:
            return

    # check_file or create_folder
    def create_folder(self,filename):
        global all_count
        all_count += 1
        all_count_format = "%06d"% all_count
        fullpath = "{}\{} {}".format(self.savePath,all_count_format,filename)
        print(fullpath)
        if not os.path.exists(fullpath):
            os.makedirs(fullpath)
        else:
            print('已存在 \t{}'.format(filename))
        return fullpath

    # get_link_title
    def get_title_BookLinks(self, page_num):
        r = self.getHtml(self.s1_url.format(page_num))
        try:
            if r:
                soup = BeautifulSoup(r, 'lxml')
                book_list = soup.find('div', attrs={'class': 'right-book-list'}).ul
                res = book_list.find_all('a', attrs={'href': re.compile(r'/book/\d+?')})
                info = [re.findall(r'<a href="(/book/\d+?)" target="_blank" title="(.+?)">', str(i)) for i in res]
                return info
            else:
                return
        except Exception as e:
            print(e)
            return

    # return url_title
    def get_chepter_info(self,book_url):
        url = self.main_url + book_url+'#Catalog'
        chapter_infos = []
        r = self.getHtml(url)
        if r:
            soup = BeautifulSoup(r,'lxml')
            try:
                list_info = soup.find_all('li',attrs={'data-rid':re.compile('\d+?')})[:-1]
                for item in list_info:
                    link = item.a.get('href')
                    if self.host in link:
                        chapter_url = 'https:' + link
                    else:
                        chapter_url = "{}{}".format(self.main_url,link)
                    chapter_title = item.get_text()
                    chapter_infos.append((chapter_url,chapter_title))
                return chapter_infos
            except Exception as e:
                return
        else:
            return

    # save contents
    def save_contents(self,savePath,chapter_info):
        chapter_url, chapter_title = chapter_info
        r = self.getHtml(chapter_url)
        if r:
            try:
                root = etree.HTML(r)
                contents = root.xpath('//*[@class="read-content j_readContent"]/p/text()')
                content_file_name = savePath +'\\'+ "".join(re.findall(r'[\u4e00-\u9fa5a-zA-Z0-9]',chapter_title)) +'.txt'
                if os.path.isfile(content_file_name):
                    print("已存在\t" + os.path.split(savePath)[-1]+chapter_title)
                    return
                else:
                    with open(content_file_name, 'w', encoding='utf-8') as f:
                        f.write('  \n'.join([i.strip() for i in contents]))
                    print('下载完成\t{}---{}'.format(os.path.split(savePath)[-1], chapter_title))
            except Exception as e:
                print(e)
                return

    def main(self):
        threads=[]
        # get_total_page_num
        total_page_num = self.get_totalPage()
        for page_num in range(1,total_page_num+1):
            # get_book_links
            book_infos = self.get_title_BookLinks(page_num)
            for item in book_infos[::2]:
                book_url = item[0][0]
                title = item[0][1]
                # create_folder
                fullpath = self.create_folder("".join(re.findall(r'[\u4e00-\u9fa5]',title)))
                # get_chapter_info
                chapter_infos = self.get_chepter_info(book_url)
                # save-content
                for chapter_info in chapter_infos:
                    try:
                        t = Thread(target=self.save_contents, args=(fullpath,chapter_info))
                        t.setDaemon(True)
                        t.start()
                    except Exception as e:
                        print(e)
                        continue





if __name__ == '__main__':
    hx = HongXiu()
    hx.main()
