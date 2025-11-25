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
    DEBUG = os.getenv('FLASK_DEBUG', 'True').lower() == 'true'
    HOST = os.getenv('FLASK_HOST', '0.0.0.0')
    PORT = int(os.getenv('FLASK_PORT', 5000))
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', 'http://localhost:5173,http://localhost:3000').split(',')
    GOOGLE_CLOUD_API_KEY = os.getenv('GOOGLE_CLOUD_API_KEY')
    OUTPUT_DIR = os.getenv('OUTPUT_DIR', 'output')
    STORAGE_BACKEND = os.getenv('STORAGE_BACKEND', 'local')

    _image_providers_config = None

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
            raise ValueError(
                f"未找到图片生成服务商配置: {provider_name}\n"
                f"可用的服务商: {available}\n"
                "解决方案：\n"
                "1. 检查 image_providers.yaml 文件中是否包含该服务商配置\n"
                "2. 确认 providers 字段下有对应的服务商名称\n"
                "3. 或修改 active_provider 为可用的服务商名称"
            )

        provider_config = config['providers'][provider_name].copy()

        api_key_env = provider_config.get('api_key_env')
        if api_key_env:
            provider_config['api_key'] = os.getenv(api_key_env)

        return provider_config
