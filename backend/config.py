import os
import yaml
import json
import base64
import logging
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

class Config:
    # User Customizations for Vercel/Env
    DEBUG = os.getenv('FLASK_DEBUG', 'True').lower() == 'true'
    HOST = os.getenv('FLASK_HOST', '0.0.0.0')
    PORT = int(os.getenv('FLASK_PORT', 5000))
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', 'http://localhost:5173,http://localhost:3000').split(',')
    GOOGLE_CLOUD_API_KEY = os.getenv('GOOGLE_CLOUD_API_KEY')
    OUTPUT_DIR = os.getenv('OUTPUT_DIR', 'output')
    STORAGE_BACKEND = os.getenv('STORAGE_BACKEND', 'local')

    _image_providers_config = None
    _text_providers_config = None

    @staticmethod
    def _deep_merge(source, destination):
        for key, value in source.items():
            if isinstance(value, dict):
                node = destination.setdefault(key, {})
                Config._deep_merge(value, node)
            else:
                destination[key] = value
        return destination

    @classmethod
    def load_image_providers_config(cls):
        if cls._image_providers_config is not None:
            return cls._image_providers_config

        # 1. Defaults
        config = {
            'active_provider': 'google_genai',
            'providers': {
                'google_genai': {
                    'type': 'google_genai',
                    'api_key_env': 'GOOGLE_CLOUD_API_KEY',
                    'model': 'gemini-3-pro-image-preview',
                    'default_aspect_ratio': '3:4'
                }
            }
        }

        # 2. File Config
        config_path = Path(__file__).parent.parent / 'image_providers.yaml'
        if config_path.exists():
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    file_config = yaml.safe_load(f)
                    if file_config and isinstance(file_config, dict):
                        cls._deep_merge(file_config, config)
                    logger.debug(f"图片配置加载成功: {list(config.get('providers', {}).keys())}")
            except Exception as e:
                logger.error(f"Error loading image_providers.yaml: {e}")

        # Helper to parse env config
        def parse_and_merge(env_val, source_name):
            if not env_val:
                return
            try:
                # Try JSON first
                try:
                    env_config = json.loads(env_val)
                except json.JSONDecodeError:
                    # Try YAML
                    env_config = yaml.safe_load(env_val)
                
                if env_config and isinstance(env_config, dict):
                    cls._deep_merge(env_config, config)
                else:
                    logger.warning(f"Parsed {source_name} is not a dictionary")
            except Exception as e:
                logger.error(f"Error parsing {source_name}: {e}")

        # 3. Env Config (Base64)
        env_b64 = os.getenv('IMAGE_PROVIDERS_CONFIG_BASE64')
        if env_b64:
            try:
                decoded = base64.b64decode(env_b64).decode('utf-8')
                parse_and_merge(decoded, "IMAGE_PROVIDERS_CONFIG_BASE64")
            except Exception as e:
                logger.error(f"Error decoding IMAGE_PROVIDERS_CONFIG_BASE64: {e}")

        # 4. Env Config (Plain)
        env_plain = os.getenv('IMAGE_PROVIDERS_CONFIG')
        if env_plain:
            parse_and_merge(env_plain, "IMAGE_PROVIDERS_CONFIG")

        cls._image_providers_config = config
        return cls._image_providers_config

    @classmethod
    def load_text_providers_config(cls):
        """加载文本生成服务商配置"""
        if cls._text_providers_config is not None:
            return cls._text_providers_config

        config_path = Path(__file__).parent.parent / 'text_providers.yaml'
        logger.debug(f"加载文本服务商配置: {config_path}")

        if not config_path.exists():
            logger.warning(f"文本配置文件不存在: {config_path}，使用默认配置")
            cls._text_providers_config = {
                'active_provider': 'google_gemini',
                'providers': {}
            }
            return cls._text_providers_config

        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                cls._text_providers_config = yaml.safe_load(f) or {}
            logger.debug(f"文本配置加载成功: {list(cls._text_providers_config.get('providers', {}).keys())}")
        except yaml.YAMLError as e:
            logger.error(f"文本配置文件 YAML 格式错误: {e}")
            raise ValueError(f"配置文件格式错误: text_providers.yaml\n{e}")

        return cls._text_providers_config

    @classmethod
    def get_active_image_provider(cls):
        config = cls.load_image_providers_config()
        # 允许通过环境变量覆盖
        return os.getenv('IMAGE_PROVIDER', config.get('active_provider', 'google_genai'))

    @classmethod
    def get_image_provider_config(cls, provider_name: str = None):
        config = cls.load_image_providers_config()

        if provider_name is None:
            provider_name = cls.get_active_image_provider()

        if provider_name not in config.get('providers', {}):
            available = ', '.join(config.get('providers', {}).keys())
            raise ValueError(f"未找到图片生成服务商配置: {provider_name}\n可用的服务商: {available}")

        provider_config = config['providers'][provider_name].copy()

        # Handle API Key from Env (User feature)
        api_key_env = provider_config.get('api_key_env')
        if api_key_env:
            provider_config['api_key'] = os.getenv(api_key_env)

        # Basic validation
        if not provider_config.get('api_key'):
             logger.warning(f"图片服务商 [{provider_name}] 未配置 API Key (config or env)")
             
        return provider_config

    @classmethod
    def reload_config(cls):
        """重新加载配置（清除缓存）"""
        logger.info("重新加载所有配置...")
        cls._image_providers_config = None
        cls._text_providers_config = None
