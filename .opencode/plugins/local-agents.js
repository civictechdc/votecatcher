export const LocalAgentsPlugin = async ({ $, client }) => {
  return {
    event: async ({ event }) => {
      if (event.type !== "session.created") return

      try {
        const result = await $`.agents/hooks/scripts/read-agents.sh --plain`
        const output = (await result.text()).trim()
        if (!output) return

        await client.app.log({
          body: {
            service: "read-agents",
            level: "info",
            message: "AGENTS.md and local preferences loaded. See hook output for details.",
            extra: { content: output },
          },
        })
      } catch {
        // Script not found — silent exit
      }
    },
  }
}
