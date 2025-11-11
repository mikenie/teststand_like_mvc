"""
测试控制器
协调UI和测试引擎之间的交互
"""
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QIcon, QPixmap, QPainter, QColor
from PyQt6.QtCore import Qt
from core import TestLoader, TestEngine


class TestController:
    """测试控制器
    
    协调UI组件和测试引擎，处理用户交互并更新界面显示
    """
    
    def __init__(self):
        self.test_loader = TestLoader()
        self.test_engine = TestEngine(self.test_loader)
        
        # UI组件引用（将由主窗口设置）
        self.function_tree = None
        self.sequence_list = None
        self.param_editor = None
        self.watcher_widget = None
        self.output_text = None
        
        # 状态图标
        self.icon_pass = None
        self.icon_fail = None
        self._init_status_icons()
    
    def _init_status_icons(self):
        """创建PASS/FAIL状态图标"""
        def make_icon(color_name):
            size = 16
            pix = QPixmap(size, size)
            try:
                pix.fill(Qt.GlobalColor.transparent)
            except Exception:
                pix.fill(QColor(0, 0, 0, 0))
            p = QPainter(pix)
            p.setRenderHint(QPainter.RenderHint.Antialiasing)
            col = QColor(color_name)
            p.setBrush(col)
            p.setPen(QColor(0, 0, 0, 0))
            p.drawEllipse(1, 1, size-3, size-3)
            p.end()
            return QIcon(pix)
        
        self.icon_pass = make_icon('#2ecc71')  # 绿色
        self.icon_fail = make_icon('#e74c3c')  # 红色
    
    def set_ui_components(self, function_tree, sequence_list, param_editor, 
                         watcher_widget, output_text):
        """设置UI组件引用
        
        Args:
            function_tree: 函数树控件
            sequence_list: 序列列表控件
            param_editor: 参数编辑器
            watcher_widget: 监视器控件
            output_text: 输出文本框
        """
        self.function_tree = function_tree
        self.sequence_list = sequence_list
        self.param_editor = param_editor
        self.watcher_widget = watcher_widget
        self.output_text = output_text
        
        # 设置参数编辑器的测试加载器
        if self.param_editor:
            self.param_editor.set_test_loader(self.test_loader)
        
        # 设置引擎回调
        self.test_engine.set_callbacks(
            output_cb=self._on_engine_output,
            watcher_cb=self._on_engine_watcher_update,
            status_cb=self._on_engine_status_update
        )
        
        # 连接序列列表的信号
        if self.sequence_list:
            self.sequence_list.itemMoved.connect(self._on_sequence_changed)
            self.sequence_list.currentItemChanged.connect(self._on_item_selection_changed)
    
    def load_test_functions(self, directory=None):
        """加载测试函数
        
        Args:
            directory: 测试函数所在目录，None表示使用默认值'Testcase'
        """
        if directory is None or isinstance(directory, bool):
            directory = 'Testcase'
        self.test_loader.load_from_directory(directory)
        
        # 更新函数树
        if self.function_tree:
            self.function_tree.populate_from_loader(self.test_loader)
        
        self._output("测试函数已加载")
    
    def run_sequence(self):
        """运行整个测试序列"""
        steps = self.sequence_list.get_all_steps() if self.sequence_list else []
        if not steps:
            self._output("序列为空，无法执行")
            return
        
        # 清除旧的状态图标
        self._clear_all_status_icons()
        
        self.test_engine.set_steps(steps)
        self.test_engine.run_all()
    
    def step_run(self):
        """单步执行"""
        steps = self.sequence_list.get_all_steps() if self.sequence_list else []
        if not steps:
            self._output("序列为空，无法执行")
            return
        
        self.test_engine.set_steps(steps)
        self.test_engine.step_run()
        
        # 更新执行标记
        exec_index = self.test_engine.get_execution_index()
        self._mark_execution_index(exec_index)
    
    def reset_execution(self):
        """重置执行状态"""
        steps = self.sequence_list.get_all_steps() if self.sequence_list else []
        self.test_engine.set_steps(steps)
        self.test_engine.reset_execution()
        
        # 清除状态图标
        self._clear_all_status_icons()
        
        # 重置执行标记
        self._mark_execution_index(0)
    
    def clear_sequence(self):
        """清空测试序列"""
        if self.sequence_list:
            self.sequence_list.clear_all_steps()
        
        if self.param_editor:
            self.param_editor.clear_params()
        
        if self.watcher_widget:
            self.watcher_widget.update_watcher({})
        
        if self.output_text:
            self.output_text.clear()
        
        # 重置执行状态
        self.test_engine.exec_state = None
    
    def _on_sequence_changed(self):
        """序列改变时的处理"""
        # 更新参数编辑器和监视器的步骤引用
        steps = self.sequence_list.get_all_steps() if self.sequence_list else []
        
        if self.param_editor:
            self.param_editor.set_all_steps(steps)
        
        if self.watcher_widget:
            self.watcher_widget.set_all_steps(steps)
            self.watcher_widget.update_watcher({})
        
        # 更新输出显示
        self._update_sequence_display()
    
    def _on_item_selection_changed(self, current, previous):
        """序列项选择改变时的处理"""
        if not current or not self.param_editor:
            if self.param_editor:
                self.param_editor.clear_params()
            return
        
        # 获取步骤对象和索引
        step = current.data(Qt.ItemDataRole.UserRole)
        index = self.sequence_list.row(current) if self.sequence_list else -1
        
        # 加载到参数编辑器
        self.param_editor.load_step(step, index)
    
    def _on_engine_output(self, message: str):
        """引擎输出回调"""
        if self.output_text:
            self.output_text.append(message)
            QApplication.processEvents()
    
    def _on_engine_watcher_update(self, runtime_vars: dict):
        """引擎监视器更新回调"""
        if self.watcher_widget:
            self.watcher_widget.update_watcher(runtime_vars)
            QApplication.processEvents()
    
    def _on_engine_status_update(self, step_index: int, success: bool):
        """引擎状态更新回调"""
        if not self.sequence_list or step_index < 0:
            return
        
        if step_index >= self.sequence_list.count():
            return
        
        item = self.sequence_list.item(step_index)
        if item:
            icon = self.icon_pass if success else self.icon_fail
            item.setIcon(icon)
            QApplication.processEvents()
    
    def _clear_all_status_icons(self):
        """清除所有状态图标"""
        if not self.sequence_list:
            return
        
        for i in range(self.sequence_list.count()):
            item = self.sequence_list.item(i)
            if item:
                item.setIcon(QIcon())
    
    def _mark_execution_index(self, index):
        """标记当前执行索引
        
        Args:
            index: 要标记的索引，None表示清除所有标记
        """
        if not self.sequence_list:
            return
        
        steps = self.sequence_list.get_all_steps()
        
        for i in range(self.sequence_list.count()):
            item = self.sequence_list.item(i)
            if i < len(steps):
                step = steps[i]
                # 构建基础标签
                if step.type == 'function':
                    base = f"{step.module}.{step.function}"
                else:
                    base = step.control
                
                display = f"{i+1}. {base}"
                if index is not None and i == index:
                    display = f"{display}  <-"
                
                item.setText(display)
    
    def _update_sequence_display(self):
        """更新序列显示"""
        if not self.output_text or not self.sequence_list:
            return
        
        sequence_text = "当前测试序列:\n"
        steps = self.sequence_list.get_all_steps()
        
        for i, step in enumerate(steps):
            if step.type == 'function':
                text = f"{step.module}.{step.function}"
            else:
                text = step.control
            sequence_text += f"{i+1}. {text}\n"
        
        self.output_text.setText(sequence_text)
    
    def _output(self, message: str):
        """输出消息到输出框"""
        if self.output_text:
            self.output_text.append(message)
