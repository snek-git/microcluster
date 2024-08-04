import sys

def main():
    name = sys.argv[1] if len(sys.argv) > 1 else "World"
    print(f"Hello, {name}!")
    print("This is a test script running on the microcluster system.")

if __name__ == "__main__":
    main()