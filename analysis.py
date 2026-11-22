# analysis.py
# Analysis of Airbnb listings in the Lisbon area.
# The program reads the Inside Airbnb dataset, cleans the prices,
# and answers questions about prices, neighbourhoods, and room types.

import pandas as pd
import matplotlib.pyplot as plt

# Path to the dataset downloaded from Inside Airbnb
DATA_FILE = "data/listings.csv.gz"

# Only these columns are needed for the analysis
COLUMNS = [
    "neighbourhood_group_cleansed",
    "neighbourhood_cleansed",
    "room_type",
    "price",
    "number_of_reviews",
    "review_scores_rating",
]

# Listings above this price per night are treated as unrealistic
MAX_PRICE = 1000
MIN_LISTINGS = 30
NAME_FIXES = {
    "Belm": "Belém",
    "Misericrdia": "Misericórdia",
    "Parque das Naes": "Parque das Nações",
    "Santo Antnio": "Santo António",
    "So Vicente": "São Vicente",
    "So Domingos de Benfica": "São Domingos de Benfica",
    "Alcntara": "Alcântara",
    "Penha de Frana": "Penha de França",
    "Lourinh": "Lourinhã",
}
# File where the bar chart is saved
CHART_FILE = "top_parishes_chart.png"


def load_data(file_path):
    """Read the CSV file and keep only the columns used in the analysis."""
    return pd.read_csv(file_path, usecols=COLUMNS)


def convert_price(price_column):
    """Convert prices from text (for example "$1,200.00") to numbers (1200.0).

    The "$" sign is only a technical detail of the export. The real
    currency of the Lisbon data is the euro.
    """
    return (
        price_column
        .str.replace("$", "", regex=False)
        .str.replace(",", "", regex=False)
        .astype(float)
    )


def clean_data(df):
    """Return a new DataFrame with numeric prices and no invalid rows.

    It fixes neighbourhood names that lost their Portuguese letters,
    removes listings with no price, and removes listings with a price
    higher than MAX_PRICE, because they would distort the averages.
    """
    clean_df = df.copy()
    clean_df["price"] = convert_price(clean_df["price"])
    clean_df = clean_df.dropna(subset=["price"])
    clean_df = clean_df[clean_df["price"] <= MAX_PRICE]
    clean_df["neighbourhood_cleansed"] = clean_df["neighbourhood_cleansed"].replace(NAME_FIXES)
    clean_df["neighbourhood_group_cleansed"] = clean_df["neighbourhood_group_cleansed"].replace(NAME_FIXES)
    return clean_df


def print_title(title):
    """Print a section title so the output is easy to read."""
    print("\n" + "=" * 60)
    print(title)
    print("=" * 60)


def print_cleaning_summary(original_df, clean_df):
    """Show how many listings were removed during the cleaning step."""
    print_title("DATA CLEANING")
    removed = len(original_df) - len(clean_df)
    print(f"Listings in the original file: {len(original_df):,}")
    print(f"Listings removed: {removed:,}")
    print(f"Listings used in the analysis: {len(clean_df):,}")
    print(f"Average price: €{clean_df['price'].mean():.2f}")
    print(f"Median price: €{clean_df['price'].median():.2f}")


def summarize_prices(df, group_column):
    """Group the listings by one column and summarize their prices.

    Returns a table with the number of listings, the average price,
    and the median price for each group.
    """
    return df.groupby(group_column)["price"].agg(
        listings="count",
        average_price="mean",
        median_price="median",
    )


def answer_question_1(df):
    """Find the parishes in the city of Lisbon with the highest average price.

    Only parishes with at least MIN_LISTINGS listings are included, so a
    few expensive listings cannot put a small parish at the top.
    Returns a table with the number of listings, the average price,
    and the median price of each parish.
    """
    lisbon_df = df[df["neighbourhood_group_cleansed"] == "Lisboa"]
    parishes = summarize_prices(lisbon_df, "neighbourhood_cleansed")
    parishes = parishes[parishes["listings"] >= MIN_LISTINGS]
    return parishes.sort_values("average_price", ascending=False)


def print_question_1(parishes):
    """Print the 10 most expensive and the 3 cheapest parishes."""
    print_title("QUESTION 1: Most expensive parishes in the city of Lisbon")
    print(f"Parishes with at least {MIN_LISTINGS} listings: {len(parishes)}")
    print("\nTop 10 most expensive parishes:")
    print(parishes.head(10).round(2))
    print("\nThe 3 cheapest parishes:")
    print(parishes.tail(3).round(2))


def answer_question_2(df):
    """Compare the room types by number of listings and price.

    Returns a table with the number of listings, the percentage of all
    listings, the average price, and the median price of each room type,
    sorted from the most common to the least common.
    """
    room_types = summarize_prices(df, "room_type")
    total = room_types["listings"].sum()
    room_types["percentage"] = room_types["listings"] / total * 100
    return room_types.sort_values("listings", ascending=False)


def print_question_2(room_types):
    """Print the room type table and compare entire homes with private rooms."""
    print_title("QUESTION 2: Room types and their prices")
    print(room_types.round(2))

    most_common = room_types.index[0]
    percentage = room_types.loc[most_common, "percentage"]
    print(f"\nThe most common room type is '{most_common}' ({percentage:.1f}%).")

    entire_home = room_types.loc["Entire home/apt", "average_price"]
    private_room = room_types.loc["Private room", "average_price"]
    print(f"On average, an entire home costs {entire_home / private_room:.1f} "
        f"times more than a private room.")


def answer_question_3(df):
    """Compare the prices of the city of Lisbon with the nearby towns.

    Only municipalities with at least MIN_LISTINGS listings are included.
    Returns the municipalities sorted from the most to the least expensive.
    """
    municipalities = summarize_prices(df, "neighbourhood_group_cleansed")
    municipalities = municipalities[municipalities["listings"] >= MIN_LISTINGS]
    return municipalities.sort_values("average_price", ascending=False)


def print_question_3(municipalities):
    """Print the municipalities and the position of the city of Lisbon."""
    print_title("QUESTION 3: Is Lisbon more expensive than nearby towns?")
    print(municipalities.round(2))
    position = list(municipalities.index).index("Lisboa") + 1
    print(f"\nThe city of Lisbon is number {position} of {len(municipalities)} "
          f"municipalities by average price.")


def plot_top_parishes(parishes, file_path):
    """Draw a horizontal bar chart with the 10 most expensive parishes.

    The most expensive parish is shown at the top, and each bar shows
    its average price. The chart is saved as an image and then displayed.
    """
    top_10 = parishes.head(10).sort_values("average_price")

    fig, ax = plt.subplots(figsize=(10, 6))
    bars = ax.barh(top_10.index, top_10["average_price"], color="#2a78d6", height=0.6)
    ax.bar_label(bars, fmt="€%.0f", padding=4, color="#52514e")

    ax.set_title("Top 10 most expensive parishes in Lisbon (average price per night)",
                 loc="left", fontsize=13)
    ax.set_xlabel("Average price per night (€)")
    ax.margins(x=0.08)
    ax.grid(axis="x", color="#e5e4e0")
    ax.set_axisbelow(True)
    ax.spines[["top", "right"]].set_visible(False)

    fig.tight_layout()
    fig.savefig(file_path, dpi=150)
    print(f"\nChart saved as {file_path}")
    plt.show()


def main():
    """Run every step of the analysis in order."""
    original_df = load_data(DATA_FILE)
    clean_df = clean_data(original_df)
    print_cleaning_summary(original_df, clean_df)
    parishes = answer_question_1(clean_df)
    print_question_1(parishes)
    room_types = answer_question_2(clean_df)
    print_question_2(room_types)
    plot_top_parishes(parishes, CHART_FILE)
    municipalities = answer_question_3(clean_df)
    print_question_3(municipalities)


if __name__ == "__main__":
    main()