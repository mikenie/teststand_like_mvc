'''
Author: mike niemike@outlook.com
Date: 2025-11-11 23:49:50
LastEditors: mike niemike@outlook.com
LastEditTime: 2025-11-11 23:50:07
FilePath: \teststand_like\teststand_like\core\step_model.py
Description: 这是默认设置,请设置`customMade`, 打开koroFileHeader查看配置 进行设置: https://github.com/OBKoro1/koro1FileHeader/wiki/%E9%85%8D%E7%BD%AE
'''
"""
测试步骤数据模型
定义步骤对象和相关数据结构
"""
import uuid


class StepObject:
    """代表测试序列中的一个步骤。
    
    每个步骤持有自己的参数状态，避免多个步骤共享参数。
    
    Attributes:
        id: 唯一标识符
        type: 步骤类型 ('function' 或 'control')
        module: 模块名（对于函数步骤）
        function: 函数名（对于函数步骤）
        control: 控制类型 ('if', 'for', 'end', 'break' 等)
        params: 参数字典 {参数名: 字符串值}
        outputs: 输出字典 {输出名: 值}
    """
    def __init__(self, type_, module=None, function=None, control=None):
        self.id = str(uuid.uuid4())
        self.type = type_
        self.module = module
        self.function = function
        self.control = control
        self.params = {}
        self.outputs = {}
    
    def __repr__(self):
        if self.type == 'function':
            return f"StepObject(function={self.module}.{self.function})"
        else:
            return f"StepObject(control={self.control})"


class BreakLoop(Exception):
    """内部异常，用于跳出最近的for循环。
    
    携带内部块消耗的动作数，以便调用者在单步运行时正确累积动作计数。
    
    Attributes:
        actions: 消耗的动作数
        runtime_vars: 运行时变量字典
    """
    def __init__(self, actions=0, runtime_vars=None):
        super().__init__()
        self.actions = actions
        self.runtime_vars = runtime_vars
