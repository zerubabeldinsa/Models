import matplotlib.pyplot as plt

from selection_algorithm import categories, get_random_sample_correlation


def plot_correlation_matrix(category, corr):
    if corr.empty:
        print(f"No correlation data for {category}. Skipping.")
        return

    fig, ax = plt.subplots(figsize=(4, 3))
    cax = ax.imshow(corr.values, cmap="coolwarm", vmin=-1, vmax=1)

    ax.set_title(f"Correlation Matrix - {category.replace('_', ' ').title()}")
    ax.set_xticks(range(len(corr.columns)))
    ax.set_yticks(range(len(corr.index)))
    ax.set_xticklabels(corr.columns, rotation=45, ha="right")
    ax.set_yticklabels(corr.index)

    fig.colorbar(cax, ax=ax, fraction=0.046, pad=0.04)
    fig.tight_layout()


def main():
    for category in categories.keys():
        sampled_symbols, corr = get_random_sample_correlation(category, sample_size=5)
        print(f"{category}: {sampled_symbols}")
        plot_correlation_matrix(category, corr)

    plt.show()


if __name__ == "__main__":
    main()
