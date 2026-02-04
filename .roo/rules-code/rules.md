IMPORTANT WORKFLOW RULES:
1. If a DEVELOPMENT_RULES.md file exists in the project root, read it FIRST before starting any task
2. NEVER commit code before testing it thoroughly
3. ALWAYS use project-specific scripts (like ./push-to-dockerhub.sh) instead of direct commands
4. Follow the workflow: Test → Verify → Commit → Build → Deploy
5. When making changes, always test locally or in Docker before committing
6. After fixing a mistake, capture the learning: `make update-rules MSG="what you learned"`
7. Check project notes in docs/project-notes/ for context before starting major work
8. Run `make validate-rules` before major changes or deployments

Check for DEVELOPMENT_RULES.md, README.md, or CONTRIBUTING.md at the start of each task for project-specific rules.

ENHANCED RULES SYSTEM:
- Use `make update-rules MSG="learning"` to capture mistakes and insights
- Use `make validate-rules` to check compliance with development rules
- Check docs/lessons-learned/ for past mistakes to avoid
- Check docs/project-notes/ for task-specific context
- Update project notes as you work, not after completion
2. Test the enhanced rules system after implementation
