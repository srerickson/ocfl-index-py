import ocflindex
import grpc


with grpc.secure_channel("ocfl-index.fly.dev", grpc.ssl_channel_credentials()) as channel:
    client = ocflindex.Client(channel)
    for obj in client.list_objects():
        print(obj.object_id)