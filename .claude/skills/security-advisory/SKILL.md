---
name: security-advisory
description: Draft or review a GitHub security advisory (GHSA) for Read the Docs. Use when writing the summary, description, or metadata of a new advisory, or checking a draft before it's published.
---

# Security advisories

Advisories are filed on `readthedocs/readthedocs.org`, including those for
the private Business code, `ext-theme`, and `readthedocs-builder`.
Don't create, edit, or publish an advisory on GitHub on your own initiative;
only do so when the user explicitly asks. When they do, you can create or update
a draft advisory with `gh` (for example, `gh api --method POST
repos/readthedocs/readthedocs.org/security-advisories`). Publishing an advisory
discloses it publicly and can't be undone, so confirm with the user before
publishing, even after they've asked you to create the draft. You can also just
write the draft for the user to paste, or review the one they point you to
(`gh api repos/readthedocs/readthedocs.org/security-advisories/<GHSA-ID>`).

## Metadata

- **Title**: `<Weakness> <in|via|on> <component>`, sentence case, no period.
  Append ` on Read the Docs Business` when only Business is affected.
  Examples: "Untrusted search path on builders",
  "Exposure of private SSH key on Read the Docs Business".
- **Ecosystem**: `pip` — GitHub's canonical name for the Python ecosystem (PyPI);
  For an app not published on PyPI this field is nominal (no dependency matching),
  and the package name is a free-text label.
- **Package**: `Read the Docs` if the community code is affected (even if Business is too),
  `Read the Docs Business` if only the private code is affected.
- **Affected versions**: `<YYYY.MM.DD`, the release that ships the fix.
  If the bug was introduced in a known release, use `>=X; <YYYY.MM.DD`.
- **Patched versions**: `YYYY.MM.DD`.
- **Severity**: CVSS 3.1 vector.
- **CWE**: the most specific one that fits.
- **Credits**: `finder` for our team, `reporter` for outside reporters.

## Description

Copy the template, pick one variant per `{...}` choice, and delete the rest.

```markdown
### Impact

This vulnerability could have allowed an attacker to <what they could do, in user terms>. <Limits: what access the key/token had, what wasn't exposed.>

In order to exploit this vulnerability, the attacker must <preconditions>.

<Optional: one paragraph on how it worked, without exploit steps.>

{Users of https://app.readthedocs.org/ and https://app.readthedocs.com/ do not need to take any further action, we have taken measures to ensure that the security issue is now fully fixed.
| Users of https://app.readthedocs.org/ are not affected, as <reason>. Users of https://app.readthedocs.com/ do not need to take any further action, we have taken measures to ensure that the security issue is now fully fixed.}

This issue was {discovered by a member of our team | reported by <Full Name> | discovered by Anthropic's [oss-scanner](https://github.com/anthropics/oss-scanner) (tracked as ANT-YYYY-XXXXXXXX)}, and we have seen no signs that this vulnerability was exploited in the wild.

### Custom installations

{We don't officially support custom installations of Read the Docs, but if you are using a custom installation, we recommend you to upgrade.
| This vulnerability was present in our private version of Read the Docs, custom installations aren't affected.}

### References

- https://github.com/readthedocs/readthedocs.org/commit/<sha>

{Other fixes have been applied in our private code, we can't share those patches publicly.
| This vulnerability has been fixed in our private code, we can't share this patch publicly.}

### For more information

If you have any questions or comments about this advisory, email us at [security@readthedocs.org](mailto:security@readthedocs.org) ([PGP](https://docs.readthedocs.io/page/security.html#pgp-key))
```

## Checklist

- The impact is written for a user deciding whether they were affected, not for a developer.
- No proof of concept, payloads, or step-by-step exploitation.
- Use current product names and domains: "Read the Docs Business", `app.readthedocs.org`, `app.readthedocs.com`.
- References point to the fix commit, not the pull request, and not to `main`.
  For fixes in `ext-theme` or `readthedocs-builder`, link the commit in that repository
  (`https://github.com/readthedocs/<repo>/commit/<sha>`).
- Replace every placeholder, like `[commit]`, before publishing.
- The contact link is `mailto:`, with the PGP link next to it.
- Spell-check
