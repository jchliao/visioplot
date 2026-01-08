[![zread](https://img.shields.io/badge/Ask_Zread-_.svg?style=flat&color=00b0aa&labelColor=000000&logo=data%3Aimage%2Fsvg%2Bxml%3Bbase64%2CPHN2ZyB3aWR0aD0iMTYiIGhlaWdodD0iMTYiIHZpZXdCb3g9IjAgMCAxNiAxNiIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHBhdGggZD0iTTQuOTYxNTYgMS42MDAxSDIuMjQxNTZDMS44ODgxIDEuNjAwMSAxLjYwMTU2IDEuODg2NjQgMS42MDE1NiAyLjI0MDFWNC45NjAxQzEuNjAxNTYgNS4zMTM1NiAxLjg4ODEgNS42MDAxIDIuMjQxNTYgNS42MDAxSDQuOTYxNTZDNS4zMTUwMiA1LjYwMDEgNS42MDE1NiA1LjMxMzU2IDUuNjAxNTYgNC45NjAxVjIuMjQwMUM1LjYwMTU2IDEuODg2NjQgNS4zMTUwMiAxLjYwMDEgNC45NjE1NiAxLjYwMDFaIiBmaWxsPSIjZmZmIi8%2BCjxwYXRoIGQ9Ik00Ljk2MTU2IDEwLjM5OTlIMi4yNDE1NkMxLjg4ODEgMTAuMzk5OSAxLjYwMTU2IDEwLjY4NjQgMS42MDE1NiAxMS4wMzk5VjEzLjc1OTlDMS42MDE1NiAxNC4xMTM0IDEuODg4MSAxNC4zOTk5IDIuMjQxNTYgMTQuMzk5OUg0Ljk2MTU2QzUuMzE1MDIgMTQuMzk5OSA1LjYwMTU2IDE0LjExMzQgNS42MDE1NiAxMy43NTk5VjExLjAzOTlDNS42MDE1NiAxMC42ODY0IDUuMzE1MDIgMTAuMzk5OSA0Ljk2MTU2IDEwLjM5OTlaIiBmaWxsPSIjZmZmIi8%2BCjxwYXRoIGQ9Ik0xMy43NTg0IDEuNjAwMUgxMS4wMzg0QzEwLjY4NSAxLjYwMDEgMTAuMzk4NCAxLjg4NjY0IDEwLjM5ODQgMi4yNDAxVjQuOTYwMUMxMC4zOTg0IDUuMzEzNTYgMTAuNjg1IDUuNjAwMSAxMS4wMzg0IDUuNjAwMUgxMy43NTg0QzE0LjExMTkgNS42MDAxIDE0LjM5ODQgNS4zMTM1NiAxNC4zOTg0IDQuOTYwMVYyLjI0MDFDMTQuMzk4NCAxLjg4NjY0IDE0LjExMTkgMS42MDAxIDEzLjc1ODQgMS42MDAxWiIgZmlsbD0iI2ZmZiIvPgo8cGF0aCBkPSJNNCAxMkwxMiA0TDQgMTJaIiBmaWxsPSIjZmZmIi8%2BCjxwYXRoIGQ9Ik00IDEyTDEyIDQiIHN0cm9rZT0iI2ZmZiIgc3Ryb2tlLXdpZHRoPSIxLjUiIHN0cm9rZS1saW5lY2FwPSJyb3VuZCIvPgo8L3N2Zz4K&logoColor=ffffff)](https://zread.ai/jchliao/ltoolx)

# Introduction

L2的妙妙工具包，包含gurobi、matplot相关函数。

## Matplotlib tools

提供更为强大的svg矢量图导出功能，完整功能需要结合axisartist使用。
在plot选项当中添加`gid="out"`参数，将折线线段化，并剔除超出坐标轴的图线，实现图像在ppt、visio等工具当中的更多编辑功能。

使用示例如下：

```python
from ltoolx.matplotlib_utils import *
from ltoolx.svg_utils import *
import mpl_toolkits.axisartist as AA
# plt直接使用方法
plt.axes(axes_class=AA.Axes)
plt.plot([1, 2, 3], [3, 5, 4], label="inax", marker="s")
plt.plot(
    [1, 2, 3], [5, 15, 3], gid="out", label="outax", linestyle="--", marker="o"
)
plt.xlim([1.25, 3])
plt.ylim([4.0, 10.0])
plt.legend()
savefig("test1.svg")

# 创建figure对象使用方法
fig= plt.figure()
ax = fig.add_subplot(axes_class=AA.Axes)
ax.plot([1,2,3],[3,2,4],label='inax')
ax.plot([1,2,3],[5,15,3],label='outax',gid='out')
ax.set_ylim([0,10])
ax.legend()
Fig(fig).savefig("test2.svg")

```

## 导出为vsd并保存到剪切板

```python
from ltoolx.matplotlib_utils import *
from ltoolx.svg_utils import *
# plt直接使用方法
plt.plot([1, 2, 3], [3, 5, 4], label="inax", marker="s")
plt.plot(
    [1, 2, 3], [5, 15, 3], gid="out", label="outax", linestyle="--", marker="o"
)
plt.xlim([1.25, 3])
plt.ylim([4.0, 10.0])
plt.legend()
savefig("test1.svg").to_vsd(clipboard=True)

# 创建figure对象使用方法
fig= plt.figure()
ax = fig.add_subplot(axes_class=AA.Axes)
ax.plot([1,2,3],[3,2,4],label='inax')
ax.plot([1,2,3],[5,15,3],label='outax',gid='out')
ax.set_ylim([0,10])
ax.legend()
Fig(fig).savefig("test2.svg").to_vsd(clipboard=True)

```
