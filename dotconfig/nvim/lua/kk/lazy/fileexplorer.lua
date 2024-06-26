-- File Explorer

-- return {
--     "nvim-tree/nvim-tree.lua",
--     version = "*",
--     lazy = false,
--     dependencies = {
--         "nvim-tree/nvim-web-devicons",
--     },
--     config = function()
--         require("nvim-tree").setup({})
--         vim.keymap.set("n", "<leader>n", ":NvimTreeFindFile<CR>")
--     end,
--  }

return {
    "nvim-neo-tree/neo-tree.nvim",
    branch = "v3.x",
    dependencies = {
        "nvim-lua/plenary.nvim",
        "nvim-tree/nvim-web-devicons", -- not strictly required, but recommended
        "MunifTanjim/nui.nvim",
        -- "3rd/image.nvim", -- Optional image support in preview window: See `# Preview Mode` for more information
    },
    config = function()
        require('neo-tree').setup({
            default_component_configs = {
                filesystem = {
                    follow_current_file = {
                        enabled = true,
                        leave_dirs_open = false,
                    },
                },
            },
        })
        vim.keymap.set("n", "<leader>n", ":Neotree reveal<CR>")
    end,
}

-- return {
--     "preservim/nerdtree",
--     version = "*",
--     lazy = false,
--     config = function()
--         -- require("nvim-tree").setup({})
--         vim.keymap.set("n", "<leader>n", ":NERDTreeFind<CR>")
--     end,
--  }

