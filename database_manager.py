import sqlite3
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from contextlib import contextmanager
import threading
from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime, Float, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError
import os

Base = declarative_base()

class ProxyModel(Base):
    """代理数据模型"""
    __tablename__ = 'proxies'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    host = Column(String(255), nullable=False)
    port = Column(Integer, nullable=False)
    username = Column(String(255), nullable=True)
    password = Column(String(255), nullable=True)
    proxy_type = Column(String(20), nullable=False, default='http')  # http, socks4, socks5
    valid = Column(Boolean, nullable=True)
    validated_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 性能统计
    success_count = Column(Integer, default=0)
    failure_count = Column(Integer, default=0)
    last_used_at = Column(DateTime, nullable=True)
    response_time = Column(Float, nullable=True)
    
    # 错误记录
    error_count = Column(Integer, default=0)
    last_error_at = Column(DateTime, nullable=True)
    last_error_message = Column(Text, nullable=True)
    
    # 地理位置信息（可选）
    country = Column(String(100), nullable=True)
    region = Column(String(100), nullable=True)
    city = Column(String(100), nullable=True)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'id': self.id,
            'host': self.host,
            'port': self.port,
            'username': self.username,
            'password': self.password,
            'type': self.proxy_type,
            'valid': self.valid,
            'validated_at': self.validated_at.isoformat() if self.validated_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'success_count': self.success_count,
            'failure_count': self.failure_count,
            'last_used_at': self.last_used_at.isoformat() if self.last_used_at else None,
            'response_time': self.response_time,
            'error_count': self.error_count,
            'last_error_at': self.last_error_at.isoformat() if self.last_error_at else None,
            'last_error_message': self.last_error_message,
            'country': self.country,
            'region': self.region,
            'city': self.city
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ProxyModel':
        """从字典创建代理模型"""
        proxy = cls()
        proxy.host = data.get('host', '')
        proxy.port = data.get('port', 0)
        proxy.username = data.get('username')
        proxy.password = data.get('password')
        proxy.proxy_type = data.get('type', 'http')
        proxy.valid = data.get('valid')
        
        # 处理时间字段
        if data.get('validated_at'):
            try:
                proxy.validated_at = datetime.fromisoformat(data['validated_at'].replace('Z', '+00:00'))
            except (ValueError, AttributeError):
                pass
        
        if data.get('last_used_at'):
            try:
                proxy.last_used_at = datetime.fromisoformat(data['last_used_at'].replace('Z', '+00:00'))
            except (ValueError, AttributeError):
                pass
        
        # 统计信息
        proxy.success_count = data.get('success_count', 0)
        proxy.failure_count = data.get('failure_count', 0)
        proxy.response_time = data.get('response_time')
        proxy.error_count = data.get('error_count', 0)
        proxy.last_error_message = data.get('last_error_message')
        
        # 地理位置
        proxy.country = data.get('country')
        proxy.region = data.get('region')
        proxy.city = data.get('city')
        
        return proxy

class DatabaseManager:
    """数据库管理器"""
    
    def __init__(self, db_path: str = 'data/proxies.db'):
        self.db_path = db_path
        self.logger = logging.getLogger(__name__)
        self._lock = threading.Lock()
        
        # 确保数据目录存在
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        # 创建数据库引擎
        self.engine = create_engine(
            f'sqlite:///{db_path}',
            echo=False,
            pool_pre_ping=True,
            connect_args={'check_same_thread': False}
        )
        
        # 创建会话工厂
        self.SessionLocal = sessionmaker(bind=self.engine)
        
        # 创建表
        self._create_tables()
        
        self.logger.info(f"数据库管理器初始化完成: {db_path}")
    
    def _create_tables(self):
        """创建数据库表"""
        try:
            Base.metadata.create_all(bind=self.engine)
            self.logger.info("数据库表创建成功")
        except SQLAlchemyError as e:
            self.logger.error(f"创建数据库表失败: {e}")
            raise
    
    @contextmanager
    def get_session(self) -> Session:
        """获取数据库会话"""
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            self.logger.error(f"数据库操作失败: {e}")
            raise
        finally:
            session.close()
    
    def add_proxy(self, proxy_data: Dict[str, Any]) -> Optional[int]:
        """添加代理"""
        try:
            with self.get_session() as session:
                # 检查是否已存在
                existing = session.query(ProxyModel).filter_by(
                    host=proxy_data.get('host'),
                    port=proxy_data.get('port')
                ).first()
                
                if existing:
                    self.logger.debug(f"代理已存在: {proxy_data.get('host')}:{proxy_data.get('port')}")
                    return existing.id
                
                # 创建新代理
                proxy = ProxyModel.from_dict(proxy_data)
                session.add(proxy)
                session.flush()  # 获取ID
                
                self.logger.debug(f"添加代理成功: {proxy.host}:{proxy.port}")
                return proxy.id
                
        except SQLAlchemyError as e:
            self.logger.error(f"添加代理失败: {e}")
            return None
    
    def save_proxies(self, proxies: List[Dict[str, Any]]) -> bool:
        """批量保存代理（更新现有或添加新的）"""
        try:
            with self.get_session() as session:
                updated_count = 0
                added_count = 0
                
                for proxy_data in proxies:
                    # 查找现有代理
                    existing = session.query(ProxyModel).filter_by(
                        host=proxy_data.get('host'),
                        port=proxy_data.get('port')
                    ).first()
                    
                    if existing:
                        # 更新现有代理
                        for key, value in proxy_data.items():
                            if key == 'type':
                                key = 'proxy_type'
                            if hasattr(existing, key):
                                setattr(existing, key, value)
                        existing.updated_at = datetime.utcnow()
                        updated_count += 1
                    else:
                        # 添加新代理
                        proxy = ProxyModel.from_dict(proxy_data)
                        session.add(proxy)
                        added_count += 1
                
                self.logger.info(f"批量保存完成 - 更新: {updated_count}, 新增: {added_count}")
                return True
                
        except SQLAlchemyError as e:
            self.logger.error(f"批量保存代理失败: {e}")
            return False
    
    def get_all_proxies(self) -> List[Dict[str, Any]]:
        """获取所有代理"""
        try:
            with self.get_session() as session:
                proxies = session.query(ProxyModel).all()
                return [proxy.to_dict() for proxy in proxies]
        except SQLAlchemyError as e:
            self.logger.error(f"获取代理列表失败: {e}")
            return []
    
    def get_valid_proxies(self) -> List[Dict[str, Any]]:
        """获取有效代理"""
        try:
            with self.get_session() as session:
                proxies = session.query(ProxyModel).filter_by(valid=True).all()
                return [proxy.to_dict() for proxy in proxies]
        except SQLAlchemyError as e:
            self.logger.error(f"获取有效代理失败: {e}")
            return []
    
    def update_proxy(self, proxy_id: int, updates: Dict[str, Any]) -> bool:
        """更新代理信息"""
        try:
            with self.get_session() as session:
                proxy = session.query(ProxyModel).filter_by(id=proxy_id).first()
                if not proxy:
                    return False
                
                # 更新字段
                for key, value in updates.items():
                    if hasattr(proxy, key):
                        setattr(proxy, key, value)
                
                proxy.updated_at = datetime.utcnow()
                return True
                
        except SQLAlchemyError as e:
            self.logger.error(f"更新代理失败: {e}")
            return False
    
    def update_proxy_by_address(self, host: str, port: int, updates: Dict[str, Any]) -> bool:
        """根据地址更新代理"""
        try:
            with self.get_session() as session:
                proxy = session.query(ProxyModel).filter_by(host=host, port=port).first()
                if not proxy:
                    return False
                
                # 更新字段
                for key, value in updates.items():
                    if key == 'type':
                        key = 'proxy_type'
                    if hasattr(proxy, key):
                        setattr(proxy, key, value)
                
                proxy.updated_at = datetime.utcnow()
                return True
                
        except SQLAlchemyError as e:
            self.logger.error(f"更新代理失败: {e}")
            return False
    
    def delete_proxy(self, proxy_id: int) -> bool:
        """删除代理"""
        try:
            with self.get_session() as session:
                proxy = session.query(ProxyModel).filter_by(id=proxy_id).first()
                if proxy:
                    session.delete(proxy)
                    return True
                return False
        except SQLAlchemyError as e:
            self.logger.error(f"删除代理失败: {e}")
            return False
    
    def delete_invalid_proxies(self) -> int:
        """删除无效代理"""
        try:
            with self.get_session() as session:
                count = session.query(ProxyModel).filter_by(valid=False).count()
                session.query(ProxyModel).filter_by(valid=False).delete()
                self.logger.info(f"删除了 {count} 个无效代理")
                return count
        except SQLAlchemyError as e:
            self.logger.error(f"删除无效代理失败: {e}")
            return 0
    
    def get_proxy_stats(self) -> Dict[str, Any]:
        """获取代理统计信息"""
        try:
            with self.get_session() as session:
                total = session.query(ProxyModel).count()
                valid = session.query(ProxyModel).filter_by(valid=True).count()
                invalid = session.query(ProxyModel).filter_by(valid=False).count()
                unvalidated = session.query(ProxyModel).filter(ProxyModel.valid.is_(None)).count()
                
                # 按类型统计
                type_stats = {}
                for proxy_type in ['http', 'socks4', 'socks5']:
                    type_count = session.query(ProxyModel).filter_by(proxy_type=proxy_type).count()
                    if type_count > 0:
                        type_stats[proxy_type] = {
                            'total': type_count,
                            'valid': session.query(ProxyModel).filter_by(
                                proxy_type=proxy_type, valid=True
                            ).count(),
                            'invalid': session.query(ProxyModel).filter_by(
                                proxy_type=proxy_type, valid=False
                            ).count()
                        }
                
                return {
                    'total': total,
                    'valid': valid,
                    'invalid': invalid,
                    'unvalidated': unvalidated,
                    'success_rate': (valid / total * 100) if total > 0 else 0,
                    'by_type': type_stats
                }
        except SQLAlchemyError as e:
            self.logger.error(f"获取统计信息失败: {e}")
            return {'total': 0, 'valid': 0, 'invalid': 0, 'unvalidated': 0, 'success_rate': 0, 'by_type': {}}
    
    def migrate_from_json(self, json_file: str) -> int:
        """从JSON文件迁移数据"""
        if not os.path.exists(json_file):
            self.logger.warning(f"JSON文件不存在: {json_file}")
            return 0
        
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            proxies = data.get('proxies', [])
            migrated_count = 0
            
            for proxy_data in proxies:
                if self.add_proxy(proxy_data):
                    migrated_count += 1
            
            self.logger.info(f"从JSON迁移了 {migrated_count} 个代理")
            return migrated_count
            
        except Exception as e:
            self.logger.error(f"JSON迁移失败: {e}")
            return 0
    
    def backup_to_json(self, json_file: str) -> bool:
        """备份到JSON文件"""
        try:
            proxies = self.get_all_proxies()
            data = {
                'proxies': proxies,
                'backup_time': datetime.now().isoformat(),
                'total_count': len(proxies)
            }
            
            os.makedirs(os.path.dirname(json_file), exist_ok=True)
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"备份到JSON完成: {json_file}")
            return True
            
        except Exception as e:
            self.logger.error(f"备份到JSON失败: {e}")
            return False
    
    def cleanup_old_records(self, days: int = 30) -> int:
        """清理旧记录"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            with self.get_session() as session:
                count = session.query(ProxyModel).filter(
                    ProxyModel.updated_at < cutoff_date,
                    ProxyModel.valid == False
                ).count()
                
                session.query(ProxyModel).filter(
                    ProxyModel.updated_at < cutoff_date,
                    ProxyModel.valid == False
                ).delete()
                
                self.logger.info(f"清理了 {count} 条旧记录")
                return count
        except SQLAlchemyError as e:
            self.logger.error(f"清理旧记录失败: {e}")
            return 0
    
    def close(self):
        """关闭数据库连接"""
        if hasattr(self, 'engine'):
            self.engine.dispose()
            self.logger.info("数据库连接已关闭")