## Description
<!-- Provide a brief description of the changes in this PR -->

## Related Issue
<!-- Link to the issue this PR addresses, if applicable -->
Closes #

## Type of Change
<!-- Mark the relevant option with an "x" -->
- [ ] Bug fix (non-breaking change which fixes an issue)
- [ ] New feature (non-breaking change which adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] Documentation update
- [ ] Infrastructure/CI change
- [ ] Performance improvement
- [ ] Code refactoring

## Checklist

### Testing
- [ ] All existing tests pass locally
- [ ] I have added tests that prove my fix is effective or that my feature works
- [ ] New and existing unit tests pass locally with my changes
- [ ] I have performed manual testing of the changes
- [ ] Testing instructions are included below (if applicable)

### Code Quality
- [ ] My code follows the style guidelines of this project
- [ ] I have performed a self-review of my own code
- [ ] I have commented my code, particularly in hard-to-understand areas
- [ ] My changes generate no new warnings or errors
- [ ] I have run `black` and `flake8` on Python code (backend)
- [ ] I have run `npm run lint` on JavaScript/React code (frontend)

### Git LFS
- [ ] Large audio files (*.wav, *.flac, *.mp3) are tracked with Git LFS
- [ ] No files larger than 100MB are committed directly to the repository
- [ ] I have run `git lfs status` to verify LFS tracking

### CI/CD
- [ ] All CI checks are passing (lint, test, etc.)
- [ ] GitHub Actions workflows complete successfully
- [ ] No breaking changes to existing workflows or deployment

### Documentation
- [ ] I have updated relevant documentation (README, API docs, etc.)
- [ ] I have added/updated docstrings for new functions and classes
- [ ] Breaking changes are documented in the PR description

### Code Review
- [ ] I have requested review from code owners (CODEOWNERS file)
- [ ] All review comments have been addressed
- [ ] I have added a clear PR title and description

## Testing Instructions
<!-- Provide step-by-step instructions for testing this PR -->
1. 
2. 
3. 

## Screenshots (if applicable)
<!-- Add screenshots or GIFs demonstrating the changes -->

## Additional Notes
<!-- Any additional information that reviewers should know -->

## Deployment Notes
<!-- Any special considerations for deployment -->
- [ ] Database migrations required
- [ ] Environment variables changed/added
- [ ] External service dependencies added
- [ ] Deployment order matters (e.g., backend before frontend)
