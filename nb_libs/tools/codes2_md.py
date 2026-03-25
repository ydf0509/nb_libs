"""
用这个将整个文件夹所有代码文件路径 + 内容, 生成到一个大的markdown文件中, 上传给ai后再提问和推理,非常好用非常高效
"""

import os
from pathlib import Path
from nb_libs.path_helper import PathHelper


# def _get_file_suffix(file_name:str):
#     return os.path.splitext(file_name)[1]


def _judge_suffixes_file_need_process(
    filename: str, exclude_suffixes: list, should_include_suffixes: list
):
    file_need_process = True
    for exclude_suffix in exclude_suffixes:
        if filename.endswith(exclude_suffix):
            file_need_process = False
            break
    if len(should_include_suffixes) == 0:
        return file_need_process
    file_need_process = False
    for should_include_suffix in should_include_suffixes:
        if filename.endswith(should_include_suffix):
            file_need_process = True
            break
    return file_need_process


def codes2md(
    root_dir: str,
    excluded_dirs: list,
    excluded_files: list,
    exclude_suffixes: list,
    should_include_suffixes: list,
    all_codes_md_path: Path,
    all_codes_first_str: str,
    abs_path_prefix: str,
    other_file_list: list=[],
):
    # print(f)

    excluded_dirs.extend([
        Path(root_dir).joinpath("__pycache__").as_posix(),
        Path(root_dir).joinpath(".vscode").as_posix(),
        Path(root_dir).joinpath(".git").as_posix(),
        Path(root_dir).joinpath(".idea").as_posix(),
        Path(root_dir).joinpath("dist").as_posix(),
        Path(root_dir).joinpath("build").as_posix(),

        Path(root_dir).joinpath(".history").as_posix(),
        Path(root_dir).joinpath("build").as_posix(),
    ])

    excluded_files.extend([
        Path(root_dir).joinpath("setup.py").as_posix(),
        Path(root_dir).joinpath("nb_log_config.py").as_posix(),
    ])

    exclude_suffixes.extend(
        [".png", ".jpg", ".ico", ".pyc", ".sqlite", ".data", ".dat", ".db", ".log"]
    )

    all_codes_str = all_codes_first_str + "\n"

    print("excluded_dirs:", excluded_dirs)
    all_need_process_full_file_list = []
    all_need_process_full_file_list.extend(other_file_list)
    for dirpath, dirnames, filenames in os.walk(root_dir):
        # Exclude specified directories
        # To be safe, we check if the current directory path starts with any of the excluded paths.
        if any(dirpath.startswith(excluded_dir) for excluded_dir in excluded_dirs):
            continue
        if any(Path(dirpath).as_posix().startswith(excluded_dir) for excluded_dir in excluded_dirs):
            continue

        
        for filename in filenames:
            file_need_process = _judge_suffixes_file_need_process(
                filename, exclude_suffixes, should_include_suffixes
            )
            if file_need_process:
                full_file_name = os.path.join(dirpath, filename)
                if any(full_file_name.startswith(excluded_file) for excluded_file in excluded_files):
                    continue
                if any(Path(full_file_name).as_posix().startswith(excluded_file) for excluded_file in excluded_files):
                    continue
                
                all_need_process_full_file_list.append(full_file_name)
    all_need_process_full_file_list = list(set(all_need_process_full_file_list))
    print(len(all_need_process_full_file_list))
    for full_file_name in all_need_process_full_file_list:
        print(full_file_name)
        file_str = open(full_file_name, "r", encoding="utf-8").read()
        short_file_name = full_file_name.replace(abs_path_prefix, "")
        lang = short_file_name.split(".")[-1]
        if lang == "py":
            lang = "python"
        if lang == "md":
            all_codes_str += (
                f"\n### 代码文件: {short_file_name}\n \n{file_str}\n \n"
            )
        else:
            all_codes_str += (
                f"\n### 代码文件: {short_file_name}\n```{lang}\n{file_str}\n```\n"
            )
    all_codes_md_path.write_text(all_codes_str, encoding="utf-8")
    print(f"{all_codes_md_path} 文件生成成功")
    print(f"{all_codes_md_path} 文件内容字母数量: {len(all_codes_str)}")
    newline_count = all_codes_str.count("\n")
 
    print(f"{all_codes_md_path} 文件内容行数: {newline_count}")
    print(f"{all_codes_md_path} 文件内容个数: {len(all_need_process_full_file_list)}")
    
    for i in range(3):
        print('* *' * 20 + '\n')

if __name__ == "__main__":
    codes2md(
        root_dir=r"D:\codes\funboost\funboost",
        excluded_dirs=[
            r"D:\codes\funboost\funboost\utils\dependency_packages",
            r"D:\codes\funboost\funboost\utils\dependency_packages_in_pythonpath",
            r"D:\codes\funboost\funboost\function_result_web\static",
        ],
        exclude_suffixes=[],
        all_codes_md_path=Path(r"D:\codes\nb_libs\tests\md_dirs").joinpath(
            "funboost_all_codes.md"
        ),
        all_codes_first_str="# funboost 项目代码文件大全 \n",
        abs_path_prefix="D:\\codes\\funboost\\",
    )
