"""
Generate all visualization panels for both papers.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from visualizations.paper1_panels import generate_all_panels as generate_paper1
from visualizations.paper2_panels import generate_all_panels as generate_paper2


def main():
    print("=" * 70)
    print("GENERATING VISUALIZATION PANELS")
    print("=" * 70)

    print("\n" + "=" * 70)
    print("Paper 1: disease-computing-framework.tex")
    print("=" * 70)
    generate_paper1()

    print("\n" + "=" * 70)
    print("Paper 2: disease-partition-state-equations.tex")
    print("=" * 70)
    generate_paper2()

    print("\n" + "=" * 70)
    print("ALL PANELS GENERATED SUCCESSFULLY")
    print("=" * 70)


if __name__ == "__main__":
    main()
