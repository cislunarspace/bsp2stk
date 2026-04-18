def run_menu():
    while True:
        print("\n=== BSP2STK ===")
        print("1. 转换 BSP → STK")
        print("2. 查看星历信息")
        print("q. 退出")
        choice = input("选择: ").strip()
        if choice == "1":
            convert_flow()
        elif choice == "2":
            info_flow()
        elif choice == "q":
            break

def convert_flow():
    print("转换功能待实现")

def info_flow():
    print("信息功能待实现")