
import os
from nb_log import LoggerMixin


class CodeLineStstistics(LoggerMixin):
    def __init__(self, file_path, k_file_extension='.py'):
        self.file_path = file_path
        self.file_list = []
        self.k_file_extension = k_file_extension

        self.count_of_code_lines = 0
        self.count_of_blank_lines = 0
        self.count_of_annotation_lines = 0
        self.count_of_letters =0


    def get_file_list(self):
        self.file_list = [os.path.join(root, file) for root, dirs, files in os.walk(self.file_path) for file in files if
                          file.endswith(self.k_file_extension)]

    def count_one_file_lines(self, file):
        with open(file, 'r', encoding='utf-8') as fp:
            content_list = fp.readlines()
            for content in content_list:
                content = content.strip()
                if content == '':
                    self.count_of_blank_lines += 1
                elif content.startswith('#'):
                    self.count_of_annotation_lines += 1
                else:
                    self.count_of_code_lines += 1
                self.count_of_letters += len(content)

    def start_count_all_files_lines(self):
        self.get_file_list()
        for file in self.file_list:
            self.count_one_file_lines(file)
        self.logger.info(
            f'文件夹 {self.file_path}  代码文件个数 {len(self.file_list)},代码总行数：{self.count_of_code_lines}，代码空行：{self.count_of_blank_lines}，代码注释：{self.count_of_annotation_lines},字母个数 {self.count_of_letters}')


if __name__ == '__main__':
    for file_pathx in [
        r'D:\codes\funboost\funboost',
        r'D:\ProgramData\Miniconda3\Lib\site-packages\celery',
        r'D:\ProgramData\Miniconda3\Lib\site-packages\kombu',
        r'D:\ProgramData\Miniconda3\Lib\site-packages\nameko',
        r'D:\codes\feapder\feapder',
        r'D:\codes_aku\feature-services\mixnew'
    ]:
        CodeLineStstistics(file_pathx).start_count_all_files_lines()
