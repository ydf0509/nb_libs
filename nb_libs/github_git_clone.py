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
        os.system('chcp 65001')  # 先设置utf8编码,避免os.system 乱码

    def get_repo_urls(self):
        for p in range(1, self.total_pages + 1):
            url_repo_list = f'https://github.com/{self.username}?language=&page={p}&q=&sort=&tab=repositories&type=source'
            resp = requests.get(url_repo_list)
            sel = Selector(resp.text)
            self.repo_list.extend(sel.xpath('//*[@id="user-repositories-list"]/ul/li/div/div/h3/a/@href').extract())
            time.sleep(10)
        self.logger.info(len(self.repo_list))

    def clone_one_repo(self, repo: str):
        url = f'git@github.com:{repo[1:]}.git'

        repo_short_name = repo.split('/')[-1]
        # print(repo, repo_short_name)
        repo_full_dir = Path(self.dir).joinpath(repo_short_name).as_posix()

        if Path(repo_full_dir).exists():
            cmd = f'cd {repo_full_dir} && git pull'
            os.system(cmd)
            self.logger.info(cmd)
            time.sleep(1)
        else:
            cmd = f'''cd {self.dir} && git clone {url}'''
            self.logger.warning(cmd)
            os.system(cmd)
            time.sleep(30)

    def start_clone(self):
        self.get_repo_urls()

        for repo in self.repo_list:
            self.clone_one_repo(repo)

    def push_one_repo(self,folder):
        folder = str(folder)
        cmd_list =[f'cd {folder}','git pull','git diff','git add ./.','git commit -m "auto commit"','git push origin','git push github']
        cmd = ' && '.join(cmd_list)
        self.logger.info(cmd)
        os.system(cmd)

    def start_push(self):
        # folder_list = list(Path(self.dir).iterdir())
        folder_list = list(Path(self.dir).iterdir())
        for folder in folder_list:
            self.push_one_repo(folder)




if __name__ == '__main__':
<<<<<<< HEAD
    GithubCloner('ydf0509', total_pages=2, dir='/codes').start()
=======
    # GithubCloner('ydf0509', total_pages=2, dir='/codes_github').start_clone()
    GithubCloner('ydf0509', total_pages=2, dir='/codes').start_push()
>>>>>>> 3b2197271f5240871290ffaa36ed333e9a6a3365

    # os.system(''' cd /codes_github/nb_log2 && git pull  ''')
