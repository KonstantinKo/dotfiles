# Path to your oh-my-zsh installation.
export ZSH=/Users/tino/.oh-my-zsh

# Set name of the theme to load.
# Look in ~/.oh-my-zsh/themes/
# Optionally, if you set this to "random", it'll load a random theme each
# time that oh-my-zsh is loaded.
ZSH_THEME="robbyrussell"

# Uncomment the following line to use case-sensitive completion.
# CASE_SENSITIVE="true"

# Uncomment the following line to use hyphen-insensitive completion. Case
# sensitive completion must be off. _ and - will be interchangeable.
# HYPHEN_INSENSITIVE="true"

# Uncomment the following line to disable bi-weekly auto-update checks.
# DISABLE_AUTO_UPDATE="true"

# Uncomment the following line to change how often to auto-update (in days).
# export UPDATE_ZSH_DAYS=13

# Uncomment the following line to disable colors in ls.
# DISABLE_LS_COLORS="true"

# Uncomment the following line to disable auto-setting terminal title.
# DISABLE_AUTO_TITLE="true"

# Uncomment the following line to enable command auto-correction.
# ENABLE_CORRECTION="true"

# Uncomment the following line to display red dots whilst waiting for completion.
# COMPLETION_WAITING_DOTS="true"

# Uncomment the following line if you want to disable marking untracked files
# under VCS as dirty. This makes repository status check for large repositories
# much, much faster.
# DISABLE_UNTRACKED_FILES_DIRTY="true"

# Uncomment the following line if you want to change the command execution time
# stamp shown in the history command output.
# The optional three formats: "mm/dd/yyyy"|"dd.mm.yyyy"|"yyyy-mm-dd"
# HIST_STAMPS="mm/dd/yyyy"

# Would you like to use another custom folder than $ZSH/custom?
# ZSH_CUSTOM=/path/to/new-custom-folder

# Which plugins would you like to load? (plugins can be found in ~/.oh-my-zsh/plugins/*)
# Custom plugins may be added to ~/.oh-my-zsh/custom/plugins/
# Example format: plugins=(rails git textmate ruby lighthouse)
# Add wisely, as too many plugins slow down shell startup.
plugins=(git osx)

# User configuration

# export MANPATH="/usr/local/man:$MANPATH"

source $ZSH/oh-my-zsh.sh

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

# ssh
# export SSH_KEY_PATH="~/.ssh/dsa_id"

# Set personal aliases, overriding those provided by oh-my-zsh libs,
# plugins, and themes. Aliases can be placed here, though oh-my-zsh
# users are encouraged to define aliases within the ZSH_CUSTOM folder.
# For a full list of active aliases, run `alias`.
#
# Example aliases
# alias zshconfig="mate ~/.zshrc"
# alias ohmyzsh="mate ~/.oh-my-zsh"
alias cda='cd /Data/Programmierung/js/meteor/adventuremaster'
alias cdc='cd /Data/Programmierung/ruby/rails_projects/clarat'
alias cdd='cd /Data/Programmierung/ruby/rails_projects/d21'
alias cde='cd /Data/Programmierung/elixir/'
alias cdex='cd ~/exercism/'
alias cdf='cd /Data/Programmierung/ruby/rails_projects/fairmondo'
alias cdj='cd /Data/Programmierung/Python/jasper'
alias cdm='cd /Data/Programmierung/js/meteor'
alias cdn='cd /Data/Programmierung/js/node'
alias cdp='cd /Data/Programmierung/'
alias cdr='cd /Data/Programmierung/ruby/rails_projects'
alias betty='/Data/Programmierung/ruby/betty/main.rb'
alias loadpg='postgres -D /usr/local/var/postgres'
alias loadredis='redis-server /usr/local/etc/redis.conf'
alias loadredis='mongod --config /usr/local/etc/mongod.conf'
alias pushclarat='git push staging develop:master && heroku run rake db:migrate -a clarat-staging'
alias fore='foreman start'
alias fored='foreman start -f Procfile.dev'
alias ftpcbu='sftp -o "IdentityFile=~/.ssh/identity.heroku.clarat" backups@ve425.wsit.network:backups'

# from .bashrc & .bash_profile
export HISTTIMEFORMAT="%d/%m/%y %T "

# added by travis gem
source /Users/tino/.travis/travis.sh

PATH="/usr/local/sbin:/opt/local/bin:/opt/local/sbin:/usr/local/bin/node:/Users/tino/.rvm/gems/ruby-2.2.2/bin:/Users/tino/.rvm/gems/ruby-2.2.2@global/bin:/Users/tino/.rvm/rubies/ruby-2.2.2/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin:/opt/X11/bin:/Users/tino/.rvm/bin:/Users/tino/.rvm/bin:/Users/tino/bin:/Users/tino/.rvm/bin:$PATH"
### Added by the Heroku Toolbelt
PATH="/usr/local/heroku/bin:$PATH"

export PATH="$PATH:$HOME/.rvm/bin" # Add RVM to PATH for scripting
source $HOME/.rvm/scripts/rvm

export NVM_DIR="/Users/tino/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && . "$NVM_DIR/nvm.sh"  # This loads nvm

eval "$(pyenv init -)" # Pyenv
