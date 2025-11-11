"""
可接收拖拽的序列列表控件
"""
from PyQt6.QtWidgets import QListWidget, QListWidgetItem, QAbstractItemView
from PyQt6.QtCore import Qt, QMimeData, QByteArray, QIODevice, pyqtSignal
from PyQt6.QtCore import QDataStream
from core.step_model import StepObject

# 定义MIME类型（需要与draggable_tree.py中一致）
MIME_TYPE = "application/x-test-item"


class DroppableListWidget(QListWidget):
    """可接收拖拽的测试序列列表"""
    
    itemMoved = pyqtSignal()  # 当项被移动或添加时发出信号
    
    def __init__(self):
        super().__init__()
        self.setAcceptDrops(True)
        self.setDragEnabled(True)
        self.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
        self.setDefaultDropAction(Qt.DropAction.MoveAction)
    
    def dragEnterEvent(self, event):
        """拖拽进入事件"""
        if event.mimeData().hasFormat(MIME_TYPE) or event.mimeData().hasText():
            event.acceptProposedAction()
        else:
            super().dragEnterEvent(event)
    
    def dragMoveEvent(self, event):
        """拖拽移动事件"""
        if event.mimeData().hasFormat(MIME_TYPE) or event.mimeData().hasText():
            event.acceptProposedAction()
        else:
            super().dragMoveEvent(event)
    
    def dropEvent(self, event):
        """放置事件"""
        if event.mimeData().hasFormat(MIME_TYPE):
            item_data = event.mimeData().data(MIME_TYPE)
            
            try:
                data_stream = QDataStream(item_data, QIODevice.OpenModeFlag.ReadOnly)
            except:
                data_stream = QDataStream(item_data, QIODevice.ReadOnly)
            
            func_name = bytes(data_stream.readString()).decode('utf-8')
            module_name = bytes(data_stream.readString()).decode('utf-8')
            
            # 如果来自流程控制分类，创建控制步骤
            if module_name == "流程控制":
                item = QListWidgetItem(func_name)
                step = StepObject(type_="control", control=func_name)
            else:
                item = QListWidgetItem(f"{module_name}.{func_name}")
                step = StepObject(type_="function", module=module_name, function=func_name)
            
            item.setData(Qt.ItemDataRole.UserRole, step)
            item.setData(Qt.ItemDataRole.UserRole + 1, step.id)
            self.addItem(item)
            event.acceptProposedAction()
            self.itemMoved.emit()
        
        elif event.mimeData().hasText():
            text = event.mimeData().text()
            if text in ["if", "for", "end", "break"]:
                item = QListWidgetItem(text)
                step = StepObject(type_="control", control=text)
                item.setData(Qt.ItemDataRole.UserRole, step)
                item.setData(Qt.ItemDataRole.UserRole + 1, step.id)
                self.addItem(item)
                event.acceptProposedAction()
                self.itemMoved.emit()
        else:
            super().dropEvent(event)
            self.itemMoved.emit()
    
    def keyPressEvent(self, event):
        """键盘事件 - 支持Delete键删除选中项"""
        if event.key() == Qt.Key.Key_Delete and self.currentItem():
            row = self.currentRow()
            item = self.takeItem(row)
            del item
            self.itemMoved.emit()
        else:
            super().keyPressEvent(event)
    
    def get_all_steps(self):
        """获取所有步骤对象"""
        steps = []
        for i in range(self.count()):
            item = self.item(i)
            step = item.data(Qt.ItemDataRole.UserRole)
            if isinstance(step, StepObject):
                steps.append(step)
        return steps
    
    def clear_all_steps(self):
        """清空所有步骤"""
        # 先清除步骤对象的数据
        for i in range(self.count()):
            item = self.item(i)
            step = item.data(Qt.ItemDataRole.UserRole)
            if isinstance(step, StepObject):
                step.params.clear()
                step.outputs.clear()
        
        # 清空列表
        self.clear()
        self.itemMoved.emit()
    
    def update_item_display(self, index, text):
        """更新指定索引项的显示文本
        
        Args:
            index: 项索引
            text: 新的显示文本
        """
        if 0 <= index < self.count():
            item = self.item(index)
            item.setText(text)
