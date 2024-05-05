-- relative line numbering
vim.opt.number = true
vim.opt.relativenumber = true
vim.opt.signcolumn = "number"

-- indentation setup
vim.opt.tabstop = 4
vim.opt.softtabstop = 4
vim.opt.shiftwidth = 4
vim.opt.expandtab = true

vim.opt.smartindent = true

-- no vim backups, instead allow undotree to access history
vim.opt.swapfile = false
vim.opt.backup = false
vim.opt.undodir = os.getenv("HOME") .. "/.vim/undodir"
vim.opt.undofile = true

-- colors
vim.opt.termguicolors = true
vim.opt.colorcolumn = "80"

-- scroll
vim.opt.scrolloff = 8

---- Auto Commands ----------------------

-- Normalization:
-- Delete trailing white space on save

-- au BufWrite * silent call DeleteTrailingWS()
vim.api.nvim_create_autocmd(
{ "BufWrite" }, {
    pattern = "*",
    callback = function()
        vim.cmd.normal("mz")
        vim.api.nvim_exec([[%s/\s\+$//ge]], false)
        vim.cmd.normal("`z")
    end
})

-- no auto commenting!
vim.api.nvim_create_autocmd(
{ "BufWinEnter", "BufNewFile" }, {
    pattern = "*",
    callback = function()
        vim.opt.formatoptions:remove { "c", "r", "o" }
    end
})

