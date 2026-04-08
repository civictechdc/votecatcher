<script lang="ts">
  import { cn } from "$lib/utils/cn";

  interface Props {
    totalItems: number;
    pageSize: number;
    currentPage: number;
    onPageChange: (page: number) => void;
    onPageSizeChange: (size: number) => void;
    class?: string;
  }

  let {
    totalItems,
    pageSize,
    currentPage,
    onPageChange,
    onPageSizeChange,
    class: className,
  }: Props = $props();

  const pageSizes = [10, 25, 50, 100];

  const totalPages = $derived(Math.ceil(totalItems / pageSize));
  const startItem = $derived((currentPage - 1) * pageSize + 1);
  const endItem = $derived(Math.min(currentPage * pageSize, totalItems));

  function handlePrevious() {
    if (currentPage > 1) {
      onPageChange(currentPage - 1);
    }
  }

  function handleNext() {
    if (currentPage < totalPages) {
      onPageChange(currentPage + 1);
    }
  }

  function handlePageSizeChange(e: Event) {
    const target = e.target as HTMLSelectElement;
    onPageSizeChange(parseInt(target.value, 10));
  }
</script>

<div class={cn("flex items-center justify-between px-4 py-3", className)}>
  <div class="flex items-center gap-4">
    <span class="text-sm text-muted-foreground">
      Showing {startItem}-{endItem} of {totalItems}
    </span>

    <div class="flex items-center gap-2">
      <label for="page-size" class="text-sm text-muted-foreground">Rows:</label>
      <select
        id="page-size"
        class="h-9 rounded-md border border-input bg-background px-2 text-sm focus-visible:border-ring focus-visible:ring-ring/50 focus-visible:ring-[3px]"
        value={pageSize}
        onchange={handlePageSizeChange}
      >
        {#each pageSizes as size}
          <option value={size}>{size}</option>
        {/each}
      </select>
    </div>
  </div>

  <div class="flex items-center gap-2">
    <span class="text-sm text-muted-foreground">
      Page {currentPage} of {totalPages}
    </span>

    <div class="flex gap-1">
      <button
        type="button"
        class="px-3 py-1 text-sm rounded-md bg-secondary text-secondary-foreground hover:bg-accent disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        onclick={handlePrevious}
        disabled={currentPage <= 1}
      >
        Previous
      </button>

      <button
        type="button"
        class="px-3 py-1 text-sm rounded-md bg-secondary text-secondary-foreground hover:bg-accent disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        onclick={handleNext}
        disabled={currentPage >= totalPages}
      >
        Next
      </button>
    </div>
  </div>
</div>
