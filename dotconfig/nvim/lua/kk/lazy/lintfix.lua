-- Async Linting Engine
-- currently only used for fixers
return {
    'dense-analysis/ale',
    config = function()
        local g = vim.g

        -- g.ale_ruby_rubocop_auto_correct_all = 1

        g.ale_linters = {elixir = {'credo'}}

        g.ale_fixers = {
            ["*"] = {'remove_trailing_lines', 'trim_whitespace'},
            elixir = {'mix_format'},
            lua = {'lua-format'},
            javascript = {'prettier'},
            json = {'prettier'}
        }

        g.ale_fix_on_save = 1

        -- disable LSP so that can be handled by other plugins
        g.ale_disable_lsp = 1
    end
}

