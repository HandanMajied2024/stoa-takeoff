"""Ask a takeoff question about one drawing and see the answer with its full reasoning trace.

    uv run python -m takeoff.ask <drawing path> "How many toilets (WC) are drawn on this floor plan?"
"""

import sys

from . import engine, pipeline, questions


def main():
    path, question = sys.argv[1], " ".join(sys.argv[2:])
    b = pipeline.load(path)
    if b is None:
        sys.exit("No extractor for this drawing type yet.")
    q = questions.parse(question)
    if q is None:
        sys.exit("Question not understood.")
    a = engine.run(b, q)
    print(f"\nANSWER: {a.value} {a.unit}   (confidence {a.confidence:.0%})\n")
    print("How it was calculated:")
    for s in a.steps:
        print("  " + s)
    if a.flags:
        print("\nCheck by a human:")
        for f in a.flags:
            print("  ! " + f)
    print(f"\nQuery: {q.model_dump(exclude_defaults=True)}")


if __name__ == "__main__":
    main()
