'''
Author: mike niemike@outlook.com
Date: 2025-11-11 23:52:12
LastEditors: mike niemike@outlook.com
LastEditTime: 2025-11-11 23:52:29
FilePath: \teststand_like\teststand_like\widgets\draggable_tree.py
Description: 这是默认设置,请设置`customMade`, 打开koroFileHeader查看配置 进行设置: https://github.com/OBKoro1/koro1FileHeader/wiki/%E9%85%8D%E7%BD%AE
'''
"""
可拖拽的函数树控件
"""
from PyQt6.QtWidgets import QTreeWidget, QTreeWidgetItem, QApplication
from PyQt6.QtCore import Qt, QMimeData, QByteArray, QIODevice, QPoint
from PyQt6.QtGui import QDrag
import sys

# 定义MIME类型
MIME_TYPE = "application/x-test-item"


class DraggableTreeWidget(QTreeWidget):
    """可拖拽的函数列表树"""
    
    def __init__(self):
        super().__init__()
        self.setDragEnabled(True)
        self.setHeaderLabel("测试函数")
        self.drag_start_position = QPoint(0, 0)
    
    def mousePressEvent(self, event):
        """鼠标按下事件"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_start_position = event.position().toPoint()
        super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event):
        """鼠标移动事件 - 启动拖拽"""
        if not (event.buttons() & Qt.MouseButton.LeftButton):
            return
        if (event.position().toPoint() - self.drag_start_position).manhattanLength() < QApplication.startDragDistance():
            return
        
        drag = QDrag(self)
        mime_data = QMimeData()
        
        # 获取当前选中项
        current_item = self.currentItem()
        if current_item and current_item.parent():  # 确保是函数而不是模块
            # 创建自定义数据格式
            item_data = QByteArray()
            data_stream = QIODevice.WriteOnly if hasattr(QIODevice, 'WriteOnly') else QIODevice.OpenModeFlag.WriteOnly
            
            # 兼容不同PyQt6版本
            try:
                from PyQt6.QtCore import QDataStream
                stream = QDataStream(item_data, QIODevice.OpenModeFlag.WriteOnly)
            except:
                from PyQt6.QtCore import QDataStream
                stream = QDataStream(item_data, QIODevice.WriteOnly)
            
            stream.writeString(current_item.text(0).encode('utf-8'))
            stream.writeString(current_item.parent().text(0).encode('utf-8'))
            
            mime_data.setData(MIME_TYPE, item_data)
            drag.setMimeData(mime_data)
            
            drag.exec(Qt.DropAction.CopyAction)
    
    def populate_from_loader(self, test_loader):
        """从TestLoader填充树"""
        self.clear()
        
        # 添加测试模块和函数
        for module_name in test_loader.get_all_modules():
            module_item = QTreeWidgetItem([module_name])
            self.addTopLevelItem(module_item)
            
            for func_name in test_loader.get_module_functions(module_name):
                func_item = QTreeWidgetItem([func_name])
                module_item.addChild(func_item)
        
        # 添加流程控制分类
        control_item = QTreeWidgetItem(["流程控制"])
        for ctrl in ["if", "for", "end", "break"]:
            child = QTreeWidgetItem([ctrl])
            control_item.addChild(child)
        self.addTopLevelItem(control_item)
        
        self.expandAll()
