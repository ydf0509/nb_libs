# -*- coding: utf-8 -*-
import os
import time
from pathlib import Path

import nb_log
import requests
from parsel import Selector

"""
自动下载和更新某人所有的github代码,仓库太多了,手动下载很麻烦.
"""
class GithubCloner(nb_log.LoggerMixin):
    def __init__(self, username: str, total_pages: int = 3, dir='/codes_github'):
        self.username = username
        self.total_pages = total_pages
        self.repo_list = []
        self.dir = dir
        os.makedirs(self.dir, exist_ok=True)

    def get_repo_urls(self):
        for p in range(1, self.total_pages + 1):
            url_repo_list = f'https://github.com/{self.username}?language=&page={p}&q=&sort=&tab=repositories&type=source'
            resp = requests.get(url_repo_list)
            sel = Selector(resp.text)
            self.repo_list.extend(sel.xpath('//*[@id="user-repositories-list"]/ul/li/div/div/h3/a/@href').extract())
            time.sleep(10)
        self.logger.info(len(self.repo_list))

    def clone_repo(self, repo: str):
        url = f'git@github.com:{repo[1:]}.git'

        repo_short_name = repo.split('/')[-1]
        # print(repo, repo_short_name)
        repo_full_dir = Path(self.dir).joinpath(repo_short_name).as_posix()

        if Path(repo_full_dir).exists():
            cmd = f'cd {repo_full_dir} && git pull'
            os.system(cmd)
            self.logger.info(cmd)
            time.sleep(5)
        else:
            cmd = f'''cd {self.dir} && git clone {url}'''
            self.logger.warning(cmd)
            os.system(cmd)
            time.sleep(30)

    def start(self):
        self.get_repo_urls()
        os.system('chcp 65001')  # 先设置utf8编码,避免os.system 乱码
        for repo in self.repo_list:
            self.clone_repo(repo)


if __name__ == '__main__':
    GithubCloner('ydf0509', total_pages=2, dir='/codes_github').start()

    # os.system(''' cd /codes_github/nb_log2 && git pull  ''')
