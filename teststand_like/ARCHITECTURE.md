# 测试序列运行器 - UI分离架构文档

## 概述

本项目已完成UI与业务逻辑的分离重构，采用**MVC（Model-View-Controller）**架构模式，使代码更加模块化、可维护和可扩展。

## 项目结构

```
teststand_like/
├── core/                      # 核心业务逻辑层（Model）
│   ├── __init__.py
│   ├── step_model.py         # 步骤数据模型
│   ├── test_loader.py        # 测试函数加载器
│   └── test_engine.py        # 测试执行引擎
│
├── widgets/                   # UI组件层（View）
│   ├── __init__.py
│   ├── draggable_tree.py     # 可拖拽函数树控件
│   ├── droppable_list.py     # 可接收拖拽的序列列表
│   ├── param_editor.py       # 参数编辑器控件
│   └── watcher_widget.py     # 变量监视器控件
│
├── controllers/               # 控制器层（Controller）
│   ├── __init__.py
│   └── test_controller.py    # 测试控制器
│
├── Testcase/                  # 测试用例目录
│   ├── test_api.py
│   ├── test_cal.py
│   └── test_user_management.py
│
├── main.py                    # 原始单体程序
├── main_refactored.py        # 重构后的主程序
└── ARCHITECTURE.md           # 本文档
```

## 架构设计

### 1. 核心层（Core / Model）

核心层包含纯粹的业务逻辑，不依赖任何UI框架。

#### step_model.py - 步骤数据模型

```python
class StepObject:
    """代表测试序列中的一个步骤"""
    - id: 唯一标识符
    - type: 步骤类型（'function' 或 'control'）
    - module: 模块名
    - function: 函数名
    - control: 控制类型（if/for/end/break）
    - params: 参数字典
    - outputs: 输出字典

class BreakLoop:
    """用于跳出循环的异常"""
```

#### test_loader.py - 测试函数加载器

```python
class TestLoader:
    """负责动态加载和解析测试模块"""
    
    主要方法:
    - load_from_directory(directory): 从目录加载测试模块
    - get_function(module_name, func_name): 获取函数对象
    - get_function_signature(): 获取函数签名
    - get_return_names(): 获取预测返回值名称
```

#### test_engine.py - 测试执行引擎

```python
class TestEngine:
    """管理测试序列的执行，包括控制流处理"""
    
    主要方法:
    - set_steps(steps): 设置要执行的步骤列表
    - set_callbacks(): 设置输出、监视器、状态回调
    - run_all(): 运行整个测试序列
    - step_run(): 执行单步
    - reset_execution(): 重置执行状态
    - resolve_references(): 解析变量引用（${#N:key}, ${@var}）
```

**关键特性**：
- 支持控制流：if/for/end/break
- 支持变量引用和传递
- 支持单步调试
- 完全独立于UI框架

### 2. UI组件层（Widgets / View）

UI组件层包含可复用的界面控件，每个控件职责单一。

#### draggable_tree.py - 可拖拽函数树

```python
class DraggableTreeWidget(QTreeWidget):
    """显示测试函数和流程控制的树形列表"""
    
    - 支持拖拽操作
    - 自动填充测试函数
    - 包含流程控制节点
```

#### droppable_list.py - 可拖拽序列列表

```python
class DroppableListWidget(QListWidget):
    """接收拖拽的测试序列列表"""
    
    - 接收函数和控制流拖拽
    - 支持Delete键删除
    - 提供步骤对象访问
    信号:
    - itemMoved: 项被添加或移动时触发
```

#### param_editor.py - 参数编辑器

```python
class ParamEditor(QWidget):
    """编辑测试步骤的输入参数"""
    
    - 根据函数签名自动生成输入框
    - 支持引用其他步骤的输出（${#N:key}）
    - 实时更新参数到StepObject
    信号:
    - paramChanged: 参数值改变时触发
```

#### watcher_widget.py - 变量监视器

```python
class WatcherWidget(QTreeWidget):
    """显示测试序列中各步骤的变量状态"""
    
    - 树形展示每个步骤的输入/输出
    - 显示运行时变量（如循环变量）
    - 实时更新
```

### 3. 控制器层（Controllers）

控制器层协调UI和业务逻辑之间的交互。

#### test_controller.py - 测试控制器

```python
class TestController:
    """协调UI组件和测试引擎"""
    
    主要职责:
    - 管理TestLoader和TestEngine实例
    - 连接UI控件信号到业务逻辑
    - 通过回调更新UI显示
    - 处理用户交互事件
    
    主要方法:
    - set_ui_components(): 设置UI组件引用
    - load_test_functions(): 加载测试函数
    - run_sequence(): 运行测试序列
    - step_run(): 单步执行
    - reset_execution(): 重置执行状态
    - clear_sequence(): 清空序列
```

### 4. 主程序（main_refactored.py）

主程序仅负责：
- 创建UI布局
- 实例化控制器
- 连接UI事件到控制器方法

```python
class MainWindow(QMainWindow):
    """主窗口 - 仅负责UI布局"""
    
    def __init__(self):
        self.controller = TestController()
        self.init_ui()
        self.create_menu_bar()
```

## 架构优势

### 1. 职责分离

- **核心层**：纯业务逻辑，可独立测试
- **UI层**：可视化组件，可独立开发和测试
- **控制器层**：协调两者，薄层设计

### 2. 可测试性

可以在不启动UI的情况下测试核心功能：

```python
from core import TestLoader, TestEngine, StepObject

# 创建测试步骤
steps = [
    StepObject(type_="function", module="test_cal", function="test_add")
]
steps[0].params = {"a": "5", "b": "3"}

# 创建引擎并执行
loader = TestLoader()
loader.load_from_directory()
engine = TestEngine(loader)
engine.set_steps(steps)
engine.run_all()

# 验证结果
assert steps[0].outputs['return'] == 8
```

### 3. 可扩展性

#### 添加新的UI界面

可以轻松创建不同的UI（CLI、Web等），复用核心逻辑：

```python
# CLI版本示例
from core import TestLoader, TestEngine

loader = TestLoader()
engine = TestEngine(loader)

# 使用相同的核心API
loader.load_from_directory()
# ... 命令行交互逻辑
```

#### 添加新功能

- 在核心层添加新的执行策略
- 在UI层添加新的可视化组件
- 在控制器层协调新功能

### 4. 可维护性

- **单一职责**：每个类只负责一件事
- **低耦合**：通过接口和回调通信
- **高内聚**：相关功能组织在一起

## 与原版对比

### 原版（main.py）

- **单体架构**：所有逻辑在MainWindow类中（~1000行）
- **强耦合**：UI和业务逻辑混合
- **难以测试**：必须启动GUI才能测试
- **难以扩展**：修改UI会影响业务逻辑

### 重构版（main_refactored.py）

- **模块化架构**：职责明确分离
- **松耦合**：通过控制器和回调通信
- **易于测试**：可独立测试核心功能
- **易于扩展**：可添加新UI而不修改核心

## 使用方法

### 运行程序

```bash
cd teststand_like
python main_refactored.py
```

### 对比运行原版

```bash
python main.py
```

## 数据流

### 加载测试函数

```
用户点击"加载" 
  → MainWindow.load_button.clicked 
  → TestController.load_test_functions()
  → TestLoader.load_from_directory()
  → TestController更新function_tree
```

### 执行测试序列

```
用户点击"运行"
  → TestController.run_sequence()
  → TestEngine.run_all()
  → 回调TestController._on_engine_output()
  → 更新output_text显示
  → 回调TestController._on_engine_watcher_update()
  → 更新watcher_widget显示
  → 回调TestController._on_engine_status_update()
  → 更新序列项图标
```

### 编辑参数

```
用户选择序列项
  → DroppableListWidget.currentItemChanged
  → TestController._on_item_selection_changed()
  → ParamEditor.load_step()
  → 显示参数输入框
用户修改参数
  → QLineEdit.textChanged
  → ParamEditor._on_param_changed()
  → StepObject.params更新
```

## 扩展示例

### 添加CLI模式

```python
# cli_runner.py
from core import TestLoader, TestEngine, StepObject

class CLIRunner:
    def __init__(self):
        self.loader = TestLoader()
        self.engine = TestEngine(self.loader)
        self.engine.set_callbacks(output_cb=print)
    
    def run_from_file(self, seq_file):
        # 从文件加载序列
        steps = self.load_sequence(seq_file)
        self.engine.set_steps(steps)
        self.engine.run_all()
```

### 添加报告生成

```python
# report_generator.py
class ReportGenerator:
    def __init__(self, engine):
        self.engine = engine
        self.results = []
        engine.set_callbacks(
            status_cb=self.on_step_complete
        )
    
    def on_step_complete(self, index, success):
        self.results.append({
            'step': index,
            'success': success,
            'timestamp': datetime.now()
        })
    
    def generate_html_report(self):
        # 生成HTML报告
        pass
```

## 总结

通过UI分离架构重构，项目获得了：

1. ✅ **更好的可测试性**：核心逻辑可独立测试
2. ✅ **更高的可维护性**：职责明确，易于定位问题
3. ✅ **更强的可扩展性**：可添加新UI或功能
4. ✅ **更好的代码复用**：核心引擎可在不同场景使用

这为未来的功能扩展和多平台支持奠定了坚实的基础。
