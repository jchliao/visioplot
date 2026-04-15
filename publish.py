#!/usr/bin/env python3
"""
一键发版脚本：更新版本号 → Git提交 → 打标签 → 推送
用法：
python release_and_push.py        # 自动小版本递增 x.y.z+1
python release_and_push.py 1.0.6  # 指定版本号
"""
import argparse
import pathlib
import re
import subprocess
import sys

# 常量配置（集中管理，一目了然）
VERSION_PATTERN = re.compile(r"^\d+\.\d+\.\d+$")
PROJECT_DIR = pathlib.Path(__file__).parent
PYPROJECT_PATH = PROJECT_DIR / "pyproject.toml"
INIT_PATH = PROJECT_DIR / "visioplot" / "__init__.py"


def run_cmd(cmd: list) -> None:
    """执行shell命令，失败直接抛出异常"""
    print("$", " ".join(cmd))
    subprocess.run(cmd, check=True)


def update_version(file: pathlib.Path, key: str, new_ver: str) -> str:
    """通用：更新文件中指定的版本字段（合并所有重复的文件修改逻辑）"""
    content = file.read_text("utf-8")
    # 正则匹配：key = "xxx"
    new_content, count = re.subn(
        rf'^(\s*{key}\s*=\s*)"[^"]+"',
        rf'\1"{new_ver}"',
        content,
        flags=re.MULTILINE
    )
    if count == 0:
        raise ValueError(f"未找到字段：{key}")
    
    file.write_text(new_content, "utf-8")
    # 返回旧版本号
    return re.search(rf'{key}\s*=\s*"([^"]+)"', content).group(1)


def get_current_version() -> str:
    """读取 pyproject.toml 中的当前版本"""
    content = PYPROJECT_PATH.read_text("utf-8")
    match = re.search(r'\[project\][\s\S]*?version\s*=\s*"([^"]+)"', content)
    if not match:
        raise ValueError("pyproject.toml 中未找到 [project] version")
    return match.group(1)


def bump_patch(version: str) -> str:
    """小版本自增：x.y.z → x.y.z+1"""
    major, minor, patch = version.split(".")
    return f"{major}.{minor}.{int(patch) + 1}"


def main() -> int:
    # 解析命令行参数
    parser = argparse.ArgumentParser(description="版本更新+Git推送一键脚本")
    parser.add_argument("version", nargs="?", help="格式：x.y.z")
    args = parser.parse_args()

    # 校验文件存在
    if not PYPROJECT_PATH.exists():
        print("错误：找不到 pyproject.toml", file=sys.stderr)
        return 2
    if not INIT_PATH.exists():
        print("错误：找不到 visioplot/__init__.py", file=sys.stderr)
        return 2

    try:
        # 确定新版本号
        current_ver = get_current_version()
        new_ver = args.version.strip() if args.version else bump_patch(current_ver)
        
        # 校验版本格式
        if not VERSION_PATTERN.match(new_ver):
            print("错误：版本号必须为 x.y.z 格式", file=sys.stderr)
            return 2

        # 更新两个文件的版本号
        old_pyproj = update_version(PYPROJECT_PATH, "version", new_ver)
        old_init = update_version(INIT_PATH, "__version__", new_ver)
        print(f"版本更新完成：{old_pyproj} → {new_ver}")

        # Git 自动化流程
        run_cmd(["git", "add", "."])
        run_cmd(["git", "commit", "-m", f"chore: bump version to {new_ver}"])
        run_cmd(["git", "tag", f"v{new_ver}"])
        run_cmd(["git", "push", "origin", "main"])
        run_cmd(["git", "push", "origin", f"v{new_ver}"])

        print("\n✅ 发版流程全部完成！")
        return 0

    except subprocess.CalledProcessError as e:
        print(f"❌ 命令执行失败：{e.cmd}", file=sys.stderr)
        return e.returncode
    except Exception as e:
        print(f"❌ 错误：{e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())