import { render, fireEvent } from "@testing-library/svelte";
import { describe, it, expect, vi } from "vitest";
import { Pagination } from "./ui";

describe("Pagination", () => {
  it("renders page size selector", () => {
    const { getByRole } = render(Pagination, {
      totalItems: 100,
      pageSize: 10,
      currentPage: 1,
    });

    const select = getByRole("combobox");
    expect(select).toBeTruthy();
  });

  it("renders current page indicator", () => {
    const { getByText } = render(Pagination, {
      totalItems: 100,
      pageSize: 10,
      currentPage: 2,
    });

    expect(getByText(/Page 2/)).toBeTruthy();
  });

  it("calls onPageChange when next button clicked", async () => {
    const onPageChange = vi.fn();
    const { getByText } = render(Pagination, {
      totalItems: 100,
      pageSize: 10,
      currentPage: 1,
      onPageChange,
    });

    const nextButton = getByText("Next");
    await fireEvent.click(nextButton);

    expect(onPageChange).toHaveBeenCalledWith(2);
  });

  it("calls onPageSizeChange when select changes", async () => {
    const onPageSizeChange = vi.fn();
    const { getByRole } = render(Pagination, {
      totalItems: 100,
      pageSize: 10,
      currentPage: 1,
      onPageSizeChange,
    });

    const select = getByRole("combobox");
    await fireEvent.change(select, { target: { value: "25" } });

    expect(onPageSizeChange).toHaveBeenCalledWith(25);
  });

  it("displays total count correctly", () => {
    const { getByText } = render(Pagination, {
      totalItems: 250,
      pageSize: 25,
      currentPage: 1,
    });

    expect(getByText(/250/)).toBeTruthy();
  });

  it("disables previous on first page", () => {
    const { getByText } = render(Pagination, {
      totalItems: 100,
      pageSize: 10,
      currentPage: 1,
    });

    const prevButton = getByText("Previous") as HTMLButtonElement;
    expect(prevButton.disabled).toBe(true);
  });

  it("disables next on last page", () => {
    const { getByText } = render(Pagination, {
      totalItems: 100,
      pageSize: 10,
      currentPage: 10,
    });

    const nextButton = getByText("Next") as HTMLButtonElement;
    expect(nextButton.disabled).toBe(true);
  });
});
