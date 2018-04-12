"""
目标网站：红袖添香
目标网站：https://www.hongxiu.com/free
目标：所有已完本的免费小说
时间：2018-4-8
作者：小易（yianxss）
"""
import math
import os
import random
import re
import time
from os import path
from threading import Thread
import threading

import requests
from lxml import etree

book_count = 0


class HongXiuOk:
    # 初始化
    def __init__(self, save_path):
        self.Host = "www.hongxiu.com"
        self.UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)' \
                  ' Chrome/64.0.3282.119 Safari/537.36'
        self.main_url = 'https://' + self.Host
        self.save_path = save_path
        self.headers = {'Host': self.Host,
                        'User-Agent': self.UA, 'Accept-Encoding': ''}

    # 获取网页源码
    def get_html(self, url):
        # 请求失败，参数重试-10次
        for TryCount in range(10):
            try:
                time.sleep(random.uniform(0.01, 1))
                html = requests.get(url, headers=self.headers,
                                    timeout=40, allow_redirects=False)
                html.raise_for_status()
                html.encoding = 'UTF-8'
                return html.text
            except Exception as e:
                print("第{}次重连\t  fail:{}".format(TryCount, e))
        # 重连10次后还未成功，将连接写入log，备查
        else:
            with open("fail_log.txt", 'a+') as f:
                f.write(url + '\n')
            return

    # 根据提供的首页url，提取总页数(total_page_num)
    def get_total_page_num(self, url):
        html = self.get_html(url)
        # 获取到内容再处理
        if html:
            try:
                # 获取到条目数
                max_page_max = int(re.findall('data-total="(\d+?)"', html)[0])
                # 初一每页条数 向上取整
                total_page_num = math.ceil(max_page_max / 10)
                print('获取总页数成功:{}'.format(total_page_num))
                return total_page_num
            except Exception as e:
                print("总页码获取失败:{}".format(e))
                return

    # 获取每页内容的小说列表及相关信息
    def get_book_info_list(self, url):
        html = self.get_html(url)
        book_link = []
        book_dict = []
        if html:
            try:
                root = etree.HTML(html)
                book_root_info = root.xpath('//div[@class="book-info"]')[0]
                if book_root_info is not None:
                    book_link_temp = book_root_info.xpath('//h3/a/@href')
                    if book_link_temp:
                        for link in book_link_temp:
                            if self.main_url not in link:
                                book_link.append(self.main_url + link)
                            else:
                                book_link.append(link)

                        # 提取 小说名称|作者|类型|字数
                        book_name = book_root_info.xpath('//h3/a/text()')
                        book_author = book_root_info.xpath('//h4/a/text()')
                        book_type = book_root_info.xpath(
                            '//p[@class="tag"]/span[1]/text()')
                        book_words_count = book_root_info.xpath(
                            '//p[@class="tag"]/span[3]/text()')

                        book_info = list(
                            zip(book_link, book_name, book_author, book_type, book_words_count))
                        book_keys = ('book_link', 'book_name',
                                     'book_author', 'book_type', 'book_words_count')

                        # 字段较多，放入字典 方便调用
                        for item in book_info:
                            book_dict_temp = dict(zip(book_keys, item))
                            book_dict.append(book_dict_temp)

                        return book_dict
            except Exception as e:
                print("获取第{}页 小说链接及标题失败 Error:{}".format(
                    re.findall('pageNum=\d+?', url)[0], e))
                return

    # 按性别 提取分类
    def get_category(self, gender_code):
        """
        :type gender_code: gender = [(1,"男"), (2,"女")]
        """
        url = 'https://www.hongxiu.com/free/all?gender={}&catId=-1'.format(
            gender_code)
        r = self.get_html(url)
        if r:
            try:
                root = etree.HTML(r)
                category_code = root.xpath(
                    '//ul[@type="category"]/li/@data-id')[2:]
                category_name = root.xpath(
                    '//ul[@type="category"]/li/a/text()')[2:]
                return list(zip(category_code, category_name))
            except Exception as e:
                print("按性别提取分类失败：{}".format(e))
                return
        else:
            return

    # 提取小说的所有章节标题及链接
    def get_catalog_info(self, book_info):
        if book_info:
            url = book_info.get('book_link') + "#Catalog"
            html = self.get_html(url)
            if html:
                try:
                    root = etree.HTML(html)
                    catalog_info_temp = root.xpath(
                        '//*[@id="j-catalogWrap"]/div[2]/div/ul')[0]
                    catalog_link = catalog_info_temp.xpath(
                        '//li[@data-rid]/a/@href')
                    catalog_link = ['https:' + item for item in catalog_link]
                    catalog_name = catalog_info_temp.xpath(
                        '//li[@data-rid]/a/text()')
                    catalog_info = list(zip(catalog_name, catalog_link))
                    return catalog_info
                except Exception as e:
                    print("章节获取失败：{}".format(e))
                    return

    # 根据提供的信息创建文件夹
    def create_folders(self, gender, type_name, book_name):
        book_name = book_name.rstrip("\\")
        book_name = re.sub(r'[\\/:*?"<>|]', '-',
                           book_name.strip().replace('\t', "_"))
        folder_path = ''
        global book_count
        book_count += 1
        folder_name_list = [self.save_path, gender,
                            type_name, "%05d " % book_count + book_name]
        # 根据字符拼接文件路径
        for item in folder_name_list:
            folder_path = path.join(folder_path, item)
        # 判断文件夹是否存在
        if os.path.exists(folder_path):
            print("文件夹已存在\t{}\t 线程：{}".format(folder_path, threading.active_count()))
            return folder_path
        else:
            # 不存在 创建：成功返回路径，否则放入其他文件件
            try:
                os.makedirs(folder_path)
                print("创建成功\t{}".format(folder_path))
                return folder_path
            except Exception as e:
                print("文件夹创建失败：{}\t 线程：{}".format(folder_path, threading.active_count()))

                # 根据小说名称创建文件夹失败-放入其他容错下载
                folder_path = path.join(os.path.split(folder_path)[0], "其他")
                os.makedirs(folder_path)
                return folder_path

    # 获取小说内容
    def get_title_content(self, catalog_info):
        if catalog_info:
            file_name, dowload_link = catalog_info
            r = self.get_html(dowload_link)
            if r:
                file_name = re.sub(r'[\\/:*?"<>|]', '-',
                                   file_name.strip().replace('\t', "_"))
                root = etree.HTML(r)
                try:
                    contents = root.xpath(
                        '//*[@class="read-content j_readContent"]/p/text()')
                    contents = '  \n'.join([i.strip() for i in contents])
                    return [file_name, contents]
                except Exception as e:
                    print("获取小说内容失败：{}".format(file_name))
            else:
                return

    # 根据提供的小说名称 和 内容 保存
    def save_content(self, save_full_path, tile_content, file_count):
        # 构建文件路径，文件名 前缀 3位数
        if tile_content:
            file_name, content = self.get_title_content(tile_content)
            file_name_d = "%03d " % file_count + file_name + '.txt'
            save_file_path = os.path.join(save_full_path, file_name_d)
            # 判断文件是否存在
            if os.path.isfile(save_file_path):
                print("文件已存在\t{}\t线程：{}".format(save_file_path, threading.active_count()))
            else:

                # 单个写入
                with open(save_file_path, 'w', encoding='utf-8') as f:
                    # 写入标题
                    f.write(" "*50 + file_name + " "*50)
                    f.write('\n')
                    f.write(content)
                    print("下载完成\t{}\t{}\t线程共：{}".format(os.path.split(save_full_path)
                                                           [-1], file_name_d, threading.active_count()))

    # 合并为一
    def join_txt(self, dir_path):
        for (spath, list_subfolders, list_file_names) in os.walk(dir_path):
            if list_file_names is not None:
                fullpath = (os.path.join(spath, file)
                            for file in list_file_names)
                for (i, item) in enumerate(fullpath):
                    try:
                        join_file_name = r"{}\000 完本 {}.txt".format(
                            spath, os.path.split(spath)[1].split(' ')[1])
                        with open(item, 'r', encoding='utf-8') as f:
                            content = f.read()
                        if i == 0:
                            if os.path.exists(join_file_name):
                                os.remove(join_file_name)
                        with open(join_file_name, 'a+', encoding='utf-8') as f1:
                            f1.write(content + '\n' * 2)
                    except Exception as e:
                        print("合并失败 -- {}".format(e))
                else:
                    print('合并完成\t{}'.format(os.path.split(spath)[1]))

    # 主下载程序
    def main(self):
        url = 'https://www.hongxiu.com/free/all?pageSize=10&gender={}&' \
              'catId={}&isFinish=1&isVip=1&size=-1&updT=-1&orderBy=0&pageNum={}'

        gender = [(1, "男"), (2, "女")]

        # 按照 gender+category 性别+分类下载
        for gender_item in gender:
            gender_code, gender_name = gender_item
            # 获取男女对应的类型 比如：玄幻
            category = self.get_category(gender_code)
            if category:
                try:
                    for item in category:
                        global book_count
                        book_count = 0
                        category_code, category_name = item
                        # 根据 性别+分类 提取总页码
                        page_num_url = url.format(
                            gender_code, category_code, 1)
                        total_page_num = self.get_total_page_num(page_num_url)

                        # 根据页数 逐页下载
                        if total_page_num > 0 and total_page_num is not None:
                            for page_num in range(1, total_page_num + 1):
                                # 获取每页内容的小说列表及相关信息
                                book_url = url.format(
                                    gender_code, category_code, page_num)
                                book_info_list = self.get_book_info_list(
                                    book_url)
                                # 获取列表成功，遍历
                                if book_info_list is not None:
                                    for book_info in book_info_list:
                                        # 所有章节的标题及链接
                                        book_name = book_info.get('book_name')
                                        # 创建文件夹
                                        folder_path = self.create_folders(
                                            gender_name, category_name,  book_name)
                                        category_info = self.get_catalog_info(
                                            book_info)
                                        # 多线程下载
                                        if category_info is not None:
                                            for (i, category_item) in enumerate(category_info):
                                                try:
                                                    t = Thread(target=self.save_content, args=(
                                                        folder_path, category_item, i+1))
                                                    t.setDaemon(True)
                                                    t.start()
                                                except Exception as e:
                                                    print(e)

                except Exception as e:
                    print("分类提取失败:{}".format(e))


if __name__ == '__main__':
    my_path = r'F:\hx_contents'
    Hx = HongXiuOk(my_path)
    Hx.main()
    print("下载完成--开始合并")
    Hx.join_txt(my_path)
