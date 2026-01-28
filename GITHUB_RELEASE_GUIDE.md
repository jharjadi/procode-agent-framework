# GitHub Release Guide - Step by Step

This guide walks you through creating the v0.1.0 public release for ProCode Agent Framework.

## Prerequisites

- GitHub CLI installed (`brew install gh` on macOS)
- Authenticated with GitHub (`gh auth login`)
- All changes committed and pushed to master

## Step 1: Create the GitHub Release

### Option A: Using GitHub CLI (Recommended)

```bash
# Create the release using the prepared content
gh release create v0.1.0 \
  --title "Initial public reference release (v0.1.0)" \
  --notes-file GITHUB_RELEASE_v0.1.0.md \
  --latest
```

### Option B: Using GitHub Web Interface

1. Go to: https://github.com/YOUR_USERNAME/procode-agent-framework/releases/new
2. Tag version: `v0.1.0`
3. Release title: `Initial public reference release (v0.1.0)`
4. Copy content from `GITHUB_RELEASE_v0.1.0.md` into the description
5. Check "Set as the latest release"
6. Click "Publish release"

## Step 2: Star Your Own Repository

```bash
# Star the repo (breaks the zero-star effect)
gh repo star YOUR_USERNAME/procode-agent-framework
```

Or via web: Click the ⭐ Star button on your repo page.

## Step 3: Enable GitHub Discussions

### Via GitHub CLI:
```bash
gh repo edit --enable-discussions
```

### Via Web Interface:
1. Go to Settings → General
2. Scroll to "Features"
3. Check "Discussions"
4. Click "Set up discussions"

## Step 4: Create the Seeded Discussion

### Via Web Interface (Required):
1. Go to your repo's Discussions tab: https://github.com/jharjadi/procode-agent-framework/discussions
2. Click "New discussion"
3. Select "Announcements" category
4. Title: `Design Trade-offs: Determinism vs LLM Routing`
5. Copy content from `GITHUB_DISCUSSION_SEED.md` and paste into the body
6. Click "Start discussion"

**Note:** The `gh` CLI doesn't support discussions in your version, so use the web interface.

## Step 5: Pin the Repository (Optional)

1. Go to your GitHub profile: https://github.com/YOUR_USERNAME
2. Click "Customize your pins"
3. Select `procode-agent-framework`
4. Click "Save pins"

## Step 6: Wait 24-48 Hours

**Do NOT:**
- Repost everywhere immediately
- Push more commits right away
- Explain yourself defensively in comments

**Let the repo breathe.** Silence after a clean announcement is a power move.

## Verification Checklist

After completing the steps above, verify:

- [ ] Release v0.1.0 is visible at `/releases`
- [ ] Release is marked as "Latest"
- [ ] Repository has at least 1 star (yours)
- [ ] Discussions are enabled
- [ ] Seeded discussion is posted in Announcements
- [ ] Repository is pinned on your profile (optional)

## What Happens Next?

Monitor for:
- Stars and watchers
- Discussion comments
- Issues opened
- Fork activity

Respond thoughtfully to genuine questions, but don't feel obligated to respond to everything immediately.

## Notes

- The release content is in `GITHUB_RELEASE_v0.1.0.md`
- The discussion seed is in `GITHUB_DISCUSSION_SEED.md`
- These files can be deleted after the release is created, or kept for reference

---

**Remember:** This is a reference implementation. The goal is to attract thoughtful engineers who want to learn, not to maximize stars or hype.
