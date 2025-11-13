"""
测试执行引擎
负责执行测试序列、处理控制流、管理变量
"""
import inspect
import re
from typing import List, Dict, Any, Tuple, Callable, Optional
from .step_model import StepObject, BreakLoop


class TestEngine:
    """测试执行引擎
    
    管理测试序列的执行，包括函数调用、控制流处理、变量管理等。
    """
    
    def __init__(self, test_loader):
        """初始化测试引擎
        
        Args:
            test_loader: TestLoader实例，用于获取测试函数
        """
        self.test_loader = test_loader
        self.steps: List[StepObject] = []
        self.exec_state = None  # 用于单步执行的状态
        self.output_callback: Optional[Callable[[str], None]] = None
        self.watcher_callback: Optional[Callable[[Dict], None]] = None
        self.status_callback: Optional[Callable[[int, bool], None]] = None
    
    def set_steps(self, steps: List[StepObject]):
        """设置要执行的步骤列表
        
        Args:
            steps: StepObject列表
        """
        self.steps = steps
    
    def set_callbacks(self, output_cb=None, watcher_cb=None, status_cb=None):
        """设置回调函数
        
        Args:
            output_cb: 输出回调 callback(message: str)
            watcher_cb: 监视器更新回调 callback(runtime_vars: dict)
            status_cb: 状态回调 callback(step_index: int, success: bool)
        """
        self.output_callback = output_cb
        self.watcher_callback = watcher_cb
        self.status_callback = status_cb
    
    def _output(self, message: str):
        """输出消息"""
        if self.output_callback:
            self.output_callback(message)
    
    def _update_watcher(self, runtime_vars: Dict):
        """更新监视器"""
        if self.watcher_callback:
            self.watcher_callback(runtime_vars)
    
    def _set_status(self, step_index: int, success: bool):
        """设置步骤状态"""
        if self.status_callback:
            self.status_callback(step_index, success)
    
    def run_all(self):
        """运行整个测试序列"""
        self._output("开始执行测试序列...\n")
        try:
            self._run_block(0, len(self.steps) - 1, {})
            self._output("测试序列执行完成。\n")
        except BreakLoop:
            self._output("遇到 break（未在循环内），已忽略。\n")
        except Exception as e:
            self._output(f"执行过程中发生错误: {str(e)}\n")
    
    def step_run(self):
        """执行单步（一个操作）"""
        if self.exec_state is None:
            self.exec_state = {'index': 0, 'vars': {}, 'loop_stack': []}
        
        start = self.exec_state['index']
        end = len(self.steps) - 1
        
        if start > end:
            self._output("已到序列末尾；请重置执行以重新开始。")
            return
        
        step = self.steps[start]
        
        # 处理for循环头
        if isinstance(step, StepObject) and step.type == 'control' and step.control == 'for':
            existing = None
            for e in self.exec_state.get('loop_stack', []):
                if e['start'] == start:
                    existing = e
                    break
            
            match = self._find_matching_end(start)
            iterable_raw = step.params.get('iterable', '')
            varname = step.params.get('var', '_loop')
            iterable_val = self.resolve_references(iterable_raw, dict(self.exec_state['vars']))
            
            if isinstance(iterable_val, int):
                iterator = list(range(iterable_val))
            elif isinstance(iterable_val, (list, tuple)):
                iterator = list(iterable_val)
            else:
                try:
                    iterator = list(self._safe_eval(str(iterable_val), dict(self.exec_state['vars'])))
                except Exception:
                    iterator = []
            
            if not iterator:
                ni = match + 1 if match != -1 else start + 1
                self.exec_state['index'] = ni
                self._output(f"单步执行: 空迭代对象，跳过 for-block，下一索引 {ni}")
                return
            
            if existing is None:
                entry = {'start': start, 'end': match, 'iterator': iterator, 'pos': 0, 'var': varname}
                self.exec_state.setdefault('loop_stack', []).append(entry)
            else:
                entry = existing
            
            new_vars = dict(self.exec_state['vars'])
            new_vars[varname] = entry['iterator'][entry['pos']]
            self.exec_state['vars'] = new_vars
            self.exec_state['index'] = start + 1 if match != -1 else start + 1
            self._output(f"进入 for: 设 {varname} = {entry['iterator'][entry['pos']]}，下一索引 {self.exec_state['index']}")
            return
        
        # 处理if语句
        if isinstance(step, StepObject) and step.type == 'control' and step.control == 'if':
            match = self._find_matching_end(start)
            cond_raw = step.params.get('condition', '')
            cond_val = self.resolve_references(cond_raw, dict(self.exec_state['vars']))
            cond_bool = cond_val if isinstance(cond_val, bool) else self._safe_eval(str(cond_val), dict(self.exec_state['vars']))
            
            self._output(f"IF condition ({cond_raw}) -> {cond_bool}")
            self._update_watcher(dict(self.exec_state['vars']))
            
            if cond_bool:
                # 条件为真，进入if块
                self.exec_state['index'] = start + 1
                self._output(f"条件为真，进入 if 块，下一索引 {self.exec_state['index']}")
            else:
                # 条件为假，跳过整个if块
                self.exec_state['index'] = match + 1 if match != -1 else start + 1
                self._output(f"条件为假，跳过 if 块，下一索引 {self.exec_state['index']}")
            return
            
        # 处理break语句
        if isinstance(step, StepObject) and step.type == 'control' and step.control == 'break':
            # 查找包含的循环
            enclosing = self._find_enclosing_loop(start)
            if enclosing is not None:
                # 从循环中移除
                try:
                    self.exec_state['loop_stack'].remove(enclosing)
                except Exception:
                    pass
                # 跳转到循环结束位置
                ni = enclosing['end'] + 1
                self.exec_state['index'] = ni
                self._output(f"在循环内遇到 break，跳至索引 {ni}")
                return
            else:
                # 不在循环内，简单地跳过break语句
                self.exec_state['index'] = start + 1
                self._output("遇到 break（未在循环内），已忽略。")
                return
        
        # 查找包含的循环
        enclosing = self._find_enclosing_loop(start)
        if enclosing is not None:
            try:
                ni, nv, a = self._run_block(start, enclosing['end'], dict(self.exec_state['vars']), max_actions=1)
            except BreakLoop as ex:
                try:
                    self.exec_state['vars'] = ex.runtime_vars or dict(self.exec_state['vars'])
                except Exception:
                    pass
                try:
                    self.exec_state['loop_stack'].remove(enclosing)
                except Exception:
                    pass
                ni = enclosing['end'] + 1
                self.exec_state['index'] = ni
                self._output(f"在循环内遇到 break，跳至索引 {ni}")
                return
            
            self.exec_state['vars'] = nv
            
            if ni > enclosing['end']:
                enclosing['pos'] += 1
                if enclosing['pos'] < len(enclosing['iterator']):
                    self.exec_state['vars'][enclosing['var']] = enclosing['iterator'][enclosing['pos']]
                    self.exec_state['index'] = enclosing['start'] + 1
                    self._output(f"循环下次迭代: 设 {enclosing['var']} = {enclosing['iterator'][enclosing['pos']]}，下一索引 {self.exec_state['index']}")
                    return
                else:
                    try:
                        self.exec_state['loop_stack'].remove(enclosing)
                    except Exception:
                        pass
                    self.exec_state['index'] = enclosing['end'] + 1
                    self._output(f"循环完成，下一索引 {self.exec_state['index']}")
                    return
            else:
                self.exec_state['index'] = ni
                self._output(f"单步执行: 完成 {a} 个操作，下一索引 {ni}")
                return
        
        # 默认情况：执行一个操作
        try:
            ni, nv, a = self._run_block(start, end, dict(self.exec_state['vars']), max_actions=1)
        except BreakLoop as ex:
            ni = start + 1
            nv = ex.runtime_vars or dict(self.exec_state['vars'])
            a = ex.actions
        
        self.exec_state['index'] = ni
        self.exec_state['vars'] = nv
        self._output(f"单步执行: 完成 {a} 个操作，下一索引 {ni}")
    
    def reset_execution(self):
        """重置执行状态"""
        self.exec_state = {'index': 0, 'vars': {}, 'loop_stack': []}
        
        # 清除所有步骤的输出
        for step in self.steps:
            if isinstance(step, StepObject):
                step.outputs.clear()
        
        self._update_watcher({})
        self._output("执行状态已重置；已清除运行时变量与步骤输出")
    
    def _run_block(self, start_idx: int, end_idx: int, runtime_vars: Dict, 
                   max_actions: Optional[int] = None) -> Tuple[int, Dict, int]:
        """执行一个代码块
        
        Args:
            start_idx: 起始索引
            end_idx: 结束索引
            runtime_vars: 运行时变量
            max_actions: 最大操作数（用于单步执行）
        
        Returns:
            (next_index, runtime_vars, actions_done)
        """
        actions = 0
        i = start_idx
        
        while i <= end_idx:
            if i >= len(self.steps):
                break
            
            step = self.steps[i]
            
            # 处理控制流
            if isinstance(step, StepObject) and step.type == 'control':
                ctrl = step.control
                
                if ctrl == 'if':
                    match = self._find_matching_end(i)
                    cond_raw = step.params.get('condition', '')
                    cond_val = self.resolve_references(cond_raw, runtime_vars)
                    cond_bool = cond_val if isinstance(cond_val, bool) else self._safe_eval(str(cond_val), runtime_vars)
                    
                    self._output(f"IF condition ({cond_raw}) -> {cond_bool}")
                    self._update_watcher(runtime_vars)
                    actions += 1
                    
                    if max_actions is not None and actions >= max_actions:
                        return (i + 1, runtime_vars, actions)
                    
                    if cond_bool:
                        if match != -1 and match > i:
                            ni, nv, a = self._run_block(i + 1, match - 1, runtime_vars, 
                                                       None if max_actions is None else (max_actions - actions))
                            actions += a
                            runtime_vars = nv
                            i = match + 1
                            if max_actions is not None and actions >= max_actions:
                                return (i, runtime_vars, actions)
                            continue
                    else:
                        i = match + 1 if match != -1 else i + 1
                        continue
                
                elif ctrl == 'for':
                    match = self._find_matching_end(i)
                    iterable_raw = step.params.get('iterable', '')
                    varname = step.params.get('var', '_loop')
                    iterable_val = self.resolve_references(iterable_raw, runtime_vars)
                    
                    if isinstance(iterable_val, int):
                        iterator = range(iterable_val)
                    elif isinstance(iterable_val, (list, tuple)):
                        iterator = iterable_val
                    else:
                        try:
                            iterator = list(self._safe_eval(str(iterable_val), runtime_vars))
                        except Exception:
                            iterator = []
                    
                    self._output(f"FOR over {iterable_raw} -> {list(iterator)}")
                    self._update_watcher(runtime_vars)
                    actions += 1
                    
                    if max_actions is not None and actions >= max_actions:
                        return (i + 1, runtime_vars, actions)
                    
                    if match != -1 and match > i:
                        for val in iterator:
                            new_vars = dict(runtime_vars)
                            new_vars[varname] = val
                            try:
                                ni, nv, a = self._run_block(i + 1, match - 1, new_vars, 
                                                           None if max_actions is None else (max_actions - actions))
                                actions += a
                            except BreakLoop as ex:
                                actions += ex.actions
                                runtime_vars = ex.runtime_vars or runtime_vars
                                if max_actions is not None and actions >= max_actions:
                                    return (match + 1, runtime_vars, actions)
                                break
                        i = match + 1
                        continue
                    else:
                        i += 1
                        continue
                
                elif ctrl == 'break':
                    actions += 1
                    self._output("BREAK")
                    self._update_watcher(runtime_vars)
                    raise BreakLoop(actions=1, runtime_vars=runtime_vars)
                
                elif ctrl == 'end':
                    i += 1
                    continue
            
            # 执行函数步骤
            if isinstance(step, StepObject) and step.type == 'function':
                module_name = step.module
                func_name = step.function
                func = self.test_loader.get_function(module_name, func_name)
                
                if func is None:
                    self._output(f"跳过未知函数: {module_name}.{func_name}")
                    self._update_watcher(runtime_vars)
                    i += 1
                    continue
                
                self._output(f"执行: {module_name}.{func_name}... ")
                self._update_watcher(runtime_vars)
                
                # 准备参数
                sig = inspect.signature(func)
                params = sig.parameters
                args = {}
                
                for param_name in params.keys():
                    raw = step.params.get(param_name, '')
                    resolved = self.resolve_references(raw, runtime_vars)
                    
                    param_type = params[param_name].annotation
                    if param_type != inspect.Parameter.empty:
                        try:
                            if param_type == bool:
                                value = bool(resolved) if isinstance(resolved, bool) else str(resolved).lower() in ('true', '1', 'yes', 'on')
                            elif param_type in (int, float):
                                value = param_type(resolved)
                            else:
                                value = resolved
                        except Exception as e:
                            self._output(f"参数 '{param_name}' 类型转换失败: {e}")
                            value = resolved
                    else:
                        value = resolved
                    args[param_name] = value
                
                # 执行函数
                try:
                    result = func(**args)
                    
                    # 存储输出
                    if isinstance(result, dict):
                        step.outputs.update(result)
                    else:
                        step.outputs['return'] = result
                        try:
                            # 将返回值与函数中使用的变量名关联
                            preds = self.test_loader.get_return_names(module_name, func_name)
                            for pred in preds:
                                step.outputs[pred] = result
                        except Exception:
                            pass
                    
                    success = (result is None) or bool(result)
                    self._output(f"{'成功' if success else '失败'}")
                    self._set_status(i, success)
                
                except Exception as e:
                    self._output(f"错误: {str(e)}")
                    self._set_status(i, False)
                
                self._update_watcher(runtime_vars)
                actions += 1
                
                if max_actions is not None and actions >= max_actions:
                    return (i + 1, runtime_vars, actions)
            
            i += 1
        
        return (i, runtime_vars, actions)
    
    def _find_matching_end(self, start_index: int) -> int:
        """查找匹配的end索引"""
        depth = 0
        for i in range(start_index, len(self.steps)):
            step = self.steps[i]
            if isinstance(step, StepObject) and step.type == "control":
                if step.control in ("if", "for"):
                    depth += 1
                elif step.control == "end":
                    depth -= 1
                    if depth == 0:
                        return i
        return -1
    
    def _find_enclosing_loop(self, start_idx: int):
        """查找包含指定索引的循环"""
        ls = self.exec_state.get('loop_stack', [])
        for entry in reversed(ls):
            if entry['start'] < start_idx <= entry['end']:
                return entry
        return None
    
    def resolve_references(self, text: str, runtime_vars: Dict = None) -> Any:
        """解析引用
        
        支持的模式:
          ${#N:key}   -> 步骤N的输出或参数
          ${@var}     -> 运行时变量
        
        Args:
            text: 要解析的文本
            runtime_vars: 运行时变量字典
        
        Returns:
            解析后的值
        """
        if runtime_vars is None:
            runtime_vars = {}
        
        if not isinstance(text, str):
            return text
        
        def repl_step(m):
            idx = int(m.group(1)) - 1
            key = m.group(2)
            if 0 <= idx < len(self.steps):
                step = self.steps[idx]
                if isinstance(step, StepObject):
                    if key in step.outputs:
                        return str(step.outputs.get(key))
                    return str(step.params.get(key, ""))
            return ""
        
        def repl_var(m):
            name = m.group(1)
            return str(runtime_vars.get(name, ""))
        
        text2 = re.sub(r"\$\{#(\d+):([^}]+)\}", repl_step, text)
        text3 = re.sub(r"\$\{@([^}]+)\}", repl_var, text2)
        
        try:
            import ast
            val = ast.literal_eval(text3)
            return val
        except Exception:
            pass
        
        return text3
    
    def _safe_eval(self, expr: str, local_vars: Dict = None) -> Any:
        """安全地求值表达式"""
        if local_vars is None:
            local_vars = {}
        try:
            import ast
            return ast.literal_eval(expr)
        except Exception:
            try:
                safe_globals = {"__builtins__": None, 'True': True, 'False': False, 'None': None}
                return eval(expr, safe_globals, local_vars)
            except Exception:
                return False
    
    def get_execution_index(self) -> Optional[int]:
        """获取当前执行索引"""
        if self.exec_state:
            return self.exec_state.get('index')
        return None
