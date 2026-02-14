# Terms of Use

<p align="left">
  <a href="TERMS_OF_USE.md">Русская версия</a> •
  <a href="SECURITY_EN.md">Security</a>
</p>

Repo Inspector is an open-source tool that evaluates GitHub repositories via API.
By using this project, you agree to the terms below.

## 1. Purpose

- The project is intended for repository quality and transparency assessment.
- It is not intended for unauthorized access to third-party data.
- It does not guarantee perfect accuracy and does not replace full security audits.

## 2. Acceptable use

Allowed:

- analyzing your own and public repositories;
- research and educational usage;
- quality gate automation in CI/CD.

Prohibited:

- bypassing GitHub API limits/restrictions;
- violating laws, GitHub rules, or third-party rights;
- intentionally submitting malicious content to this project.

## 3. Tokens and access

- User-provided GitHub token in UI/API is used only for the current scan request.
- By design, tokens are not stored in DB rows, report files, or exports.
- Users are responsible for token scopes and rotation.

## 4. Data and privacy

- Repositories are analyzed via GitHub API without cloning or code execution.
- Reports contain only API-visible data and derived metrics.
- User is responsible for lawful processing of the target repository data.

## 5. Disclaimer

Software is provided "as is", without warranties of any kind, express or implied.
Contributors are not liable for direct or indirect damages arising from use
or inability to use the project, to the extent permitted by applicable law.

## 6. Changes to terms

These terms may be updated as the project evolves.
The latest version in the repository is authoritative.

## 7. Acceptance

If you use Repo Inspector, you accept these terms.
If you disagree, stop using the software.
