import ocflindex

with ocflindex.Client("https://ocfl-index.fly.dev") as client:
    print(client.get_status())