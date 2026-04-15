#!/usr/bin/env python3
"""
1. 修改 pyproject.toml 的版本号
2. 修改 visioplot/__init__.py 的 __version__
3. git add .
4. git commit -m "chore: bump version to x.x.x"
5. git tag vx.x.x
6. git push origin main
7. git push origin vx.x.x

使用方法：
python release_and_push.py 1.0.6
python release_and_push.py
"""

import argparse
import pathlib
import re
import subprocess
import sys


VERSION_RE = re.compile(r"^\d+\.\d+\.\d+$")


def run_cmd(cmd):
    # 执行命令并在失败时抛出异常
    print("$", " ".join(cmd))
    subprocess.run(cmd, check=True)


def bump_pyproject_version(pyproject_path: pathlib.Path, new_version: str) -> str:
    # 只更新 [project] 段中的 version 字段
    text = pyproject_path.read_text(encoding="utf-8")
    lines = text.splitlines(keepends=True)
    in_project = False

    for i, line in enumerate(lines):
        stripped = line.strip()

        if stripped == "[project]":
            in_project = True
            continue

        if in_project and stripped.startswith("[") and stripped.endswith("]") and stripped != "[project]":
            in_project = False

        if in_project:
            m = re.match(r'^(\s*version\s*=\s*)"([^"]+)"(\s*)$', line)
            if m:
                old_version = m.group(2)
                prefix = m.group(1)
                suffix = m.group(3)
                lines[i] = f'{prefix}"{new_version}"{suffix}'
                pyproject_path.write_text("".join(lines), encoding="utf-8")
                return old_version

    raise ValueError("未在 [project] 段找到 version 字段")


def get_pyproject_version(pyproject_path: pathlib.Path) -> str:
    # 读取 [project] 段中的当前 version
    text = pyproject_path.read_text(encoding="utf-8")
    lines = text.splitlines()
    in_project = False

    for line in lines:
        stripped = line.strip()

        if stripped == "[project]":
            in_project = True
            continue

        if in_project and stripped.startswith("[") and stripped.endswith("]") and stripped != "[project]":
            in_project = False

        if in_project:
            m = re.match(r'^\s*version\s*=\s*"([^"]+)"\s*$', line)
            if m:
                return m.group(1)

    raise ValueError("未在 [project] 段找到 version 字段")


def bump_patch(version: str) -> str:
    # 小版本自增：x.y.z -> x.y.(z+1)
    major, minor, patch = version.split(".")
    return f"{major}.{minor}.{int(patch) + 1}"


def bump_init_version(init_path: pathlib.Path, new_version: str) -> str:
    # 更新包内 __version__ 字段
    text = init_path.read_text(encoding="utf-8")
    lines = text.splitlines(keepends=True)

    for i, line in enumerate(lines):
        m = re.match(r'^(\s*__version__\s*=\s*)"([^"]+)"(\s*)$', line)
        if m:
            old_version = m.group(2)
            prefix = m.group(1)
            suffix = m.group(3)
            lines[i] = f'{prefix}"{new_version}"{suffix}'
            init_path.write_text("".join(lines), encoding="utf-8")
            return old_version

    raise ValueError("未找到 __version__ 字段")


def main() -> int:
    parser = argparse.ArgumentParser(description="一键更新版本并推送 GitHub 标签")
    parser.add_argument("version", nargs="?", help="版本号，格式 x.y.z，例如 1.0.6")
    args = parser.parse_args()

    repo_root = pathlib.Path(__file__).resolve().parent
    pyproject_path = repo_root / "pyproject.toml"
    init_path = repo_root / "visioplot" / "__init__.py"
    if not pyproject_path.exists():
        print("错误：找不到 pyproject.toml", file=sys.stderr)
        return 2
    if not init_path.exists():
        print("错误：找不到 visioplot/__init__.py", file=sys.stderr)
        return 2

    try:
        current_version = get_pyproject_version(pyproject_path)

        if args.version:
            new_version = args.version.strip()
            if not VERSION_RE.match(new_version):
                print("错误：版本号格式必须是 x.y.z，例如 1.0.6", file=sys.stderr)
                return 2
        else:
            if not VERSION_RE.match(current_version):
                print(f"错误：当前版本号不支持自动递增: {current_version}", file=sys.stderr)
                return 2
            new_version = bump_patch(current_version)

        old_version = bump_pyproject_version(pyproject_path, new_version)
        old_init_version = bump_init_version(init_path, new_version)
        print(f"已更新 pyproject 版本号: {old_version} -> {new_version}")
        print(f"已更新 __init__ 版本号: {old_init_version} -> {new_version}")

        # 按你的固定流程执行
        run_cmd(["git", "add", "."])
        run_cmd(["git", "commit", "-m", f"chore: bump version to {new_version}"])
        run_cmd(["git", "tag", f"v{new_version}"])
        run_cmd(["git", "push", "origin", "main"])
        run_cmd(["git", "push", "origin", f"v{new_version}"])


        print("发版流程完成")
        return 0
    except subprocess.CalledProcessError as exc:
        print(f"命令执行失败，退出码 {exc.returncode}: {exc.cmd}", file=sys.stderr)
        return exc.returncode
    except Exception as exc:
        print(f"发生错误: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
