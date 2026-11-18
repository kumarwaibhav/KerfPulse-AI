$ErrorActionPreference = 'Stop'
Set-Location (Split-Path $PSScriptRoot -Parent)
$expectedName = 'Kumar Waibhav Akshat'
$expectedEmail = '130293310+kumarwaibhav@users.noreply.github.com'
$expectedRemote = 'https://github.com/kumarwaibhav/KerfPulse-AI.git'
if ((& gh api user --jq .login) -ne 'kumarwaibhav' -or $LASTEXITCODE -ne 0) { throw 'GitHub must authenticate as kumarwaibhav' }
if ((& git config user.name) -ne $expectedName -or (& git config user.email) -ne $expectedEmail) { throw 'Local Git identity differs from owner-approved identity' }
if ((& git branch --show-current) -ne 'main') { throw 'Publish only audited main branch' }
if ((& git remote get-url --push origin) -ne $expectedRemote) { throw 'Unexpected publication destination' }
if (@(& git status --porcelain).Count -ne 0) { throw 'Commit reviewed changes before publication' }
$expected = "$expectedName|$expectedEmail|$expectedName|$expectedEmail"
# Keep the already published snapshot intact; require verified owner identity on every later commit.
# Its configured email linked to another profile, although push credentials and displayed names were correct.
$publishedBaseline = '487fc2892d5514334318a71feda9dc4de60182f9'
& git merge-base --is-ancestor $publishedBaseline main
if ($LASTEXITCODE -ne 0) { throw 'Published baseline missing; review lineage before publication' }
foreach ($identity in (& git log --format='%an|%ae|%cn|%ce' "$publishedBaseline..main")) {
    if ($identity -ne $expected) { throw 'Unapproved author/committer in publication history; review locally' }
}
$previousPrompt = $env:GIT_TERMINAL_PROMPT
try {
    $env:GIT_TERMINAL_PROMPT = '0'
    # Reset other helpers for this invocation; use the verified active gh account.
    & git -c 'credential.helper=' -c 'credential.helper=!gh auth git-credential' push --set-upstream origin main
    if ($LASTEXITCODE -ne 0) { throw 'Publication failed; no force push attempted' }
} finally { $env:GIT_TERMINAL_PROMPT = $previousPrompt }
