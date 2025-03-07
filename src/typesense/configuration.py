from .exceptions import ConfigError
from .logger import logger
from urllib.parse import urlparse

class Node(object):
    def __init__(self, url):
        parsed = urlparse(url);
        if not parsed.hostname:
            raise ConfigError('Node URL does not contain the host name.')
        if not parsed.port:
            raise ConfigError('Node URL does not contain the port.')
        if not parsed.scheme:
            raise ConfigError('Node URL does not contain the protocol.')
        self.__init__(parsed.hostname, parsed.port, parsed.path, parsed.scheme)

    def __init__(self, host, port, path, protocol):
        self.host = host
        self.port = port
        self.path = path
        self.protocol = protocol

        # Used to skip bad hosts
        self.healthy = True

    def url(self):
        return '{0}://{1}:{2}{3}'.format(self.protocol, self.host, self.port, self.path)


class Configuration(object):
    def __init__(self, config_dict):
        Configuration.show_deprecation_warnings(config_dict)
        Configuration.validate_config_dict(config_dict)

        self.nodes = []
        for node_config in config_dict.get('nodes', []):
            if isinstance(node_config, str):
                node = Node(node_config)
            else:
                node = Node(node_config['host'], node_config['port'], node_config.get('path', ''), node_config['protocol'])
            self.nodes.append(node)

        nearest_node = config_dict.get('nearest_node', None)
        if not nearest_node:
            self.nearest_node = None
        elif isinstance(nearest_node, str):
            self.nearest_node = Node(nearest_node)
        else:
            self.nearest_node = Node(nearest_node['host'], nearest_node['port'], nearest_node.get('path', ''), nearest_node['protocol'])

        self.api_key = config_dict.get('api_key', '')
        self.connection_timeout_seconds = config_dict.get('connection_timeout_seconds', 3.0)
        self.num_retries = config_dict.get('num_retries', 3)
        self.retry_interval_seconds = config_dict.get('retry_interval_seconds', 1.0)
        self.healthcheck_interval_seconds = config_dict.get('healthcheck_interval_seconds', 60)

    @staticmethod
    def validate_config_dict(config_dict):
        nodes = config_dict.get('nodes', None)
        if not nodes:
            raise ConfigError('`nodes` is not defined.')

        api_key = config_dict.get('api_key', None)
        if not api_key:
            raise ConfigError('`api_key` is not defined.')

        for node in nodes:
            if not Configuration.validate_node_fields(node):
                raise ConfigError('`node` entry must be a URL string or a dictionary with the following required keys: '
                                  'host, port, protocol')

        nearest_node = config_dict.get('nearest_node', None)
        if nearest_node and not Configuration.validate_node_fields(nearest_node):
            raise ConfigError('`nearest_node` entry must be a URL string or a dictionary with the following required keys: '
                                  'host, port, protocol')

    @staticmethod
    def validate_node_fields(node):
        if isinstance(node, str):
            return True
        expected_fields = {'host', 'port', 'protocol'}
        return expected_fields.issubset(node)

    @staticmethod
    def show_deprecation_warnings(config_dict):
        if config_dict.get('timeout_seconds'):
            logger.warn('Deprecation warning: timeout_seconds is now renamed to connection_timeout_seconds')

        if config_dict.get('master_node'):
            logger.warn('Deprecation warning: master_node is now consolidated to nodes, starting with Typesense Server v0.12')

        if config_dict.get('read_replica_nodes'):
            logger.warn('Deprecation warning: read_replica_nodes is now consolidated to nodes, starting with Typesense Server v0.12')
