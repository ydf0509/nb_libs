import functools
import importlib.util
import os
import shutil
import sys
import threading
import types
import typing
from pathlib import Path, WindowsPath, PosixPath
from nb_log import get_logger


class PathHelper:
    _modules_cache = {}
    _lock = threading.Lock()
    logger = get_logger(name=__name__)
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
    def path_str(self):
        return self.path.as_posix()
    
    def get_relative_path(self, parent_path: Path) -> Path:
        return self.path.relative_to(parent_path)

    def ensure_parent(self) -> 'PathHelper':
        """确保当前路径的父目录存在，如果不存在则创建。"""
        """
        PathHelper('data/reports/2023/sales.csv').ensure_parent().write_text('...')
        """
        parent_dir = self.path.parent
        parent_dir.mkdir(parents=True, exist_ok=True)
        return self

    def read_text(self, encoding: str = 'utf-8') -> str:
        return self.path.read_text(encoding=encoding)
    
    def write_text(self, text: str, encoding: str = 'utf-8') -> None:
        return self.path.write_text(text, encoding=encoding)

    def copy_to(self, destination: typing.Union[os.PathLike, str]) -> 'PathHelper':
        """
        将文件或目录复制到指定位置。
        - 如果 destination 是一个目录，则复制到该目录下。
        - 如果 destination 是一个文件路径，则复制并重命名。
        """
        dest_path = Path(destination)
        if self.path.is_file():
            shutil.copy2(self.path, dest_path)  # copy2 同时复制元数据
        elif self.path.is_dir():
            # 如果目标是目录，需要指定新目录名
            dest_path_final = dest_path if not dest_path.is_dir() else dest_path / self.path.name
            shutil.copytree(self.path, dest_path_final)
        return self.__class__(dest_path)
    
    def move_to(self, destination: typing.Union[os.PathLike, str]) -> 'PathHelper':
        """将文件或目录移动到指定位置。"""
        moved_path = shutil.move(str(self.path), str(destination))
        return self.__class__(moved_path)

    def rglob_files(self, pattern: str, ) -> typing.List[Path]:
        """递归查找所有匹配的文件。"""
        files = [p for p in self.path.rglob(pattern) if p.is_file()]
        if self._is_always_resolve:
            # 只在最后对结果列表进行一次 resolve 操作
            return [p.resolve() for p in files]
        return files

    def rglob_dirs(self, pattern: str, ) -> typing.List[Path]:
        """递归查找所有匹配的目录。"""
        dirs = [p for p in self.path.rglob(pattern) if p.is_dir()]
        if self._is_always_resolve:
            return [p.resolve() for p in dirs]
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
            
            if Path(file_path) == Path(sys._getframe(1).f_code.co_filename):
                self.logger.warning(f'排除导入调用PathHelper的模块自身 {file_path}')  # 否则下面的import这个文件,会造成无限懵逼死循环
                continue
            self.logger.debug(f'导入模块 {file_path}')
            self.__class__(file_path).import_as_module()

    def get_module_name(self, ) -> str:
        """获取当前文件的模块名字"""
        relative_path = None
        for python_path in sys.path[0:]:
            try:
                relative_path = self.path.relative_to(Path(python_path))
                break
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
    cur_dir = Path(__file__).parent
    print(PathHelper(cur_dir, is_always_resolve=True))
    print(PathHelper(cur_dir, is_always_resolve=True).path)
    print(list(PathHelper(cur_dir).rglob_files('*.py', )))
    print(PathHelper(r'D:\codes\nb_libs\nb_libs\dict_util.py').import_as_module())

    PathHelper(Path(__file__).parent.parent.joinpath('tests/test_import_dir')).auto_import_pyfiles_in_dir()

    print(PathHelper(r'D:\codes\nb_libs\nb_libs\dict_util.py').get_module_name())

    import nb_libs.dict_util
