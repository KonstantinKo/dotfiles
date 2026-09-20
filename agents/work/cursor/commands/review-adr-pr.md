# review-adr-pr

Please review the changes made by this branch vs the state of main that it was branched off of.

Guidelines:

- docs/principles - should contain high level principles, made for human consumption, used for onboarding or optional on-demand context for LLMs
- docs/decisions and docs/deviations - see docs/README.md
- docs/guides - also made for humans, used for onboarding of new colleagues, can explain principles or other concepts more in detail, should only exist when there's significantly more to tell than the instruction already does
- .github/instructions - are for copilot (but can be read by humans), they should be concise enough to conserve tokens and can deal with implementation specifics

All of these are optional to have. Having something is better than having nothing. Though having superfluous things is worse.
There shouldn't be too much duplication of content.
