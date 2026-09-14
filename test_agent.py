from agent import RuneStoneAgent


def main():
    agent = RuneStoneAgent()

    result = agent.run(
        "Inspect server/llm.py and explain what the LocalLLM class does."
    )

    print("\n==============================")
    print("Rune Stone")
    print("==============================\n")

    print(result)


if __name__ == "__main__":
    main()