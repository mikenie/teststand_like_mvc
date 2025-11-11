"""
测试函数加载器
负责动态加载和解析测试模块
"""
import os
import importlib.util
import ast
import inspect


class TestLoader:
    """测试函数加载器
    
    从指定目录加载Python测试模块，并解析函数签名和返回值。
    """
    
    def __init__(self):
        self.test_functions = {}  # {module_name: {func_name: function_obj}}
        self.func_return_names = {}  # {module_name: {func_name: [return_var_names]}}
    
    def load_from_directory(self, directory='Testcase'):
        """从目录加载所有测试模块
        
        Args:
            directory: 测试模块所在目录，默认为'Testcase'
        
        Returns:
            dict: 加载的函数字典 {module_name: {func_name: function}}
        """
        self.test_functions.clear()
        self.func_return_names.clear()
        
        # 查找目录
        test_dir = os.path.join(os.getcwd(), directory)
        base_dir = test_dir if os.path.isdir(test_dir) else os.getcwd()
        
        if not os.path.exists(base_dir):
            return self.test_functions
        
        # 遍历目录中的Python文件
        for fname in os.listdir(base_dir):
            if fname.endswith('.py') and fname.startswith('test_') and fname != 'test_functions.py':
                file_path = os.path.join(base_dir, fname)
                module_name = os.path.splitext(os.path.basename(file_path))[0]
                
                try:
                    # 动态加载模块
                    spec = importlib.util.spec_from_file_location(module_name, file_path)
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
                    
                    # 解析源码以获取返回值名称
                    self._parse_return_names(file_path, module_name)
                    
                    # 获取模块中的函数
                    functions = []
                    for name in dir(module):
                        obj = getattr(module, name)
                        if callable(obj) and not name.startswith("_"):
                            functions.append(name)
                            # 保存函数引用
                            if module_name not in self.test_functions:
                                self.test_functions[module_name] = {}
                            self.test_functions[module_name][name] = obj
                    
                except Exception as e:
                    print(f"无法加载模块 {module_name}: {e}")
        
        return self.test_functions
    
    def _parse_return_names(self, file_path, module_name):
        """解析源码以提取函数返回值的变量名
        
        Args:
            file_path: 源码文件路径
            module_name: 模块名
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                src = f.read()
            
            tree = ast.parse(src)
            func_returns = {}
            
            for node in tree.body:
                if isinstance(node, ast.FunctionDef):
                    ret_names = []
                    for st in ast.walk(node):
                        if isinstance(st, ast.Return) and st.value is not None:
                            v = st.value
                            # 返回简单变量名: return sum
                            if isinstance(v, ast.Name):
                                ret_names.append(v.id)
                            # 返回字典字面量: return {'k': val}
                            elif isinstance(v, ast.Dict):
                                for key in v.keys:
                                    if isinstance(key, ast.Constant):
                                        ret_names.append(str(key.value))
                    
                    if ret_names:
                        func_returns[node.name] = list(dict.fromkeys(ret_names))
            
            if func_returns:
                self.func_return_names[module_name] = func_returns
        
        except Exception:
            # 忽略解析错误
            pass
    
    def get_function(self, module_name, func_name):
        """获取指定的函数对象
        
        Args:
            module_name: 模块名
            func_name: 函数名
        
        Returns:
            function: 函数对象，如果不存在返回None
        """
        return self.test_functions.get(module_name, {}).get(func_name)
    
    def get_function_signature(self, module_name, func_name):
        """获取函数签名
        
        Args:
            module_name: 模块名
            func_name: 函数名
        
        Returns:
            inspect.Signature: 函数签名，如果不存在返回None
        """
        func = self.get_function(module_name, func_name)
        if func:
            return inspect.signature(func)
        return None
    
    def get_return_names(self, module_name, func_name):
        """获取函数的预测返回值名称列表
        
        Args:
            module_name: 模块名
            func_name: 函数名
        
        Returns:
            list: 返回值变量名列表
        """
        return self.func_return_names.get(module_name, {}).get(func_name, [])
    
    def get_all_modules(self):
        """获取所有已加载的模块名
        
        Returns:
            list: 模块名列表
        """
        return list(self.test_functions.keys())
    
    def get_module_functions(self, module_name):
        """获取指定模块的所有函数名
        
        Args:
            module_name: 模块名
        
        Returns:
            list: 函数名列表
        """
        return list(self.test_functions.get(module_name, {}).keys())
