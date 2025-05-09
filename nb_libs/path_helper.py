import functools
import importlib.util
import os
import sys
import threading
import types
import typing
from pathlib import Path, WindowsPath, PosixPath
from nb_log import LoggerMixin


class PathHelper(LoggerMixin):
    _modules_cache = {}
    _lock = threading.Lock()

    def __init__(self, path: typing.Union[os.PathLike, str], is_always_resolve=False):
        """
        :param path:
        :param is_always_resolve:  是否总是使用绝对路径.
        """
        self._is_always_resolve = is_always_resolve
        path_obj = Path(path)
        if is_always_resolve:
            path_obj = path_obj.resolve()
        self.path: Path = path_obj

    @property
    def path_resolve_str(self):
        return self.path.resolve().as_posix()

    def rglob_files(self, pattern: str, ) -> typing.List[Path]:
        entries = self.path.rglob(pattern, )
        files = []
        # 遍历文件夹和文件
        for entry in entries:
            if self._is_always_resolve:
                entry = entry.resolve()
            if entry.is_file():
                # print('file: ', entry)
                pass
                files.append(entry.resolve())
            elif entry.is_dir():
                pass
                # print('dir: ', entry)
        return files

    def rglob_dirs(self, pattern: str, ) -> typing.List[Path]:
        entries = self.path.rglob(pattern, )
        dirs = []
        for entry in entries:
            if self._is_always_resolve:
                entry = entry.resolve()
            if entry.is_file():
                # print('file: ', entry)
                pass
            elif entry.is_dir():
                # print('dir: ', entry)
                pass
                dirs.append(entry)
        return dirs

    @staticmethod
    @functools.lru_cache()
    def _get_file__module_map():
        file__module_map = {}
        for k, v in sys.modules.items():
            try:
                # print(v)
                # print(v.__file__)
                file__module_map[Path(v.__file__).resolve().as_posix()] = v
            except (AttributeError, TypeError):
                pass
        # print(file__module_map)
        return file__module_map

    def import_as_module(self, module_name: str = None) -> types.ModuleType:
        """import 当前文件路径"""
        with self._lock:
            path_str = self.path.resolve().as_posix()
            key = (path_str, module_name)
            if key in self._modules_cache:
                return self._modules_cache[key]
            file__module_map = self._get_file__module_map()
            if path_str in file__module_map:
                module = file__module_map[path_str]
                self._modules_cache[key] = module
                return module
            if module_name is None:
                module_name = self.path.parent.as_posix().replace('/', '.') + '.' + self.path.stem
            module_spec = importlib.util.spec_from_file_location(module_name, self.path)
            module = importlib.util.module_from_spec(module_spec)
            module_spec.loader.exec_module(module)
            self._modules_cache[key] = module
            return module
        # except FileNotFoundError:
        #     self.logger.exception(f"Module file '{self.path}' not found.")
        # except Exception as e:
        #     self.logger.exception(f"Failed to import module '{module_name}': {str(e)}")

    def auto_import_pyfiles_in_dir(self, pattern: str = '*.py') -> None:
        for file_path in self.rglob_files(pattern):
            self.logger.debug(f'导入模块 {file_path}')
            if Path(file_path) == Path(sys._getframe(1).f_code.co_filename):
                self.logger.warning(f'排除导入调用PathHelper的模块自身 {file_path}')  # 否则下面的import这个文件,会造成无限懵逼死循环
                continue
            self.__class__(file_path).import_as_module()

    def get_module_name(self, ) -> str:
        """获取当前文件的模块名字"""
        relative_path = None
        for python_path in sys.path[1:]:
            try:
                relative_path = self.path.relative_to(Path(python_path))
                # print(relative_path)
            except ValueError as e:
                pass
                # print(type(e))
        if relative_path is None:
            raise ValueError(f'{self.path} not in sys.path')
        module_name= str(relative_path).replace('\\','.').replace('/', '.').replace('.py', '')
        return module_name
        # return PathHelper(relative_path).path_resolve_str.replace('/', '.').replace('.py', '')

    @staticmethod
    @functools.lru_cache()
    def import_module(module_name:str):
        """import a.b.c 这样"""
        return importlib.import_module(module_name)

    def __str__(self):
        return f'''<PathHelper["{self.path}"]>'''


if __name__ == '__main__':
    print(type(Path('/')))
    print(PathHelper('./', is_always_resolve=True))
    print(PathHelper('./', is_always_resolve=True).path)
    print(list(PathHelper(r'../').rglob_files('*', )))
    print(PathHelper(r'D:\codes\nb_libs\nb_libs/dict2json.py').import_as_module())

    PathHelper(Path(__file__).parent.parent.joinpath('tests/test_import_dir')).auto_import_pyfiles_in_dir()

    print(PathHelper(r'D:\codes\nb_libs\nb_libs/dict2json.py').get_module_name())

    import nb_libs.dict2json
