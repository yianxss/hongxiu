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


class HongXiu:
    def __init__(self):
        self.headers = {
            'Host': 'www.hongxiu.com',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                          'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.119 Safari/537.36'
        }
        self.s1_url = 'https://www.hongxiu.com/free/all?pageSize=10&gender=2' \
                      '&catId=-1&isFinish=-1&isVip=1&size=-1&updT=-1&orderBy=0&pageNum={}'
        self.main_url = 'https://www.hongxiu.com'

        self.savePath = r'F:\hongxiu_free'


    # get_html_code
    def getHtml(self, url):
        for tryCount in range(10):
            try:
                response = requests.get(url, headers=self.headers, timeout=10)
                response.raise_for_status()
                response.encoding='UTF-8'
                return response.text
            except Exception as e:
                print("tryConnectionCount:{}\tfail:{}".format(tryCount, e))
                with open("fail.txt", 'a+') as f:
                    f.write(url + '\n')
        else:
            return

    # get_total_page_num
    def get_totalPage(self):
        url = 'https://www.hongxiu.com/free/all'
        r = self.getHtml(url)
        if r:
            totalpage = int(re.findall('data-total="(\d+?)"',r)[0])
            return math.ceil(totalpage/10)
        else:
            return

    # check_file or create_folder
    def create_folder(self,filename):
        fullpath = os.path.join(self.savePath,filename)
        if not os.path.exists(fullpath):
            os.makedirs(fullpath)
        else:
            print('{}\t 已存在'.format(filename))
        return fullpath

    # get_title_bookLinks and title
    def get_title_BookLinks(self, page_num):
        r = self.getHtml(self.s1_url.format(page_num))
        if r:
            soup = BeautifulSoup(r, 'lxml')
            book_list = soup.find('div', attrs={'class': 'right-book-list'}).ul
            res = book_list.find_all('a', attrs={'href': re.compile(r'/book/\d+?')})
            info = [re.findall(r'<a href="(/book/\d+?)" target="_blank" title="(.+?)">', str(i)) for i in res]
            return info
        else:
            return


    # return url_title
    def get_chepter_info(self,book_url):
        url = self.main_url + book_url+'#Catalog'
        chapter_infos = []
        r = self.getHtml(url)
        if r:
            soup = BeautifulSoup(r,'lxml')
            list_info = soup.find_all('li',attrs={'data-rid':re.compile('\d+?')})[:-1]
            for item in list_info:
                chapter_url = 'https:'+item.a.get('href')
                chapter_title = item.get_text()
                chapter_infos.append((chapter_url,chapter_title))
            return chapter_infos
        else:
            return
    # save contents
    def save_contents(self,savePath,chapter_info):
        chapter_url, chapter_title = chapter_info
        r = self.getHtml(chapter_url)
        if r:
            root = etree.HTML(r)
            contents = root.xpath('//*[@class="read-content j_readContent"]/p/text()')
            content_file_name = savePath +'\\'+ chapter_title +'.txt'
            if os.path.isfile(content_file_name):
                print("已存在\t" + os.path.split(savePath)[-1]+chapter_title)
                return
            else:
                with open(savePath +'\\'+ chapter_title +'.txt', 'w', encoding='utf-8') as f:
                    f.write('  \n'.join([i.strip() for i in contents]))
                print('{}-{}\t下载完成'.format(os.path.split(savePath)[-1], chapter_title))

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
                fullpath = self.create_folder(re.sub('[\/:*?"<>|]','-',title))
                # get_chapter_info
                chapter_infos = self.get_chepter_info(book_url)
                # save-content
                for chapter_info in chapter_infos:
                    t = Thread(target=self.save_contents, args=(fullpath,chapter_info))
                    t.start()
                    threads.append(t)
                    for t in threads:
                        t.join()




if __name__ == '__main__':
    hx = HongXiu()
    hx.main()
