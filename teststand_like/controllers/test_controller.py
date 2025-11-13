"""
测试控制器
协调UI和测试引擎之间的交互
"""
import json
import os
from PyQt6.QtWidgets import QApplication, QFileDialog
from PyQt6.QtGui import QIcon, QPixmap, QPainter, QColor
from PyQt6.QtCore import Qt
from core import TestLoader, TestEngine, ConfigManager


class TestController:
    """测试控制器
    
    协调UI组件和测试引擎，处理用户交互并更新界面显示
    """
    
    def __init__(self):
        self.test_loader = TestLoader()
        self.test_engine = TestEngine(self.test_loader)
        self.config_manager = ConfigManager()
        
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
        
        # 初始化监视器
        if self.watcher_widget:
            self.watcher_widget.update_watcher({})
        
        # 设置引擎回调
        self.test_engine.set_callbacks(
            output_cb=self._on_engine_output,
            watcher_cb=self._on_engine_watcher_update,
            status_cb=self._on_engine_status_update
        )
        
        # 连接序列列表的信号
        if self.sequence_list:
            self.sequence_list.itemMoved.connect(self._on_sequence_changed)
            self.sequence_list.currentItemChanged.connect(self._on_item_selection_changed_wrapper)
    
    def load_test_functions(self, directory=None):
        """加载测试函数
        
        Args:
            directory: 测试函数所在目录，None表示使用默认值'Testcase'
        """
        if directory is None or isinstance(directory, bool):
            directory = self.config_manager.get("test_directory", "Testcase")
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
    
    def clear_sequence(self):
        """清空测试序列"""
        if self.sequence_list:
            self.sequence_list.clear_all_steps()
        
        if self.param_editor:
            self.param_editor.clear_params()
        
        if self.watcher_widget:
            # 确保清除监视器显示
            self.watcher_widget.set_all_steps([])
            self.watcher_widget.update_watcher({})
        
        if self.output_text:
            self.output_text.clear()
        
        # 重置执行状态
        self.test_engine.exec_state = None
    
    def reset_execution(self):
        """重置执行状态"""
        steps = self.sequence_list.get_all_steps() if self.sequence_list else []
        self.test_engine.set_steps(steps)
        self.test_engine.reset_execution()
        
        # 清除状态图标
        self._clear_all_status_icons()
        
        # 重置执行标记
        self._mark_execution_index(0)
        
        # 更新监视器显示
        if self.watcher_widget:
            self.watcher_widget.update_watcher({})
    
    def save_sequence(self, file_path=None):
        """保存测试序列到文件
        
        Args:
            file_path: 保存文件路径，如果为None则弹出文件选择对话框
        """
        if not self.sequence_list:
            self._output("序列列表未初始化")
            return False
            
        steps = self.sequence_list.get_all_steps()
        if not steps:
            self._output("序列为空，无需保存")
            return False
            
        # 如果没有提供文件路径，则弹出文件选择对话框
        if not file_path:
            file_path, _ = QFileDialog.getSaveFileName(
                None, "保存测试序列", "", "JSON Files (*.json);;All Files (*)"
            )
            if not file_path:
                return False
        
        try:
            # 序列化步骤
            sequence_data = []
            for step in steps:
                step_data = {
                    'id': step.id,
                    'type': step.type,
                    'module': step.module,
                    'function': step.function,
                    'control': step.control,
                    'params': step.params,
                    'outputs': step.outputs
                }
                sequence_data.append(step_data)
            
            # 保存到文件
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(sequence_data, f, ensure_ascii=False, indent=2)
            
            # 更新配置中的最后序列文件路径
            self.config_manager.set_last_sequence_file(file_path)
            self.config_manager.save_config()
            
            self._output(f"测试序列已保存到: {file_path}")
            return True
        except Exception as e:
            self._output(f"保存序列失败: {str(e)}")
            return False
    
    def load_sequence(self, file_path=None):
        """从文件加载测试序列
        
        Args:
            file_path: 加载文件路径，如果为None则弹出文件选择对话框
        """
        # 如果没有提供文件路径，则弹出文件选择对话框
        if not file_path:
            file_path, _ = QFileDialog.getOpenFileName(
                None, "加载测试序列", "", "JSON Files (*.json);;All Files (*)"
            )
            if not file_path:
                return False
        
        if not os.path.exists(file_path):
            self._output(f"文件不存在: {file_path}")
            return False
            
        try:
            # 从文件读取数据
            with open(file_path, 'r', encoding='utf-8') as f:
                sequence_data = json.load(f)
            
            # 清空当前序列
            self.clear_sequence()
            
            # 反序列化步骤并添加到列表
            for step_data in sequence_data:
                # 创建步骤对象
                step = StepObject(
                    type_=step_data['type'],
                    module=step_data.get('module'),
                    function=step_data.get('function'),
                    control=step_data.get('control')
                )
                
                # 恢复参数和输出
                step.params = step_data.get('params', {})
                step.outputs = step_data.get('outputs', {})
                step.id = step_data.get('id', step.id)  # 尽可能保持原有ID
                
                # 创建列表项
                if step.type == 'function':
                    display_text = f"{step.module}.{step.function}"
                else:
                    display_text = step.control
                
                from PyQt6.QtWidgets import QListWidgetItem
                item = QListWidgetItem(display_text)
                item.setData(Qt.ItemDataRole.UserRole, step)
                item.setData(Qt.ItemDataRole.UserRole + 1, step.id)
                
                # 添加到序列列表
                self.sequence_list.addItem(item)
            
            # 更新配置中的最后序列文件路径
            self.config_manager.set_last_sequence_file(file_path)
            self.config_manager.save_config()
            
            self._output(f"测试序列已从 {file_path} 加载")
            self._on_sequence_changed()  # 触发序列变更处理
            return True
        except Exception as e:
            self._output(f"加载序列失败: {str(e)}")
            return False
    
    def _on_sequence_changed(self):
        """序列改变时的处理"""
        # 更新参数编辑器和监视器的步骤引用
        steps = self.sequence_list.get_all_steps() if self.sequence_list else []
        
        if self.param_editor:
            self.param_editor.set_all_steps(steps)
        
        if self.watcher_widget:
            self.watcher_widget.set_all_steps(steps)
            # 重要：更新监视器显示，而不仅仅是在清空时更新
            self.watcher_widget.update_watcher({})
        
        # 更新输出显示
        self._update_sequence_display()
    
    def _on_engine_watcher_update(self, runtime_vars: dict):
        """引擎监视器更新回调"""
        if self.watcher_widget:
            self.watcher_widget.update_watcher(runtime_vars)
            QApplication.processEvents()
    
    def _on_engine_output(self, message: str):
        """引擎输出回调"""
        if self.output_text:
            self.output_text.append(message)
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
    
    def _on_item_selection_changed_wrapper(self):
        """序列项选择改变时的处理包装器（用于itemSelectionChanged信号）"""
        if not self.sequence_list:
            return
            
        current = self.sequence_list.currentItem()
        # 注意：这里我们没有previous项的引用，所以传递None
        self._on_item_selection_changed(current, None)
    
    def _on_item_selection_changed(self, current, previous):
        """序列项选择改变时的处理"""
        if not current or not self.param_editor:
            if self.param_editor:
                self.param_editor.clear_params()
            return
        
        # 获取步骤对象和索引
        step = current.data(Qt.ItemDataRole.UserRole)
        index = self.sequence_list.row(current) if self.sequence_list else -1
        
        # 验证步骤对象的有效性
        if not step:
            self.param_editor.clear_params()
            return
            
        # 确保参数编辑器的test_loader已设置
        if not self.param_editor.test_loader and self.test_loader:
            self.param_editor.set_test_loader(self.test_loader)
            
        # 确保参数编辑器有所有步骤的引用
        if self.param_editor and self.sequence_list:
            steps = self.sequence_list.get_all_steps()
            self.param_editor.set_all_steps(steps)
        
        # 加载到参数编辑器
        self.param_editor.load_step(step, index)
    
    def update_watcher_display(self):
        """主动更新监视器显示"""
        if self.watcher_widget:
            steps = self.sequence_list.get_all_steps() if self.sequence_list else []
            self.watcher_widget.set_all_steps(steps)
            self.watcher_widget.update_watcher({})
    
    def _output(self, message: str):
        """输出消息到输出框"""
        if self.output_text:
            self.output_text.append(message)
    
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
    
    def _clear_all_status_icons(self):
        """清除所有状态图标"""
        if not self.sequence_list:
            return
        
        for i in range(self.sequence_list.count()):
            item = self.sequence_list.item(i)
            if item:
                item.setIcon(QIcon())

# 导入StepObject以确保在load_sequence中可用
from core.step_model import StepObject