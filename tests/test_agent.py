import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from agent import RuneStoneAgent


def main():
    agent = RuneStoneAgent()

    result = agent.run( "Explain how FAISS and BGE Embedding works?" )

    print("\n==============================")
    print("Rune Stone")
    print("==============================\n")

    print(result)


if __name__ == "__main__":
    main()