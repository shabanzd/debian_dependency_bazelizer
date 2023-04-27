import subprocess

IP_PATH = "../iproute2_amd64/bin/ip"

def main():
    print(subprocess.check_output(["ldd", IP_PATH]))

if __name__ == "__main__":
    main()