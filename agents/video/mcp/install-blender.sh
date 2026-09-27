#!/usr/bin/env bash
set -euo pipefail

package_version=0.2.2
blender_executable=/Applications/Blender.app/Contents/MacOS/Blender
install_dir="$HOME/.higgsfield/blender-mcp"

node --version
test -x "$blender_executable"
npm install --prefix "$install_dir" --registry=https://registry.npmjs.org/ \
  --no-audit --no-fund --ignore-scripts "fnf-blender-mcp@$package_version"
node "$install_dir/node_modules/fnf-blender-mcp/dist/cli.js" doctor \
  --blender "$blender_executable"
