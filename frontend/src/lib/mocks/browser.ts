import { setupWorker } from "msw/browser";
import { handlers } from "./handlers";

// Browser worker instance used for client-side interception in dev.
// Exported so init helper can import dynamically.
export const worker = setupWorker(...handlers);
