import ocflindex

with ocflindex.Client("https://ocfl-index.fly.dev") as client:
    obj = client.get_object("https://osf.io/9xhsd")
    print(obj)