'''
Author: mike niemike@outlook.com
Date: 2025-11-11 23:54:00
LastEditors: mike niemike@outlook.com
LastEditTime: 2025-11-11 23:54:16
FilePath: \teststand_like\teststand_like\widgets\watcher_widget.py
Description: 这是默认设置,请设置`customMade`, 打开koroFileHeader查看配置 进行设置: https://github.com/OBKoro1/koro1FileHeader/wiki/%E9%85%8D%E7%BD%AE
'''
"""
变量监视器控件
"""
from PyQt6.QtWidgets import QTreeWidget, QTreeWidgetItem
from core.step_model import StepObject


class WatcherWidget(QTreeWidget):
    """变量监视器
    
    显示测试序列中各步骤的输入参数、输出结果和运行时变量
    """
    
    def __init__(self):
        super().__init__()
        self.setHeaderLabel("变量")
        self.all_steps = []
        # 添加初始提示信息，让用户知道监视器的功能
        self._show_initial_info()
    
    def _show_initial_info(self):
        """显示初始信息"""
        info_node = QTreeWidgetItem(["使用说明"])
        info_node.addChild(QTreeWidgetItem(["1. 添加测试步骤到序列"]))
        info_node.addChild(QTreeWidgetItem(["2. 运行测试查看变量状态"]))
        info_node.addChild(QTreeWidgetItem(["3. 监视输入参数和输出结果"]))
        self.addTopLevelItem(info_node)
        self.expandAll()
    
    def set_all_steps(self, steps):
        """设置所有步骤的引用"""
        self.all_steps = steps
        
    def update_watcher(self, runtime_vars=None):
        """更新监视器显示
            
        Args:
            runtime_vars: 运行时变量字典（如循环变量）
        """
        if runtime_vars is None:
            runtime_vars = {}
            
        self.clear()
            
        # 显示按序列步骤组织的变量
        for i, step in enumerate(self.all_steps):
            if not isinstance(step, StepObject):
                continue
                
            # 获取步骤标题
            if step.type == 'function':
                title = f"{step.module}.{step.function}" if step.module and step.function else "未知函数"
            else:
                title = step.control if step.control else "未知控制"
                
            # 创建步骤节点
            step_node = QTreeWidgetItem([f"步骤 {i+1}: {title}"])
                
            if step.type == 'function':
                # 函数步骤显示输入参数和输出结果
                if step.params:
                    inputs_node = QTreeWidgetItem(["输入参数"])
                    for k, v in step.params.items():
                        inputs_node.addChild(QTreeWidgetItem([f"{k}: {v}"]))
                    step_node.addChild(inputs_node)
                else:
                    inputs_node = QTreeWidgetItem(["输入参数"])
                    inputs_node.addChild(QTreeWidgetItem(["无参数"]))
                    step_node.addChild(inputs_node)
                    
                if step.outputs:
                    outputs_node = QTreeWidgetItem(["输出结果"])
                    for k, v in step.outputs.items():
                        outputs_node.addChild(QTreeWidgetItem([f"{k}: {v}"]))
                    step_node.addChild(outputs_node)
                else:
                    outputs_node = QTreeWidgetItem(["输出结果"])
                    outputs_node.addChild(QTreeWidgetItem(["无输出"]))
                    step_node.addChild(outputs_node)
                
            elif step.type == 'control':
                # 控制步骤显示特定参数
                if step.control == 'if':
                    ctrl_node = QTreeWidgetItem(["条件"])
                    condition = step.params.get('condition', '')
                    ctrl_node.addChild(QTreeWidgetItem([f"表达式: {condition}"]))
                    step_node.addChild(ctrl_node)
                    
                elif step.control == 'for':
                    ctrl_node = QTreeWidgetItem(["循环"])
                    iterable = step.params.get('iterable', '')
                    varname = step.params.get('var', '_loop')
                    ctrl_node.addChild(QTreeWidgetItem([f"迭代对象: {iterable}"]))
                    ctrl_node.addChild(QTreeWidgetItem([f"循环变量: {varname}"]))
                    step_node.addChild(ctrl_node)
                    
                elif step.control in ['end', 'break']:
                    ctrl_node = QTreeWidgetItem(["控制语句"])
                    ctrl_node.addChild(QTreeWidgetItem([f"类型: {step.control}"]))
                    step_node.addChild(ctrl_node)
                
            self.addTopLevelItem(step_node)
            
        # 运行时变量（如循环变量）
        if runtime_vars:
            runtime_node = QTreeWidgetItem(["运行时变量"])
            for k, v in runtime_vars.items():
                runtime_node.addChild(QTreeWidgetItem([f"{k}: {v}"]))
            self.addTopLevelItem(runtime_node)
        else:
            # 如果没有运行时变量，添加提示信息
            if self.all_steps:  # 只有在有步骤时才显示此提示
                runtime_node = QTreeWidgetItem(["运行时变量"])
                runtime_node.addChild(QTreeWidgetItem(["暂无运行时变量"]))
                self.addTopLevelItem(runtime_node)
            else:
                # 没有步骤时显示初始信息
                self._show_initial_info()
            
        # 展开所有节点
        self.expandAll()