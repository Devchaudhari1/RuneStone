from tools.terminal import run_command


def test_workspace_write():
    result = run_command(
        "python -c \"from pathlib import Path; Path('/workspace/security_test.txt').write_text('ok')\""
    )
    print("\n=== WORKSPACE WRITE ===")
    print(result)


def test_host_isolation():
    result = run_command(
        "python -c \"import os; print(os.path.exists('/mnt/c/Users'))\""
    )
    print("\n=== HOST ISOLATION ===")
    print(result)


def test_network_isolation():
    result = run_command(
        "python -c \"import urllib.request; urllib.request.urlopen('https://example.com', timeout=3)\""
    )
    print("\n=== NETWORK ISOLATION ===")
    print(result)


def test_non_root():
    result = run_command("id")
    print("\n=== USER ===")
    print(result)


def test_read_only_root():
    result = run_command(
        "python -c \"open('/sandbox_root_test.txt','w').write('x')\""
    )
    print("\n=== READ-ONLY ROOT ===")
    print(result)


def test_timeout():
    result = run_command(
        "python -c \"import time; time.sleep(10)\"",
        timeout=3,
    )
    print("\n=== TIMEOUT ===")
    print(result)


def test_command_allowlist():
    result = run_command("powershell Get-ChildItem")
    print("\n=== COMMAND ALLOWLIST ===")
    print(result)


if __name__ == "__main__":
    test_workspace_write()
    test_host_isolation()
    test_network_isolation()
    test_non_root()
    test_read_only_root()
    test_timeout()
    test_command_allowlist()