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
        
        func = self.test_loader.get_function(step.module, step.function)
        if not func:
            self.add_param_row("error", "函数未找到", read_only=True)
            return
        
        try:
            sig = inspect.signature(func)
            params = list(sig.parameters.keys())
            
            for param_name in params:
                cached_value = step.params.get(param_name, "")
                edit = self.add_param_row(param_name, cached_value)
                # 连接信号
                edit.textChanged.connect(
                    lambda val, pn=param_name: self._on_param_changed(pn, val)
                )
            
            # 显示输出参数
            return_annotation = sig.return_annotation
            if return_annotation != inspect.Signature.empty:
                if hasattr(return_annotation, '__name__'):
                    output_name = return_annotation.__name__
                else:
                    output_name = str(return_annotation)
                self.output_params_label.setText(output_name)
            else:
                self.output_params_label.setText("未知（无类型注解）")
        
        except Exception as e:
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
        row_layout = QHBoxLayout()
        row_layout.setSpacing(0)
        row_layout.setContentsMargins(0, 0, 0, 0)
        
        label = QLabel(f"{param_name}:")
        label.setFixedWidth(100)
        edit = QLineEdit(str(default_value))
        edit.setReadOnly(read_only)
        
        row_layout.addWidget(label)
        row_layout.addWidget(edit)
        
        # 引用按钮
        ref_btn = QPushButton("引用")
        ref_btn.setToolTip("插入对前一步骤输出/参数的引用")
        ref_btn.setFixedWidth(48)
        ref_btn.clicked.connect(lambda: self._show_ref_menu(edit))
        row_layout.addWidget(ref_btn)
        
        self.input_params_layout.addLayout(row_layout)
        self.param_widgets[param_name] = edit
        
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
        while self.input_params_layout.count():
            child = self.input_params_layout.takeAt(0)
            if child.layout():
                while child.layout().count():
                    widget = child.layout().takeAt(0).widget()
                    if widget:
                        widget.deleteLater()
        
        self.param_widgets.clear()
        self.output_params_label.setText("-")
