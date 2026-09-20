const mcpName = "dev-env-machines";
const mcpUrl = "https://mcp.doinstruct.dev/api/mcp/machines";

export default async function devEnvMcpAuthPlugin() {
  return {
    config(config) {
      const configured = config.mcp?.[mcpName];
      const existing =
        configured && configured.type === "remote" ? configured : {};
      const headers = Object.fromEntries(
        Object.entries(existing.headers ?? {}).filter(
          ([name]) => name.toLowerCase() !== "authorization",
        ),
      );
      const server = {
        ...existing,
        enabled: configured?.enabled ?? true,
        type: "remote",
        url: mcpUrl,
      };

      if (Object.keys(headers).length > 0) {
        server.headers = headers;
      } else {
        delete server.headers;
      }

      if (server.oauth === false) {
        delete server.oauth;
      }

      config.mcp = {
        ...config.mcp,
        [mcpName]: server,
      };
    },
  };
}
