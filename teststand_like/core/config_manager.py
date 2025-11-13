"""
配置管理器
负责管理测试序列运行器的配置文件
"""
import json
import os
from typing import Dict, Any


class ConfigManager:
    """配置管理器
    
    管理应用程序的配置，包括测试目录路径、UI设置等
    """
    
    def __init__(self, config_file: str = "config.json"):
        """初始化配置管理器
        
        Args:
            config_file: 配置文件路径
        """
        self.config_file = config_file
        self.config = {
            "test_directory": "Testcase",
            "last_sequence_file": "",
            "window_geometry": {
                "x": 100,
                "y": 100,
                "width": 1200,
                "height": 700
            },
            "splitter_sizes": {
                "main": [300, 900],
                "sequence_watcher": [600, 400]
            }
        }
        self.load_config()
    
    def load_config(self) -> bool:
        """从文件加载配置
        
        Returns:
            bool: 加载成功返回True，否则返回False
        """
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    loaded_config = json.load(f)
                    # 合并默认配置和加载的配置
                    self.config.update(loaded_config)
                return True
            return False
        except Exception as e:
            print(f"加载配置文件失败: {e}")
            return False
    
    def save_config(self) -> bool:
        """保存配置到文件
        
        Returns:
            bool: 保存成功返回True，否则返回False
        """
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"保存配置文件失败: {e}")
            return False
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取配置项的值
        
        Args:
            key: 配置项键名（支持点号分隔的嵌套键，如"window_geometry.width"）
            default: 默认值
            
        Returns:
            配置项的值或默认值
        """
        keys = key.split('.')
        value = self.config
        
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default
    
    def set(self, key: str, value: Any) -> None:
        """设置配置项的值
        
        Args:
            key: 配置项键名（支持点号分隔的嵌套键，如"window_geometry.width"）
            value: 要设置的值
        """
        keys = key.split('.')
        config = self.config
        
        # 遍历到倒数第二个键，创建缺失的嵌套字典
        for k in keys[:-1]:
            if k not in config or not isinstance(config[k], dict):
                config[k] = {}
            config = config[k]
        
        # 设置最后一个键的值
        config[keys[-1]] = value
    
    def update_window_geometry(self, x: int, y: int, width: int, height: int) -> None:
        """更新窗口几何信息
        
        Args:
            x: 窗口X坐标
            y: 窗口Y坐标
            width: 窗口宽度
            height: 窗口高度
        """
        self.config["window_geometry"] = {
            "x": x,
            "y": y,
            "width": width,
            "height": height
        }
    
    def update_splitter_sizes(self, main_sizes: list, sequence_watcher_sizes: list) -> None:
        """更新分割器尺寸
        
        Args:
            main_sizes: 主分割器尺寸
            sequence_watcher_sizes: 序列-监视器分割器尺寸
        """
        self.config["splitter_sizes"] = {
            "main": main_sizes,
            "sequence_watcher": sequence_watcher_sizes
        }
    
    def set_test_directory(self, directory: str) -> None:
        """设置测试目录
        
        Args:
            directory: 测试目录路径
        """
        self.config["test_directory"] = directory
    
    def set_last_sequence_file(self, file_path: str) -> None:
        """设置最后加载的序列文件路径
        
        Args:
            file_path: 序列文件路径
        """
        self.config["last_sequence_file"] = file_path