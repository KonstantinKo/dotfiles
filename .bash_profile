export rvmsudo_secure_path=0

# alias
alias cda='cd /Data/Programmierung/ruby/rails_projects/routiny'
alias cdb='cd /Applications/XAMPP/xamppfiles/htdocs/lessonshark'
alias cdf='cd /Data/Programmierung/ruby/rails_projects/fairmondo'
alias cdc='cd /Data/Programmierung/ruby/rails_projects/clarat'
alias cdq='cd /Data/Programmierung/ruby/rails_projects/cert-quiz'
alias cdq2='cd /Data/Programmierung/ruby/rails_projects/cert_quiz'
alias cdm='cd /Data/Programmierung/meteor/levelup'
alias cdp='cd /Data/Programmierung/'
alias cdj='cd /Data/Programmierung/Python/jasper'
alias bake='cd ~/.cakephp/lib/cake/console;./cake bake'
alias betty='/Data/Programmierung/ruby/betty/main.rb'
alias loadpg='postgres -D /usr/local/var/postgres'
alias loadredis='redis-server /usr/local/etc/redis.conf'
alias loadredis='mongod --config /usr/local/etc/mongod.conf'
alias loades='/Users/tino/elasticsearch-1.3.4/bin/elasticsearch'
alias pushclarat='git push staging develop:master && heroku run rake db:migrate -a clarat-staging'
alias fore='foreman start'
alias fored='foreman start -f Procfile.dev'
alias ftpcbu='sftp -o "IdentityFile=~/.ssh/identity.heroku.clarat" backups@ve425.wsit.network:backups'
alias asdfghjkl='echo "Quit slacking off!"'
alias c="echo \"You\'re not in a pry console anymore...\""

# Git tab completion
source ~/git-completion.bash

# Show branch in status line
source ~/.git-prompt.sh
PS1='[\W$(__git_ps1 " (%s)")]\$ '
export PROMPT_COMMAND='echo -ne "\033]0;${PWD/#$HOME/~}\007"'
##
# Your previous /Users/tino/.bash_profile file was backed up as /Users/tino/.bash_profile.macports-saved_2011-07-24_at_17:45:23
##

# MacPorts Installer addition on 2011-07-24_at_17:45:23: adding an appropriate PATH variable for use with MacPorts.
export PATH=/opt/local/bin:/opt/local/sbin:/usr/local/bin/node:$PATH
# Finished adapting your PATH environment variable for use with MacPorts.

test -r /sw/bin/init.sh && . /sw/bin/init.sh
NNTPSERVER='wieslauf.sub.de' && export NNTPSERVER

# {{{
# Node Completion - Auto-generated, do not touch.
shopt -s progcomp
for f in $(command ls ~/.node-completion); do
  f="$HOME/.node-completion/$f"
  test -f "$f" && . "$f"
done
# }}}

# ENV

export JAVA_HOME=$(/Library/Internet\ Plug-Ins/JavaAppletPlugin.plugin/Contents/Home)

export HISTTIMEFORMAT="%d/%m/%y %T "
export PATH="/usr/local/sbin:$PATH"

[[ -s "$HOME/.rvm/scripts/rvm" ]] && source "$HOME/.rvm/scripts/rvm" # Load RVM into a shell session *as a function*
