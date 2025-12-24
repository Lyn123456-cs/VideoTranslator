#!/usr/bin/env python3
"""
配置管理器
用于保存和加载用户配置
"""

import json
import os
from pathlib import Path
from typing import Dict, Any


class ConfigManager:
    """配置管理器"""
    
    def __init__(self):
        # 配置文件路径
        self.config_dir = Path.home() / "Library" / "Application Support" / "VideoTranslator"
        self.config_file = self.config_dir / "config.json"
        
        # 默认配置
        self.default_config = {
            'target_language': 'zh',  # 默认目标语言
            'voice_index': 0,  # 默认音色索引
            'subtitle_position': 'bottom',  # 默认字幕位置
            'margin': 10,  # 默认边距
            'last_video_dir': str(Path.home()),  # 上次打开的视频目录
            'window_geometry': None,  # 窗口位置和大小
        }
        
        self.config = self.load_config()
    
    def ensure_config_dir(self):
        """确保配置目录存在"""
        self.config_dir.mkdir(parents=True, exist_ok=True)
    
    def load_config(self) -> Dict[str, Any]:
        """加载配置"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    loaded_config = json.load(f)
                    # 合并默认配置和加载的配置
                    config = self.default_config.copy()
                    config.update(loaded_config)
                    return config
            except Exception as e:
                print(f"加载配置失败: {e}，使用默认配置")
                return self.default_config.copy()
        else:
            return self.default_config.copy()
    
    def save_config(self):
        """保存配置"""
        try:
            self.ensure_config_dir()
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存配置失败: {e}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取配置项"""
        return self.config.get(key, default)
    
    def set(self, key: str, value: Any):
        """设置配置项"""
        self.config[key] = value
    
    def save_window_geometry(self, geometry: bytes):
        """保存窗口几何信息"""
        # 将bytes转换为hex字符串以便JSON序列化
        self.config['window_geometry'] = geometry.hex()
        self.save_config()
    
    def get_window_geometry(self) -> bytes:
        """获取窗口几何信息"""
        geom_hex = self.config.get('window_geometry')
        if geom_hex:
            try:
                return bytes.fromhex(geom_hex)
            except:
                return None
        return None
