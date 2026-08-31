# If you come from bash you might have to change your $PATH.
# export PATH=$HOME/bin:/usr/local/bin:$PATH

# Path to your oh-my-zsh installation.
export ZSH="$HOME/.oh-my-zsh"

# Set name of the theme to load --- if set to "random", it will
# load a random theme each time oh-my-zsh is loaded, in which case,
# to know which specific one was loaded, run: echo $RANDOM_THEME
# See https://github.com/ohmyzsh/ohmyzsh/wiki/Themes
ZSH_THEME="robbyrussell"

# Set list of themes to pick from when loading at random
# Setting this variable when ZSH_THEME=random will cause zsh to load
# a theme from this variable instead of looking in $ZSH/themes/
# If set to an empty array, this variable will have no effect.
# ZSH_THEME_RANDOM_CANDIDATES=( "robbyrussell" "agnoster" )

# Uncomment the following line to use case-sensitive completion.
# CASE_SENSITIVE="true"

# Uncomment the following line to use hyphen-insensitive completion.
# Case-sensitive completion must be off. _ and - will be interchangeable.
# HYPHEN_INSENSITIVE="true"

# Uncomment one of the following lines to change the auto-update behavior
# zstyle ':omz:update' mode disabled  # disable automatic updates
# zstyle ':omz:update' mode auto      # update automatically without asking
# zstyle ':omz:update' mode reminder  # just remind me to update when it's time

# Uncomment the following line to change how often to auto-update (in days).
# zstyle ':omz:update' frequency 13

# Uncomment the following line if pasting URLs and other text is messed up.
# DISABLE_MAGIC_FUNCTIONS="true"

# Uncomment the following line to disable colors in ls.
# DISABLE_LS_COLORS="true"

# Uncomment the following line to disable auto-setting terminal title.
# DISABLE_AUTO_TITLE="true"

# Uncomment the following line to enable command auto-correction.
# ENABLE_CORRECTION="true"

# Uncomment the following line to display red dots whilst waiting for completion.
# You can also set it to another string to have that shown instead of the default red dots.
# e.g. COMPLETION_WAITING_DOTS="%F{yellow}waiting...%f"
# Caution: this setting can cause issues with multiline prompts in zsh < 5.7.1 (see #5765)
# COMPLETION_WAITING_DOTS="true"

# Uncomment the following line if you want to disable marking untracked files
# under VCS as dirty. This makes repository status check for large repositories
# much, much faster.
# DISABLE_UNTRACKED_FILES_DIRTY="true"

# Uncomment the following line if you want to change the command execution time
# stamp shown in the history command output.
# You can set one of the optional three formats:
# "mm/dd/yyyy"|"dd.mm.yyyy"|"yyyy-mm-dd"
# or set a custom format using the strftime function format specifications,
# see 'man strftime' for details.
# HIST_STAMPS="mm/dd/yyyy"

# Would you like to use another custom folder than $ZSH/custom?
# ZSH_CUSTOM=/path/to/new-custom-folder

# Which plugins would you like to load?
# Standard plugins can be found in $ZSH/plugins/
# Custom plugins may be added to $ZSH_CUSTOM/plugins/
# Example format: plugins=(rails git textmate ruby lighthouse)
# Add wisely, as too many plugins slow down shell startup.
plugins=(git)

source $ZSH/oh-my-zsh.sh

# User configuration

# export MANPATH="/usr/local/man:$MANPATH"

# You may need to manually set your language environment
# export LANG=en_US.UTF-8

# Preferred editor for local and remote sessions
# if [[ -n $SSH_CONNECTION ]]; then
#   export EDITOR='vim'
# else
#   export EDITOR='mvim'
# fi

# Compilation flags
# export ARCHFLAGS="-arch x86_64"

# Set personal aliases, overriding those provided by oh-my-zsh libs,
# plugins, and themes. Aliases can be placed here, though oh-my-zsh
# users are encouraged to define aliases within the ZSH_CUSTOM folder.
# For a full list of active aliases, run `alias`.
#
# Example aliases
# alias zshconfig="mate ~/.zshrc"
# alias ohmyzsh="mate ~/.oh-my-zsh"
alias oco='opencode'
alias odysseus='"/Users/konstantin/projects/os/odysseus/start-macos.sh"'
alias odysseus-up='cd "/Users/konstantin/projects/os/odysseus" && git pull --ff-only origin dev'
alias prestol='cd "/Users/konstantin/projects/os/presto" && cargo tauri dev'

presto-open-last-production-build() {
  local repo="/Users/konstantin/projects/os/presto"
  local -a apps
  apps=("$repo"/target/release/bundle/**/*.app(N/om))

  if (( ${#apps} == 0 )); then
    echo "No local presto production build found. Run: cd \"$repo\" && cargo tauri build"
    return 1
  fi

  open "${apps[1]}"
}
alias presto='presto-open-last-production-build'

# CUSTOM:
if [[ -z "${DEV_ENV_MCP_TOKEN:-}" ]]; then
  dev_env_mcp_token="$(security find-generic-password -a "$USER" -s dev-env-mcp-token -w 2>/dev/null)"
  [[ -n "$dev_env_mcp_token" ]] && export DEV_ENV_MCP_TOKEN="$dev_env_mcp_token"
  unset dev_env_mcp_token
fi

if [[ -z "${DOINSTRUCT_MCP_TOKEN:-}" ]]; then
  doinstruct_mcp_token="$(security find-generic-password -a "$USER" -s doinstruct-mcp-token -w 2>/dev/null)"
  [[ -n "$doinstruct_mcp_token" ]] && export DOINSTRUCT_MCP_TOKEN="$doinstruct_mcp_token"
  unset doinstruct_mcp_token
fi

export PATH=~/.asdf/shims:/Users/konstantin/.asdf/installs/lua/5.4.6/luarocks/bin:$PATH

export NVM_DIR="$HOME/.nvm"
  [ -s "/opt/homebrew/opt/nvm/nvm.sh" ] && \. "/opt/homebrew/opt/nvm/nvm.sh"  # This loads nvm
  [ -s "/opt/homebrew/opt/nvm/etc/bash_completion.d/nvm" ] && \. "/opt/homebrew/opt/nvm/etc/bash_completion.d/nvm"  # This loads nvm bash_completion
export PATH="/opt/homebrew/opt/crowdin@4/bin:$PATH"
export PATH="/Users/konstantin/.bun/bin:$PATH"

# bun completions
[ -s "/Users/konstantin/.bun/_bun" ] && source "/Users/konstantin/.bun/_bun"

# Added by Antigravity
export PATH="/Users/konstantin/.antigravity/antigravity/bin:$PATH"
export PATH="$HOME/.local/bin:$PATH"
export PATH="$HOME/.venvs/llm-stack/bin:$PATH"

. "$HOME/.atuin/bin/env"

eval "$(atuin init zsh)"

# Android SDK
export ANDROID_HOME="/opt/homebrew/share/android-commandlinetools"
export ANDROID_SDK_ROOT="$ANDROID_HOME"
export PATH="$ANDROID_HOME/emulator:$ANDROID_HOME/platform-tools:$ANDROID_HOME/cmdline-tools/latest/bin:$PATH"
export JAVA_HOME="/Users/konstantin/.asdf/installs/java/temurin-17.0.14+7"

# Android ADB functions
phone-deploy() {
  adb install -r ~/projects/aivm/rosary.apk
}

phone-connect() {
  adb connect 192.168.2.58:5555
}

# Start Android emulator and expose ADB server to the VM (192.168.2.58)
# On the VM, set: export ANDROID_ADB_SERVER_ADDRESS=192.168.2.34
emu-start() {
  local avd="${1:-Pixel_9_API35}"
  echo "Restarting ADB server on all interfaces..."
  adb kill-server
  adb -a nodaemon server start &
  echo "Starting emulator: $avd"
  nohup emulator -avd "$avd" > /tmp/emulator.log 2>&1 &
  echo "Emulator starting in background. Logs: tail -f /tmp/emulator.log"
  echo "ADB server listening on 192.168.2.34:5037"
  echo ""
  echo "On the VM, run:  export ANDROID_ADB_SERVER_ADDRESS=192.168.2.34"
  echo "Then check:      adb devices"
}

emu-stop() {
  adb emu kill 2>/dev/null || true
  adb kill-server
  echo "Emulator and ADB server stopped."
}

biblemem-dev() {
  PATH="/opt/homebrew/share/android-commandlinetools/platform-tools:$PATH" \
  adb shell am start -a android.intent.action.VIEW \
    -d "exp+biblemem://expo-development-client/?url=http%3A%2F%2F192.168.64.2%3A8081" \
    com.biblemem.app
}

confessing-scripture-dev() {
  local ADB="PATH=/opt/homebrew/share/android-commandlinetools/platform-tools:$PATH adb"
  eval "$ADB shell am force-stop com.confessing.scripture"
  sleep 1
  eval "$ADB shell am start -n com.confessing.scripture/.MainActivity"
}

# direnv loads repo-local .envrc files after explicit `direnv allow`.
eval "$(direnv hook zsh)"
