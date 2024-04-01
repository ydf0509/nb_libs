import importlib.util
import os
import sys
import types
import typing
from pathlib import Path, WindowsPath, PosixPath
from nb_log import LoggerMixin


class PathHelper(LoggerMixin):
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

    def rglob_dirs(self, pattern: str, is_resolve: bool = False) -> typing.List[Path]:
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

    def import_as_module(self, module_name: str = None) -> types.ModuleType:
        if module_name is None:
            module_name = self.path.parent.as_posix().replace('/', '.') + '.' + self.path.stem

        module_spec = importlib.util.spec_from_file_location(module_name, self.path)
        module = importlib.util.module_from_spec(module_spec)
        module_spec.loader.exec_module(module)
        return module
        # except FileNotFoundError:
        #     self.logger.exception(f"Module file '{self.path}' not found.")
        # except Exception as e:
        #     self.logger.exception(f"Failed to import module '{module_name}': {str(e)}")

    def auto_import_files_in_dir(self, ) -> None:
        for file_path in self.rglob_files('*.py'):
            self.logger.debug(f'导入模块 {file_path}')
            if Path(file_path) == Path(sys._getframe(1).f_code.co_filename):
                self.logger.warning(f'排除导入调用PathHelper的模块自身 {file_path}')  # 否则下面的import这个文件,会造成无限懵逼死循环
                continue
            self.__class__(file_path).import_as_module()


if __name__ == '__main__':
    print(type(Path('/')))
    print(list(PathHelper(r'../').rglob_files('*', is_resolve=True)))
    print(PathHelper(r'D:\codes\nb_libs\nb_libs/dict2json.py').import_as_module().__dict__)

    PathHelper('./').auto_import_files_in_dir()
