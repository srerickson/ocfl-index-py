import ocflindex


with ocflindex.Client("ocfl-index.fly.dev") as client:
    obj = client.get_object("https://osf.io/9xhsd")
    for v in obj.versions:
        print(v)