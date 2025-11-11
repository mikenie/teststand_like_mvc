"""
测试序列运行器 - 重构版本（UI分离架构）
"""
import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow, QSplitter, QVBoxLayout, 
                             QWidget, QPushButton, QTextEdit, QHBoxLayout, QLabel)
from PyQt6.QtCore import Qt

# 导入UI组件
from widgets import DraggableTreeWidget, DroppableListWidget, ParamEditor, WatcherWidget

# 导入控制器
from controllers import TestController


class MainWindow(QMainWindow):
    """主窗口 - 仅负责UI布局"""
    
    def __init__(self):
        super().__init__()
        self.controller = TestController()
        self.init_ui()
        self.create_menu_bar()
        
        # 初始化加载测试函数
        self.controller.load_test_functions()
    
    def init_ui(self):
        """初始化UI布局"""
        self.setWindowTitle("测试序列运行器 - 重构版")
        self.setGeometry(100, 100, 1200, 700)
        
        # 创建主分割器
        main_splitter = QSplitter(Qt.Orientation.Horizontal)
        self.setCentralWidget(main_splitter)
        
        # === 左侧区域：函数树 ===
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(0)
        
        self.function_tree = DraggableTreeWidget()
        left_layout.addWidget(self.function_tree)
        
        # === 右侧区域：序列+监视器 ===
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)
        
        # 创建序列区和监视器的水平分割
        seq_watcher_splitter = QSplitter(Qt.Orientation.Horizontal)
        seq_watcher_splitter.setHandleWidth(1)
        
        # --- 序列区域（左） ---
        seq_area = QWidget()
        seq_layout = QVBoxLayout(seq_area)
        seq_layout.setContentsMargins(0, 0, 0, 0)
        seq_layout.setSpacing(0)
        
        # 控制按钮栏
        control_bar = QHBoxLayout()
        self.load_button = QPushButton("加载测试函数")
        self.run_button = QPushButton("运行测试序列")
        self.step_button = QPushButton("单步运行")
        self.reset_button = QPushButton("重置执行")
        self.clear_button = QPushButton("清空序列")
        
        control_bar.addWidget(self.load_button)
        control_bar.addWidget(self.run_button)
        control_bar.addWidget(self.step_button)
        control_bar.addWidget(self.reset_button)
        control_bar.addWidget(self.clear_button)
        seq_layout.addLayout(control_bar)
        
        # 测试序列列表
        self.sequence_list = DroppableListWidget()
        seq_layout.addWidget(self.sequence_list)
        
        # 步骤设置区域（参数编辑器）
        self.param_editor = ParamEditor()
        seq_layout.addWidget(self.param_editor)
        
        # 输出区域
        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)
        seq_layout.addWidget(self.output_text)
        
        seq_watcher_splitter.addWidget(seq_area)
        
        # --- 监视器区域（右） ---
        watcher_widget = QWidget()
        watcher_layout = QVBoxLayout(watcher_widget)
        watcher_layout.setContentsMargins(0, 0, 0, 0)
        watcher_layout.addWidget(QLabel("变量监视器"))
        
        self.watcher = WatcherWidget()
        watcher_layout.addWidget(self.watcher)
        
        seq_watcher_splitter.addWidget(watcher_widget)
        
        # 设置默认比例
        seq_watcher_splitter.setSizes([700, 300])
        
        right_layout.addWidget(seq_watcher_splitter)
        
        # === 添加到主分割器 ===
        main_splitter.addWidget(left_widget)
        main_splitter.addWidget(right_widget)
        main_splitter.setHandleWidth(1)
        main_splitter.setSizes([300, 900])
        
        # === 设置控制器的UI组件 ===
        self.controller.set_ui_components(
            function_tree=self.function_tree,
            sequence_list=self.sequence_list,
            param_editor=self.param_editor,
            watcher_widget=self.watcher,
            output_text=self.output_text
        )
        
        # === 连接按钮信号到控制器 ===
        self.load_button.clicked.connect(lambda: self.controller.load_test_functions())
        self.run_button.clicked.connect(lambda: self.controller.run_sequence())
        self.step_button.clicked.connect(lambda: self.controller.step_run())
        self.reset_button.clicked.connect(lambda: self.controller.reset_execution())
        self.clear_button.clicked.connect(lambda: self.controller.clear_sequence())
    
    def create_menu_bar(self):
        """创建菜单栏"""
        menu_bar = self.menuBar()
        
        # File 菜单
        file_menu = menu_bar.addMenu('File')
        load_action = file_menu.addAction('Load Test Functions')
        load_action.triggered.connect(self.controller.load_test_functions)
        
        clear_action = file_menu.addAction('Clear Sequence')
        clear_action.triggered.connect(self.controller.clear_sequence)
        
        file_menu.addSeparator()
        exit_action = file_menu.addAction('Exit')
        exit_action.triggered.connect(self.close)
        
        # Edit 菜单
        edit_menu = menu_bar.addMenu('Edit')
        
        # View 菜单
        view_menu = menu_bar.addMenu('View')
        
        # Execute 菜单
        execute_menu = menu_bar.addMenu('Execute')
        run_action = execute_menu.addAction('Run Test Sequence')
        run_action.triggered.connect(self.controller.run_sequence)
        
        step_action = execute_menu.addAction('Step Run')
        step_action.triggered.connect(self.controller.step_run)
        
        reset_action = execute_menu.addAction('Reset Execution')
        reset_action.triggered.connect(self.controller.reset_execution)
        
        # Debug 菜单
        debug_menu = menu_bar.addMenu('Debug')
        
        # Configure 菜单
        config_menu = menu_bar.addMenu('Configure')
        
        # Tools 菜单
        tools_menu = menu_bar.addMenu('Tools')
        
        # Window 和 Help 菜单
        window_menu = menu_bar.addMenu('Window')
        help_menu = menu_bar.addMenu('Help')


def main():
    """主函数"""
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
