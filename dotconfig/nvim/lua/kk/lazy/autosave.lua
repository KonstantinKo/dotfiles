return {
    "Pocco81/auto-save.nvim",
    config = function()
        require("auto-save").setup {}

        -- mnemonic: AutoSave
        vim.keymap.set("n", "<leader>as", ":ASToggle<CR>", {})
        vim.cmd(":ASToggle") -- start disabled
    end,
}
