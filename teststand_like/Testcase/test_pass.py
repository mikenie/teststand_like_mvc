def test_string(str1: str = "", str2: str = "") -> bool:
    """测试字符串连接
    
    Args:
        str1 (str): 待测试字符串
        str2 (str): 字符串
    
    Returns:
        str: 连接后的字符串
    """
    if str1 in str2:
        return True
    
    return False

def test_in_range(num: int = 0, start: int = 0, end: int = 10) -> bool:
    """测试数字范围
    
    Args:
        num (int): 待测试数字
        start (int): 范围开始
        end (int): 范围结束
    
    Returns:
        bool: 是否在范围内
    """
    return start <= num <= end
def test_boolean_logic(a: bool = True, b: bool = False) -> bool:
    """测试布尔逻辑运算
    
    Args:
        a (bool): 第一个布尔值
        b (bool): 第二个布尔值
    
    Returns:
        bool: 逻辑与的结果
    """
    return a and b 

