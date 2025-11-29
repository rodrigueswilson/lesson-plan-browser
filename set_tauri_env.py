import winreg


def set_user_env(name: str, value: str) -> None:
    with winreg.OpenKey(
        winreg.HKEY_CURRENT_USER,
        r"Environment",
        0,
        winreg.KEY_SET_VALUE,
    ) as key:
        winreg.SetValueEx(key, name, 0, winreg.REG_SZ, value)


def main() -> None:
    set_user_env("TAURI_CLI_NO_DEV_SERVER_WAIT", "true")
    set_user_env("TAURI_CLI_NO_DEV_SERVER", "1")
    set_user_env("TAURI_CLI_GENERATE_DEVSERVER_CONFIG", "0")
    print("Updated TAURI_CLI_NO_DEV_SERVER_WAIT=true")
    print("Updated TAURI_CLI_NO_DEV_SERVER=1")
    print("Updated TAURI_CLI_GENERATE_DEVSERVER_CONFIG=0")
    print("Open a new terminal session to use these values.")


if __name__ == "__main__":
    main()
