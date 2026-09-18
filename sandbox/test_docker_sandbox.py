from sandbox.docker_sandbox import DockerSandbox


def main():
    sandbox = DockerSandbox()

    print("\n=== Python ===")
    print(
        sandbox.run(
            ["python", "--version"]
        )
    )

    print("\n=== Workspace ===")
    print(
        sandbox.run(
            [
                "python",
                "-c",
                "print('Hello from Rune Stone sandbox')",
            ]
        )
    )

    print("\n=== Pytest ===")
    print(
        sandbox.run(
            ["pytest", "--version"]
        )
    )


if __name__ == "__main__":
    main()