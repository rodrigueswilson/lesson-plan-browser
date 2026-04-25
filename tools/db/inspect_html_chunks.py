import os

path = r'd:\LP\temp_u2\originals\Unit_2__Area_and_Multiplication.html'
with open(path, 'r', encoding='utf-8', errors='ignore') as f:
    for s in [1500000, 2000000, 3000000, 4500000]:
        f.seek(s)
        print(f"--- AT {s} ---")
        print(f.read(4000))
        print("\n\n")
