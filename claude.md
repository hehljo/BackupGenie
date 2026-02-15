# Claude Code Guidelines for BackupGenie

## IMPORTANT: No Claude References in Code

**Effective Date:** November 16, 2025

### Strict Rules:

1. **No Claude/Anthropic References**
   - Do NOT add "Generated with Claude Code" in commits
   - Do NOT add "Co-Authored-By: Claude" in commits
   - Do NOT mention Claude or Anthropic in any code files
   - Do NOT mention Claude in documentation unless specifically about AI tooling

2. **Git Commit Messages**
   - Use standard commit messages without AI attribution
   - Focus on what was changed, not who/what made the change
   - Example: "Add password change endpoint" instead of "🤖 Generated with Claude Code"

3. **Code Comments**
   - Write comments as if written by a human developer
   - Avoid meta-references to AI assistance
   - Focus on explaining the code, not its origin

4. **Documentation**
   - Write docs in first-person plural ("we", "our")
   - Avoid mentioning the development process unless relevant
   - Focus on user-facing information

### Exceptions:

- This file (claude.md) - internal development notes
- .gitignore or .claudeignore - configuration files
- Private development notes not committed to the repository

### Reasoning:

- Users don't need to know how code was created
- Focus should be on code quality, not tools used
- Professional appearance in public repository
- Avoid confusion about project ownership and contributions

---

**Last Updated:** November 16, 2025
