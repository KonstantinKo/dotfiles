-- LEADER!
vim.g.mapleader = " "
vim.g.maplocalleader = "\\"

vim.keymap.set("n", "<leader>pv", vim.cmd.Ex)

-- move lines in vis mode
vim.keymap.set("v", "J", ":m '>+1<CR>gv=gv")
vim.keymap.set("v", "K", ":m '<-2<CR>gv=gv")

-- leave cursor on half-page jumps
vim.keymap.set("n", "<C-d>", "<C-d>zz")
vim.keymap.set("n", "<C-u>", "<C-u>zz")

-- paste/del without replacing buffer! (FINALLY)
vim.keymap.set("x", "<leader>p", "\"_dP")

vim.keymap.set("n", "<leader>d", "\"_d")
vim.keymap.set("v", "<leader>d", "\"_d")

-- yank to system clipboard
vim.keymap.set("n", "<leader>y", "\"+y")
vim.keymap.set("v", "<leader>y", "\"+y")
vim.keymap.set("n", "<leader>Y", "\"+Y")

-- Q sucks
vim.keymap.set("n", "Q", "<nop>")

-- replace currently hovered word in file
vim.keymap.set("n", "<leader>s", [[:%s/\<<C-r><C-w>\>/<C-r><C-w>/gI<Left><Left><Left>]])

-- CTRL+HJKL + = window / split movement
for i = 0,9,1 do
    vim.keymap.set("n", "<leader>" .. i, ":" .. i .. "wincmd w<CR>")
end
vim.keymap.set("n", "<C-h>", "<C-w>h")
vim.keymap.set("n", "<C-l>", "<C-w>l")
vim.keymap.set("n", "<C-j>", "<C-w>j")
vim.keymap.set("n", "<C-k>", "<C-w>k")
-- visual CTRL-J/K are context dependent: move in autocomplete selection OR split windows
-- DOESNT WORK YET
-- vim.keymap.set('i', '<C-j>', function() return vim.fn.pumvisible() == 1 and '<C-n>' or '<Esc>ji' end, {silent = true, expr = true})
-- vim.keymap.set('i', '<C-k>', function() return vim.fn.pumvisible() == 1 and '<C-p>' or '<Esc>ki' end, {silent = true, expr = true})

-- indent entire file
vim.keymap.set("n", "=af", "mzggVG='z")

-- clear indentation
vim.keymap.set("n", "\\", ":nohl<CR>")

-- Quicksave
vim.keymap.set("n", "<C-s>", ":w<CR>")
-- Indent lines with tab
vim.keymap.set("v", "<tab>", ">gv")
vim.keymap.set("v", "<S-tab>", "<gv")

