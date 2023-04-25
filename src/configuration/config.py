from environs import Env


class Config:
    def __init__(self, path: str) -> None:
        env: Env = Env()
        env.read_env(path)
        self.name: str = env("NAME")
        self.ostype: str = env("OS_TYPE")
        self.ram: str = env("RAM_MEMORY")
        self.sockets: str = env("SOCKETS")
        self.cores: str = env("CORES")
        self.ide1: str = env("IDE1")
        self.ide2: str = env("IDE2")
        self.size_ide1: str = env("SIZE_IDE1")
        self.size_ide2: str = env("SIZE_IDE2")
        self.vm_storage: str = env("VM_STORAGE")
        self.node_storage_name: str = env("NODE_STORAGE_NAME")
        self.brigde: str = env("BRIDGE")
        self.firewall: str = env("FIREWALL")
