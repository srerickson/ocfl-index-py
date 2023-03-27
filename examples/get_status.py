import ocflindex
import grpc


with grpc.secure_channel("ocfl-index.fly.dev", grpc.ssl_channel_credentials()) as channel:
    client = ocflindex.Client(channel)
    print(client.get_status())