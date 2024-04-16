import subprocess
from iproute2_amd64_paths import paths

def main():
    print(subprocess.check_output(["ldd", paths()["ip"]], encoding="utf-8"))

if __name__ == "__main__":
    main()