import ocflindex
import grpc

with ocflindex.Client("ocfl-index.fly.dev") as client:
    obj = client.get_object_state("https://osf.io/9xhsd", recursive=True)
    client.request_digest("0407a659e3c6aecd2b8832f6af33610c4cc88a786c03f678cd8b2df791ef06290744871604e3dce31134b520b95f20ab824471b3228d54d88c0af14ded760118")