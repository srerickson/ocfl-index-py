import ocflindex

with ocflindex.Client("https://ocfl-index.fly.dev") as client:
    for obj in client.list_objects():
        print(obj)