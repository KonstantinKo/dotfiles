-- Read-only Resolve API probe for Workspace > Console (Lua mode).
local resolve = Resolve()
if not resolve then
    error("Resolve scripting handle is unavailable")
end

local function show(label, value)
    print(label .. ": " .. tostring(value))
end

show("Resolve version", resolve:GetVersionString())

local projectManager = resolve:GetProjectManager()
local project = projectManager and projectManager:GetCurrentProject()
if project then
    show("Project", project:GetName())
    show("Project ID", project:GetUniqueId())

    local timeline = project:GetCurrentTimeline()
    if timeline then
        local settings = timeline:GetSettings()
        if not settings or not settings.timelineFrameRate then
            settings = project:GetSettings()
        end

        show("Timeline", timeline:GetName())
        show("Timeline ID", timeline:GetUniqueId())
        show("Timeline frame rate", settings and settings.timelineFrameRate)
        show("Timeline start frame", timeline:GetStartFrame())
        show("Timeline end frame", timeline:GetEndFrame())
        show("Video tracks", timeline:GetTrackCount("video"))
    else
        show("Timeline", "none selected")
    end
else
    show("Project", "none loaded")
end
