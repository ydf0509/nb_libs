import os
import subprocess
import time


def getstatusoutput(cmd):
    try:
        data = subprocess.check_output(cmd, shell=True, universal_newlines=True,
                                       stderr=subprocess.STDOUT, encoding='utf8')  # 必須設置為utf8， 不然报错了。
        exitcode = 0
    except subprocess.CalledProcessError as ex:
        data = ex.output
        exitcode = ex.returncode
    if data[-1:] == '\n':
        data = data[:-1]
    return exitcode, data


def do_cmd(cmd_strx, is_print_out=True):
    print(f'执行 {cmd_strx}')
    t0 = time.time()
    exitcode, data = getstatusoutput(cmd_strx)
    if is_print_out:
        print(f'exitcode: {exitcode}, 耗时 {time.time() -t0} 秒')
        print(data, '\n', '- -' * 20, '\n\n')
    if exitcode == 1 and 'nothing to commit' in data:
        return
    if exitcode != 0:
        raise ValueError('要检查git提交')

    return exitcode, data


class GitDevMerge:
    # MY_BRANCH = 'yangmei/0607ym'   #0707
    # TARGET_BRANCH = 'develop'
    # commit_msg = '特征需求'

    def __init__(self, my_branch='master', target_branch='master', commit_msg='', git_root_path='./',
                 only_push_my_branch=True):
        self.my_branch = my_branch
        self.target_branch = target_branch
        self.commit_msg = commit_msg
        self.git_root_path = git_root_path
        self.only_push_my_branch = only_push_my_branch

    def _chdir_and_do_cmd(self, cmd: str, is_print_out=True):
        cmd = f'cd {self.git_root_path} && {cmd}'
        return do_cmd(cmd, is_print_out)

    def do_merge(self):
        t1 = time.perf_counter()
        # do_cmd(f'git checkout {MY_BRANCH}')

        git_branch_str = self._chdir_and_do_cmd('git branch', is_print_out=False)[1]
        if '* ' + self.my_branch not in git_branch_str + '\n':
            raise ValueError(f'当前分支不是处在 {self.my_branch},退出提交')

        diff_text = self._chdir_and_do_cmd('git diff')
        print('差异:\n', diff_text[1])
        self._chdir_and_do_cmd(f'git add {self.git_root_path}')
        self._chdir_and_do_cmd(f'''git commit -m "{self.commit_msg}" ''')
        self._chdir_and_do_cmd(f''' git push --set-upstream origin {self.my_branch} ''')
        self._chdir_and_do_cmd('git push')

        if self.only_push_my_branch is False:
            self._chdir_and_do_cmd(f'git checkout {self.target_branch}')
            self._chdir_and_do_cmd('git  pull')
            self._chdir_and_do_cmd(f'git merge {self.my_branch}')
            self._chdir_and_do_cmd('git push')
            self._chdir_and_do_cmd(f'git checkout {self.my_branch}')

        git_branch_str = self._chdir_and_do_cmd('git branch', is_print_out=False)[1]
        if '* ' + self.my_branch not in git_branch_str + '\n':
            raise ValueError(f'当前分支不是处在 {self.my_branch},合并冲突')

        print(f'耗时 {time.perf_counter() - t1}  ...')

        time.sleep(5)
        print(time.strftime('%H:%M:%S'))
        time.sleep(3600000)
