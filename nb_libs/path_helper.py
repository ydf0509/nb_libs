import os
import typing
from pathlib import Path, WindowsPath, PosixPath


class PathHelper:
    def __init__(self, path: typing.Union[os.PathLike, str]):
        self.path = Path(path)

    def rglob_files(self, pattern: str, is_resolve: bool = False) -> typing.List[Path]:
        entries = self.path.rglob(pattern, )
        files = []
        # 遍历文件夹和文件
        for entry in entries:
            if is_resolve:
                entry = entry.resolve()
            # 如果是文件，打印文件路径
            if entry.is_file():
                # print('file: ', entry)
                pass
                files.append(entry.resolve())
            # 如果是文件夹，递归调用 find_files() 函数
            elif entry.is_dir():
                pass
                # print('dir: ', entry)
        return files

    def rglob_dirs(self, pattern: str,  is_resolve: bool = False) -> typing.List[Path]:
        entries = self.path.rglob(pattern, )
        dirs = []
        # 遍历文件夹和文件
        for entry in entries:
            if is_resolve:
                entry = entry.resolve()
            # 如果是文件，打印文件路径
            if entry.is_file():
                # print('file: ', entry)
                pass
            # 如果是文件夹，递归调用 find_files() 函数
            elif entry.is_dir():
                # print('dir: ', entry)
                pass
                dirs.append(entry)
        return dirs


if __name__ == '__main__':
    print(type(Path('/')))
    print(list(PathHelper(r'../').rglob_files('*',is_resolve=True)))

    print(Path(r'D:\codes\nb_libs\nb_libs\..\tests\tests_time.py').resolve())
