"""Generate engine comparison graphs for documentation.

Usage:
    cd backend
    uv run python3 scripts/generate_engine_graphs.py

Outputs SVGs to docs/development/img/:
    - engine_comparison_surface.svg — combined score heatmaps for each engine
    - engine_delta_heatmap.svg — difference between engines
    - engine_confidence_regions.svg — confidence threshold boundaries
    - engine_score_profiles.svg — combined score at fixed name_score values
"""

from pathlib import Path

import matplotlib
import matplotlib.pyplot as plt
import numpy as np

matplotlib.use("agg")

OUT_DIR = Path(__file__).resolve().parent.parent.parent / "docs" / "development" / "img"
OUT_DIR.mkdir(parents=True, exist_ok=True)

THRESHOLD_HIGH = 0.85
THRESHOLD_MEDIUM = 0.60


def harmonic(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    with np.errstate(divide="ignore", invalid="ignore"):
        result = np.where(
            (a + b) == 0,
            0.0,
            np.where(
                (a == 0) | (b == 0),
                0.0,
                (2 * a * b) / (a + b),
            ),
        )
    return result


def weighted_avg(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    return (a + b) / 2.0


def engine_comparison_surface():
    """Side-by-side heatmaps of combined score for each engine."""
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))

    x = np.linspace(0, 1, 201)
    y = np.linspace(0, 1, 201)
    X, Y = np.meshgrid(x, y)

    for ax, engine_fn, title in [
        (axes[0], harmonic, "Harmonic Mean"),
        (axes[1], weighted_avg, "Weighted Average"),
    ]:
        Z = engine_fn(X, Y)
        pcm = ax.pcolormesh(X, Y, Z, cmap="viridis", vmin=0, vmax=1, shading="auto")
        contours = ax.contour(
            X,
            Y,
            Z,
            levels=[THRESHOLD_MEDIUM, THRESHOLD_HIGH],
            colors=["white", "white"],
            linestyles=["dashed", "solid"],
            linewidths=1.5,
        )
        ax.clabel(
            contours,
            fmt={THRESHOLD_MEDIUM: "MEDIUM", THRESHOLD_HIGH: "HIGH"},
            fontsize=9,
        )
        ax.set_xlabel("Address Score")
        ax.set_ylabel("Name Score")
        ax.set_title(title)
        ax.set_aspect("equal")
        fig.colorbar(pcm, ax=ax, label="Combined Score")

    fig.suptitle(
        "Matching Engine: Combined Score Surfaces", fontsize=14, fontweight="bold"
    )
    fig.tight_layout()
    path = OUT_DIR / "engine_comparison_surface.svg"
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  {path}")


def engine_delta_heatmap():
    """Heatmap of the difference between engines (weighted - harmonic)."""
    fig, ax = plt.subplots(figsize=(8, 7))

    x = np.linspace(0, 1, 201)
    y = np.linspace(0, 1, 201)
    X, Y = np.meshgrid(x, y)

    H = harmonic(X, Y)
    W = weighted_avg(X, Y)
    delta = W - H

    vmax = np.max(np.abs(delta))
    pcm = ax.pcolormesh(
        X, Y, delta, cmap="RdBu_r", vmin=-vmax, vmax=vmax, shading="auto"
    )
    fig.colorbar(pcm, ax=ax, label="Weighted − Harmonic")

    contours = ax.contour(
        X,
        Y,
        delta,
        levels=[0.01, 0.02, 0.03, 0.04, 0.05],
        colors="black",
        linestyles="dotted",
        linewidths=0.8,
    )
    ax.clabel(contours, fmt="%.2f", fontsize=8)

    ax.set_xlabel("Address Score")
    ax.set_ylabel("Name Score")
    ax.set_title(
        "Weighted Average − Harmonic Mean Delta", fontsize=13, fontweight="bold"
    )
    ax.set_aspect("equal")

    fig.tight_layout()
    path = OUT_DIR / "engine_delta_heatmap.svg"
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  {path}")


def engine_confidence_regions():
    """Confidence boundary comparison."""
    fig, ax = plt.subplots(figsize=(8, 7))

    x = np.linspace(0, 1, 201)
    y = np.linspace(0, 1, 201)
    X, Y = np.meshgrid(x, y)

    H = harmonic(X, Y)
    W = weighted_avg(X, Y)

    ax.contour(X, Y, H, levels=[THRESHOLD_HIGH], colors=["#2563eb"], linewidths=2.5)
    ax.contour(
        X,
        Y,
        H,
        levels=[THRESHOLD_MEDIUM],
        colors=["#2563eb"],
        linewidths=2.0,
        linestyles=["dashed"],
    )
    ax.contour(
        X,
        Y,
        W,
        levels=[THRESHOLD_HIGH],
        colors=["#dc2626"],
        linewidths=2.5,
        linestyles=["dotted"],
    )
    ax.contour(
        X,
        Y,
        W,
        levels=[THRESHOLD_MEDIUM],
        colors=["#dc2626"],
        linewidths=2.0,
        linestyles=["dashdot"],
    )

    ax.plot([], [], color="#2563eb", linewidth=2.5, label="Harmonic HIGH")
    ax.plot(
        [],
        [],
        color="#2563eb",
        linewidth=2.0,
        linestyle="dashed",
        label="Harmonic MEDIUM",
    )
    ax.plot(
        [],
        [],
        color="#dc2626",
        linewidth=2.5,
        linestyle="dotted",
        label="Weighted HIGH",
    )
    ax.plot(
        [],
        [],
        color="#dc2626",
        linewidth=2.0,
        linestyle="dashdot",
        label="Weighted MEDIUM",
    )

    ax.fill_between([0, 1], [0, 0], [0, 0], alpha=0.05, color="green")
    ax.text(
        0.5,
        0.95,
        "HIGH",
        fontsize=14,
        ha="center",
        va="top",
        color="#16a34a",
        fontweight="bold",
    )
    ax.text(
        0.15,
        0.5,
        "MED",
        fontsize=12,
        ha="center",
        va="center",
        color="#ca8a04",
        fontweight="bold",
    )
    ax.text(
        0.05,
        0.05,
        "LOW",
        fontsize=12,
        ha="left",
        va="bottom",
        color="#dc2626",
        fontweight="bold",
    )

    ax.set_xlabel("Address Score")
    ax.set_ylabel("Name Score")
    ax.set_title(
        "Confidence Regions: Harmonic vs Weighted", fontsize=13, fontweight="bold"
    )
    ax.set_aspect("equal")
    ax.legend(loc="center right", fontsize=10)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)

    fig.tight_layout()
    path = OUT_DIR / "engine_confidence_regions.svg"
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  {path}")


def engine_score_profiles():
    """Line plots: combined score vs address score at fixed name scores."""
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))

    addr = np.linspace(0, 1, 201)
    name_levels = [1.0, 0.9, 0.75, 0.6, 0.5, 0.3]

    for ax, engine_fn, title in [
        (axes[0], harmonic, "Harmonic Mean"),
        (axes[1], weighted_avg, "Weighted Average"),
    ]:
        for ns in name_levels:
            combined = engine_fn(np.full_like(addr, ns), addr)
            ax.plot(addr, combined, label=f"name={ns:.2f}", linewidth=1.5)

        ax.axhline(
            y=THRESHOLD_HIGH,
            color="green",
            linestyle=":",
            alpha=0.7,
            label=f"HIGH={THRESHOLD_HIGH}",
        )
        ax.axhline(
            y=THRESHOLD_MEDIUM,
            color="orange",
            linestyle=":",
            alpha=0.7,
            label=f"MEDIUM={THRESHOLD_MEDIUM}",
        )
        ax.set_xlabel("Address Score")
        ax.set_ylabel("Combined Score")
        ax.set_title(title)
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1.05)
        ax.legend(fontsize=8, loc="lower right")
        ax.grid(True, alpha=0.3)

    fig.suptitle(
        "Combined Score vs Address Score (varying name score)",
        fontsize=14,
        fontweight="bold",
    )
    fig.tight_layout()
    path = OUT_DIR / "engine_score_profiles.svg"
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  {path}")


if __name__ == "__main__":
    print("Generating engine comparison graphs...")
    engine_comparison_surface()
    engine_delta_heatmap()
    engine_confidence_regions()
    engine_score_profiles()
    print("Done.")
