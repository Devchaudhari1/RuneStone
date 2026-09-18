from agent import RuneStoneAgent


def main():
    print("Loading Rune Stone...")

    agent = RuneStoneAgent()

    print("Rune Stone ready.")
    print("Type 'exit' or 'quit' to stop.")

    while True:
        prompt = input("\nYou: ").strip()

        if prompt.lower() in {"exit", "quit"}:
            break

        if not prompt:
            continue

        try:
            response = agent.run(prompt)

            print("\nRune Stone:")
            print(response)

        except Exception as exc:
            print(f"\nError: {exc}")


if __name__ == "__main__":
    main()