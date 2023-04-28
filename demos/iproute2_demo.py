import subprocess

def main():
    print(subprocess.check_output(["ldd", "../iproute2_amd64~5.15.0-1ubuntu2/bin/ip"], encoding="utf-8"))

if __name__ == "__main__":
    main()