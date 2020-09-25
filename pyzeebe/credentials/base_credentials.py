from grpc import ChannelCredentials


class BaseCredentials(object):
    grpc_credentials: ChannelCredentials
