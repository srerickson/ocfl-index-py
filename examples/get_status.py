import ocflindex

with ocflindex.Client("ocfl-index.fly.dev") as client:
    print(client.get_status())