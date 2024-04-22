
"""
import markdown
from weasyprint import HTML

# 读取Markdown文件
with open('input.md', 'r', encoding='utf-8') as file:
    markdown_text = file.read()

# 将Markdown转换为HTML
html_text = markdown.markdown(markdown_text)

# 将HTML写入临时文件
with open('temp.html', 'w', encoding='utf-8') as file:
    file.write(html_text)

# 使用weasyprint将HTML转换为PDF
HTML(filename='temp.html').write_pdf('output.pdf')
"""

import markdown
from weasyprint import HTML
from pathlib import Path


class MarkdownConvter:
    def __init__(self,markdown_file_list:list,html_file,pdf_file):

        self.markdown_file_list = markdown_file_list
        self.html_file = html_file
        self.pdf_file = pdf_file

        self.markdown_text_all = ''
        self.html_text = ''
        self.get_text()


    def get_text(self,):
        for md_file in self.markdown_file_list:
            with Path(md_file).open('r', encoding='utf-8') as fs:
                markdown_text = fs.read()
                self.markdown_text_all += markdown_text
        self.html_text = markdown.markdown(self.markdown_text_all)

    def convert2html(self):
        with open(self.html_file, 'w', encoding='utf-8') as file:
            file.write(self.html_text)

    def convert2pdf(self):
        self.convert2html()
        HTML(filename=self.html_file).write_pdf(self.pdf_file)



if __name__ == '__main__':
    MarkdownConvter([r'D:\codes\funboost_docs\source\articles\c1.md',r'D:\codes\funboost_docs\source\articles\c2.md'],
                    html_file='tmp.html',pdf_file='temp.pdf').convert2pdf()
