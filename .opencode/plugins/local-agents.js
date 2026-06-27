export const LocalAgentsPlugin = async ({ $, client }) => {
  return {
    event: async ({ event }) => {
      if (event.type !== "session.created") return

      try {
        const result = await $`.agents/hooks/scripts/read-local-agents.sh`
        const output = (await result.text()).trim()
        if (!output) return

        await client.app.log({
          body: {
            service: "local-agents",
            level: "info",
            message: "Local AGENTS preferences found. Run .agents/hooks/scripts/read-local-agents.sh to load them.",
            extra: { content: output },
          },
        })
      } catch {
        // Script not found or no local file — silent exit
      }
    },
  }
}
