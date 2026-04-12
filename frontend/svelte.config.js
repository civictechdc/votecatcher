import adapterAuto from "@sveltejs/adapter-auto";
import adapterNode from "@sveltejs/adapter-node";

const adapter = process.env.ADAPTER === "node" ? adapterNode() : adapterAuto();

/** @type {import('@sveltejs/kit').Config} */
const config = {
	kit: {
		adapter,
	},
};

export default config;
