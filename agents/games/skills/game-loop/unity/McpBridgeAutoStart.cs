using MCPForUnity.Editor.Services.Transport.Transports;
using UnityEditor;
using UnityEngine;

// Starts the MCP for Unity bridge in stdio mode whenever this project opens,
// so a plain `unity open` is enough for codg's Unity MCP to connect.
[InitializeOnLoad]
static class McpBridgeAutoStart
{
    static McpBridgeAutoStart()
    {
        if (Application.isBatchMode) return;
        EditorPrefs.SetBool("MCPForUnity.UseHttpTransport", false);
        EditorPrefs.SetBool("MCPForUnity.TelemetryDisabled", true);
        EditorApplication.delayCall += () =>
        {
            if (!StdioBridgeHost.IsRunning) StdioBridgeHost.StartAutoConnect();
        };
    }
}
