<script lang="ts">
	import { MatchColumn } from '$lib/workspace-types';

	interface Props {
		column: MatchColumn;
		sortAscending: boolean;
		toggleSort: (sortState: [boolean, MatchColumn]) => void;
	}

	let { column, sortAscending = false, toggleSort }: Props = $props();
	function onSortClick() {
		console.log('column data: ', column);
		toggleSort([!sortAscending, column]);
	}
</script>

{#if column.isSortable}
	<button onclick={onSortClick} class="hover:bg-blue-gray-50 cursor-pointer">
		{column.name}
		<svg
			xmlns="http://www.w3.org/2000/svg"
			fill="none"
			viewBox="0 0 24 24"
			stroke-width="2"
			stroke="currentColor"
			aria-hidden="true"
			class="h-4 w-4"
		>
			<path
				stroke-linecap="round"
				stroke-linejoin="round"
				d="M8.25 15L12 18.75 15.75 15m-7.5-6L12 5.25 15.75 9"
			></path>
		</svg>
	</button>
{:else}
	<p>{column.name}</p>
{/if}
