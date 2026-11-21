# Security notes

The intake boundary accepts only `https://github.com/{owner}/{repo}/pull/{number}` and constructs provider URLs from parsed components, preventing arbitrary redirects and SSRF through submitted URLs. Private-source AI transmission remains disabled by default (`PRISM_ALLOW_PRIVATE_AI=false`). Secrets belong in environment configuration and are excluded by `.gitignore`.
