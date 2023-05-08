import ocflindex

with ocflindex.Client("https://ocfl-index.fly.dev") as client:
    obj = client.get_object_state("https://osf.io/9xhsd", recursive=True)
    for ch in obj.children:
        print(f"[{ch.digest}] {ch.name}")
