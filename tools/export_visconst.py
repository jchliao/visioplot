# %%
import win32com.client
from win32com.client import gencache
import os

# 确保生成缓存以获取完整的常量库
try:
    # 这一步会自动触发 win32com 生成本地 Python 常量定义
    visio = gencache.EnsureDispatch("Visio.Application")
except Exception as e:
    print(f"❌ 无法启动 Visio 或生成缓存: {e}")
    exit()

def export_all_constants(filename="visio_constants_lib.py"):
    """将所有 Visio 常量导出到本地 Python 文件中"""
    consts = win32com.client.constants
    
    try:
        # 从 win32com 的内部字典获取所有已加载的常量
        all_consts = consts.__dicts__[0]
        
        with open(filename, "w", encoding="utf-8") as f:
            f.write('"""\nVisio 常量库 - 自动导出\n此文件可直接打包到项目中，避免实时调用 win32com 加载常量\n"""\n\n')
            
            # 1. 导出为大字典格式，方便按字符串名称动态查找
            f.write("CONSTANTS = {\n")
            sorted_names = sorted(all_consts.keys())
            for name in sorted_names:
                value = all_consts[name]
                f.write(f"    '{name}': {value},\n")
            f.write("}\n\n")
            
            # 2. 导出为标准变量格式，支持 IDE 的代码自动补全
            f.write("# 直接调用示例: from visio_constants_lib import visSectionObject\n")
            f.write("# --- 常量定义开始 ---\n")
            for name in sorted_names:
                value = all_consts[name]
                f.write(f"{name} = {value}\n")
                
        print(f"✅ 导出成功！文件位置: {os.path.abspath(filename)}")
        print(f"📊 文件大小: {os.path.getsize(filename) / 1024:.1f} KB")
        print(f"🔢 共计导出 {len(all_consts)} 个常量。")

    except (IndexError, AttributeError):
        print("❌ 常量库加载失败。请确保 Visio 已安装且 gencache 已运行。")

if __name__ == "__main__":
    export_all_constants()