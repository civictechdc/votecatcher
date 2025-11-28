export type StringToType<T extends string> = T extends 'string'
	? string
	: T extends 'Float64'
		? number
		: T extends 'boolean'
			? boolean
			: never; // Fallback for unknown type names
