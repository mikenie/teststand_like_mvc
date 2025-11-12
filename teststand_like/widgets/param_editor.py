"""
参数编辑器控件
"""
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                            QLineEdit, QPushButton, QMenu)
from PyQt6.QtCore import pyqtSignal
from core.step_model import StepObject
import inspect


class ParamEditor(QWidget):
    """参数编辑器
    
    用于编辑测试步骤的输入参数
    """
    
    paramChanged = pyqtSignal(str, str)  # 参数名, 新值
    
    def __init__(self):
        super().__init__()
        self.current_step = None
        self.current_step_index = -1
        self.test_loader = None
        self.all_steps = []  # 所有步骤的引用
        
        self.param_widgets = {}  # 参数名 -> QLineEdit映射
        
        self.init_ui()
    
    def init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        layout.addWidget(QLabel("<b>步骤设置</b>"))
        
        # 输入参数区
        layout.addWidget(QLabel("输入参数:"))
        self.input_params_widget = QWidget()
        self.input_params_layout = QVBoxLayout(self.input_params_widget)
        self.input_params_layout.setSpacing(0)
        self.input_params_layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.input_params_widget)
        
        # 输出参数区
        layout.addWidget(QLabel("输出参数:"))
        self.output_params_label = QLabel("-")
        self.output_params_label.setStyleSheet(
            "QLabel { background-color: #f0f0f0; padding: 5px; border: 1px solid #ccc; }"
        )
        layout.addWidget(self.output_params_label)
    
    def set_test_loader(self, loader):
        """设置测试加载器"""
        self.test_loader = loader
    
    def set_all_steps(self, steps):
        """设置所有步骤的引用（用于引用功能）"""
        self.all_steps = steps
    
    def load_step(self, step: StepObject, step_index: int):
        """加载步骤进行编辑
        
        Args:
            step: 要编辑的步骤对象
            step_index: 步骤在序列中的索引
        """
        self.current_step = step
        self.current_step_index = step_index
        self.clear_params()
        
        if not step:
            self.output_params_label.setText("-")
            return
        
        if step.type == 'function':
            self._load_function_params(step)
        elif step.type == 'control':
            self._load_control_params(step)
    
    def _load_function_params(self, step: StepObject):
        """加载函数参数"""
        if not self.test_loader:
            self.add_param_row("error", "测试加载器未设置", read_only=True)
            return

        # 确保step对象包含必要的模块和函数信息
        if not step.module or not step.function:
            self.add_param_row("error", "步骤缺少模块或函数信息", read_only=True)
            return
            
        # 尝试获取函数对象
        try:
            func = self.test_loader.get_function(step.module, step.function)
            if not func:
                # 尝试重新加载模块
                self.test_loader.load_from_directory()
                func = self.test_loader.get_function(step.module, step.function)
                
            if not func:
                self.add_param_row("error", f"函数未找到: {step.module}.{step.function}", read_only=True)
                return

            # 直接添加调试信息，确保函数信息正确显示
            self.add_param_row("function_debug", f"加载函数: {step.module}.{step.function}", read_only=True)

            # 获取函数签名
            sig = inspect.signature(func)
            params = list(sig.parameters.keys())
            
            # 添加参数数量调试信息
            self.add_param_row("param_count", f"参数数量: {len(params)}", read_only=True)

            # 如果有参数，添加参数行
            if params:
                # 清除之前的调试行，只保留实际参数行
                self.clear_params()
                
                for param_name in params:
                    cached_value = step.params.get(param_name, "")
                    # 确保创建的输入框能够正确显示
                    edit = self.add_param_row(param_name, cached_value)
                    # 确保输入框可见
                    edit.setVisible(True)
                    # 连接信号
                    edit.textChanged.connect(
                        lambda val, pn=param_name: self._on_param_changed(pn, val)
                    )
                
                # 强制布局更新
                self.input_params_widget.updateGeometry()
                self.input_params_widget.show()
            else:
                # 没有参数时显示提示
                self.add_param_row("提示", "该函数无输入参数", read_only=True)

            # 显示输出参数
            # 方法1: 使用函数返回注解
            return_annotation = sig.return_annotation
            if return_annotation != inspect.Signature.empty:
                if hasattr(return_annotation, '__name__'):
                    output_name = return_annotation.__name__
                else:
                    output_name = str(return_annotation)
                self.output_params_label.setText(output_name)
            else:
                # 方法2: 尝试从test_loader获取预测的返回值名称
                pred_returns = self.test_loader.get_return_names(step.module, step.function)
                if pred_returns:
                    self.output_params_label.setText(", ".join(pred_returns))
                else:
                    self.output_params_label.setText("未知（无类型注解）")
            
            # 确保输出参数标签可见
            self.output_params_label.setVisible(True)

        except Exception as e:
            # 清除之前的参数，显示错误信息
            self.clear_params()
            self.add_param_row("error", f"解析失败: {str(e)}", read_only=True)
    
    def _load_control_params(self, step: StepObject):
        """加载控制流参数"""
        if step.control == "if":
            cond = step.params.get("condition", "")
            edit = self.add_param_row("condition", cond)
            edit.textChanged.connect(lambda val: self._on_param_changed("condition", val))
        
        elif step.control == "for":
            iterable = step.params.get("iterable", "")
            varname = step.params.get("var", "_loop")
            edit1 = self.add_param_row("iterable", iterable)
            edit2 = self.add_param_row("var", varname)
            edit1.textChanged.connect(lambda val: self._on_param_changed("iterable", val))
            edit2.textChanged.connect(lambda val: self._on_param_changed("var", val))
        
        else:
            self.output_params_label.setText("-")
    
    def add_param_row(self, param_name: str, default_value: str = "", read_only: bool = False):
        """添加一行参数输入
        
        Args:
            param_name: 参数名
            default_value: 默认值
            read_only: 是否只读
        
        Returns:
            QLineEdit: 创建的输入框
        """
        # 创建一个容器widget来容纳这一行的所有元素，确保整行能够正确显示
        row_widget = QWidget()
        row_layout = QHBoxLayout(row_widget)
        row_layout.setSpacing(5)  # 增加间距以确保元素不会重叠
        row_layout.setContentsMargins(2, 2, 2, 2)  # 增加边距
        
        # 创建标签
        label = QLabel(f"{param_name}:")
        label.setFixedWidth(100)
        label.setWordWrap(True)  # 允许标签文本换行
        label.setVisible(True)  # 确保标签可见
        
        # 创建输入框
        edit = QLineEdit(str(default_value))
        edit.setReadOnly(read_only)
        edit.setMinimumWidth(200)  # 设置最小宽度，确保有足够空间输入
        edit.setVisible(True)  # 确保输入框可见
        
        # 将控件添加到布局
        row_layout.addWidget(label)
        row_layout.addWidget(edit, 1)  # 设置伸展系数，使输入框能够占据剩余空间
        
        # 只有非只读项才添加引用按钮
        if not read_only:
            ref_btn = QPushButton("引用")
            ref_btn.setToolTip("插入对前一步骤输出/参数的引用")
            ref_btn.setFixedWidth(48)
            ref_btn.clicked.connect(lambda: self._show_ref_menu(edit))
            row_layout.addWidget(ref_btn)
        
        # 确保行widget可见
        row_widget.setVisible(True)
        
        # 将整行widget添加到参数布局中
        self.input_params_layout.addWidget(row_widget)
        
        # 保存输入框引用
        self.param_widgets[param_name] = edit
        
        # 强制更新布局
        self.input_params_widget.update()
        self.input_params_widget.repaint()
        
        return edit
    
    def _show_ref_menu(self, target_edit: QLineEdit):
        """显示引用菜单"""
        menu = QMenu(self)
        has_any = False
        
        # 遍历所有步骤，收集可引用的键
        for i, step in enumerate(self.all_steps):
            if not isinstance(step, StepObject):
                continue
            
            # 获取步骤标题
            if step.type == 'function':
                title = f"{step.module}.{step.function}"
            else:
                title = step.control
            
            # 收集键：优先输出，然后参数
            keys = []
            for k in step.outputs.keys():
                keys.append((k, 'out'))
            for k in step.params.keys():
                if k not in step.outputs:
                    keys.append((k, 'param'))
            
            # 添加预测的返回值名称
            if step.type == 'function' and self.test_loader:
                preds = self.test_loader.get_return_names(step.module, step.function)
                for k in preds:
                    if not any(k == ex for ex, _ in keys):
                        keys.append((k, 'pred'))
            
            if not keys:
                continue
            
            for key, kind in keys:
                suffix = ' (out)' if kind in ('out', 'pred') else ''
                action_text = f"#{i+1} {title} :: {key}{suffix}"
                act = menu.addAction(action_text)
                
                if kind == 'pred':
                    act.setToolTip('预测输出（未运行）：运行后会填充真实值')
                
                # 创建闭包以捕获正确的值
                def make_handler(step_index, k):
                    return lambda: target_edit.insert(f"${{{'#'}{step_index}:{k}}}")
                
                act.triggered.connect(make_handler(i+1, key))
                has_any = True
        
        if not has_any:
            a = menu.addAction("无可用引用")
            a.setEnabled(False)
        
        menu.exec(ref_btn.mapToGlobal(ref_btn.rect().bottomLeft()) 
                 if hasattr(self, 'ref_btn') else self.mapToGlobal(self.rect().center()))
    
    def _on_param_changed(self, param_name: str, value: str):
        """参数值改变"""
        if self.current_step:
            self.current_step.params[param_name] = value
            self.paramChanged.emit(param_name, value)
    
    def clear_params(self):
        """清除所有参数输入框"""
        # 遍历并移除所有子部件
        while self.input_params_layout.count() > 0:
            item = self.input_params_layout.takeAt(0)
            widget = item.widget()
            
            if widget:
                # 如果是widget，直接删除
                widget.deleteLater()
            elif item.layout():
                # 如果是layout，删除其中的所有widget
                layout = item.layout()
                while layout.count() > 0:
                    sub_item = layout.takeAt(0)
                    sub_widget = sub_item.widget()
                    if sub_widget:
                        sub_widget.deleteLater()
                # 删除layout本身
                layout.deleteLater()
        
        # 清空参数映射
        self.param_widgets.clear()
        
        # 重置输出参数标签
        self.output_params_label.setText("-")
        
        # 强制更新布局
        self.input_params_widget.update()
        self.input_params_widget.repaint()
        self.updateGeometry()
