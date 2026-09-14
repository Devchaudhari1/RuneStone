from llm import LocalLLM


def main():
    llm = LocalLLM()

    messages = [
        {
            "role": "system",
            "content": (
                "You are Rune Stone, a local AI software engineering agent. "
                "Be concise and technically accurate."
            ),
        },
        {
            "role": "user",
            "content": "Explain what a Python virtual environment is.",
        },
    ]

    response = llm.chat(messages)

    print("\n=== Rune Stone ===\n")
    print(response)


if __name__ == "__main__":
    main()