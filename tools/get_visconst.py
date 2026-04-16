# %%
import win32com.client
from win32com.client import gencache

# 确保生成缓存以加载常量库
visio = gencache.EnsureDispatch("Visio.Application")

def get_visio_constant_id(search_name):
    consts = win32com.client.constants
    try:
        all_consts = consts.__dicts__[0]
        # 查找匹配的键
        for name, value in all_consts.items():
            if name.lower() == search_name.lower():
                return value, name # 返回数值和标准名称
        return None, None
    except (IndexError, AttributeError):
        return "Error", None

if __name__ == "__main__":
    print("--- Visio 常量查询工具 (输入 'exit' 退出) ---")
    
    while True:
        target = input("\n请输入常量名称: ").strip()
        
        if target.lower() in ['exit', 'quit', '退出']:
            print("程序已退出。")
            break
            
        if not target:
            continue

        const_id, formal_name = get_visio_constant_id(target)
        
        if const_id == "Error":
            print("❌ 常量库加载失败。")
        elif const_id is not None:
            print(f"✅ 找到常量: {formal_name}")
            print(f"   数值 ID: {const_id}")
        else:
            print(f"❌ 未找到名为 '{target}' 的常量。")