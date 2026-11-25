
import os
import random
import re
import statistics
import sys
from collections import Counter


DEFAULT_SOURCE = "python_class_question.html"


def load_html(source):
    if source.startswith(("http://", "https://")):
        from urllib.request import urlopen
        with urlopen(source) as resp:
            return resp.read().decode("utf-8", errors="ignore")
    with open(source, encoding="utf-8", errors="ignore") as f:
        return f.read()


def extract_colours(html):
    colours = []
    for row in re.findall(r"<tr.*?>(.*?)</tr>", html, re.S | re.I):
        cells = re.findall(r"<t[dh].*?>(.*?)</t[dh]>", row, re.S | re.I)
        if len(cells) < 2:
            continue
        day, colour_cell = cells[0], cells[1]
        if re.search(r"day\b", day, re.I) and re.search(r"colou?rs?", colour_cell, re.I):
            continue  # header row
        colour_cell = re.sub(r"<.*?>", " ", colour_cell)
        for c in colour_cell.split(","):
            c = c.strip().upper()
            if c:
                colours.append(c)
    return colours


def mean_colour(freq):
    avg = statistics.mean(freq.values())
    colour = min(freq, key=lambda c: abs(freq[c] - avg))
    return colour, avg


def most_worn(freq):
    return freq.most_common(1)[0]


def median_colour(freq):
    ordered = sorted(freq.items(), key=lambda kv: (kv[1], kv[0]))
    return ordered[len(ordered) // 2]


def variance_of_frequencies(freq):
    values = list(freq.values())
    return statistics.pvariance(values), statistics.variance(values)


def probability(colours, target="RED"):
    return colours.count(target) / len(colours)


def save_to_postgres(freq):
    import psycopg2

    conn = psycopg2.connect(
        host=os.getenv("PGHOST", "localhost"),
        port=os.getenv("PGPORT", "5432"),
        dbname=os.getenv("PGDATABASE", "postgres"),
        user=os.getenv("PGUSER", "postgres"),
        password=os.getenv("PGPASSWORD", ""),
    )
    with conn, conn.cursor() as cur:
        cur.execute(
            """CREATE TABLE IF NOT EXISTS colour_frequency (
                   colour    VARCHAR(50) PRIMARY KEY,
                   frequency INTEGER NOT NULL
               )"""
        )
        for colour, count in freq.items():
            cur.execute(
                """INSERT INTO colour_frequency (colour, frequency)
                   VALUES (%s, %s)
                   ON CONFLICT (colour) DO UPDATE SET frequency = EXCLUDED.frequency""",
                (colour, count),
            )
    conn.close()

def recursive_search(numbers, target, index=0):
    """Return the index of target in numbers, or -1. Pure recursion."""
    if index >= len(numbers):
        return -1
    if numbers[index] == target:
        return index
    return recursive_search(numbers, target, index + 1)


def random_binary_to_decimal():
    binary = "".join(random.choice("01") for _ in range(4))
    decimal = 0
    for digit in binary:
        decimal = decimal * 2 + int(digit)
    assert decimal == int(binary, 2)
    return binary, decimal


def fibonacci_sum(n=50):
    a, b, total = 0, 1, 0
    for _ in range(n):
        total += a
        a, b = b, a + b
    return total


def main():
    source = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_SOURCE
    if source.startswith(("http://", "https://")) or os.path.exists(source):
        colours = extract_colours(load_html(source))
        freq = Counter(colours)
        print("Frequencies:", dict(freq.most_common()))

        colour, avg = mean_colour(freq)
        print(f"1. Mean colour: {colour} (average frequency = {avg:.2f})")

        colour, n = most_worn(freq)
        print(f"2. Most worn colour: {colour} ({n} times)")

        colour, n = median_colour(freq)
        print(f"3. Median colour: {colour} ({n} times)")

        pvar, svar = variance_of_frequencies(freq)
        print(f"4. Variance of frequencies: population={pvar:.4f}, sample={svar:.4f}")

        print(f"5. P(red) = {probability(colours):.4f}")

        try:
            save_to_postgres(freq)
            print("6. Saved to PostgreSQL table colour_frequency")
        except Exception as exc:
            print("6. Could not save to PostgreSQL:", exc)
    else:
        print(f"(Could not find '{source}' - put the HTML file in the same folder "
              "as this script, or pass its path/URL. Skipping questions 1-6)")

    nums = [3, 8, 15, 22, 41, 57, 63]
    raw = input(f"7. Enter a number to search for in {nums}: ")
    idx = recursive_search(nums, int(raw))
    print(f"   Found at index {idx}" if idx != -1 else "   Not found")

    binary, decimal = random_binary_to_decimal()
    print(f"8. Random binary {binary} = {decimal} in base 10")

    print(f"9. Sum of first 50 Fibonacci numbers = {fibonacci_sum(50)}")


if __name__ == "__main__":
    main()